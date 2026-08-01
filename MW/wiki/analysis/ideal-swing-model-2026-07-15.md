---
type: analysis
tags: [strategy, swing-trading, model, allocation, hindsight-review]
created: 2026-07-15
---

# Ideal swing model (v3 candidate) — hindsight-derived, simulated vs both books

**Question:** knowing all our trades, what strategy would have been ideal for swing trading this tape,
and what's the delta vs what we run?

## What the trade history taught (evidence basis)
1. **Winners were individual-stock runners held for weeks** (FTNT, ASTH, HACK, PANW, LTH, DDOG) —
   [[pnl-report-2026-07-07]], the open-book runner cohort.
2. **ETFs were dead money** — KBE/KRE/IWM/FSTR ⏳stale for weeks; index ETFs added churn, not P&L.
3. **Extended breakouts died; entries near support survived** — same-day stop-outs clustered in names
   >8% above the 21-SMA ([[process-improvements-2026-07-09]]); pullback-type setups (ASTH, ETON) ran.
4. **Regime gating was worth ~$42k MTD** ([[mtd-pnl-2026-07]]) but the gated book still bled via
   marginal entries in NEUTRAL tapes.

## The model ("leader-pullback swing")
Identical engine/exits to the book of record (v2 rules, day-only stop-limit entries, cooldown, group
cap, pilots ×½ in NEUTRAL), with three hindsight changes:
- **Stocks only** — no ETFs at all.
- **Trigger ≤5% above the 21-day SMA** (vs 8%) — buy leaders *near support*, never stretched.
- **Max 8 names** (vs 12), orders 4 (uptrend) / 2 (neutral) / 0 (distribution).

## Results (simulated point-in-time; rule design is hindsight, execution is not)
| Book | MTD (July) | Since inception | Open positions | Daily swing |
| --- | ---: | ---: | ---: | ---: |
| **Ideal (v3 candidate)** | **+$2,261** ✅ | −$5,817 | 5 (~17.5% deployed) | ±$0.4–1.3k |
| 📘 Gated (book of record) | −$6,665 | −$8,656 | 10 | ±$0.8–6.5k |
| Benchmark (every-signal) | −$48,653 | −$44,687 | 30 (~150% committed) | ±$4–30k |

**Delta of ideal vs gated: +$8.9k MTD (+$2.8k inception) · vs full book: +$50.9k MTD.**
Ideal holdings (07-14): FTNT +11.5% (runner), AAPL +1.7%, CVS +0.7%, TRGP +0.1%, JAZZ −2.4% —
it naturally caught the energy rotation (TRGP) because a fresh leader near support passes its filters.

## Allocation delta (current gated → ideal)
| Dimension | Gated today | Ideal model |
| --- | --- | --- |
| Instruments | stocks + ETFs (½ size) | **stocks only** |
| Extension cap | ≤8% above 21-SMA | **≤5%** |
| Max names | 12 | **8** |
| Capital deployed (now) | ~30% | **~17.5%** (rest cash in a weak tape) |
| Orders/day | 5 / 2 / 0 | 4 / 2 / 0 |

## Honest caveats
- **In-sample:** the rules were chosen *after* seeing which trades worked — classic overfit risk. The
  edge is plausible (each rule has a causal story + book support), but unproven out-of-sample.
- **Small sample:** 10 closed trades; one month; one regime type (chop/distribution). The tight
  extension cap + 8-name cap may *lag* the gated book in a confirmed uptrend, where breakouts extend fast.
- It wins July partly by holding more cash — correct in this tape, untested in a rally.

## Recommendation
Run it as a **paper v3 book in parallel** (third line in [[mtd-pnl-2026-07]] and the report) for at least
one confirmed-uptrend stretch before promoting it. Adopt immediately only the least-risky element:
**drop standalone index ETFs from the buy funnel** (they were pure dead money in every configuration).

_Not financial advice; simulated, in-sample analysis of our own books._
