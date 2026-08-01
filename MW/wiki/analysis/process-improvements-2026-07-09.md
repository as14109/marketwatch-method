---
type: analysis
tags: [strategy, process, expectancy, risk-management, recommendations]
created: 2026-07-09
---

# Process improvements for profitability — expert synthesis (2026-07-09)

> [!success] Implemented 2026-07-09 (same day, user-approved) as **discipline layer v2.1**
> All 6 tweaks are live: `tools/gated_book.py` (disciplined parallel sim: #1 gated book, #2 cooldown,
> #3 extension filter, #4 pilot sizing, #5 heat caps), ⏳stale flags in `open_positions.py` (#6,
> flag-only), Action-read flags + pilot/ETF-sized order plan in the report and `tos_orders.py`.
> Constants in `tools/update_watchlist.py`; rules doc [[key-list-trade-rules]] §Discipline layer.
> First reading: gated book **−0.06% eq** vs every-signal single-account book **−0.60% eq**
> (open +6.89% + closed −7.49%) — the discipline is ahead by ~$5.4k with 12 positions vs 33.

Follow-up to [[strategy-review-2026-07-07]] with two more days of data (July realized book now
1W/13L, −$25.3k; open book +$68.9k across 33 positions). Synthesizes the ingested playbooks
([[think-and-trade-like-a-champion-minervini]], [[momentum-masters-minervini]], [[can-slim]],
[[master-swing-trader-farley]], [[steidlmayer-on-markets]]) against our own backtest evidence.
**Process recommendations, not financial advice — user decides.**

## Where the P&L actually comes from (measured)
- **Winners are concentrated in runners.** Every big open gain is a name that reached +12% and
  trails (ASTH +14%, HACK +14%, LTH/FTNT/DDOG +12%). The system's edge = a few trends held long.
- **Losses are churn, not catastrophe.** July's 13 realized losses are almost all clean −5%/−$2.5k
  stops. The killers are *re-entries into the same name* (CRWD stopped 07-02 and 07-06 lists, DELL
  stopped 07-08 then re-entered 07-09, DDOG stopped from three lists while the 06-29 runner wins)
  and *same-day stop-outs* (trigger hit late in an extended move, reversed intraday).
- **The gate exists but nothing obeys it.** Regime said 1–2 pilots on 07-08/07-09; the sim book
  took every trigger (10/15 on 07-09) and sits at 33 positions ≈ $1.65M notional on a $1M book —
  nearly 3× the masters' 8–12-name concentration guidance.

## Prioritized tweaks

### 1. Run a second, *gated* book (measure the discipline we already designed)
The every-signal sim measures list quality; it can't tell us what following our own rules earns.
Add a parallel simulation: regime-allowed count × Trend-Template passers only × top-N by setup
quality (closest-to-pivot, group leadership). Report both books side by side.
*Basis: [[can-slim]] "M", [[eight-keys]] progressive exposure; our 06-22 distribution-week list
lost −$35.8k alone — the regime call dwarfs every other refinement combined.*

### 2. Re-entry cooldown after a stop-out
After a name stops out, skip re-triggers unless it builds a new setup — proxy: N trading days
(start with 5) or price reclaiming the 21-day MA. CRWD/DELL/DDOG July churn is the direct evidence.
*Basis: Minervini re-enters only on a proper re-setup; Zanger cuts and moves on. Testable in
`backtest.py` with a cooldown flag.*

### 3. Extension filter at entry (don't buy stretched pivots)
Several same-day stop-outs entered far above the short MAs. Skip (or half-size) triggers >~8%
above the 21-day MA. Sweepable from our own trade log: stop-out rate vs. entry distance-to-21MA.
*Basis: Minervini buys the pivot of a proper base, not extension; Farley [[cross-verification]]
wants MAs clustered near the pivot; [[value-area]] logic — initiating trades far from value fail
more often in balanced tape.*

### 4. Pilot sizing in NEUTRAL regime
The gate caps the *count* (1–2) but every entry is still full $50k. In regime 4–6, enter at half
size ($25k), add the second half only on follow-through (+3–4% or a strong-volume confirmation
day). *Basis: [[eight-keys]] "trade small before you trade big"; [[smart-add-on-strategy]].
Halves the cost of being wrong in chop, where our data says most losses live.*

### 5. Sector & ETF heat caps
Tonight's book: 8 of 33 are ETFs (24%) and ~9 more are one theme (cyber/cloud/software). A single
group reversal hits half the book at once, and ETFs double the regime beta we already carry.
Cap: ≤25% of open positions per group, ETFs at half size (they rarely reach +12% fast; they are
the market we're already gating on). *Basis: masters' group-exposure discipline; O'Neil
concentrates in leading stocks, not averages.*

### 6. Time stop for dead money
ETON sat 8 sessions going nowhere and exited at breakeven; capital and attention were parked.
Flag (then exit) positions <+2% after 10 sessions — rotate into the day's best validated setup
(Ryan's 2-for-1). *Basis: Zanger/Minervini — if it doesn't perform promptly it's wrong; opportunity
cost is a real cost. Add a "stale" flag to `open_positions.py` first, measure before enforcing.*

### Still open from [[strategy-review-2026-07-07]]
Earnings guard (#4), risk-equalized sizing (#5), pyramiding re-listed winners (#6), 21-day trail
after +20% (#7), intraday backtest (#8) — all still worth doing; none contradicted by new data.

## Suggested order
**Now (no new risk, pure measurement):** #1 gated book · #2 cooldown backtest · #3 extension sweep.
**Next (risk reduction):** #4 pilot sizing · #5 heat caps · earnings guard.
**Then:** time stop + the profit-side items (pyramiding, longer trails) once the sweeps confirm.

> Every rule stays falsifiable: re-run `optimize_rules.py` / `cumulative_pnl.py` after each change.
> Not financial advice.
