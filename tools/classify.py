#!/usr/bin/env python3
"""
Ticker classification for the gated book's group/ETF heat caps: is it an ETF,
and what sector/group does it belong to?

Sources, in order:
  1. classify_cache.json next to this file (persisted lookups)
  2. a hardcoded ETF set (robust even when the vendor lookup fails)
  3. yfinance Ticker.info quoteType/sector (slow; cached after first fetch)

Groups: stocks -> their yfinance sector ("Technology", "Healthcare", ...);
every ETF -> the single group "ETF" (they are index/theme beta, capped as one
bucket per process-improvements-2026-07-09 #5).

Usage: import classify; classify.group("CRWD") -> ("Technology", False)
"""
import json, os

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "classify_cache.json")

# ETFs seen on Key Lists so far — fallback when the vendor lookup fails.
KNOWN_ETFS = {
    "SMH", "HACK", "CIBR", "CLOU", "SKYY", "ARKK", "ARKW", "ARKG", "FDN", "FBL",
    "SSO", "QLD", "IWM", "MDY", "KBE", "KRE", "FFTY", "JETS", "SPY", "QQQ", "RSP",
}

_cache = None


def _load():
    global _cache
    if _cache is None:
        try:
            _cache = json.load(open(CACHE_PATH, encoding="utf-8"))
        except Exception:
            _cache = {}
    return _cache


def _save():
    try:
        json.dump(_cache, open(CACHE_PATH, "w", encoding="utf-8"), indent=1, sort_keys=True)
    except Exception:
        pass


def group(tkr):
    """Return (group_name, is_etf). Never raises; unknowns come back ("Unknown", False)."""
    tkr = tkr.upper()
    cache = _load()
    if tkr in cache:
        e = cache[tkr]
        return e["group"], e["etf"]
    is_etf, grp = tkr in KNOWN_ETFS, None
    try:
        import yfinance as yf
        info = yf.Ticker(tkr).info or {}
        qt = (info.get("quoteType") or "").upper()
        if qt == "ETF":
            is_etf = True
        if not is_etf:
            grp = info.get("sector")
    except Exception:
        pass
    grp = "ETF" if is_etf else (grp or "Unknown")
    cache[tkr] = {"group": grp, "etf": is_etf}
    _save()
    return grp, is_etf


if __name__ == "__main__":
    import sys
    for t in sys.argv[1:]:
        g, e = group(t)
        print(f"{t.upper():6} {'ETF' if e else 'stock':6} {g}")
