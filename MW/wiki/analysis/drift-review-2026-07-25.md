---
type: analysis
tags: [drift, verification, pnl, exits, gated-book, ideal-book, benchmark, review]
created: 2026-07-25
updated: 2026-07-25
---

# Drift review — why the books trail the indices, independently verified (2026-07-25)

**Trigger:** our YTD books are red while the S&P 500 and Nasdaq are up strongly.
The user asked to *independently verify* the result before trusting it, then
document the drift on all strategies and propose improvements **for review (not
yet implemented)**. This is that verification. Companion data: [[ytd-review-2026-07-25]],
[[period-pnl-2026-07-25]].

> **Bottom line:** The drift is real and not a P&L bug. Our **stock selection is
> good** (the picks, simply held, roughly match the indices). Our **exit rules are
> destroying the entire edge** — a −5% stop + breakeven-move + +12% half-sale +
> fast 9-EMA trail whipsaws us out of good names on normal pullbacks, costing
> **7–15 points of return** across every book. The fix is in trade management, not
> selection or the entry gate.

## 1. The divergence is real (index buy-and-hold, Jan 2 → Jul 24)

| Index | YTD | Our gated book | Gap |
| --- | ---: | ---: | ---: |
| SPY (S&P 500) | **+8.74%** | −1.88% | −10.6 pts |
| QQQ (Nasdaq 100) | **+11.86%** | −1.88% | −13.7 pts |
| RSP (S&P equal-weight) | **+11.64%** | −1.88% | −13.5 pts |
| IWM (Russell 2000) | **+17.53%** | −1.88% | −19.4 pts |
| ^VIX | +28% (14.5→18.6) | — | — |

This was a **broad, healthy bull market** — equal-weight +11.6% and small-caps
+17.5% mean it wasn't just a handful of mega-caps. A breakout-momentum system
should *thrive* here. Losing money is a red flag that demanded root-causing.

## 2. Independent verification — it is not a computational bug

- **P&L re-summed independently** from the raw trade list (realized + unrealized,
  weight-adjusted): **−1.884%**, matching the book engine exactly.
- **Same-day stop-outs: 4%** of stops (2 of 56) — the exits are legitimate −5%
  hits, not a daily-bar modeling artifact.
- **Decisive test — the same picks, simply held to Jul 24:**

| Book | Picks | Rules P&L | **Same picks, HELD** | Rules cost |
| --- | ---: | ---: | ---: | ---: |
| 📘 Gated | 79 | −1.88% | **+12.80%** | **−14.68%** |
| 🧪 Ideal | 54 | −1.33% | +5.91% | −7.24% |
| 📊 Benchmark | 625 | −4.61% | +246.7%¹ | — |

¹ The benchmark "held" figure over-commits capital (625 overlapping positions each
counted at 5%); read it as *signal quality*, not an achievable return.

**Gated's picks held = +12.80%**, in line with SPY/QQQ/RSP. The Trend-Template +
regime-gate **selection has real edge**. The rules gave all of it back, and then some.

## 3. Root cause — the exit rules, quantified

Closed gated trades: **24% win rate, 76% stopped out** (avg win +11.97%, avg loss
−4.35% → expectancy **−0.43%/trade**). A 24% breakout win rate in a +17.5% small-cap
year is abnormally low — the names *worked*, but we were shaken out before they ran.

Exit-rule sensitivity on the **same 79 gated picks** (selection held fixed; parametric
replica validated to ±0.05% of the engine):

| Exit rule | Return | vs current |
| --- | ---: | ---: |
| **CURRENT** (−5% stop, BE@+7%, sell½@+12%, trail 9-EMA) | **−1.9%** | — |
| Wider −8% stop, keep +12% target, trail 9-EMA | −3.2% | worse |
| −8% stop, **no target**, trail 21-EMA | +3.3% | +5.2 |
| −10% stop, no target, trail 21-EMA | +3.8% | +5.7 |
| Close < **50-day SMA** (pure trend-follow, no hard stop) | +3.8% | +5.7 |
| Close < 50-SMA + −10% disaster stop | +3.0% | +4.9 |
| Chandelier trail (4×ATR from highest high) | +2.9% | +4.8 |
| **Buy & hold** to Jul 24 (ceiling) | **+12.8%** | +14.7 |

What this says:
- **The +12% "sell half" target is the biggest self-inflicted wound.** Capping
  winners at +12% while −5% stops cut losers is backwards for momentum. Removing
  it is worth ~+5 points on its own.
- **The 9-EMA trail is too fast** — it exits on the first minor pullback. A 21-EMA
  or 50-SMA trail holds trends far longer.
- **Widening the stop *alone* makes it worse** (−3.2%): bigger losses with no
  offsetting winner upside. Stop width only helps *after* you stop capping winners.
- **Every disciplined exit still leaves ~9 points on the table vs buy-and-hold.**
  In a no-crash trending year, stops are pure cost — insurance with no claim.

## 4. The real diagnosis

Our framework is a **swing-trade** rule set (tight stop, quick profit, fast trail)
applied to what 2026 actually offered: a **position/trend-follow** opportunity
(strong leaders in a durable uptrend). That mismatch *is* the drift. The ingested
masters are explicit — *cut losses short **and let winners run***; our rules do the
first and actively prevent the second. Backlog **B5 (longer runner trail)** already
anticipated this; the data now makes it the top priority.

## 5. Proposed improvements — ranked, for your review (not implemented)

**A. Regime-condition the EXITS, not just the entry count (highest-value, most robust).**
The same 8-point regime score that gates entries should set the exit style:
- **Confirmed uptrend (score 7–8):** wide stop (−8 to −10%), **no fixed target**,
  trail on the 21-EMA/50-SMA — let leaders run.
- **Neutral (4–6):** current-ish (moderate stop, trail 9/21-EMA, optional partial).
- **Distribution (≤3):** tight stop, take partials — capital preservation.
This ties the fix to a mechanism we already compute and to book wisdom, and it
avoids the trap of "wide stops always" (which lose badly in 2022-style bears).

**B. Kill or raise the fixed profit target.** Drop the +12% sell-half in uptrends
(or move it to +25–30%). This is the single biggest lever (~+5 pts) and the
cleanest change to test first.

**C. Slow the trail.** 9-EMA → 21-EMA (or 50-SMA in strong trends). Holds the meat
of the move instead of the first wiggle.

**D. Widen the initial stop to volatility (ATR).** Replace the flat −5% with
~2.5–3×ATR(14) so the stop reflects each name's noise — but only *together* with B/C.

**E. Re-test entry timing (lower priority).** The day-only, buy-at-exact-trigger
rule may enter at local tops; a small pullback-buy or a 1–2 day confirmation window
could improve fill quality. Selection is already good, so this is secondary.

## 6. Caveats (why we review before implementing)

- **2026 had no crash.** Wide stops / no targets / hold-the-trend win in trending
  years and *lose* in choppy/bear years — exactly when the current tight rules earn
  their keep. This is why **A (regime-conditioned exits)** is the recommendation, not
  a blanket loosening. The −3%→−5% widening on [[stop-target-optimization-2026-07-02]]
  was fit on choppier data and was locally correct for *that* regime.
- **In-sample risk.** The sensitivity table is fit on 2026's realized path. Treat the
  specific numbers as directional, not a promise; validate any change forward and on
  the 2025 history before adopting into the book of record.
- **The ideal book's selection is weaker than the gated book's** over the full year
  (+5.9% vs +12.8% held) — its July edge was exit-timing luck, not better picks. Keep
  the gated book's Trend-Template selection as the base; fix its exits.

_Simulated. Educational only — not investment advice._
