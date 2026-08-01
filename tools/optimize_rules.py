#!/usr/bin/env python3
"""
Stop-loss / take-profit parameter sweep over ALL ingested Key Lists.

Replays every list through the backtest engine (tools/backtest.py — corrected
gap fills + vendor-data guards) for a grid of (stop%, target%) combinations.
Breakeven trigger is scaled with the target (BE = ~70% of T1, floored at the
stop) to keep the rule structure intact. Entry logic is unchanged, so the set
of triggered signals is identical across combos — only exits differ.

Outputs a ranked grid (win rate, avg return/trade, cumulative P&L across all
signals at 10%/name) and writes wiki/analysis/stop-target-optimization-<date>.md.

Caveats printed with the results: one month of data, overlapping lists, mostly
open positions, single regime cycle — treat as evidence, not truth.

Usage: python tools/optimize_rules.py
"""
import sys, glob, os, re, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import backtest

# ---- cache yfinance downloads so the grid doesn't re-fetch per combo ----
_cache = {}
_orig_download = backtest.yf.download
def _cached_download(tkr, *a, **k):
    if tkr not in _cache:
        _cache[tkr] = _orig_download(tkr, *a, **k)
    df = _cache[tkr]
    return df.copy() if df is not None else None
backtest.yf.download = _cached_download

STOPS   = [0.02, 0.03, 0.04, 0.05]
TARGETS = [0.05, 0.07, 0.09, 0.12, 0.15]

def all_dates():
    return sorted({m.group(1) for f in glob.glob(os.path.join(uw.RAW, "*key-list*.md"))
                   if (m := re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(f)))})

def sweep(dates):
    results = []
    for s in STOPS:
        for t in TARGETS:
            if t <= s:      # need reward >= risk to be worth testing
                continue
            backtest.STOP, backtest.T1 = s, t
            backtest.BE = max(s, round(0.7 * t, 3))   # breakeven arms at ~70% of target
            trades = []
            for d in dates:
                try:
                    _, agg = backtest.sim_list(d)
                except Exception:
                    agg = None
                if agg:
                    trades += agg["trades"]
            n = len(trades)
            if not n:
                continue
            wins = sum(1 for r in trades if r["ret"] > 0)
            avg = sum(r["ret"] for r in trades) / n
            port = sum(r["ret"] * backtest.FULL_W for r in trades)
            results.append(dict(stop=s, t1=t, n=n, winr=wins / n, avg=avg, port=port))
    return results

def main():
    dates = all_dates()
    run = dt.date.today().isoformat()
    print(f"Sweeping {len(STOPS)}x{len(TARGETS)} stop/target grid over {len(dates)} Key Lists "
          f"({dates[0]} → {dates[-1]}); BE = ~70% of target.\n")
    res = sweep(dates)
    res.sort(key=lambda r: r["avg"], reverse=True)
    print(f"{'STOP':>6}{'TARGET':>8}{'BE~':>6}{'N':>5}{'WIN%':>7}{'AVG/trade':>11}{'CUM P&L':>10}")
    for r in res:
        print(f"{r['stop']*100:>5.0f}%{r['t1']*100:>7.0f}%{max(r['stop'],0.7*r['t1'])*100:>5.1f}%"
              f"{r['n']:>5}{r['winr']*100:>6.0f}%{r['avg']*100:>+10.2f}%{r['port']*100:>+9.2f}%")

    md = [f"---\ntype: analysis\ntags: [backtest, optimization, stops, targets, expectancy]\ncreated: {run}\n---\n",
          f"# Stop/target optimization — run {run}",
          f"Grid sweep over {len(dates)} Key Lists ({dates[0]} → {dates[-1]}), ~{res[0]['n'] if res else 0} signals per combo. "
          "Engine: corrected gap fills + vendor-data guards; BE arms at ~70% of target; trailing 9-EMA unchanged. "
          "Entries identical across combos — only exits differ.\n",
          "| Stop | Target | N | Win% | Avg/trade | Cum P&L (10%/name) |", "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in res:
        md.append(f"| −{r['stop']*100:.0f}% | +{r['t1']*100:.0f}% | {r['n']} | {r['winr']*100:.0f}% | "
                  f"{r['avg']*100:+.2f}% | {r['port']*100:+.2f}% |")
    md.append("\n## Caveats\n- ~3 weeks of data, one regime cycle (chop → selloff → rebound → whipsaw); "
              "lists overlap; most positions open (marked to last close); daily bars.\n"
              "- Per [[expectancy]]: don't loosen stops for volatility; the tighter the stop, the more "
              "timing accuracy required. Cross-check any change against [[key-list-trade-rules]] and re-run monthly.")
    out = os.path.join(uw.WIKI, "analysis", f"stop-target-optimization-{run}.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"\n[wrote {out}]")

if __name__ == "__main__":
    main()
