---
type: analysis
tags: [strategy, review, risk-management, expectancy, recommendations]
created: 2026-07-07
---

# Strategy review — recommendations to raise profits & cut risk (2026-07-07)

Synthesis of three weeks of measured results (backtests, [[stop-target-optimization-2026-07-02]],
[[pnl-report-2026-07-07]], [[backtest-validation-2026-06-28]]) against the ingested playbooks
([[expectancy]], [[eight-keys]], [[momentum-masters-minervini]], [[can-slim]], [[seven-bells]],
[[auction-market-theory]]). **Process recommendations, not financial advice — user decides.**

## What the data already proved
- **Regime is the whole ballgame.** The one distribution-week list (06-22) lost −$35.8k by itself;
  rebound-week lists made +$22.6k. Every rule refinement combined moved P&L less than one regime call.
- **Discipline layers each paid:** −5% stop (vs −3%), day-only triggers, no-gap entries — 135 → 57
  signals, all-signals P&L −$13.8k → **+$7.3k**. Fewer, cleaner trades > more trades.
- **The book over-diversifies:** 27 open positions vs. the masters' 8–12 max. Equal $50k to every
  trigger regardless of quality or regime.

## Recommendations (prioritized by expected impact)

### 1. Mechanize the regime gate ⭐ highest impact, directly evidenced
Today the regime lives in prose. Make it a computed score the routine prints daily, e.g.:
SPY vs 21/50-day, **equal-weight vs cap-weight trend**, % of open book above its 9-EMA, VIX level/trend,
IBD-style distribution-day count. Map score → allowed new entries: **0 in distribution / 1–2 in neutral /
3–5 in confirmed uptrend** ([[eight-keys]] "trade small before you trade big"; CAN SLIM "M").
*Evidence: would have zeroed the 06-22/06-23 damage — the single biggest P&L lever we've measured.*

### 2. Take only Trend-Template passers, cap 3–5 new entries/day
We built the validator; wire it as a **hard filter** + take the *top* setups only (the source itself
says "3–5 is plenty"). First **test it**: backtest TT-passers vs. failers point-in-time (truncate price
history at each list date). *Hypothesis from live data: AMZN 5/8 flag, ETF failers (SKYY/CLOU/ARKK) —
the filter already discriminates.*

### 3. Portfolio heat cap + rotation (risk)
Cap the open book at **10–12 positions** (masters' consensus). When full and a better validated setup
triggers, apply **Ryan's 2-for-1 rule**: sell half of the two weakest (vs 9-EMA distance) to fund the
new name. Add a **results-gated total-heat rule** (Ritchie II): open risk ≤1% of equity after a losing
week → scale to 2–3% only after banked wins.

### 4. Earnings guard (risk)
Never carry full size into an earnings report (source rule; the MU episode). Add an earnings-date check
(yfinance calendar) to `validate_list.py` and the report: flag names reporting within N days; halve or
skip. *Gap-down exits protect us after the fact; this avoids the coin-flip entirely.*

### 5. Risk-equalized sizing (open item in [[overview]])
Replace flat $50k with **size = risk budget ÷ stop distance** (risk $2,500/name constant). With chart-
based stops later, this also lets tighter setups take larger size at equal risk ([[expectancy]]).

### 6. Pyramid re-listed winners (profit)
The service re-lists open winners as "add-ons" (MU, CRWD, LTH…); our sim ignores them. Model adds per
[[pyramid-50-30-20-strategy]] (add ~half the current size at the new trigger, stop for the add at its
own −5%). *This is where the books say the big money compounds — currently unmodeled upside.*

### 7. Let runners run longer (profit)
The 9-EMA trail cuts runners fast in normal chop. Test: after a runner reaches **+20%**, trail the
**21-day MA** instead (Minervini holds leaders through 9-EMA noise; sweep already hinted wider exits
help). Extend `optimize_rules.py` to sweep trail variants.

### 8. Intraday-precision backtest (accuracy, longstanding item)
15-min bars would resolve same-day stop/target ordering and give clean fills for the ambiguous days.

## Suggested order of adoption
**Now:** #1 regime score + #2 TT-filter/cap (both are selection-layer, no new risk).
**Next:** #3 heat cap + #4 earnings guard (pure risk reduction).
**Then, after testing:** #5–#7 (sizing/pyramiding/trailing — need sweeps first).

> Keep re-running `optimize_rules.py` and `cumulative_pnl.py` monthly; every rule here should stay
> falsifiable against our own data. Not financial advice.
