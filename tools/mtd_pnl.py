#!/usr/bin/env python3
"""
MTD P&L — daily closing values for ALL THREE books (gated book of record,
paper ideal swing book, every-signal benchmark), month-to-date.

For every trading day of the current month, both books are re-simulated
point-in-time (`asof` = that close): entries/exits/marks use only price bars
up to that day. Rows show each book's cumulative P&L at that close and the
day-over-day change. The MTD line = latest close vs the prior month-end close.

Writes/overwrites wiki/analysis/mtd-pnl-<YYYY-MM>.md — re-run any day to
extend the table through the latest close ("keep the list going").

Usage: python tools/mtd_pnl.py [YYYY-MM]
"""
import sys, os, re, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import backtest, open_positions as op, gated_book, ideal_book
import yfinance as yf
import pandas as pd, math


def _ok(x):
    """Guard against a NaN return from a single-day vendor price gap poisoning the sum."""
    return isinstance(x, (int, float)) and not math.isnan(x)


def trading_days(month):
    df = yf.download("SPY", period="4mo", interval="1d", progress=False, auto_adjust=True)
    days = sorted(d.date() for d in df.index)
    in_month = [d for d in days if d.isoformat()[:7] == month]
    prior = [d for d in days if d < in_month[0]]
    return prior[-1], in_month          # (prior month-end close, month's trading days)


def full_book_total(asof):
    """Every-signal benchmark: deduped open marks + deduped closed realized, % of equity."""
    openp = op.collect(asof=asof)
    closed = op.collect_closed(openp, asof=asof)
    return sum(r["ret"] for r in openp + closed if _ok(r["ret"])) * uw.FULL_POSITION_PCT


def gated_total(asof):
    """Book of record: weighted open + closed, % of equity."""
    gpos, gclosed, _s, _d = gated_book.simulate(asof=asof)
    return sum(p["ret"] * p["weight"] for p in gpos + gclosed if _ok(p["ret"]))


def ideal_total(asof):
    """Paper leader-pullback swing book: weighted open + closed, % of equity."""
    ipos, iclosed, _s, _d = ideal_book.simulate(asof=asof)
    return sum(p["ret"] * p["weight"] for p in ipos + iclosed if _ok(p["ret"]))


def main():
    month = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().strftime("%Y-%m")
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = float(re.sub(r"[,$\s]", "", eq_raw)) if eq_raw else 1_000_000.0

    base_day, days = trading_days(month)
    print(f"MTD P&L {month} — baseline {base_day} (prior month-end close)\n")
    g0, i0, f0 = gated_total(base_day), ideal_total(base_day), full_book_total(base_day)

    print(f"{'DATE':12}{'GATED $':>12}{'IDEAL $':>12}{'FULL $':>12}")
    print(f"{'baseline':12}{g0*equity:>+12,.0f}{i0*equity:>+12,.0f}{f0*equity:>+12,.0f}")
    md_rows = []
    gp, ip, fp = g0, i0, f0
    for d in days:
        g, i, f = gated_total(d), ideal_total(d), full_book_total(d)
        print(f"{d.isoformat():12}{g*equity:>+12,.0f}{i*equity:>+12,.0f}{f*equity:>+12,.0f}")
        md_rows.append(f"| {d} | ${g*equity:+,.0f} | ${(g-gp)*equity:+,.0f} | ${i*equity:+,.0f} "
                       f"| ${(i-ip)*equity:+,.0f} | ${f*equity:+,.0f} | ${(f-fp)*equity:+,.0f} |")
        gp, ip, fp = g, i, f

    g_mtd, i_mtd, f_mtd = (gp - g0) * equity, (ip - i0) * equity, (fp - f0) * equity
    print(f"\nMTD ({month}):  GATED {g_mtd:+,.0f}  ·  IDEAL {i_mtd:+,.0f}  ·  FULL {f_mtd:+,.0f}")

    run = dt.date.today().isoformat()
    md = [f"---\ntype: analysis\ntags: [pnl, mtd, gated-book, ideal-book, benchmark, daily]\ncreated: {run}\nupdated: {run}\n---\n",
          f"# MTD P&L — {month} (daily closes, all three books)",
          f"Point-in-time daily closing P&L (cumulative since inception, $ at ${int(equity):,} equity) for the "
          f"**gated book of record**, the **paper ideal swing book** ([[ideal-swing-model-2026-07-15]]), and the "
          f"**every-signal benchmark**. Each row re-simulates all three using only bars up to that close "
          f"(`tools/mtd_pnl.py`; re-run daily to extend). Baseline = {base_day} close.\n",
          f"**Baseline ({base_day}):** gated ${g0*equity:+,.0f} · ideal ${i0*equity:+,.0f} · full ${f0*equity:+,.0f}\n",
          "| Date | 📘 Gated | Δ day | 🧪 Ideal | Δ day | Benchmark | Δ day |",
          "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    md += md_rows
    md.append(f"\n**MTD ({month}): 📘 gated ${g_mtd:+,.0f} · 🧪 ideal ${i_mtd:+,.0f} · benchmark ${f_mtd:+,.0f}**")
    md.append("\n_Simulated, single-account views; the ideal book is in-sample/paper. Not investment advice._")
    out = os.path.join(uw.WIKI, "analysis", f"mtd-pnl-{month}.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
