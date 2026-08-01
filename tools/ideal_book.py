#!/usr/bin/env python3
"""
Ideal book — the "leader-pullback swing" model (v3 candidate, hindsight-derived
from ideal-swing-model-2026-07-15). Runs as a THIRD parallel book next to the
gated book of record and the every-signal benchmark.

Same rules engine/exits as the gated book (v3: 50-SMA trend-hold, disaster stop
-12%, day-only stop-limit fills, cooldown, group cap, pilots ×½ in NEUTRAL).
Three hindsight changes, from what our trade history showed worked:

  1. STOCKS ONLY  — no ETFs (every ETF we held became stale dead money).
  2. NEAR SUPPORT — trigger must be <= IDEAL_EXT_MAX (5%) above the 21-day SMA
     (vs 8% gated); stretched pivots produced our same-day stop-outs.
  3. CONCENTRATE  — <= IDEAL_MAX_POS (8) names; orders 4/2/0 by regime.

CAVEAT: rules were chosen after seeing which trades worked (in-sample / overfit
risk). Run in parallel as a paper book; do not promote to book-of-record until
it survives an out-of-sample confirmed-uptrend stretch. See the analysis page.

Importable: simulate(asof) -> (open_pos, closed); held_tickers() -> set.
Usage: python tools/ideal_book.py
"""
import sys, os, re, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import backtest, regime, classify
import validate_list as vl
import gated_book

START, END = "<!-- IDEAL:START -->", "<!-- IDEAL:END -->"

IDEAL_EXT_MAX = 0.05     # trigger must be <= 5% above the 21-day SMA (near support)
IDEAL_MAX_POS = 8        # tighter concentration than the gated book's 12


def allowed(score):
    """Regime score -> (max orders, pilot?). Slightly tighter than gated (4 vs 5)."""
    if score >= 7:
        return 4, False
    if score >= 4:
        return 2, True
    return 0, True


def simulate(asof=None):
    spy = vl.series("SPY")
    open_pos, closed, skipped, daily = [], [], [], []
    cooldown = {}
    gcap = max(1, int(IDEAL_MAX_POS * uw.GROUP_CAP))

    for d in gated_book.all_dates():
        dd = dt.date.fromisoformat(d)
        if asof is not None and dd > asof:
            break

        still = []
        for p in open_pos:
            if p.get("exit_date") and dt.date.fromisoformat(p["exit_date"]) < dd:
                closed.append(p)
                if p["ret"] <= 0 and "stop" in (p.get("exit_kind") or ""):
                    cooldown[p["tkr"]] = dt.date.fromisoformat(p["exit_date"])
            else:
                still.append(p)
        open_pos = still

        try:
            score, _v, _a, _c = regime.compute(asof=dd)
        except Exception:
            score = 8
        n_orders, pilot = allowed(score)
        daily.append(dict(date=d, score=score, orders=0, filled=0, pilot=pilot))
        if n_orders == 0:
            continue

        try:
            rows, _ = backtest.sim_list(d, asof=asof)
        except Exception:
            continue
        sim = {r["tkr"]: r for r in rows}
        held = {p["tkr"] for p in open_pos}

        cands = []
        for tkr, entry in uw.parse_entries(backtest.find_raw(d)):
            r = sim.get(tkr)
            if not r or r["ret"] is None or tkr in held:
                continue
            grp, is_etf = classify.group(tkr)
            if is_etf:
                skipped.append((d, tkr, "ETF (stocks only)")); continue
            cd = cooldown.get(tkr)
            if cd and (dd - cd).days <= uw.COOLDOWN_DAYS:
                skipped.append((d, tkr, f"cooldown (stopped {cd})")); continue
            passed, _f = vl.check(tkr, spy, asof=dd)
            if passed != 8:
                skipped.append((d, tkr, f"TT {passed if passed is not None else '—'}/8")); continue
            c = vl.series(tkr, asof=dd)
            ma21 = float(c.rolling(21).mean().iloc[-1])
            ext = entry / ma21 - 1
            if ext > IDEAL_EXT_MAX:
                skipped.append((d, tkr, f"extended +{ext*100:.1f}% vs 21MA (>{int(IDEAL_EXT_MAX*100)}%)")); continue
            cands.append(dict(tkr=tkr, entry=entry, near=float(c.iloc[-1]) / entry, sim=r, grp=grp))

        cands.sort(key=lambda x: -x["near"])
        for cnd in cands:
            if daily[-1]["orders"] >= n_orders or len(open_pos) >= IDEAL_MAX_POS:
                break
            if sum(1 for p in open_pos if p["group"] == cnd["grp"]) >= gcap:
                skipped.append((d, cnd["tkr"], f"group cap ({cnd['grp']})")); continue
            daily[-1]["orders"] += 1
            r = cnd["sim"]
            if r["status"] == "not triggered":
                skipped.append((d, cnd["tkr"], "order placed, never triggered")); continue
            daily[-1]["filled"] += 1
            w = uw.FULL_POSITION_PCT * (uw.PILOT_FRACTION if pilot else 1.0)
            open_pos.append(dict(r, list_date=d, weight=w, group=cnd["grp"], pilot=pilot))

    return open_pos, closed, skipped, daily


def held_tickers():
    o, _c, _s, _d = simulate()
    return {p["tkr"] for p in o}


def build_block(open_pos, closed, equity=None):
    port = sum(p["ret"] * p["weight"] for p in open_pos + closed)
    realized = sum(p["ret"] * p["weight"] for p in closed)
    unreal = sum(p["ret"] * p["weight"] for p in open_pos)
    lines = [f"_Paper v3 candidate ([[ideal-swing-model-2026-07-15]]): stocks only, trigger ≤{int(IDEAL_EXT_MAX*100)}% "
             f"above the 21-SMA (near support), ≤{IDEAL_MAX_POS} names, orders 4/2/0 by regime, pilots ×"
             f"{uw.PILOT_FRACTION} in NEUTRAL. In-sample — not the book of record; run in parallel._", ""]
    lines.append("| Ticker | From list | Size | Group | Entered | Fill | Status | Ret % | Equity % |")
    lines.append("| --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |")
    for p in sorted(open_pos, key=lambda x: -x["ret"]) + sorted(closed, key=lambda x: x.get("exit_date") or ""):
        size = f"{p['weight']*100:.2f}%" + (" (pilot)" if p["pilot"] else "")
        lines.append(f"| [[{p['tkr'].lower()}]] | {p['list_date']} | {size} | {p['group']} | "
                     f"{p['entry_date']} | {p['fill']:.2f} | {p['status']} | {p['ret']*100:+.2f}% | "
                     f"{p['ret']*p['weight']*100:+.2f}% |")
    dollar = f" ≈ ${port*equity:+,.0f}" if equity else ""
    lines.append(f"\n**Ideal book: {len(open_pos)} open + {len(closed)} closed · realized {realized*100:+.2f}% eq "
                 f"· unrealized {unreal*100:+.2f}% eq · total {port*100:+.2f}% of equity{dollar}**")
    return "\n".join(lines), port


def main():
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = float(re.sub(r"[,$\s]", "", eq_raw)) if eq_raw else None
    open_pos, closed, skipped, daily = simulate()
    block, port = build_block(open_pos, closed, equity)
    print(block.replace("[[", "").replace("]]", ""))

    ov = os.path.join(uw.WIKI, "overview.md")
    text = open(ov, encoding="utf-8").read()
    blk = f"{START}\n{block}\n{END}"
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), blk, text, flags=re.DOTALL)
        open(ov, "w", encoding="utf-8").write(text)
        print(f"\n[updated ideal-book block in {ov}]")
    else:
        print(f"\n[IDEAL markers not found in {ov} — add them to overview.md]")


if __name__ == "__main__":
    main()
