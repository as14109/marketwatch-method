---
type: analysis
tags: [strategy, backlog, books, risk-management, profit-maximization, review]
created: 2026-07-22
---

# Books re-read → actionable backlog (2026-07-22)

Re-read all six ingested books ([[think-and-trade-like-a-champion-minervini]],
[[momentum-masters-minervini]], [[master-swing-trader-farley]], [[steidlmayer-on-markets]],
[[high-probability-trade-setups-knight]], [[trade-chart-patterns-like-the-pros-duddella]]) and
cross-referenced their teachings against **our measured July results** and what's **already built**.

## What the month proved (the lens)
- **Profits came from runners held for weeks** (the few winners that trended). → *amplify winners.*
- **Losses came from failed breakouts in a chop/distribution tape** (benchmark −$97k, 12% closed win rate
  in [[drift-review-2026-07-11]]). → *cut losers faster + stop buying breakouts in weak regimes.*
- **The regime gate was the biggest lever** and is already in. → *time its flip better; add profit-side rules.*

## Already implemented (don't re-litigate)
Regime gate · Trend-Template 8/8 filter · extension filter · cooldown · heat caps (≤12 / 25% group / ETF ×½)
· pilot sizing · stale flag · day-only triggers · no-gap-up entry · gap-down exit · 3 parallel books · MTD
scoreboard. (v2.1 — [[process-improvements-2026-07-09]], [[strategy-review-2026-07-07]].)

## The backlog — prioritized, each testable against our engine

### TIER 1 — attack the loss source (biggest measured problem)
- **B1. Earnings guard/exit** — ✅ **advisory shipped 2026-07-23** (`tools/earnings.py`; report excludes
  names reporting ≤`EARN_GUARD_DAYS`=7 from the buy shortlist + an ⚠ earnings line flags held names to trim).
  **Measurement:** re-ran the actual July book trades — **0 of 16 gated / 0 of 7 ideal trades entered within
  7 days of an earnings report** (the disciplined books naturally avoided pre-earnings entries in the
  distribution regime), so the sim-modeling half (skip earnings entries in the backtest) had **$0 measured
  impact → deferred** as unnecessary complexity. The forward-looking value is the *trim-held-into-earnings*
  advisory (e.g. 07-23 flagged AAPL 7d out, held). Revisit the sim rule only if a future month shows the
  books taking pre-earnings entries. *(Minervini + Zanger; = [[strategy-review-2026-07-07]] #4.)*
- **B2. Violation-based early exits** *(Minervini's post-buy "violations" checklist).* Beyond the −5% stop,
  exit early on: heavy-volume reversal after a low-volume breakout · a close **below the 20- or 50-day right
  after a breakout** · 3–4 consecutive lower lows · more down days than up on rising volume. Model in
  `backtest.py`; measure vs the current stop-only exits. *Cuts failed breakouts before they hit −5%.*
  **High · medium.**
- **B3. Pullback-entry mode in weak regimes** *(Farley Dip Trip / First Pullback + Steidlmayer "buy below
  value").* When regime <7, prefer **buying strength into support** (near the 21-EMA / prior pivot) over
  chasing the breakout that fails in chop. Backtest pullback vs breakout fills in NEUTRAL/distribution.
  *Directly addresses the chop-tape breakout tax.* (= [[drift-review-2026-07-11]] #2.) **High · medium.**

### TIER 2 — amplify the profit source (winners)
- **B4. Pyramid / add to winners** *(Ryan: "only add to winners after new bases"; [[pyramid-50-30-20-strategy]]).*
  Model adds when a held name re-lists or confirms (+7%/BE) — concentrate into what's working instead of
  spreading into new breakouts. *Where the books say the big money compounds; currently unmodeled upside.*
  (= [[strategy-review-2026-07-07]] #6.) **Medium-high · medium.**
- **B5. Let runners run longer** *(Ryan: "don't cap winners"; that 20% becomes 300%).* After a runner is
  **+20%**, switch the trail from the 9-EMA to the **21-day** (or a chandelier/ATR trail) so it isn't shaken
  out early. Extend `optimize_rules.py` to sweep trail variants. **Medium · easy to test.**
- **B6. Follow-through-day regime timing** *(O'Neil/CAN SLIM "M").* Add an explicit **follow-through day**
  detector (rally day 4–7, index +~1.5% on higher volume) to sharpen when the regime flips risk-off → risk-on,
  and a "3 distribution days in a tight window → step back" rule. *Times the gate's re-engagement — the
  single biggest lever.* **Medium · feasible.**

### TIER 3 — selectivity & edge refinement
- **B7. Cross-verification ranking** *(Farley).* Rank the buy shortlist by **confluence** — how many of
  {9/21/50/200-day MA, prior highs, round number} cluster near the pivot. Buy the highest-confluence setups
  first. *Cheap, novel, improves which pilots we take when slots are scarce.* **Low-risk · feasible.**
- **B8. Risk-equalized / chart-based stops** *(Minervini "back into risk"; Farley/Knight technical stops).*
  Test a stop placed **below the last VCP contraction / base low** with size adjusted so risk = a fixed
  0.25–0.5% of equity, vs the flat −5%. *May beat the flat stop on volatile names.* **Medium · needs a sweep.**
- **B9. Results-gated total-heat ladder** *(Ritchie II).* Scale **total open risk** with banked results:
  ~1% equity when struggling → 2–3% working → up to 5% only after profits. Formalize on top of the regime
  gate. **Low-medium.**
- **B10. 7-Bells / Pattern-Cycle phase tags** *(Farley).* Tag each watchlist name by setup type (Dip Trip
  pullback · Coiled Spring base · 3rd Watch breakout) for context and to route B3's entry method.
  **Low (nice-to-have).**

## Suggested run order tomorrow
1. **B1 earnings guard** — highest value, self-contained, feasible in one session.
2. **B6 follow-through-day** — sharpens the top lever; then **B5 longer trail** (quick sweep).
3. Backtest **B2 violations** and **B3 pullback-entries** (both need engine work + a measured comparison
   before adopting — don't adopt on theory).
4. Defer B4/B7/B8/B9/B10 to later, adopting each only if a backtest shows it earns its place.

> Method note: every item ships only after it's **measured against our 3-book engine** (gated / ideal /
> benchmark) and the MTD scoreboard — the same falsifiable discipline as the earlier reviews. Not financial advice.
