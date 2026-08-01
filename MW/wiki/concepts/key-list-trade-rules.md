---
type: concept
concept_kind: strategy
tags: [rules, risk-management, exits, stops]
created: 2026-06-14
updated: 2026-07-09
---

# Key List trade rules

**Definition:** The mechanical risk/exit rules applied to every Key List name. Entries come from the
Key List **setup/pivot price** ("entry"); these rules turn an entry into a managed trade.

> [!note] Rules revised 2026-07-02 (v2)
> Original rules (2026-06-14): stop −3% / BE +5% / sell½ +7%, full position 10% ($100k). Revised after the
> quarter-end grid sweep [[stop-target-optimization-2026-07-02]] showed −3% was selling the noise
> (results improved monotonically out to −5%) and wider targets ran better. Position cut to $50k so
> dollar-risk per name *falls* despite the wider stop.

## Trigger validity (clarified 2026-07-07)
**A trigger is only valid on its list's trading day** — entry buy-stops are **DAY orders, not GTC**.
The Key List is prepared for the next session; names still worth buying re-appear on the next day's
list (often at updated levels). To buy a name on any given day, it must be on **that day's** list.
The backtest enforces this (`TRIGGER_DAYS = 1` in `tools/backtest.py`); `tos_orders.py` marks entries DAY.

**No gap-up entries (added 2026-07-07):** buy **only as price breaches the trigger — the buy price IS the
trigger price**. If the session opens above the trigger, we never chase the open — but the resting **DAY
stop-limit stays live**: if price **revisits the trigger intraday, the limit fills at the trigger price**
(refined 2026-07-07). Only a gap-and-go that never revisits goes unfilled. In practice: a **BUY STOP-LIMIT
with stop = limit = trigger, DAY**. Conservative same-day modeling on revisit fills: only the stop (never
the target/BE) can be assumed hit that day, since price was falling through the trigger. Basis: gap-chasing was the #1 P&L drag in
[[backtest-2026-06-18]] and later runs (e.g. GEO filled 32.12 vs a 30.70 pivot, −7.5%).

**Gap-down exits (made explicit 2026-07-07):** if a session **opens below the stop, the position closes
immediately at the open** — no waiting, no hoping. Mechanics: the protective sell order is a **STOP
(market)**, never a stop-limit — a stop-limit can skip a gap-down fill and leave you holding a loser.
The backtest models this (`min(open, stop)` fill); on gap days the realized loss can exceed −5%.

> [!important] Rules revised 2026-07-25 (v3) — EXIT MODEL replaced: 50-SMA TREND-HOLD
> A three-year backtest ([[structural-exit-test-2026-07-25]], validated on 2024/2025/2026)
> showed the v2 swing exit (−5% stop, BE+7, sell½@+12, 9-EMA trail) was **giving back the
> whole edge** — our selection was good but the tight exits whipsawed winners. The v2 exit
> beat by holding the **full** position to a **daily close below the 50-day SMA** with a wide
> disaster stop. Result: +$230k vs +$32k over three years, winning **every** year. This
> converts the book from *swing* to *position/trend-following*. The **entry** rules, the
> **regime gate**, and the **heat caps** are unchanged — they are the down-year insurance.

## The rules (v3, 2026-07-25) — trend-hold exit + profit-lock
1. **Disaster stop −12%** — initial hard stop at `entry × 0.88`. STOP-MARKET; a gap-down below
   it closes at the open. Max risk per trade. It is *wide on purpose* — the 50-SMA, not the
   stop, is the normal exit; the stop only catches a fast break.
2. **Hold the FULL position** — no breakeven move, no profit target, no partial sale. Ride the
   trend. (Reverses the v2 mistake of capping winners.)
3. **Exit on a daily CLOSE below the 50-day SMA** — when the stock closes under its 50-day
   simple MA, sell the whole position. Classic Minervini stage-2 trend-following
   ([[trend-template]], [[momentum-masters-minervini]]): stay while the intermediate trend holds.
4. **Profit-lock: at +30%, raise the stop to +15%** — once the stock trades **+30% above entry**,
   ratchet the −12% disaster stop **up to +15% above entry**. This protects accumulated profit on
   a big winner (it can no longer round-trip below +15%) **without capping upside** — the position
   still rides to the 50-SMA. High, one-way, no shares sold. Validated across 2024/2025/2026
   (+$89k/3yr vs pure hold); a *lower* lock, a give-back trail, or a partial sale all tested
   **worse** (they re-created the winner-capping problem) — see [[profit-protection-2026-07-25]].

## Worked example (entry = 100.00)
- Disaster stop = **88.00** (−12%); risk = 12% of a $100k position = **$12,000 (0.86% of equity)**.
- No target, no breakeven — hold the full position as it trends up.
- Each day, check the 50-day SMA. The day the stock **closes below its 50-SMA**, sell in full.
- **Profit-lock:** when the stock touches **130.00 (+30%)**, move the stop up to **115.00 (+15%)**.
  Now it can't give back below +15% — but it still rides to the 50-SMA on the upside. Hold through
  pullbacks that break neither the +15% stop nor the 50-SMA close.

## How the MAs are used
- **50 SMA** — **the exit**: a daily close below it ends the trade. The single most important line.
- **9 EMA / 21 MA** — short-/near-term trend reads only (no longer exit triggers under v3).
- **200 MA** — long-term trend; above = healthy backdrop (part of the [[trend-template]] entry gate).
- Live values per ticker are in the [[overview]] watchlist, refreshed by `tools/update_watchlist.py`.

> [!note] v2 (2026-07-02) exit — superseded, kept for history
> −5% stop / BE +7% / sell½ +12% / trail remaining ½ under the 9-EMA. Basis
> [[stop-target-optimization-2026-07-02]]. Replaced by v3 after the 3-year OOS test.

## Position sizing (v2)
- **A full position = 5% of the portfolio = $50,000** on the $1M book. Up to 20 names possible, but the
  [[portfolio-plan]] target is still ~8–12; being fully invested no longer requires taking every signal.
- **Risk per full position = 5% × $50k = $2,500 (0.25% of equity)** — *lower* than v1's $3,000 despite the
  wider stop; this is the "risk = size × stop" trade-off from [[expectancy]] applied deliberately.
- **Build into it ([[position-scaling]]):** pilot ~20–35% of full (≈$10–17k), then add on confirmation
  ([[pyramid-50-30-20-strategy]]: ~$25k → $15k → $10k to reach the $50k full size).
- **Share count** per name is shown in the [[overview]] watchlist via `MW_PORTFOLIO_EQUITY`:
  `full shares = floor(equity × 5% / entry)`.

## Discipline layer (v2.1, added 2026-07-09)
Selection/sizing gates layered ON TOP of the exit rules above, from
[[process-improvements-2026-07-09]]. Constants live in `tools/update_watchlist.py`;
`tools/gated_book.py` simulates the fully disciplined book daily; the emailed report and
`tos_orders.py` carry the same flags/sizing.
1. **Regime-gated order count** — daily `regime.py` score: 7–8 → up to 5 orders · 4–6 → 2 pilot
   orders · ≤3 → none. ([[can-slim]] "M", [[eight-keys]] progressive exposure.)
2. **Trend-Template hard filter** — only 8/8 passers ([[trend-template]]) are order candidates.
3. **Extension filter** — skip triggers **>8% above the 21-day SMA** (`EXT_MAX_PCT`); stretched
   pivots produced our same-day stop-outs. (Buy the pivot, not the extension — Minervini.)
4. **Re-entry cooldown** — after a losing stop-out, no re-entry for **~5 sessions
   (7 calendar days, `COOLDOWN_DAYS`)** unless a fresh setup forms. (Re-enter on a re-setup,
   not a re-trigger.)
5. **Pilot sizing in NEUTRAL** — regime 4–6 → enter at **half size** (`PILOT_FRACTION`), add the
   rest only on follow-through.
6. **Heat caps** — gated book holds **≤12 names** (`MAX_POSITIONS`), **≤25% per sector group**
   (`GROUP_CAP`), **ETFs at half size** (`ETF_FRACTION`, all ETFs = one group).
7. **Time-stop flag** — open positions **<+2% after 10 sessions** (`STALE_DAYS`/`STALE_MIN_RET`)
   are flagged ⏳stale as rotation candidates (Ryan's 2-for-1). Flag-only for now — measure first.

## How it connects
- Sits on top of [[position-scaling]]: a "new buy" starts via [[smart-add-on-strategy]]; a confirmed
  add-on uses [[pyramid-50-30-20-strategy]]. Under v3 the exit is the 50-SMA trend-break (not a
  fixed trim) — the "sell into strength" step is retired in favor of holding the trend.
- Triggers/ratings interpreted via [[can-slim]]; entry quality gated by [[trend-template]] + [[vcp]];
  the whole thing must produce positive [[expectancy]].

## Source trail
- v1 rule set specified by the user (2026-06-14); v2 revision (2026-07-02) from
  [[stop-target-optimization-2026-07-02]] — grid sweep over 11 lists / 119 signals.
