#!/usr/bin/env python3
"""
Period P&L — YTD / QTD / MTD for all three books (gated book of record,
paper ideal swing book, every-signal benchmark).

All three books are inception-dated to MODEL_START (2026-01-01), so:
  - YTD  = total since inception            (baseline = prior year-end close = $0)
  - QTD  = total now  -  total at last close of the prior quarter
  - MTD  = total now  -  total at last close of the prior month

The heavy full-year re-simulation runs once here and is cached to
`tools/.period_pnl_cache.json` keyed by the latest trading-close date, so the
daily report reads it instantly (recomputes only when the close date changes or
`--force` is passed). Also writes wiki/analysis/period-pnl-<rundate>.md.

Usage:
  python tools/period_pnl.py [--force]     # compute/refresh + write analysis page
  (build_report imports report_block() / numbers())
"""
import sys, os, re, json, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import yfinance as yf
import pricecache
# reuse the three shared total-calculators (they share backtest._dl_cache)
from mtd_pnl import gated_total, ideal_total, full_book_total

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".period_pnl_cache.json")


def _equity():
    eq = uw.env("MW_PORTFOLIO_EQUITY")
    return float(re.sub(r"[,$\s]", "", eq)) if eq else 1_000_000.0


def _boundaries():
    """(latest_close, prior_month_end, prior_quarter_end) as datetime.date.

    Reads SPY through the SHARED price cache, not a direct yf.download. Fetching it
    directly is what let this tool label output with the true latest session while the
    book simulations underneath were reading a stale cached session — the 2026-08-05
    incident. Both must see the same session or the label lies about the data.
    """
    df = pricecache.get("SPY")
    days = sorted(d.date() for d in df.index)
    today = days[-1]
    m0 = dt.date(today.year, today.month, 1)
    q_month = ((today.month - 1) // 3) * 3 + 1          # first month of this quarter
    q0 = dt.date(today.year, q_month, 1)
    prior_month = [d for d in days if d < m0]
    prior_qtr = [d for d in days if d < q0]
    return today, (prior_month[-1] if prior_month else None), (prior_qtr[-1] if prior_qtr else None)


def compute():
    """Run the full-year sim for all three books at the three boundary dates.
    Returns a dict of raw fractions-of-equity (before $ scaling)."""
    today, pm, pq = _boundaries()
    # totals now
    g_now, i_now, f_now = gated_total(today), ideal_total(today), full_book_total(today)
    # prior month-end
    g_pm = gated_total(pm) if pm else 0.0
    i_pm = ideal_total(pm) if pm else 0.0
    f_pm = full_book_total(pm) if pm else 0.0
    # prior quarter-end (reuse month-end if same date — July: both = Jun-30)
    if pq == pm:
        g_pq, i_pq, f_pq = g_pm, i_pm, f_pm
    else:
        g_pq = gated_total(pq) if pq else 0.0
        i_pq = ideal_total(pq) if pq else 0.0
        f_pq = full_book_total(pq) if pq else 0.0
    # YTD baseline = prior year-end = $0 (inception 2026-01-01, no lists before Jan)
    data = dict(
        close=today.isoformat(), prior_month=pm.isoformat() if pm else None,
        prior_quarter=pq.isoformat() if pq else None,
        gated=dict(now=g_now, mtd=g_now - g_pm, qtd=g_now - g_pq, ytd=g_now),
        ideal=dict(now=i_now, mtd=i_now - i_pm, qtd=i_now - i_pq, ytd=i_now),
        full=dict(now=f_now, mtd=f_now - f_pm, qtd=f_now - f_pq, ytd=f_now),
        computed=dt.datetime.now().isoformat(timespec="seconds"),
    )
    json.dump(data, open(CACHE, "w"))
    return data


def numbers(force=False):
    """Cached period P&L; recompute if the cache is missing, stale (close-date
    changed vs the latest SPY close), or force=True."""
    cached = None
    if not force and os.path.exists(CACHE):
        try: cached = json.load(open(CACHE))
        except Exception: cached = None
    if cached is not None:
        try:
            # same session source the price cache keys on, so "is the cache current?"
            # and "what data will the sims see?" can never disagree
            if cached.get("close") == pricecache.latest_session():
                return cached
        except Exception:
            return cached          # offline — reuse whatever we have
    return compute()


def report_block(force=False, equity=None):
    """Compact markdown block for the top of the daily report."""
    d = numbers(force=force)
    eq = equity or _equity()
    def pct(x): return f"{x*100:+.2f}%"
    def usd(x): return f"${x*eq:+,.0f}"
    rows = [
        ("📘 Gated (record)", d["gated"]),
        ("🧪 Ideal (paper)",  d["ideal"]),
        ("📊 Benchmark",      d["full"]),
    ]
    out = [f"**Performance since inception (2026-01-01) — as of close {d['close']}**", "",
           "| Book | YTD | QTD | MTD |",
           "| --- | ---: | ---: | ---: |"]
    for name, b in rows:
        out.append(f"| {name} | {usd(b['ytd'])} ({pct(b['ytd'])}) | {usd(b['qtd'])} | {usd(b['mtd'])} |")
    out.append("")
    out.append(f"_QTD & MTD share the {d['prior_quarter']} baseline this quarter (Q3 began Jul 1); "
               f"they diverge next month. YTD baseline = $0 at inception._")
    return "\n".join(out)


def report_block_html(force=False, equity=None):
    d = numbers(force=force)
    eq = equity or _equity()
    def pct(x): return f"{x*100:+.2f}%"
    def usd(x): return f"${x*eq:+,.0f}"
    def color(x): return "#1a7f37" if x >= 0 else "#cf222e"
    rows = [("📘 Gated (record)", d["gated"]), ("🧪 Ideal (paper)", d["ideal"]), ("📊 Benchmark", d["full"])]
    cells = []
    for name, b in rows:
        cells.append(
            f"<tr><td style='padding:4px 10px'>{name}</td>"
            f"<td style='padding:4px 10px;text-align:right;color:{color(b['ytd'])}'>{usd(b['ytd'])} ({pct(b['ytd'])})</td>"
            f"<td style='padding:4px 10px;text-align:right;color:{color(b['qtd'])}'>{usd(b['qtd'])}</td>"
            f"<td style='padding:4px 10px;text-align:right;color:{color(b['mtd'])}'>{usd(b['mtd'])}</td></tr>")
    return (
        f"<p style='margin:0 0 4px;font-weight:600'>Performance since inception (2026-01-01) — as of close {d['close']}</p>"
        "<table style='border-collapse:collapse;font-size:13px'>"
        "<tr style='border-bottom:1px solid #d0d7de'><th style='padding:4px 10px;text-align:left'>Book</th>"
        "<th style='padding:4px 10px;text-align:right'>YTD</th><th style='padding:4px 10px;text-align:right'>QTD</th>"
        "<th style='padding:4px 10px;text-align:right'>MTD</th></tr>" + "".join(cells) + "</table>")


def main():
    force = "--force" in sys.argv
    d = compute() if force else numbers(force=force)
    eq = _equity()
    def line(name, b):
        return (f"{name:22} YTD ${b['ytd']*eq:>+11,.0f} ({b['ytd']*100:+.2f}%)   "
                f"QTD ${b['qtd']*eq:>+11,.0f}   MTD ${b['mtd']*eq:>+11,.0f}")
    print(f"Period P&L — as of close {d['close']}  (prior month-end {d['prior_month']}, "
          f"prior quarter-end {d['prior_quarter']})\n")
    print(line("Gated (book of record)", d["gated"]))
    print(line("Ideal (paper swing)", d["ideal"]))
    print(line("Benchmark (every-signal)", d["full"]))

    run = dt.date.today().isoformat()
    def pct(x): return f"{x*100:+.2f}%"
    def usd(x): return f"${x*eq:+,.0f}"
    md = [f"---\ntype: analysis\ntags: [pnl, ytd, qtd, mtd, gated-book, ideal-book, benchmark]\n"
          f"created: {run}\nupdated: {run}\n---\n",
          f"# Period P&L — YTD / QTD / MTD (all three books)",
          f"Point-in-time P&L (cumulative since inception 2026-01-01, $ at ${int(eq):,} equity) for the "
          f"**gated book of record**, the **paper [[ideal_book|ideal swing book]]**, and the "
          f"**every-signal benchmark**. As of close **{d['close']}**. Prior month-end **{d['prior_month']}**, "
          f"prior quarter-end **{d['prior_quarter']}** (`tools/period_pnl.py`).\n",
          "| Book | YTD | QTD | MTD |",
          "| --- | ---: | ---: | ---: |",
          f"| 📘 Gated (record) | {usd(d['gated']['ytd'])} ({pct(d['gated']['ytd'])}) | {usd(d['gated']['qtd'])} | {usd(d['gated']['mtd'])} |",
          f"| 🧪 Ideal (paper) | {usd(d['ideal']['ytd'])} ({pct(d['ideal']['ytd'])}) | {usd(d['ideal']['qtd'])} | {usd(d['ideal']['mtd'])} |",
          f"| 📊 Benchmark | {usd(d['full']['ytd'])} ({pct(d['full']['ytd'])}) | {usd(d['full']['qtd'])} | {usd(d['full']['mtd'])} |",
          f"\n_QTD & MTD share the {d['prior_quarter']} baseline this quarter (Q3 began Jul 1). "
          f"YTD baseline = $0 at inception (no Key Lists before Jan 2). Simulated, single-account, paper "
          f"for the ideal book. Not investment advice._"]
    out = os.path.join(uw.WIKI, "analysis", f"period-pnl-{run}.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"\n[wrote {out}]  [cache {CACHE}]")


if __name__ == "__main__":
    main()
