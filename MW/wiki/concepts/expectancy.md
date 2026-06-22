---
type: concept
concept_kind: mechanism
tags: [risk-management, math, edge, minervini]
created: 2026-06-14
updated: 2026-06-14
---

# Expectancy (batting average & reward/risk)

**Definition:** The mathematical edge of a trading system — the average profit per trade given your
**batting average** (% winning trades), **average gain**, and **average loss**. Positive expectancy =
you win over time; the goal of every rule in [[key-list-trade-rules]].

`Expectancy = (PWT × avg gain) − (PLT × avg loss)`  (PWT/PLT = % winning/losing trades)

## Key lessons (from [[think-and-trade-like-a-champion-minervini]])
- **Keep losses a fraction of gains** so you can be wrong often and still profit — "build failure in."
  Minervini would rather stay profitable at a **25% batting average than 75%**.
- **Losses compound geometrically against you.** At a 40% win rate with a 2:1 ratio:
  - **4% gain / 2% loss → +3.63% per 10 trades** ✅
  - **42% gain / 21% loss → −1.16% per 10 trades** ❌ (same ratio!)
  → **Smaller absolute losses win.** This is why he **rejects widening stops for volatility / ATR** —
  in hard markets win rates fall, so losses must be cut *shorter*, not looser.
- **Optimal gain/loss ratio depends on batting average** (e.g. at 40%, ~20%/10%); going bigger reduces returns.
- To hold a 2:1 reward/risk: at 50% win rate keep losses ≤ ½ of gains; at 40% keep losses ≤ ⅓ of gains.

## How it connects
- Drives [[key-list-trade-rules]] (why a tight −3% stop + risk-based sizing makes sense) and
  [[position-scaling]] ("trade small before you trade big" until your batting average proves out).
- Related concepts: [[selling-into-strength]], [[trend-template]]
- People: [[mark-minervini]], [[mark-ritchie-ii]] (gates total risk by recent win/loss results)

## Source trail
- [[think-and-trade-like-a-champion-minervini]] — Sections 3–4 (the expectancy math).
