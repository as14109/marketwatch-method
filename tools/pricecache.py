#!/usr/bin/env python3
"""
Shared on-disk daily price cache.

The full-year books re-download ~440 tickers of 3y daily bars on every run.
Across a routine (update_watchlist, validate_list, regime, gated_book,
ideal_book, open_positions, mtd_pnl, period_pnl, build_report) that is the same
download repeated 8-9 times. This caches each ticker's 3y history to disk keyed
by the calendar day, so the FIRST tool of the day downloads and every tool after
reads from disk. Stale files (older calendar days) are pruned on access.

Point-in-time (`asof`) slicing happens in each caller AFTER fetch, on the full
3y frame — so caching the whole frame is safe and does not affect backtests.

The EOD routine runs after the close, so the day's first fetch captures final
closes; intraday callers may cache a forming last bar (backtest drops incomplete
bars anyway).
"""
import os, glob, datetime as dt, pickle
import yfinance as yf

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".price_cache")

# Optional global override for the download window. The live routine uses 3y
# (callers pass period="3y"). Multi-year backtests (e.g. the 2024/2025/2026
# validation) set this to "5y" so even a Jan-2024 entry has 221 bars before it
# for a valid 200-day SMA. Set PERIOD_OVERRIDE = "5y" before importing the books.
PERIOD_OVERRIDE = None


def get(tkr, period="3y", interval="1d"):
    if PERIOD_OVERRIDE:
        period = PERIOD_OVERRIDE
    os.makedirs(CACHE_DIR, exist_ok=True)
    today = dt.date.today().isoformat()
    safe = tkr.replace("^", "_").replace("/", "_")
    fn = os.path.join(CACHE_DIR, f"{safe}_{period}_{today}.pkl")
    if os.path.exists(fn):
        try:
            return pickle.load(open(fn, "rb"))
        except Exception:
            pass
    df = yf.download(tkr, period=period, interval=interval, progress=False, auto_adjust=True)
    try:
        pickle.dump(df, open(fn, "wb"))
        # prune this ticker's older-day files
        for old in glob.glob(os.path.join(CACHE_DIR, f"{safe}_{period}_*.pkl")):
            if not old.endswith(f"_{today}.pkl"):
                try: os.remove(old)
                except OSError: pass
    except Exception:
        pass
    return df
