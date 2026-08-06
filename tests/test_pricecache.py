#!/usr/bin/env python3
"""Regression tests for the price cache's session keying.

Guards the 2026-08-05 defect: pricecache keyed on the wall-clock calendar date, so a
fetch made DURING a session was reused for the rest of that day even after the real
close landed. 2,118 of 2,141 tickers ended up a full day stale while every artifact
was labelled the current close — and it changed a buy recommendation.

The fix keys cache files by the latest COMPLETED session instead, so a pre-close run
and a post-close run land in different buckets.

Run: python tests/test_pricecache.py     (needs network — it fetches a reference ticker)
"""
import os, sys, pickle, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import pricecache

_fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))
    if not cond:
        _fails.append(name)


def test_latest_session():
    print("latest_session() resolves to a real completed session")
    s = pricecache.latest_session()
    check("returns an ISO date", bool(s) and len(s) == 10, s)
    check("not in the future", s <= dt.date.today().isoformat(), f"{s} <= {dt.date.today()}")
    return s


def test_session_keyed(session):
    print("\ncache files are keyed by SESSION, not wall-clock date")
    df = pricecache.get("SPY")
    fn = os.path.join(pricecache.CACHE_DIR, f"SPY_3y_{session}.pkl")
    check("cached under the session key", os.path.exists(fn), os.path.basename(fn))
    check("cached last bar == session", str(df.index[-1].date()) == session,
          f"last bar {df.index[-1].date()}")
    return df


def test_stale_file_not_served(session, fresh):
    """THE regression: a file written mid-session (missing the newest bar) must not
    be served once the session has completed."""
    print("\nregression: a pre-close cache file is NOT reused after the close")
    prior = (dt.date.fromisoformat(session) - dt.timedelta(days=1)).isoformat()
    stale_fn = os.path.join(pricecache.CACHE_DIR, f"SPY_3y_{prior}.pkl")
    pickle.dump(fresh.iloc[:-1], open(stale_fn, "wb"))
    try:
        got = pricecache.get("SPY")
        check("returns data through the current session", str(got.index[-1].date()) == session,
              f"got {got.index[-1].date()}, stale file held {fresh.index[-2].date()}")
        check("stale file not silently served", len(got) == len(fresh),
              f"{len(got)} rows vs {len(fresh)}")
    finally:
        try: os.remove(stale_fn)
        except OSError: pass


def test_period_pnl_agrees(session):
    """period_pnl used to fetch SPY directly, bypassing the cache — so it could label
    output with the true session while the sims underneath read a stale one."""
    print("\nperiod_pnl and the price cache agree on 'now'")
    import period_pnl
    today, _pm, _pq = period_pnl._boundaries()
    check("boundary close == cache session", today.isoformat() == session, f"{today} vs {session}")


def main():
    session = test_latest_session()
    fresh = test_session_keyed(session)
    test_stale_file_not_served(session, fresh)
    test_period_pnl_agrees(session)
    print("\n" + ("ALL CHECKS PASSED" if not _fails else f"{len(_fails)} FAILURE(S): {', '.join(_fails)}"))
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
