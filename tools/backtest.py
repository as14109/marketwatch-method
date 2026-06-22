#!/usr/bin/env python3
"""
Backtest the Key List trade rules against real daily prices.

Rules (from key-list-trade-rules):
- Enter long when price trades through the Key List pivot (buy-stop). Fill at the
  pivot, or at the open if it gaps above the pivot.
- Initial stop = entry x (1 - STOP_PCT)  [-3%].
- When a day's high reaches entry x (1 + BE_PCT) [+5%], raise the stop to breakeven (entry).
- When a day's high reaches entry x (1 + T1_PCT) [+7%], sell 50% at that level.
- Trail the remaining 50% under the 9-day EMA: exit on a daily CLOSE below the 9 EMA.

Modeling notes (daily bars, no intraday):
- If a day touches both the stop and the +7% target, we assume the STOP first (conservative),
  unless the day OPENED above the target (gap), in which case the target fills at the open.
- Positions still open at the last bar are marked-to-market at the last close (unrealized).
- Returns are per-position (%). A full position = 10% of the portfolio, so the portfolio
  contribution = position return x 10%.

Usage: python tools/backtest.py 2026-06-15
"""
import sys, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import glob, os, re
import update_watchlist as uw
import yfinance as yf

STOP, BE, T1 = uw.STOP_PCT, uw.BE_PCT, uw.T1_PCT
FULL_W = uw.FULL_POSITION_PCT  # 0.10


def find_raw(list_date):
    for f in glob.glob(os.path.join(uw.RAW, "*key-list*.md")):
        if list_date in os.path.basename(f):
            return f
    sys.exit(f"no raw key-list for {list_date}")


def sim_one(tkr, E, list_date):
    try:
        df = yf.download(tkr, period="6mo", interval="1d", progress=False, auto_adjust=True)
    except Exception as e:
        return dict(tkr=tkr, E=E, status="error", ret=None, note=str(e)[:40])
    if df is None or df.empty:
        return dict(tkr=tkr, E=E, status="no data", ret=None, note="")
    import pandas as pd
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close"]].copy()
    df["ema9"] = df["Close"].ewm(span=9, adjust=False).mean()
    sim = df[df.index.date >= dt.date.fromisoformat(list_date)]
    if sim.empty:
        return dict(tkr=tkr, E=E, status="no data after date", ret=None, note="")

    stop0, be_trig, t1 = E*(1-STOP), E*(1+BE), E*(1+T1)
    state, fill, cur_stop, be_on, realized = "waiting", None, stop0, False, 0.0
    notes = []
    rows = [(d.date(), float(r.Open), float(r.High), float(r.Low), float(r.Close), float(r.ema9))
            for d, r in sim.iterrows()]
    for d, O, H, L, C, ema in rows:
        if state == "waiting":
            if H >= E:
                fill = O if O > E else E
                state = "full"
                notes.append(f"{d} entry@{fill:.2f}")
            else:
                continue
        if state == "full":
            if O >= t1:                      # gapped through target
                realized += 0.5*(t1/fill-1); state = "half"; notes.append(f"{d} +7% sold½ (gap open)")
            elif L <= cur_stop and H >= t1:  # ambiguous -> assume stop first
                realized += (cur_stop/fill-1); state = "closed"; notes.append(f"{d} STOP@{cur_stop:.2f} (amb)"); break
            elif L <= cur_stop:
                realized += (cur_stop/fill-1); state = "closed"; notes.append(f"{d} STOP@{cur_stop:.2f}"); break
            elif H >= t1:
                realized += 0.5*(t1/fill-1); state = "half"; notes.append(f"{d} +7% sold½")
            if H >= be_trig and not be_on:
                be_on = True; cur_stop = max(cur_stop, E); notes.append(f"{d} +5% stop->breakeven")
            continue
        if state == "half":                  # trailing the runner under 9 EMA
            if L <= cur_stop:
                realized += 0.5*(cur_stop/fill-1); state = "closed"; notes.append(f"{d} runner stop@{cur_stop:.2f}"); break
            if C < ema:
                realized += 0.5*(C/fill-1); state = "closed"; notes.append(f"{d} runner exit<9EMA @{C:.2f}"); break

    lastC = rows[-1][4]
    if state == "waiting":
        return dict(tkr=tkr, E=E, status="not triggered", ret=0.0, fill=None, note="; ".join(notes))
    if state == "full":
        ret = (lastC/fill-1); status = "OPEN (full)"
    elif state == "half":
        ret = realized + 0.5*(lastC/fill-1); status = "OPEN (½ runner)"
    else:
        ret = realized; status = "closed"
    return dict(tkr=tkr, E=E, status=status, ret=ret, fill=fill, note="; ".join(notes))


def main():
    list_date = sys.argv[1] if len(sys.argv) > 1 else None
    if not list_date:
        sys.exit("usage: python tools/backtest.py YYYY-MM-DD")
    raw = find_raw(list_date)
    entries = uw.parse_entries(raw)
    print(f"Backtest of Key List {list_date} ({len(entries)} names) — rules: -3% stop, BE@+5%, sell½@+7%, trail 9EMA\n")
    rows = [sim_one(t, E, list_date) for t, E in entries]
    trig = [r for r in rows if r["ret"] is not None and r["status"] != "not triggered"]
    print(f"{'TKR':6}{'entry':>9}{'fill':>9}{'status':>16}{'return%':>9}  notes")
    for r in sorted(rows, key=lambda x: (x['ret'] is None, -(x['ret'] or -99))):
        ret = "—" if r["ret"] is None else f"{r['ret']*100:+.2f}"
        fill = r.get("fill"); fills = f"{fill:.2f}" if fill else "—"
        print(f"{r['tkr']:6}{r['E']:9.2f}{fills:>9}{r['status']:>16}{ret:>9}  {r.get('note','')}")

    if trig:
        avg = sum(r["ret"] for r in trig)/len(trig)
        port = sum(r["ret"]*FULL_W for r in trig)   # each full position = 10% of portfolio
        wins = [r for r in trig if r["ret"] > 0]
        print(f"\nTriggered: {len(trig)}/{len(rows)} | win rate {len(wins)}/{len(trig)} = {100*len(wins)/len(trig):.0f}%")
        print(f"Avg return per triggered position: {avg*100:+.2f}%")
        print(f"Portfolio P&L (each full=10% weight): {port*100:+.2f}% of equity  (realized+open)")
    else:
        print("\nNo names triggered in the window.")


if __name__ == "__main__":
    main()
