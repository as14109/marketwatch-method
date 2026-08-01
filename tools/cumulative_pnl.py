#!/usr/bin/env python3
"""
Cumulative P&L across ALL ingested Key Lists (month/quarter-end review).

Backtests every MW/raw/*key-list*.md with the trade rules and aggregates. Reports:
  - per-list result (triggered, win rate, portfolio P&L at 10%/name)
  - overall across every triggered signal (treated as a $100k / 10% trade)

Caveat: lists overlap (the same name recurs), so this is NOT one clean portfolio
return — it's the strategy's aggregate result across all signals ("if you took
every trigger at full size"), which over-commits capital. Read it as expectancy,
not a single account curve. Writes wiki/analysis/cumulative-pnl-<rundate>.md.

Usage: python tools/cumulative_pnl.py
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

    per_list, all_trades = [], []
    for d in dates:
        try:
            rows, agg = backtest.sim_list(d)
        except Exception:
            rows, agg = [], None
        per_list.append((d, agg))
        if agg:
            all_trades += agg["trades"]

    md = [f"---\ntype: analysis\ntags: [backtest, cumulative, pnl, review]\ncreated: {run}\n---\n",
          f"# Cumulative P&L — all Key Lists (run {run})",
          f"Every ingested Key List backtested with exit v3 (hold to a close below the {backtest.TMA}-day SMA, "
          f"disaster stop −{backtest.DIS*100:.0f}%). Full position = {int(backtest.FULL_W*100)}% of ${int(equity):,} = ${int(full):,}. "
          f"Mostly open positions marked to last close.\n",
          "> **Caveat:** lists overlap (names recur), so this aggregates *every signal as a $100k trade* — "
          "it over-commits capital and is not one clean account curve. Read as strategy expectancy.\n",
          "## Per list", "| Key List | Triggered | Win rate | Portfolio P&L (10%/name) |",
          "| --- | ---: | ---: | ---: |"]
    print(f"Cumulative P&L — {len(dates)} Key Lists, full position = ${int(full):,}\n")
    print(f"{'LIST':12}{'TRIG':>8}{'WIN%':>7}{'P&L%':>8}")
    for d, a in per_list:
        if a:
            wr = 100*a["wins"]/a["trig"]
            print(f"{d:12}{a['trig']:>3}/{a['n']:<4}{wr:>6.0f}%{a['port']*100:>7.2f}%")
            md.append(f"| {d} | {a['trig']}/{a['n']} | {wr:.0f}% | {a['port']*100:+.2f}% |")
        else:
            print(f"{d:12}{'—':>8}")
            md.append(f"| {d} | — | — | — |")

    n = len(all_trades)
    if n:
        wins = sum(1 for r in all_trades if r["ret"] > 0)
        avg = sum(r["ret"] for r in all_trades)/n
        dollars = sum(r["ret"]*full for r in all_trades)
        port_avg = sum(a["port"] for _, a in per_list if a)/sum(1 for _, a in per_list if a)
        best = max(all_trades, key=lambda r: r["ret"]); worst = min(all_trades, key=lambda r: r["ret"])
        lines = [
            f"Total signals taken (triggered): {n}",
            f"Win rate: {wins}/{n} = {100*wins/n:.0f}%",
            f"Average return per trade: {avg*100:+.2f}%",
            f"Cumulative P&L (every trigger at ${int(full):,}): ${dollars:,.0f}  (realized+open)",
            f"Avg portfolio P&L per list (each as its own book): {port_avg*100:+.2f}%",
            f"Best: {best['tkr']} {best['ret']*100:+.1f}%  |  Worst: {worst['tkr']} {worst['ret']*100:+.1f}%",
        ]
        print("\n" + "\n".join(lines))
        md.append("\n## Overall (every triggered signal as a $%s trade)" % format(int(full), ","))
        md += ["- " + x for x in lines]
        md.append("\n_Educational only — not investment advice._")

    out = os.path.join(uw.WIKI, "analysis", f"cumulative-pnl-{run}.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"\n[wrote {out}]")

if __name__ == "__main__":
    main()
