#!/usr/bin/env python3
"""
Earnings dates (backlog B1 — earnings guard). Thin wrapper over yfinance's
get_earnings_dates with a once-a-day on-disk cache (.earnings_cache.json) so the
daily report doesn't re-hit the network for every name.

days_to_earnings(tkr) -> int days until the next scheduled report, or None.
Requires lxml (pip install --user lxml). Any failure returns None (fail-open:
no earnings info just means no guard, never a crash).

Usage: python tools/earnings.py AAPL NVDA ADPT
"""
import os, json, datetime as dt

CACHE = os.path.join(os.path.dirname(__file__), ".earnings_cache.json")


def _load():
    try:
        return json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        return {}


def _save(d):
    try:
        json.dump(d, open(CACHE, "w", encoding="utf-8"))
    except Exception:
        pass


def next_earnings(tkr, today=None):
    """Next scheduled earnings date (datetime.date) at/after `today`, or None."""
    today = today or dt.date.today()
    key = tkr.upper()
    disk = _load()
    ent = disk.get(key)
    if ent and ent.get("asof") == today.isoformat():
        return dt.date.fromisoformat(ent["next"]) if ent.get("next") else None
    nd = None
    try:
        import yfinance as yf
        ed = yf.Ticker(tkr).get_earnings_dates(limit=12)
        if ed is not None and not ed.empty:
            fut = sorted(d.date() for d in ed.index if d.date() >= today)
            nd = fut[0] if fut else None
    except Exception:
        nd = None
    disk[key] = {"asof": today.isoformat(), "next": nd.isoformat() if nd else None}
    _save(disk)
    return nd


def days_to_earnings(tkr, today=None):
    """Whole days until the next earnings report, or None if unknown."""
    today = today or dt.date.today()
    nd = next_earnings(tkr, today)
    return (nd - today).days if nd else None


if __name__ == "__main__":
    import sys
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
    for t in sys.argv[1:] or ["AAPL", "NVDA", "ADPT"]:
        d = days_to_earnings(t)
        print(f"{t}: {'no data' if d is None else str(d)+' days'}")
