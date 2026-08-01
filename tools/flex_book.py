#!/usr/bin/env python3
"""
Flex book — the gated book of record's SELECTION with regime-conditioned EXITS.

Motive: [[drift-review-2026-07-25]] proved our stock selection is good (the gated
picks, simply held, ~match the indices) but the fixed exit rules (−5% stop, BE@+7%,
sell½@+12%, 9-EMA trail) give the whole edge back by whipsawing winners. This book
keeps the gated book's entry selection *exactly* (same TT gate, regime order count,
extension filter, cooldown, caps) and swaps in exits that adapt to the regime score
AT ENTRY:

  score 7-8 (confirmed uptrend): stop −8%, NO target, trail 21-EMA   → let leaders run
  score 4-6 (neutral):           stop −6%, sell ⅓ @+20%, trail 21-EMA → give room, bank some
  score ≤3 (distribution):       stop −5%, BE@+7%, sell½@+12%, 9-EMA  → = current (unused; ≤3 → 0 orders)

The book of record's engine (tools/backtest.py) is NOT modified. Entry detection
reuses backtest.sim_one (fill/date are independent of exit params); the exit is a
parametric replica validated to ±0.05% of the engine on the current rules.

This is a PARALLEL research book — not the book of record. Validate out-of-sample
before adopting. Usage: python tools/flex_book.py [--current]  (--current = apply
the current rules to every entry, to prove parity with the gated book).
"""
import sys, os, re, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import backtest, regime, classify, pricecache
import validate_list as vl
import gated_book
import pandas as pd

# --- regime-conditioned exit parameter sets ------------------------------------
CURRENT = dict(stop=0.05, be=0.07, t1=0.12, t1_frac=0.5, trail=9)   # today's rules

def exit_params(score, force_current=False):
    if force_current:
        return CURRENT
    if score >= 7:      # confirmed uptrend — widest room, let leaders run
        return dict(stop=0.10, be=None, t1=0.30, t1_frac=1/3, trail=21)
    if score >= 4:      # neutral — wide stop, bank a partial high, trail the rest
        return dict(stop=0.08, be=None, t1=0.25, t1_frac=1/3, trail=21)
    return CURRENT      # distribution (≤3 → 0 orders, so effectively unused)


# A1 — volume confirmation on entry (Weinstein/O'Neil/Darvas): require the
# breakout-day volume >= VOL_MULT x the trailing 50-day average. None = off.
VOL_MULT = None
_vol = {}
def vol_confirmed(tkr, list_date):
    """True if the trigger-day (list_date) volume >= VOL_MULT x its prior 50-day
    average. Fail-OPEN (True) when volume data is missing/short, so the filter
    only ever REMOVES clearly light-volume breakouts."""
    if not VOL_MULT:
        return True
    import pandas as pd, datetime as _dt
    if tkr not in _vol:
        df = pricecache.get(tkr, period="3y")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        _vol[tkr] = df["Volume"].dropna() if (df is not None and "Volume" in df) else None
    v = _vol[tkr]
    if v is None:
        return True
    ld = _dt.date.fromisoformat(list_date)
    hist = v[v.index.date <= ld]
    if len(hist) < 51:
        return True
    day_vol = float(hist.iloc[-1])
    avg50 = float(hist.iloc[-51:-1].mean())
    return avg50 <= 0 or day_vol >= VOL_MULT * avg50


_bars = {}
def bars(tkr, entry_date, asof):
    key = (tkr,)
    if key not in _bars:
        df = pricecache.get(tkr, period="3y")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close"]].dropna()
        df["e9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["e21"] = df["Close"].ewm(span=21, adjust=False).mean()
        df["ma21"] = df["Close"].rolling(21).mean()
        df["ma50"] = df["Close"].rolling(50).mean()
        df["ma200"] = df["Close"].rolling(200).mean()
        _bars[key] = df
    df = _bars[key]
    ed = dt.date.fromisoformat(entry_date)
    sl = df[df.index.date >= ed]
    if asof is not None:
        sl = sl[sl.index.date <= asof]
    def g(v):
        return float(v) if v == v else None   # NaN -> None
    return [(d.date(), float(r.Open), float(r.High), float(r.Low), float(r.Close),
             float(r.e9), float(r.e21), g(r.ma21), g(r.ma50), g(r.ma200))
            for d, r in sl.iterrows()]


def flex_exit(tkr, fill, entry_date, p, asof=None):
    """Parametric exit from the fill. Returns dict(ret, exit_date, exit_kind,
    status, days_held). Mirrors backtest.sim_one's daily-bar exit handling
    (gap-down closes at the open) with configurable stop/target/trail."""
    rows = bars(tkr, entry_date, asof)
    if not rows:
        return dict(ret=0.0, exit_date=None, exit_kind=None, status="no data", days_held=0)

    # --- structural hold-the-trend mode: hold the FULL position until a daily close
    #     below the N-day SMA (hold_sma), with an optional disaster stop underneath.
    #     Low-parameter (1-2 knobs) -> far less overfit-prone than tuned stop/target. ---
    hs = p.get("hold_sma")
    if hs:
        smacol = {21: 7, 50: 8, 200: 9}[hs]      # index into the bars tuple
        stop = fill * (1 - p["stop"]) if p.get("stop") else None
        # optional PROFIT-PROTECTION knobs (all default off -> pure trend-hold):
        be_lock = p.get("be_lock")               # once high>=fill*(1+be_lock) -> stop to entry
        lock_at, lock_to = p.get("lock_at"), p.get("lock_to")   # ratchet stop to +lock_to at +lock_at
        gb_arm, gb = p.get("gb_arm"), p.get("gb")               # give-back trail: exit if close<peak*(1-gb) once armed
        pt_at, pt_frac = p.get("ptake_at"), p.get("ptake_frac") # sell pt_frac at +pt_at (partial)
        realized, remaining, armed, peak_close = 0.0, 1.0, False, fill
        for i, row in enumerate(rows):
            d, O, H, L, C = row[0], row[1], row[2], row[3], row[4]
            sma = row[smacol]
            if stop is not None and L <= stop:       # stop (incl. ratcheted profit stop)
                px = min(O, stop)
                return dict(ret=realized + remaining * (px / fill - 1), exit_date=str(d),
                            exit_kind=("stop (gap-down)" if O < stop else "stop"),
                            status="closed", days_held=i + 1)
            if pt_at and remaining >= 1.0 and H >= fill * (1 + pt_at):   # high partial (once)
                realized += pt_frac * pt_at; remaining -= pt_frac
            if sma is not None and C < sma:          # 50-SMA trend break — exit the rest
                return dict(ret=realized + remaining * (C / fill - 1), exit_date=str(d),
                            exit_kind=f"close<{hs}SMA", status="closed", days_held=i + 1)
            if gb_arm and gb:                        # give-back trailing exit
                if C >= fill * (1 + gb_arm): armed = True
                peak_close = max(peak_close, C)
                if armed and C < peak_close * (1 - gb):
                    return dict(ret=realized + remaining * (C / fill - 1), exit_date=str(d),
                                exit_kind=f"giveback {int(gb*100)}%", status="closed", days_held=i + 1)
            if stop is not None:                     # ratchet the hard stop up (protect profit)
                if be_lock and H >= fill * (1 + be_lock):
                    stop = max(stop, fill)
                if lock_at and lock_to and H >= fill * (1 + lock_at):
                    stop = max(stop, fill * (1 + lock_to))
        return dict(ret=realized + remaining * (rows[-1][4] / fill - 1), exit_date=None,
                    exit_kind=None, status="OPEN (trend)", days_held=len(rows))

    stop = fill * (1 - p["stop"])
    be_trig = fill * (1 + p["be"]) if p["be"] else None
    t1 = fill * (1 + p["t1"]) if p["t1"] else None
    remaining, realized, be_on, state = 1.0, 0.0, False, "full"
    for i, (d, O, H, L, C, e9, e21, ma21, ma50, ma200) in enumerate(rows):
        ema = e21 if p["trail"] == 21 else e9
        if state == "full":
            if t1 is not None and O >= t1:                 # gap through target
                px = max(O, t1); realized += p["t1_frac"] * (px / fill - 1)
                remaining -= p["t1_frac"]; state = "half"
            elif L <= stop:                                # stop (gap-down -> open)
                px = min(O, stop); realized += remaining * (px / fill - 1)
                kind = ("stop (gap-down)" if O < stop else
                        ("stop (breakeven)" if be_on and stop >= fill else "stop"))
                return dict(ret=realized, exit_date=str(d), exit_kind=kind, status="closed", days_held=i + 1)
            elif t1 is not None and H >= t1:               # target intraday
                realized += p["t1_frac"] * (t1 / fill - 1)
                remaining -= p["t1_frac"]; state = "half"
            if t1 is None and p.get("full_trail") and C < ema:  # opt-in: trail the whole position
                realized += remaining * (C / fill - 1)
                return dict(ret=realized, exit_date=str(d), exit_kind=f"trail<{p['trail']}EMA",
                            status="closed", days_held=i + 1)
            if be_trig is not None and H >= be_trig and not be_on:
                be_on = True; stop = max(stop, fill)
            continue
        if state == "half":                                # trail the runner
            if L <= stop:
                px = min(O, stop); realized += remaining * (px / fill - 1)
                return dict(ret=realized, exit_date=str(d), exit_kind="runner stop",
                            status="closed", days_held=i + 1)
            if C < ema:
                realized += remaining * (C / fill - 1)
                return dict(ret=realized, exit_date=str(d), exit_kind=f"runner<{p['trail']}EMA",
                            status="closed", days_held=i + 1)
    lastC = rows[-1][4]
    ret = realized + remaining * (lastC / fill - 1)
    status = "OPEN (full)" if state == "full" else "OPEN (runner)"
    return dict(ret=ret, exit_date=None, exit_kind=None, status=status, days_held=len(rows))


def simulate(asof=None, force_current=False):
    """Gated selection loop (identical to gated_book) with regime-conditioned exits."""
    spy = vl.series("SPY")
    open_pos, closed, skipped, daily = [], [], [], []
    cooldown = {}
    group_cap_n = max(1, int(uw.MAX_POSITIONS * uw.GROUP_CAP))

    for d in gated_book.all_dates():
        dd = dt.date.fromisoformat(d)
        if asof is not None and dd > asof:
            break
        # roll positions closed before this list's trading day
        still = []
        for pos in open_pos:
            if pos.get("exit_date") and dt.date.fromisoformat(pos["exit_date"]) < dd:
                closed.append(pos)
                if pos["ret"] <= 0 and "stop" in (pos.get("exit_kind") or ""):
                    cooldown[pos["tkr"]] = dt.date.fromisoformat(pos["exit_date"])
            else:
                still.append(pos)
        open_pos = still

        try:
            score, verdict, _, _ = regime.compute(asof=dd)
        except Exception:
            score, verdict = 8, "unavailable (ungated)"
        n_orders, pilot = gated_book.allowed(score)
        day = dict(date=d, score=score, orders=0, filled=0, pilot=pilot)
        daily.append(day)
        if n_orders == 0:
            continue

        try:
            rows, _ = backtest.sim_list(d, asof=asof)
        except Exception:
            continue
        sim = {r["tkr"]: r for r in rows}
        held = {p["tkr"] for p in open_pos}

        cands = []
        for tkr, entry in uw.parse_entries(backtest.find_raw(d)):
            r = sim.get(tkr)
            if not r or r["ret"] is None:
                continue
            if tkr in held:
                skipped.append((d, tkr, "already held")); continue
            cd = cooldown.get(tkr)
            if cd and (dd - cd).days <= uw.COOLDOWN_DAYS:
                skipped.append((d, tkr, f"cooldown (stopped {cd})")); continue
            passed, fails = vl.check(tkr, spy, asof=dd)
            if passed != 8:
                skipped.append((d, tkr, f"TT {passed if passed is not None else '—'}/8")); continue
            c = vl.series(tkr, asof=dd)
            ma21 = float(c.rolling(21).mean().iloc[-1]); last = float(c.iloc[-1])
            if entry / ma21 - 1 > uw.EXT_MAX_PCT:
                skipped.append((d, tkr, "extended")); continue
            if not vol_confirmed(tkr, d):                    # A1: breakout-day volume gate
                skipped.append((d, tkr, "low volume")); continue
            cands.append(dict(tkr=tkr, entry=entry, near=last / entry, sim=r))

        cands.sort(key=lambda x: -x["near"])
        p = exit_params(score, force_current)
        for cnd in cands:
            if day["orders"] >= n_orders:
                break
            if len(open_pos) >= uw.MAX_POSITIONS:
                skipped.append((d, cnd["tkr"], "book full")); continue
            grp, is_etf = classify.group(cnd["tkr"])
            if sum(1 for pos in open_pos if pos["group"] == grp) >= group_cap_n:
                skipped.append((d, cnd["tkr"], f"group cap ({grp})")); continue
            day["orders"] += 1
            r = cnd["sim"]
            if r["status"] == "not triggered":
                skipped.append((d, cnd["tkr"], "order placed, never triggered")); continue
            day["filled"] += 1
            w = uw.FULL_POSITION_PCT * (uw.PILOT_FRACTION if pilot else 1) * (uw.ETF_FRACTION if is_etf else 1)
            ex = flex_exit(cnd["tkr"], r["fill"], r["entry_date"], p, asof=asof)
            open_pos.append(dict(tkr=cnd["tkr"], list_date=d, entry_date=r["entry_date"],
                                 fill=r["fill"], weight=w, group=grp, etf=is_etf, pilot=pilot,
                                 score_at_entry=score, **ex))
    return open_pos, closed, skipped, daily


def total(open_pos, closed):
    return sum(p["ret"] * p["weight"] for p in open_pos + closed
               if isinstance(p["ret"], (int, float)))


def main():
    force = "--current" in sys.argv
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = float(re.sub(r"[,$\s]", "", eq_raw)) if eq_raw else 1_000_000.0
    op, cl, sk, dl = simulate(force_current=force)
    tot = total(op, cl)
    label = "CURRENT rules (parity check)" if force else "REGIME-CONDITIONED exits"
    wins = [p for p in cl if p["ret"] > 0]
    print(f"Flex book — {label}")
    print(f"  {len(op)} open + {len(cl)} closed · total {tot*100:+.2f}% of equity ≈ ${tot*equity:+,.0f}")
    if cl:
        print(f"  closed win rate {100*len(wins)/len(cl):.0f}%  "
              f"avg win {sum(p['ret'] for p in wins)/max(1,len(wins))*100:+.2f}%  "
              f"avg loss {sum(p['ret'] for p in cl if p['ret']<=0)/max(1,len(cl)-len(wins))*100:+.2f}%")


if __name__ == "__main__":
    main()
