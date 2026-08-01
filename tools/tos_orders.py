#!/usr/bin/env python3
"""
Generate a thinkorswim order plan from the latest Key List + our trade rules.

For each name it produces: a BUY STOP-LIMIT entry at the Key List trigger (stop = limit
= trigger, so gap-up opens never fill) plus a protective STOP-MARKET at the −12% disaster
level. Exit v3 (trend-hold): there is NO profit target — hold the full position until a
daily CLOSE below the 50-day SMA, then sell. The 50-SMA level is monitored daily (pair
with tools/keylist_levels.ts for alerts).

Note: thinkorswim cannot place orders from ThinkScript — these are the tickets to
enter via the order screen. NOT trading advice; review and place every order yourself.

Entry buy-stops are DAY orders (the Key List trigger is only valid for its own
session); the disaster stop goes GTC once a fill occurs.

Usage: python tools/tos_orders.py
"""
import sys, glob, os, re
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw

DIS, TMA, FULL = uw.DISASTER_PCT, uw.TREND_MA, uw.FULL_POSITION_PCT

def latest():
    dated = []
    for f in glob.glob(os.path.join(uw.RAW, "*key-list*.md")):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(f))
        if m: dated.append((m.group(1), f))
    dated.sort(); return dated[-1]

def main():
    import classify
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = float(re.sub(r"[,$\s]", "", eq_raw)) if eq_raw else None
    date, path = latest()
    rows = uw.parse_entries(path)
    # pilot sizing in a NEUTRAL regime; ETFs at half size (process-improvements-2026-07-09)
    try:
        import regime
        rscore, _, _, _ = regime.compute()
    except Exception:
        rscore = None
    pilot = isinstance(rscore, int) and 4 <= rscore <= 6
    eq_note = f"  (full position = {int(FULL*100)}% of ${int(equity):,})" if equity else ""
    print(f"thinkorswim order plan — Key List {date}{eq_note}")
    print(f"Exit v3 (trend-hold): buy-stop entry + −{int(DIS*100)}% disaster stop; NO target — "
          f"hold to a daily CLOSE below the {TMA}-day SMA, then sell.")
    if pilot:
        print(f"REGIME {rscore}/8 NEUTRAL -> quantities below are PILOT size "
              f"(x{uw.PILOT_FRACTION}); ETFs a further x{uw.ETF_FRACTION}.")
    print()
    s_lbl = f"DISASTER -{int(DIS*100)}%"
    print(f"{'SYM':6}{'BUY STOP':>11}{'QTY':>7}{s_lbl:>16}{'EXIT':>16}  FLAGS")
    for sym, entry in rows:
        stop = entry * (1 - DIS)
        w = FULL * (uw.PILOT_FRACTION if pilot else 1)
        _, is_etf = classify.group(sym)
        if is_etf:
            w *= uw.ETF_FRACTION
        qty = int(equity * w / entry) if equity else 0
        flags = ("ETF x%.1f" % uw.ETF_FRACTION) if is_etf else ""
        print(f"{sym:6}{entry:>11.2f}{qty:>7}{stop:>16.2f}{('close<'+str(TMA)+'SMA'):>16}  {flags}")
    print("\nCheck the emailed report's Action read for cooldown (recently stopped) and")
    print("extended (>8% above the 21-day MA) flags before placing any ticket.")
    print("\nTicket (per symbol) — entry = DAY order (trigger valid only for this session;")
    print("names still valid re-appear on the next list). The disaster stop goes GTC once filled:")
    print("  BUY  +QTY  STOP-LIMIT @ trigger/trigger  [DAY]  <- fills only AT the trigger; a gap-up open above it does NOT fill (no chasing)")
    print(f"     SELL -QTY  STOP  @ <DISASTER -{int(DIS*100)}%>   <- STOP-MARKET (never stop-limit): a gap-down")
    print("                                            below the stop closes the position at the open")
    print(f"  No profit target: hold the full position until a daily CLOSE below the {TMA}-day SMA,")
    print(f"  then sell at that day's close/next open. Monitor the {TMA}-SMA daily (keylist_levels.ts).")

if __name__ == "__main__":
    main()
