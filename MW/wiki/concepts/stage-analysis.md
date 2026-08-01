---
type: concept
concept_kind: strategy
tags: [trend-following, stages, weinstein, exits, regime]
created: 2026-07-27
updated: 2026-07-27
---

# Stage Analysis (Stan Weinstein)

**Definition:** Stan Weinstein's framework (*Secrets for Profiting in Bull and Bear Markets*) that
classifies every stock's price cycle into **four stages** relative to its **30-week (~150-day) moving
average**, and trades only the phase where the odds favor the trend. Synthesis in my own words for
strategy use — not a reproduction of the book. Pat Walker's Mission Winners breakout approach is
explicitly modeled on Weinstein's Stage-2 principle.

## The four stages
1. **Stage 1 — Basing (accumulation).** After a decline, price flattens and oscillates around a
   flattening MA. Neutral; wait.
2. **Stage 2 — Advancing (markup).** Price breaks out of the base **above a rising 30-week MA**, ideally
   on **expanding volume**. This is the only stage to be long. Ride it while the trend holds.
3. **Stage 3 — Topping (distribution).** The advance stalls, the MA flattens, price churns. Take profits;
   tighten.
4. **Stage 4 — Declining (markdown).** Price breaks **below a falling 30-week MA**. Avoid / be short.
   Never buy here.

## Core rules
- **Buy** only Stage-2 breakouts from a sound base, above a **rising** 30-week MA, with volume confirmation.
- **Sell** when price **closes below the 30-week MA** (or the MA rolls over) — the stage has ended.
- **Relative strength:** favor stocks outperforming the market (Mansfield RS line rising).
- **Market first:** apply the same stage logic to the major averages — press exposure only when the broad
  market is Stage 2.

## How it maps to our system
- Our **exit v3 (50-SMA trend-hold)** is a *faster* Weinstein: hold while price is above a rising
  intermediate MA, exit on a close below it. Weinstein uses the 30-week (150-day); we use the 50-day.
  ([[key-list-trade-rules]], [[structural-exit-test-2026-07-25]].)
- Our **regime gate** ([[regime]] score) = Weinstein's "only press when the market is Stage 2."
- Our **Trend Template** selection ([[trend-template]]) already encodes Stage-2 structure (price above
  rising 150/200-day MAs).
- **Gap / open question:** Weinstein weights **breakout volume** heavily; we do **not** currently check
  volume on entry. And he uses the **30-week (150-day)** trend line, not the 50-day. Both are testable
  refinements — see [[books-revalidation-2026-07-27]].

Related: [[trend-following]], [[can-slim]], [[trend-template]], [[sepa]], [[box-theory]].
