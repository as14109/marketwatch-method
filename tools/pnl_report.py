#!/usr/bin/env python3
"""
Total P&L report — realized + unrealized, across ALL ingested Key Lists,
with the trigger (entry) date of every position. One-off analysis tool
(not part of the daily routine).

Per list: every triggered signal with trigger date, fill, status,
realized %, unrealized %, total %, and $ P&L at the current full-position
size. Grand totals across all signals, plus the deduped one-position-per-
name book view (matches the open-positions tracker).

Writes wiki/analysis/pnl-report-<rundate>.md.
Usage: python tools/pnl_report.py
"""
import sys, glob, os, re, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import backtest

def main():
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = float(re.sub(r"[,$\s]", "", eq_raw)) if eq_raw else 1_000_000.0
    full = equity * uw.FULL_POSITION_PCT
    dates = sorted({m.group(1) for f in glob.glob(os.path.join(uw.RAW, "*key-list*.md"))
                    if (m := re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(f)))})
    run = dt.date.today().isoformat()

    md = [f"---\ntype: analysis\ntags: [pnl, backtest, realized, unrealized, review]\ncreated: {run}\n---\n",
          f"# Total P&L report — realized + unrealized (run {run})",
          f"All {len(dates)} Key Lists ({dates[0]} → {dates[-1]}) replayed under [[key-list-trade-rules]] v2 "
          f"(−{backtest.STOP*100:.0f}% stop, BE +{backtest.BE*100:.0f}%, sell ½ at +{backtest.T1*100:.0f}%, trail 9-EMA). "
          f"Every triggered signal sized at ${int(full):,} ({int(uw.FULL_POSITION_PCT*100)}% of ${int(equity):,}). "
          "Open positions marked to last close.\n",
          "> **Caveat:** lists overlap — the same name re-triggers across lists, so the all-signals totals "
          "over-commit capital. The deduped book view at the bottom is the realistic single-account picture.\n"]

    grand = dict(real=0.0, unreal=0.0, n=0, closed=0, open=0)
    print(f"TOTAL P&L — {len(dates)} lists, ${int(full):,}/position\n")
    for d in dates:
        try:
            rows, agg = backtest.sim_list(d)
        except Exception:
            continue
        trig = [r for r in rows if r["ret"] is not None and r["status"] != "not triggered"]
        if not trig:
            md.append(f"## {d}\n_no data / nothing triggered_\n"); continue
        md.append(f"## {d}")
        md.append("| Ticker | Triggered on | Fill | Status | Realized % | Unreal. % | Total % | $ P&L |")
        md.append("| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |")
        lr = lu = 0.0
        for r in sorted(trig, key=lambda x: -x["ret"]):
            real = r.get("realized", 0.0) or 0.0
            unreal = r["ret"] - real
            dollars = r["ret"] * full
            lr += real; lu += unreal
            md.append(f"| {r['tkr']} | {r['entry_date']} | {r['fill']:.2f} | {r['status']} | "
                      f"{real*100:+.2f}% | {unreal*100:+.2f}% | {r['ret']*100:+.2f}% | {dollars:+,.0f} |")
            grand["n"] += 1
            grand["closed" if r["status"] == "closed" else "open"] += 1
        grand["real"] += lr; grand["unreal"] += lu
        tot = lr + lu
        line = (f"{d}: {len(trig)} signals | realized {lr*full:+,.0f} | unreal {lu*full:+,.0f} | total {tot*full:+,.0f}")
        print(line)
        md.append(f"\n**List total: realized ${lr*full:+,.0f} · unrealized ${lu*full:+,.0f} · ${tot*full:+,.0f}**\n")

    g = grand
    tot = g["real"] + g["unreal"]
    summary = [
        f"Signals: {g['n']} triggered ({g['closed']} closed, {g['open']} still open)",
        f"Realized P&L:   ${g['real']*full:+,.0f}",
        f"Unrealized P&L: ${g['unreal']*full:+,.0f}",
        f"TOTAL P&L:      ${tot*full:+,.0f}  ({tot*full/equity*100:+.2f}% of ${int(equity):,} — overlapping-capital basis)",
    ]
    print("\n" + "\n".join(summary))
    md.append("## Grand total — all signals (overlapping capital)")
    md += ["- " + s for s in summary]

    # deduped book (one position per name, earliest trigger) — realistic account view
    import open_positions
    pos = open_positions.collect()
    if pos:
        breal = sum((r.get("realized", 0.0) or 0.0) for r in pos)
        bunreal = sum(r["ret"] - (r.get("realized", 0.0) or 0.0) for r in pos)
        md.append("\n## Deduped open book (one position per name — matches the open-positions tracker)")
        md.append(f"- {len(pos)} open positions · realized-so-far ${breal*full:+,.0f} · "
                  f"unrealized ${bunreal*full:+,.0f} · total ${(breal+bunreal)*full:+,.0f} "
                  f"({(breal+bunreal)*full/equity*100:+.2f}% of equity)")
        print(f"\nDeduped open book: {len(pos)} positions | realized {breal*full:+,.0f} | "
              f"unreal {bunreal*full:+,.0f} | total {(breal+bunreal)*full:+,.0f}")

        # by entry week
        weeks = {}
        for r in pos:
            d = dt.date.fromisoformat(r["entry_date"])
            monday = d - dt.timedelta(days=d.weekday())
            w = weeks.setdefault(monday, dict(n=0, real=0.0, unreal=0.0, best=None, worst=None))
            real = r.get("realized", 0.0) or 0.0
            w["n"] += 1; w["real"] += real; w["unreal"] += r["ret"] - real
            if w["best"] is None or r["ret"] > w["best"][1]: w["best"] = (r["tkr"], r["ret"])
            if w["worst"] is None or r["ret"] < w["worst"][1]: w["worst"] = (r["tkr"], r["ret"])
        md.append("\n### Deduped book by entry week")
        md.append("| Entry week | Pos | Realized | Unreal. | Total | Best / worst |")
        md.append("| --- | ---: | ---: | ---: | ---: | --- |")
        for monday in sorted(weeks):
            w = weeks[monday]; tot = (w["real"] + w["unreal"]) * full
            md.append(f"| wk of {monday} | {w['n']} | ${w['real']*full:+,.0f} | ${w['unreal']*full:+,.0f} | "
                      f"**${tot:+,.0f}** | {w['best'][0]} {w['best'][1]*100:+.1f}% / {w['worst'][0]} {w['worst'][1]*100:+.1f}% |")

    md.append("\n_Not financial advice. Simulated fills on daily bars; see backtest modeling notes._")
    out = os.path.join(uw.WIKI, "analysis", f"pnl-report-{run}.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"\n[wrote {out}]")

if __name__ == "__main__":
    main()
