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

Cache files are keyed by the **latest completed session available upstream**, NOT
by the wall-clock calendar date. That distinction matters: keying on the calendar
date meant a tool run DURING a session cached an incomplete day and every later
run that day silently reused it. On 2026-08-05 a ~9am run left 2,118 of 2,141
tickers holding 08-04 bars while the artifacts were labelled the 08-05 close —
which changed a buy recommendation (see MW/wiki/sources/2026-08-06-key-list.md).
Keying on the session means a pre-close run writes `..._2026-08-04.pkl`, and the
first post-close run sees a new session, misses, and re-fetches.
"""
import os, glob, datetime as dt, pickle
import yfinance as yf

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".price_cache")

# Reference ticker used to discover the latest completed trading session. Resolved
# once per process (never cached to disk — caching it is the bug this prevents).
_SESSION_REF = "SPY"
_session = None

# Optional global override for the download window. The live routine uses 3y
# (callers pass period="3y"). Multi-year backtests (e.g. the 2024/2025/2026
# validation) set this to "5y" so even a Jan-2024 entry has 221 bars before it
# for a valid 200-day SMA. Set PERIOD_OVERRIDE = "5y" before importing the books.
PERIOD_OVERRIDE = None


def _looks_valid(df):
    """A download is usable if non-empty and has at least one real (non-NaN) Close
    bar. Guards against caching a transient empty/garbage response for the rest of
    the day — yfinance can return an empty frame (rate-limit, ambiguous/delisted
    symbol) without raising, and every downstream tool silently treats that as
    "no data" for the ticker (see the 2026-08-04 AAOI audit: an unvalidated empty
    download got cached and quietly dropped a real trade from a book's totals)."""
    if df is None or len(df) == 0:
        return False
    cols = df.columns
    if hasattr(cols, "nlevels") and cols.nlevels > 1:
        cols = cols.get_level_values(0)
    if "Close" not in cols:
        return False
    close = df["Close"]
    if hasattr(close, "columns"):   # still 2-D if the MultiIndex collapse above missed it
        close = close.iloc[:, 0]
    return bool(close.notna().any())


def latest_session():
    """Date of the most recent COMPLETED session available upstream, as an ISO string.

    Resolved once per process from a liquid reference ticker and deliberately never
    written to disk. Everything else keys off this, so a run that happens mid-session
    and a run that happens after the close land in different cache buckets instead of
    sharing one stale bucket for the calendar day.

    Falls back to today's date if the reference can't be fetched — that restores the
    old (weaker) behaviour rather than failing the whole routine.
    """
    global _session
    if _session is None:
        try:
            df = yf.download(_SESSION_REF, period="5d", interval="1d",
                             progress=False, auto_adjust=True)
            _session = df.index[-1].date().isoformat() if _looks_valid(df) else None
        except Exception:
            _session = None
        if _session is None:
            _session = dt.date.today().isoformat()
    return _session


def get(tkr, period="3y", interval="1d"):
    if PERIOD_OVERRIDE:
        period = PERIOD_OVERRIDE
    os.makedirs(CACHE_DIR, exist_ok=True)
    today = latest_session()          # session-keyed, not wall-clock keyed
    safe = tkr.replace("^", "_").replace("/", "_")
    fn = os.path.join(CACHE_DIR, f"{safe}_{period}_{today}.pkl")
    if os.path.exists(fn):
        try:
            cached = pickle.load(open(fn, "rb"))
            if _looks_valid(cached):
                return cached
            os.remove(fn)   # a bad file cached before this guard existed — drop it, fall through to re-fetch
        except Exception:
            pass
    df = yf.download(tkr, period=period, interval=interval, progress=False, auto_adjust=True)
    if not _looks_valid(df):
        # Don't cache an empty/invalid response: a transient failure would otherwise
        # be persisted and silently reused by every tool for the rest of the day.
        return df
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
