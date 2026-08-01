---
type: analysis
tags: [exits, regime, backtest, flex-book, gated-book, proposal, review]
created: 2026-07-25
updated: 2026-07-25
---

# Regime-conditioned exits — backtest & decision memo (2026-07-25)

Follow-up to [[drift-review-2026-07-25]], which proved our **selection is good but the
fixed exit rules cost 7–15 pts**. This builds the fix — exits that adapt to the regime
score at entry — as a **parallel research book** (`tools/flex_book.py`) that keeps the
gated book's selection *exactly* and swaps only the exits. **The book-of-record engine
(`backtest.py`) is unchanged; no live constants were touched.**

> [!warning] Out-of-sample verdict (2025): DO NOT PROMOTE
> The design was tuned on 2026. Tested on a full year of **2025** Key Lists (244 lists,
> backfilled 2026-07-25 — genuinely out-of-sample), the regime-conditioned exits **LOSE
> to the current rules by ~$29k** (current +2.15% / +$21.5k vs regime-conditioned −0.76%
> / −$7.6k; win rate 15% vs 21%). The +$67.7k 2026 gain was **overfit to one trending
> year.** Recommendation reversed: **keep the current exits; do not promote.** See §OOS.

## The design

Same selection as [[gated_book]] (regime order count, TT 8/8, extension, cooldown, caps).
Exit style set by the **regime score at entry**:

| Regime at entry | Stop | Target | Trail |
| --- | --- | --- | --- |
| 7–8 (confirmed uptrend) | −10% | sell ⅓ @ +30% | 21-EMA on the rest |
| 4–6 (neutral) | −8% | sell ⅓ @ +25% | 21-EMA on the rest |
| ≤3 (distribution) | −5% | sell ½ @ +12% | 9-EMA (= current; ≤3 → 0 orders, so unused) |

Principle: hold with a **wide stop** (not a fast EMA) so normal pullbacks don't eject us;
bank a **partial only at a high target**; trail the remainder slowly. This directly
reverses the two things the drift review flagged — the +12% winner-cap and the 9-EMA whip.

## Validation the replica is faithful

Running the parallel book with the **current** rules on every entry reproduces the gated
book of record **to the dollar**: −1.88%, 9 open + 70 closed, 24% win, avg win +11.97% /
avg loss −4.35%. So any difference below is the *exit change*, not a modeling artifact.

## Results — 2026 full year ($1,000,000 equity)

| Design | Total | $ | Win % | Avg win / loss |
| --- | ---: | ---: | ---: | ---: |
| **D0 — current** (−5% / BE+7 / T1+12 / 9-EMA) | −1.88% | −$18,842 | 24% | +12.0 / −4.3 |
| **CHOSEN — regime-conditioned** (above) | **+4.89%** | **+$48,902** | 26% | +33.9 / −8.5 |
| alt A — −8%/+25%/⅓/21-EMA for all ≥4 | +5.25% | +$52,524 | 25% | +33.6 / −8.1 |
| alt B — −10% stop, no target, ride stop | +6.45% | +$64,483 | — | (≈ hold + disaster stop) |
| alt C — −8%/+25%/½ partial/21-EMA | +4.59% | +$45,900 | 25% | +31.9 / −8.1 |
| _reference: SPY +8.7% · QQQ +11.9% · picks buy&hold +12.8%_ | | | | |

The chosen design is a **+6.8-point / +$67.7k full-year swing** vs current. Note the
monotonic pattern: the *less* you manage, the closer to buy-and-hold — alt B (+6.45%) is
essentially "hold with a −10% catastrophe stop, no profit-taking," which would bleed in a
choppy year. The chosen design keeps real risk management (partials, trailing) and still
recovers most of the lost edge.

## Robustness within 2026 (does it win in the bad stretches, not just the trend?)

| Design | H1 → Jun 30 (choppy) | July (AI-reset drawdown) | Full YTD |
| --- | ---: | ---: | ---: |
| Current | −$15,671 | −$3,170 | −$18,842 |
| **Regime-conditioned** | **+$43,472** | **+$5,430** | **+$48,902** |

It beats current in **both** halves — including the July reset month, where it stayed
**positive** while current was negative (wider stops avoided the whipsaw exits; looser
trails held June winners through the dip). That is evidence the gain isn't a single lucky
trend ride.

## Honest caveats — why this is a proposal, not yet the book of record

1. **All of this is in-sample to 2026 — a trending year with no crash.** In an up-year,
   *any* loosening beats tight stops almost tautologically (see the monotonic table). The
   true test is a **down / choppy regime**, which 2026 didn't provide.
2. **We do not yet have out-of-sample data.** Our Key Lists start Jan 2026. A real OOS
   test needs **2025 (and ideally a 2022-style) list history**, which we'd have to
   backfill the same way we did 2026.
3. **Wider stops mean bigger individual losses** (avg loss −8.5% vs −4.3%). The regime
   *entry* gate is what keeps that acceptable — it stops us entering in distribution. If
   the entry gate ever mis-scores, wide stops amplify the damage.

## OOS — 2025 out-of-sample test (the decider)

We backfilled **all 244 of 2025's Key Lists** (Jan 2 – Dec 31; the design never saw them)
and re-ran current-vs-regime-conditioned. Parity holds — `flex@current` reproduces the
current book exactly — so the delta is purely the exit change.

| Period | Current | Regime-conditioned | Delta |
| --- | ---: | ---: | ---: |
| **2025 full year** | **+2.15% (+$21,527)** | **−0.76% (−$7,583)** | **−$29,111** |
| 2025 H1 (→Jun 30) | +1.63% (+$16,335) | −2.21% (−$22,137) | −$38,471 |
| _(2026 in-sample, for contrast)_ | −1.88% | +4.89% | +$67,744 |

**The regime-conditioned exits lose in 2025** — by ~$29k, with win rate collapsing to 15%
(vs current 21%). The change that looked like a +$67.7k win is a **−$29k loss the very
next dataset back.** Note 2025 was *also* an up year for the indices (double-digit gains),
so this isn't "trending vs choppy" — the loosened exits simply gave back, in 2025, the
partial profits the +12% target banks. Across both years the regime design is positive
*only because* the in-sample year dominates — the textbook signature of overfitting.

## Recommendation — REVERSED: do not promote

- **Keep the current exit rules as the book of record.** The regime-conditioned overhaul
  fails out-of-sample; adopting it would be fitting to 2026's luck.
- **`flex_book.py` stays as a labeled negative result / research tool**, not wired into
  the live report. The OOS test did its job — it caught an overfit before it shipped.
- **The robust finding from [[drift-review-2026-07-25]] still stands and is year-independent:**
  selection is good, and *all* stop-based exits leave most of the edge on the table (true
  in both 2025 and 2026). The lever that matters is **structural** — "trade with tight
  stops" vs "hold the trend" — not fine-tuning stop widths and targets, which is where the
  overfitting lives.
- **Next, if pursued:** test *structural* hold-the-trend exits (e.g. exit only on a close
  below the 50-day SMA, or on a Trend-Template violation) **across both 2025 and 2026** —
  a lower-parameter rule is far less prone to the overfit we just caught. Only a change
  that wins (or holds) in **both** years should ever touch `backtest.py`.

_Simulated. The 2026 numbers are in-sample; the 2025 numbers are out-of-sample. Educational
only — not investment advice._
