#!/usr/bin/env python3
"""Export every trade taken in 2026 — both books — as JSON for the site's
members-only transaction-history page.

Two books:
  * gated      — the book of record (regime-gated, Trend-Template only, caps)
  * benchmark  — every triggered signal, no selection discipline, capital-capped

Each trade carries entry date/price, exit date/price, exit reason, % return and
$ P&L. Open positions are marked at the latest close and flagged `open`.

Runs on the DEFAULT 3-year price window — the same configuration period_pnl.py and
the daily routine use. Do NOT set pricecache.PERIOD_OVERRIDE here: the benchmark
admits signals chronologically until it hits the capital cap, so a wider window
changes which signals win the cap and produces a different book (a 5y run missed
the committed 2026 total by 19 points).

Writes web/data/transactions.json — deliberately OUTSIDE web/public/, because
anything under public/ is served statically and would be readable without a login.
The file is bundled into the members-only /api/transactions Function at deploy time.

Usage: python tools/export_transactions.py
"""
import os, sys, json, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_watchlist as uw
import gated_book, open_positions as op

YEAR = "2026"
OUT = os.path.join(uw.BASE, "web", "data", "transactions.json")   # NOT under public/


def _equity():
    raw = uw.env("MW_PORTFOLIO_EQUITY")
    if not raw:
        return 1_400_000.0
    import re
    return float(re.sub(r"[,$\s]", "", raw))


def _row(r, weight, equity):
    """Normalize one position/closed record into a transaction row."""
    ret = r.get("ret")
    if ret is None:
        return None
    closed = bool(r.get("exit_date"))
    return {
        "tkr": r["tkr"].upper(),
        "list_date": r.get("list_date"),
        "entry_date": r.get("entry_date"),
        "buy": round(r["fill"], 2) if r.get("fill") else None,
        "exit_date": r.get("exit_date"),
        "sell": round(r["exit_px"], 2) if r.get("exit_px") else (
            round(r["last"], 2) if r.get("last") else None),
        "exit_kind": r.get("exit_kind") or ("—" if closed else "open"),
        "status": "closed" if closed else "open",
        "size_pct": round(weight * 100, 2),
        "ret_pct": round(ret * 100, 2),
        "pnl_usd": round(ret * weight * equity),
    }


def _summary(rows):
    closed = [t for t in rows if t["status"] == "closed"]
    openp = [t for t in rows if t["status"] == "open"]
    wins = [t for t in closed if t["pnl_usd"] > 0]
    return {
        "trades": len(rows),
        "closed": len(closed),
        "open": len(openp),
        "wins": len(wins),
        "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else None,
        "realized_usd": sum(t["pnl_usd"] for t in closed),
        "unrealized_usd": sum(t["pnl_usd"] for t in openp),
        "total_usd": sum(t["pnl_usd"] for t in rows),
    }


def main():
    equity = _equity()
    full_w = uw.FULL_POSITION_PCT

    # --- book of record: per-position weight varies (pilots/ETFs are fractional)
    gpos, gclosed, _sk, _dr, _daily = gated_book.simulate()
    gated_rows = [x for x in (_row(r, r.get("weight", full_w), equity)
                              for r in gpos + gclosed) if x]

    # --- benchmark: every admitted signal at a full position
    bopen = op.collect()
    bclosed = op.collect_closed(bopen)
    bench_rows = [x for x in (_row(r, full_w, equity) for r in bopen + bclosed) if x]

    for rows in (gated_rows, bench_rows):
        rows.sort(key=lambda t: (t["entry_date"] or "", t["tkr"]))

    data = {
        "as_of": dt.date.today().isoformat(),
        "year": YEAR,
        "equity": equity,
        "full_position_usd": round(full_w * equity),
        "disclaimer": ("SIMULATED / BACKTESTED. No real trades were placed. Open positions are "
                       "marked at the latest close. Hypothetical results have inherent limitations "
                       "and are not indicative of future results. Educational only — not investment advice."),
        "books": {
            "gated": {"label": "Book of record (gated)",
                      "note": ("Regime-gated entries, Trend-Template only, extension and cooldown "
                               "limits, ≤12 names. Position size varies: full ≈7.14% of equity, "
                               "pilots and ETFs at half or quarter."),
                      "summary": _summary(gated_rows), "trades": gated_rows},
            "benchmark": {"label": "Every-signal benchmark",
                          "note": ("Every triggered signal, earliest entry per name, no Trend-Template "
                                   "and no regime gating — but still capital-capped at 12 concurrent "
                                   "positions. Every position is full size."),
                          "summary": _summary(bench_rows), "trades": bench_rows},
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)

    for k, b in data["books"].items():
        s = b["summary"]
        print(f"{b['label']:28} {s['trades']:3} trades ({s['closed']} closed / {s['open']} open) · "
              f"win {s['win_rate']}% · realized ${s['realized_usd']:+,} · total ${s['total_usd']:+,}")
    print(f"\n[wrote {OUT}]")


if __name__ == "__main__":
    main()
