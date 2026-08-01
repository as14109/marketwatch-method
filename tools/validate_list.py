#!/usr/bin/env python3
"""
Validate a Key List against the wiki's knowledge — specifically Minervini's
Trend Template (the computable part of our quality filter).

For each ticker it checks the 8 Trend Template criteria (wiki/concepts/trend-template):
  1. price > 150-day SMA and > 200-day SMA
  2. 150-day SMA > 200-day SMA
  3. 200-day SMA trending up (vs ~1 month ago)
  4. 50-day SMA > 150-day and > 200-day
  5. price >= 25% above its 52-week low
  6. price within 25% of its 52-week high
  7. relative strength (proxy): 6-month return beats SPY  (IBD RS rank not available)
  8. price > 50-day SMA
A name "PASSES" the trend filter if it meets all 8 (criterion 7 is a proxy).

The fundamental/ratings parts of CAN SLIM (composite, EPS, accumulation/distribution,
group rank) come from the Key List itself, not price — so this validates the technical
trend, not the fundamentals.

Usage: python tools/validate_list.py 2026-06-29
"""
import sys, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import yfinance as yf
import pricecache
import pandas as pd

_dl = {}

def series(tkr, asof=None):
    if tkr not in _dl:
        df = pricecache.get(tkr, period="3y")
        if df is not None and not df.empty and isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        _dl[tkr] = df
    df = _dl[tkr]
    if df is None or df.empty: return None
    c = df["Close"].dropna()
    if asof:  # point-in-time: only closes strictly BEFORE the list's trading day
        c = c[c.index.date < asof]
    return c

_check_cache = {}
def check(tkr, spy, asof=None):
    """Memoized wrapper: the Trend-Template result is a pure, point-in-time function
    of (tkr, asof) and the day-fixed price data (spy is constant), so cache it —
    tools/mtd_pnl.py otherwise recomputes each (tkr, list-date) check ~18× over."""
    key = (tkr, asof)
    if key not in _check_cache:
        _check_cache[key] = _check_impl(tkr, spy, asof=asof)
    return _check_cache[key]


def _check_impl(tkr, spy, asof=None):
    c = series(tkr, asof=asof)
    if c is None or len(c) < 221:  # need 200-SMA plus a 21-bar lookback for criterion 3
        return None, "insufficient history"
    if c.pct_change().abs().max() > 0.60:  # adjusted closes never legitimately jump >60%/day
        return None, "data suspect (bad split/adjustment in vendor history)"
    px = float(c.iloc[-1])
    sma50 = c.rolling(50).mean().iloc[-1]
    sma150 = c.rolling(150).mean().iloc[-1]
    sma200 = c.rolling(200).mean().iloc[-1]
    sma200_1mo = c.rolling(200).mean().iloc[-21]
    lo52 = c.iloc[-252:].min(); hi52 = c.iloc[-252:].max()
    # RS proxy: 6-month (126d) return vs SPY
    r_stock = px / c.iloc[-126] - 1
    r_spy = spy.iloc[-1] / spy.iloc[-126] - 1
    crit = {
        "1 px>150&200": px > sma150 and px > sma200,
        "2 150>200":    sma150 > sma200,
        "3 200 rising": sma200 > sma200_1mo,
        "4 50>150&200": sma50 > sma150 and sma50 > sma200,
        "5 >=25% off low": px >= 1.25 * lo52,
        "6 within 25% high": px >= 0.75 * hi52,
        "7 RS>SPY (proxy)": r_stock > r_spy,
        "8 px>50":      px > sma50,
    }
    passed = sum(crit.values())
    fails = [k for k, v in crit.items() if not v]
    return passed, fails

def main():
    list_date = sys.argv[1] if len(sys.argv) > 1 else None
    if not list_date: sys.exit("usage: python tools/validate_list.py YYYY-MM-DD")
    raw = None
    import glob, os
    for f in glob.glob(os.path.join(uw.RAW, "*key-list*.md")):
        if list_date in os.path.basename(f): raw = f
    if not raw: sys.exit(f"no raw key-list for {list_date}")
    entries = uw.parse_entries(raw)
    spy = series("SPY")
    print(f"Trend Template validation — Key List {list_date} ({len(entries)} names)")
    print("PASS = all 8 Stage-2 criteria met (crit 7 = RS-vs-SPY proxy). Fundamentals come from the Key List itself.\n")
    print(f"{'TKR':6}{'score':>7}  verdict / failed criteria")
    rows = []
    for t, _ in entries:
        passed, fails = check(t, spy)
        rows.append((t, passed, fails))
    for t, passed, fails in sorted(rows, key=lambda r: (r[1] is None, -(r[1] or -1))):
        if passed is None:
            print(f"{t:6}{'—':>7}  {fails}")
        elif passed == 8:
            print(f"{t:6}{passed:>5}/8  ✅ PASS")
        else:
            print(f"{t:6}{passed:>5}/8  ⚠ fails: {', '.join(fails)}")
    ok = [t for t, p, _ in rows if p == 8]
    print(f"\nFull Trend-Template pass: {len(ok)}/{len(rows)} — {', '.join(ok) or 'none'}")

if __name__ == "__main__":
    main()
