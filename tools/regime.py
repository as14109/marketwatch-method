#!/usr/bin/env python3
"""
Regime gate — computed daily market-health score (strategy-review rec #1).

8 checks, one point each (mirrors the Trend Template style):
  1. SPY > 21-day SMA                      (primary trend, near)
  2. SPY > 50-day SMA                      (primary trend, intermediate)
  3. QQQ > 21-day SMA                      (growth tape)
  4. IWM > 21-day SMA                      (small caps participating)
  5. RSP/SPY ratio > its 21-day mean       (equal-weight breadth healthy)
  6. VIX < 20                              (volatility calm)
  7. VIX < its 10-day SMA                  (volatility falling)
  8. SPY distribution days <= 4 in last 25 (IBD-style: down >0.2% on higher volume)

Score -> allowed NEW entries per day (per portfolio-plan §1):
  7-8  CONFIRMED UPTREND  -> up to 3-5 new entries (pyramid tape)
  4-6  NEUTRAL/SELECTIVE  -> 1-2 pilots only, best validated setups
  0-3  DISTRIBUTION       -> 0 new entries; manage exits, raise cash

Splices the result between the REGIME markers in overview.md. Importable:
compute() returns (score, verdict, allowed, details) for the emailed report.

Usage: python tools/regime.py
"""
import sys, os, re
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import yfinance as yf
import pricecache
import pandas as pd

START, END = "<!-- REGIME:START -->", "<!-- REGIME:END -->"


_dl = {}

def _series(tkr, field="Close", asof=None):
    if tkr not in _dl:
        _dl[tkr] = pricecache.get(tkr, period="3y")
    df = _dl[tkr]
    if df is None or df.empty:
        return None, None
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy(); df.columns = df.columns.get_level_values(0)
    if asof:  # point-in-time: only bars strictly BEFORE the list's trading day
        df = df[df.index.date < asof]
    return df[field].dropna(), (df["Volume"].dropna() if "Volume" in df else None)


_compute_cache = {}
def compute(asof=None):
    """Memoized wrapper: the regime score is a pure, point-in-time function of `asof`
    and the day-fixed price data, so cache it. This collapses the thousands of
    redundant recomputes that tools/mtd_pnl.py triggers (all 3 books re-simulated at
    every close call regime.compute for every prior list date)."""
    if asof not in _compute_cache:
        _compute_cache[asof] = _compute_impl(asof)
    return _compute_cache[asof]


def _compute_impl(asof=None):
    """Regime score from data through the close before `asof` (a datetime.date);
    asof=None -> latest close. Used point-in-time by tools/gated_book.py."""
    spy, spy_vol = _series("SPY", asof=asof)
    qqq, _ = _series("QQQ", asof=asof)
    iwm, _ = _series("IWM", asof=asof)
    rsp, _ = _series("RSP", asof=asof)
    vix, _ = _series("^VIX", asof=asof)

    checks = {}
    checks["1 SPY>21d"] = float(spy.iloc[-1]) > float(spy.rolling(21).mean().iloc[-1])
    checks["2 SPY>50d"] = float(spy.iloc[-1]) > float(spy.rolling(50).mean().iloc[-1])
    checks["3 QQQ>21d"] = float(qqq.iloc[-1]) > float(qqq.rolling(21).mean().iloc[-1])
    checks["4 IWM>21d"] = float(iwm.iloc[-1]) > float(iwm.rolling(21).mean().iloc[-1])
    ratio = (rsp / spy.reindex(rsp.index)).dropna()
    checks["5 breadth RSP/SPY>21d"] = float(ratio.iloc[-1]) > float(ratio.rolling(21).mean().iloc[-1])
    checks["6 VIX<20"] = float(vix.iloc[-1]) < 20.0
    checks["7 VIX falling"] = float(vix.iloc[-1]) < float(vix.rolling(10).mean().iloc[-1])
    rets = spy.pct_change().iloc[-25:]
    volu = spy_vol.pct_change().iloc[-25:]
    dist = int(((rets < -0.002) & (volu > 0)).sum())
    checks[f"8 distribution days<=4 (n={dist})"] = dist <= 4

    score = sum(checks.values())
    if score >= 7:
        verdict, allowed = "CONFIRMED UPTREND", "3-5"
    elif score >= 4:
        verdict, allowed = "NEUTRAL / SELECTIVE", "1-2 (pilots, best setups only)"
    else:
        verdict, allowed = "DISTRIBUTION / RISK-OFF", "0 (manage exits, raise cash)"
    return score, verdict, allowed, checks


def main():
    score, verdict, allowed, checks = compute()
    lines = [f"**Regime score: {score}/8 — {verdict}** · allowed new entries today: **{allowed}**", ""]
    for k, v in checks.items():
        line = f"- {'✅' if v else '❌'} {k}"
        lines.append(line)
    lines.append("")
    lines.append("_Computed by `tools/regime.py` ([[strategy-review-2026-07-07]] rec #1). Gate per "
                 "[[portfolio-plan]] §1: only press in a confirmed uptrend._")
    table = "\n".join(lines)
    print(table.replace("[[", "").replace("]]", ""))

    ov = os.path.join(uw.WIKI, "overview.md")
    text = open(ov, encoding="utf-8").read()
    block = f"{START}\n{table}\n{END}"
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.DOTALL)
        open(ov, "w", encoding="utf-8").write(text)
        print(f"\n[updated regime block in {ov}]")
    else:
        print(f"\n[REGIME markers not found in {ov}]")


if __name__ == "__main__":
    main()
