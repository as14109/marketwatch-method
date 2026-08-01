#!/usr/bin/env python3
"""
Backtest the Key List trade rules against real daily prices.

Rules (exit v3, from key-list-trade-rules — 50-SMA trend-hold, adopted 2026-07-25):
- Enter long only as price breaches the Key List pivot intraday (stop-limit at the
  pivot): fill = the trigger price. If the session OPENS above the trigger (gap-up), we
  never chase the open — but the resting DAY limit fills at the trigger if the day's
  low revisits it; only gap-and-go days (low > trigger) go unfilled. Triggers are DAY-only (TRIGGER_DAYS).
- Disaster stop = entry x (1 - DISASTER_PCT) [-12%] — the only hard stop.
- HOLD the full position (no breakeven, no target, no partial) until a daily CLOSE
  below the TREND_MA-day SMA [50], then exit the whole position at that close.

Modeling notes (daily bars, no intraday):
- A gap-down opening below the disaster stop closes at the OPEN (STOP-MARKET; min(open, stop)).
- The 50-SMA exit is a close-based signal, so there is no intraday ambiguity.
- Positions still open at the last bar are marked-to-market at the last close (unrealized).
- Returns are per-position (%). A full position = FULL_POSITION_PCT of the portfolio, so the
  portfolio contribution = position return x that weight.

Usage: python tools/backtest.py 2026-06-15
"""
import sys, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import glob, os, re
import update_watchlist as uw
import yfinance as yf
import pricecache

DIS, TMA = uw.DISASTER_PCT, uw.TREND_MA   # exit v3: 50-SMA trend-hold + disaster stop
ARM, LOCK = uw.PROFIT_ARM_PCT, uw.PROFIT_LOCK_PCT   # profit-lock: +30% -> stop to +15%
STOP, BE, T1 = uw.STOP_PCT, uw.BE_PCT, uw.T1_PCT   # legacy (unused by the exit engine)
FULL_W = uw.FULL_POSITION_PCT
TRIGGER_DAYS = 1  # a Key List trigger is only valid on the list's trading day
                  # (DAY order, not GTC) — names still valid re-appear on the next list


def find_raw(list_date):
    for f in glob.glob(os.path.join(uw.RAW, "*key-list*.md")):
        if list_date in os.path.basename(f):
            return f
    sys.exit(f"no raw key-list for {list_date}")


_dl_cache = {}

def sim_one(tkr, E, list_date, asof=None):
    """Simulate one signal. `asof` (datetime.date) truncates price history at that
    close — the position is marked/exited using only bars up to `asof`, giving a
    point-in-time view (used by tools/mtd_pnl.py for daily equity curves)."""
    try:
        if tkr in _dl_cache:
            df = _dl_cache[tkr].copy()
        else:
            df = pricecache.get(tkr, period="3y")
            _dl_cache[tkr] = df.copy() if df is not None else None
    except Exception as e:
        return dict(tkr=tkr, E=E, status="error", ret=None, note=str(e)[:40])
    if df is None or df.empty:
        return dict(tkr=tkr, E=E, status="no data", ret=None, note="")
    import pandas as pd
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close"]].copy()
    df = df.dropna(subset=["Open", "High", "Low", "Close"])  # drop forming/empty bars
    if df.empty:
        return dict(tkr=tkr, E=E, status="no data", ret=None, note="")
    if len(df) > 1 and df["Close"].pct_change().abs().max() > 0.60:
        # vendor series corrupted (bad split/adjustment seam) — don't simulate on it
        return dict(tkr=tkr, E=E, status="data suspect", ret=None, note="vendor history glitch")
    df["ema9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["ma50"] = df["Close"].rolling(TMA).mean()
    sim = df[df.index.date >= dt.date.fromisoformat(list_date)]
    if sim.empty:
        return dict(tkr=tkr, E=E, status="no data after date", ret=None, note="")

    # EXIT v3 — 50-SMA trend-hold: hold the full position until a daily CLOSE below
    # the TMA-day SMA; hard disaster stop DIS below entry. No breakeven, target, or
    # partial. Profit-lock: once the high reaches +ARM, ratchet the stop up to +LOCK
    # (protects big winners without capping upside). (Basis: structural-exit-test /
    # profit-protection tests 2026-07-25; validated 2024/2025/2026.)
    cur_stop = E * (1 - DIS)
    lock_trig, locked = E * (1 + ARM), False
    state, fill, realized = "waiting", None, 0.0
    exit_info = None   # (date, px, kind) set whenever the position closes
    entry_i = None     # bar index of the fill, for sessions-held (stale flag)
    notes = []
    def _f(x):
        return float(x) if x == x else None   # NaN-safe (early bars have no SMA)
    rows = [(d.date(), float(r.Open), float(r.High), float(r.Low), float(r.Close),
             float(r.ema9), _f(r.ma50)) for d, r in sim.iterrows()]
    if asof is not None:
        rows = [r for r in rows if r[0] <= asof]
        if not rows:
            return dict(tkr=tkr, E=E, status="no data after date", ret=None, note="")
    for i, (d, O, H, L, C, ema, ma50) in enumerate(rows):
        if state == "waiting":
            if i >= TRIGGER_DAYS:            # trigger expired — DAY order, not GTC
                break
            if O > E:                        # gapped above the trigger — never chase the open,
                if L <= E:                   # but the resting DAY limit fills if price REVISITS it
                    fill = E; state = "full"; entry_i = i
                    notes.append(f"{d} entry@{E:.2f} (gap-up revisited trigger)")
                else:
                    notes.append(f"{d} gap-up open {O:.2f} > trigger {E:.2f}, never revisited — no entry")
                    continue
            elif H >= E:
                fill = E; state = "full"; entry_i = i   # buy as price breaches the trigger
                notes.append(f"{d} entry@{fill:.2f}")
            else:
                continue
        if state == "full":                  # hold until 50-SMA close-break or disaster stop
            if L <= cur_stop:                # disaster stop (gap-down opens below -> fill at open)
                px = min(O, cur_stop)
                realized = px/fill - 1; state = "closed"
                exit_info = (d, px, "stop (gap-down)" if O < cur_stop else "disaster stop")
                notes.append(f"{d} STOP@{px:.2f}"); break
            if ma50 is not None and C < ma50:  # trend break — exit on the close
                realized = C/fill - 1; state = "closed"
                exit_info = (d, C, f"close<{TMA}SMA")
                notes.append(f"{d} exit close {C:.2f} < {TMA}SMA {ma50:.2f}"); break
            if not locked and H >= lock_trig:   # profit-lock arms at +ARM -> stop up to +LOCK
                cur_stop = max(cur_stop, E * (1 + LOCK)); locked = True
                notes.append(f"{d} profit-lock armed (+{int(ARM*100)}%) → stop +{int(LOCK*100)}%")
            continue

    lastC = rows[-1][4]
    last_ema = rows[-1][5]
    last_ma50 = rows[-1][6]
    if state == "waiting":
        return dict(tkr=tkr, E=E, status="not triggered", ret=0.0, fill=None, note="; ".join(notes))
    if state == "full":
        ret = (lastC/fill-1); status = "OPEN (trend)"
    else:
        ret = realized; status = "closed"
    out = dict(tkr=tkr, E=E, status=status, ret=ret, fill=fill, note="; ".join(notes),
               realized=realized if state != "full" else 0.0,
               entry_date=notes[0].split(" ")[0] if notes else "",
               days_held=(len(rows) - entry_i) if entry_i is not None else 0)
    if state == "full":   # live-position management fields
        out.update(last=lastC, stop_now=cur_stop, ema9=last_ema, ma50=last_ma50,
                   locked=locked, arm_px=fill*(1+ARM), lock_px=fill*(1+LOCK))
    if state == "closed" and exit_info:
        out.update(exit_date=str(exit_info[0]), exit_px=exit_info[1], exit_kind=exit_info[2])
    return out


_simlist_cache = {}
def sim_list(list_date, asof=None):
    """Backtest one list without printing. Returns (rows, aggregate-dict-or-None).
    `asof` truncates every simulation at that close (point-in-time view).

    Memoized by (list_date, asof): a pure, point-in-time function of day-fixed data.
    All three books call this for overlapping list dates at the same asof, and
    tools/mtd_pnl.py repeats it across ~18 closes — callers only ever read the rows
    or shallow-copy them (dict(r, ...)), never mutate in place, so sharing is safe."""
    key = (list_date, asof)
    if key in _simlist_cache:
        return _simlist_cache[key]
    raw = find_raw(list_date)
    rows = [sim_one(t, E, list_date, asof=asof) for t, E in uw.parse_entries(raw)]
    trig = [r for r in rows if r["ret"] is not None and r["status"] != "not triggered"]
    agg = None
    if trig:
        agg = dict(n=len(rows), trig=len(trig),
                   wins=sum(1 for r in trig if r["ret"] > 0),
                   avg=sum(r["ret"] for r in trig) / len(trig),
                   port=sum(r["ret"] * FULL_W for r in trig),
                   trades=trig)
    _simlist_cache[key] = (rows, agg)
    return rows, agg


def run_list(list_date, md):
    """Backtest one list; print to console and append a markdown section to `md`."""
    raw = find_raw(list_date)
    entries = uw.parse_entries(raw)
    rows = [sim_one(t, E, list_date) for t, E in entries]
    trig = [r for r in rows if r["ret"] is not None and r["status"] != "not triggered"]
    hdr = (f"Backtest of Key List {list_date} ({len(entries)} names) — exit v3: hold to a close "
           f"below the {TMA}-day SMA, disaster stop −{DIS*100:.0f}%")
    print(hdr + "\n")
    print(f"{'TKR':6}{'entry':>9}{'fill':>9}{'status':>16}{'return%':>9}  notes")
    md.append(f"## {list_date}")
    md.append("| Ticker | Entry | Fill | Status | Return % |")
    md.append("| --- | ---: | ---: | --- | ---: |")
    for r in sorted(rows, key=lambda x: (x['ret'] is None, -(x['ret'] or -99))):
        ret = "—" if r["ret"] is None else f"{r['ret']*100:+.2f}"
        fill = r.get("fill"); fills = f"{fill:.2f}" if fill else "—"
        print(f"{r['tkr']:6}{r['E']:9.2f}{fills:>9}{r['status']:>16}{ret:>9}  {r.get('note','')}")
        md.append(f"| {r['tkr']} | {r['E']:.2f} | {fills} | {r['status']} | {ret} |")
    if trig:
        avg = sum(r["ret"] for r in trig)/len(trig)
        port = sum(r["ret"]*FULL_W for r in trig)
        wins = [r for r in trig if r["ret"] > 0]
        s1 = f"Triggered: {len(trig)}/{len(rows)} | win rate {len(wins)}/{len(trig)} = {100*len(wins)/len(trig):.0f}%"
        s2 = f"Avg return per triggered position: {avg*100:+.2f}%"
        s3 = f"Portfolio P&L (each full=10% weight): {port*100:+.2f}% of equity (realized+open)"
        print("\n" + s1 + "\n" + s2 + "\n" + s3 + "\n")
        md.append(f"\n**{s1}. {s2}. {s3}.**\n")
    else:
        print("\nNo names triggered in the window.\n")
        md.append("\n_No names triggered in the window._\n")


def main():
    dates = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not dates:
        sys.exit("usage: python tools/backtest.py YYYY-MM-DD [YYYY-MM-DD ...]")
    run = dt.date.today().isoformat()
    md = [f"---\ntype: analysis\ntags: [backtest, key-list]\ncreated: {run}\n---\n",
          f"# Backtest — run {run}",
          f"Auto-generated by `tools/backtest.py`. Exit v3 ([[key-list-trade-rules]]): hold the full position "
          f"to a daily close below the {TMA}-day SMA; disaster stop −{DIS*100:.0f}%. Each full position = "
          f"{int(FULL_W*100)}% of equity. Mostly open positions marked to last close; daily-bar gap-day "
          "ambiguity can understate gappers (see [[backtest-2026-06-18]]).\n"]
    for d in dates:
        run_list(d, md)
    out = os.path.join(uw.WIKI, "analysis", f"backtest-{run}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"[wrote {out}]")


if __name__ == "__main__":
    main()
