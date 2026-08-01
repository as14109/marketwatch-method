#!/usr/bin/env python3
"""
Gated book — the DISCIPLINED parallel simulation (process-improvements-2026-07-09).

The every-signal book (open_positions.py) takes every trigger to measure list
quality. This book simulates actually following our own rules, walking every
ingested Key List chronologically and applying, per list date:

  1. Regime gate (point-in-time `regime.compute(asof)`): score 7-8 -> up to 5
     orders, 4-6 -> 2 pilot orders at half size, <=3 -> 0.
  2. Trend-Template hard filter: only 8/8 passers (point-in-time).
  3. Extension filter: skip triggers > EXT_MAX_PCT above the 21-day SMA.
  4. Re-entry cooldown: skip names that stopped out of THIS book at a loss
     within COOLDOWN_DAYS calendar days.
  5. Concentration: MAX_POSITIONS total; GROUP_CAP per sector; ETFs one group
     at ETF_FRACTION size. No adds (one position per name, like the main book).

Candidates that survive are ranked by closeness to the pivot (last close /
entry) and the top N get "orders" — an order consumes a slot whether or not it
fills. Fills/exits reuse backtest.sim_one outcomes (same rules engine).

Writes the summary between the GATED markers in overview.md; importable:
simulate() -> (open_pos, closed, skipped, daily) for the emailed report.

Usage: python tools/gated_book.py
"""
import sys, os, re, glob, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import backtest, regime, classify
import validate_list as vl

START, END = "<!-- GATED:START -->", "<!-- GATED:END -->"


def all_dates():
    return sorted({m.group(1) for f in glob.glob(os.path.join(uw.RAW, "*key-list*.md"))
                   if (m := re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(f)))
                   and m.group(1) >= uw.MODEL_START})   # book inception (July 1); June excluded


def allowed(score):
    """Regime score -> (max orders today, pilot sizing?)."""
    if score >= 7:
        return 5, False
    if score >= 4:
        return 2, True
    return 0, True


def simulate(asof=None):
    """`asof` (datetime.date) = stop processing lists after that date and mark all
    positions point-in-time at that close (used by tools/mtd_pnl.py)."""
    spy = vl.series("SPY")
    open_pos, closed, skipped, daily = [], [], [], []
    cooldown = {}          # tkr -> date of last losing stop-out in THIS book
    group_cap_n = max(1, int(uw.MAX_POSITIONS * uw.GROUP_CAP))

    for d in all_dates():
        dd = dt.date.fromisoformat(d)
        if asof is not None and dd > asof:
            break

        # roll positions whose exit happened before this list's trading day
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
            score, verdict, _, _ = regime.compute(asof=dd)
        except Exception:
            score, verdict = 8, "unavailable (ungated)"
        n_orders, pilot = allowed(score)
        day = dict(date=d, score=score, orders=0, filled=0, pilot=pilot)
        daily.append(day)
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
            if not r or r["ret"] is None:            # no usable price history
                continue
            if tkr in held:
                skipped.append((d, tkr, "already held"))
                continue
            cd = cooldown.get(tkr)
            if cd and (dd - cd).days <= uw.COOLDOWN_DAYS:
                skipped.append((d, tkr, f"cooldown (stopped {cd})"))
                continue
            passed, fails = vl.check(tkr, spy, asof=dd)
            if passed != 8:
                skipped.append((d, tkr, f"TT {passed if passed is not None else '—'}/8"))
                continue
            c = vl.series(tkr, asof=dd)
            ma21 = float(c.rolling(21).mean().iloc[-1])
            last = float(c.iloc[-1])
            ext = entry / ma21 - 1
            if ext > uw.EXT_MAX_PCT:
                skipped.append((d, tkr, f"extended +{ext*100:.1f}% vs 21MA"))
                continue
            cands.append(dict(tkr=tkr, entry=entry, near=last / entry, sim=r))

        cands.sort(key=lambda x: -x["near"])          # closest to the pivot first
        for cnd in cands:
            if day["orders"] >= n_orders:
                break
            if len(open_pos) >= uw.MAX_POSITIONS:
                skipped.append((d, cnd["tkr"], f"book full ({uw.MAX_POSITIONS})"))
                continue
            grp, is_etf = classify.group(cnd["tkr"])
            if sum(1 for p in open_pos if p["group"] == grp) >= group_cap_n:
                skipped.append((d, cnd["tkr"], f"group cap ({grp})"))
                continue
            day["orders"] += 1                        # an order consumes a slot, filled or not
            r = cnd["sim"]
            if r["status"] == "not triggered":
                skipped.append((d, cnd["tkr"], "order placed, never triggered"))
                continue
            day["filled"] += 1
            w = uw.FULL_POSITION_PCT
            if pilot:
                w *= uw.PILOT_FRACTION
            if is_etf:
                w *= uw.ETF_FRACTION
            open_pos.append(dict(r, list_date=d, weight=w, group=grp, etf=is_etf, pilot=pilot))

    return open_pos, closed, skipped, daily


def held_tickers():
    """Set of tickers currently open in the gated (book-of-record) sim.
    Used to flag watchlist names that are actually in the disciplined book."""
    open_pos, _closed, _skip, _daily = simulate()
    return {p["tkr"] for p in open_pos}


def build_block(open_pos, closed, daily, equity=None):
    port = sum(p["ret"] * p["weight"] for p in open_pos + closed)
    realized = sum(p["ret"] * p["weight"] for p in closed)
    lines = [f"_Disciplined parallel sim ([[process-improvements-2026-07-09]]): regime-gated order count, "
             f"TT-only, ≤+{int(uw.EXT_MAX_PCT*100)}% ext, {uw.COOLDOWN_DAYS}d cooldown, "
             f"≤{uw.MAX_POSITIONS} names, group cap {group_lbl()}, pilots ×{uw.PILOT_FRACTION} in NEUTRAL, "
             f"ETFs ×{uw.ETF_FRACTION}. Same fills/exits as the main sim._", ""]
    lines.append("| Ticker | From list | Size | Group | Entered | Fill | Status | Ret % | Equity % |")
    lines.append("| --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |")
    for p in sorted(open_pos, key=lambda x: -x["ret"]) + sorted(closed, key=lambda x: x.get("exit_date") or ""):
        size = f"{p['weight']*100:.2f}%" + (" (pilot)" if p["pilot"] else "")
        lines.append(f"| [[{p['tkr'].lower()}]] | {p['list_date']} | {size} | {p['group']} | "
                     f"{p['entry_date']} | {p['fill']:.2f} | {p['status']} | {p['ret']*100:+.2f}% | "
                     f"{p['ret']*p['weight']*100:+.2f}% |")
    dollar = f" ≈ ${port*equity:+,.0f}" if equity else ""
    lines.append(f"\n**Gated book: {len(open_pos)} open + {len(closed)} closed · "
                 f"realized {realized*100:+.2f}% eq · total {port*100:+.2f}% of equity{dollar}**")
    return "\n".join(lines), port


def group_lbl():
    return f"{int(uw.GROUP_CAP*100)}%"


def main():
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = float(re.sub(r"[,$\s]", "", eq_raw)) if eq_raw else None
    open_pos, closed, skipped, daily = simulate()
    block, port = build_block(open_pos, closed, daily, equity)
    print(block.replace("[[", "").replace("]]", ""))
    print(f"\nDaily gate: " + " · ".join(f"{x['date']}({x['score']}/8:{x['orders']}o/{x['filled']}f)"
                                         for x in daily))
    print(f"\nSkipped {len(skipped)} candidates. Last 15:")
    for d, t, why in skipped[-15:]:
        print(f"  {d} {t:6} {why}")

    ov = os.path.join(uw.WIKI, "overview.md")
    text = open(ov, encoding="utf-8").read()
    blk = f"{START}\n{block}\n{END}"
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), blk, text, flags=re.DOTALL)
        open(ov, "w", encoding="utf-8").write(text)
        print(f"\n[updated gated-book block in {ov}]")
    else:
        print(f"\n[GATED markers not found in {ov} — add them to overview.md]")


if __name__ == "__main__":
    main()
