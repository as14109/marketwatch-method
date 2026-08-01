---
type: analysis
tags: [pnl, ytd, review, gated-book, ideal-book, benchmark, knowledge-base]
created: 2026-07-25
updated: 2026-07-25
---

# YTD review — full-year backtest of all three books (2026)

**One-time knowledge-base build (2026-07-25).** Every Mission Winners Key List of
2026 was backfilled (138 lists, Jan 2 → Jul 24, ~2,150 signals across 438 unique
tickers) and all three books re-simulated point-in-time against real prices from
inception **2026-01-01**. This is the long-run picture of mechanical Key List swing
trading — what a year of it actually returns, and what the discipline layer is worth.

Data page: [[period-pnl-2026-07-25]] · engine `tools/period_pnl.py` (recurring) ·
books [[gated_book]] / [[ideal_book]] / benchmark. $ at $1,000,000 equity.

## The scoreboard (since inception, as of close 2026-07-24)

| Book | YTD | of equity | July (QTD/MTD) | H1 (thru Jun 30) |
| --- | ---: | ---: | ---: | ---: |
| 📘 **Gated** (book of record) | **−$18,842** | −1.88% | −$3,170 | −$15,672 |
| 🧪 **Ideal** (paper swing) | **−$13,331** | −1.33% | **+$2,938** | −$16,269 |
| 📊 **Benchmark** (every signal) | **−$46,136** | −4.61% | −$130,679 | +$84,543 |

## What the year says

1. **Mechanical Key List breakout trading was net-negative YTD 2026 — for all three
   books.** This is the honest headline. 2026 H1 was a choppy, whippy tape where
   breakouts repeatedly failed; no version of the strategy made money over the full
   year. Anyone selling "just buy the breakouts" would be down.

2. **Discipline did not turn it positive — but it cut the loss by more than half.**
   Gated −1.88% and ideal −1.33% vs the take-everything benchmark −4.61%. The regime
   gate + Trend-Template filter + heat caps saved roughly **$27–33k** over the year by
   simply *not taking* most of the failed-breakout signals in distribution weeks.

3. **The benchmark's arc is the entire case for caps.** Take-everything was **+$84.5k
   (+8.5%) at mid-year** — it looked like the winner. Then the late-July AI-spending
   reset (Nasdaq −2.2%, all Magnificent Seven lower) hit its enormous uncapped open
   book and it gave back **−$130.7k in July alone**, ending −4.6%. An uncapped book
   compounds gains in a trend and surrenders them faster in the shift. The 📘 book,
   holding ≤12 names, lost only **−$3.2k** through the same reset.

4. **In a distribution tape, buy pullbacks-to-support, not breakout-extension.** The
   🧪 ideal book (leader pullback, trigger ≤5% above the 21-SMA, near support) was the
   **only book green in July (+$2.9k)** while everything sold off. Buying strength into
   extension (the benchmark) was exactly wrong for the July regime; buying near support
   held up. This is the strongest signal in the data for a future rule refinement.

5. **The gated book bled slowly and steadily (−$15.7k H1, −$3.2k July).** Its few
   entries were net losers, but the gate kept position count and loss size small — no
   single month blew a hole in it. That is the trade-off the book of record makes:
   give up the benchmark's H1 upside to avoid the benchmark's July cliff.

## Implications for the rules (candidates, not yet adopted)

- **Favor near-support entries over extended breakouts** — point 4 is the clearest
  edge. The ideal book's ≤5%-above-21-SMA rule beat the benchmark by ~$115k in July.
  Consider tightening the gated book's extension cap toward the ideal book's, or
  weighting pullback setups higher. (Relates to backlog **B3** pullback entries.)
- **The regime gate earned its keep** — its biggest win (avoiding the July benchmark
  cliff) validates keeping new entries near-zero in distribution. No change needed.
- **2026 is simply a hard year for this strategy** — expectancy is negative in a
  whippy tape. The right posture is small size and patience for a confirmed-uptrend
  regime, not more trades. Re-evaluate expectancy after the next sustained uptrend.

## Method notes / caveats

- Point-in-time: each list's entries gated by the regime score and Trend Template
  **as computed from data before that list's trading day** (3-year history window, so
  even Jan-2 entries have a valid 200-day SMA — an earlier 14-month window silently
  dropped all of H1's early entries for lack of history; fixed in this build).
- Single-account, one position per name at a time (re-triggers = adds, not modeled).
- The **ideal book is in-sample / paper** — its edge is suggestive, not out-of-sample
  proof. Treat point 4 as a hypothesis to forward-test, not a settled result.
- Backfilled June-and-earlier lists are CSV (trigger prices only); the fundamental
  CAN SLIM context that richer summaries carry is absent, but the price-based rules
  (entry/stop/target/TT/regime) are fully computable, which is all the books use.

_Simulated. Educational only — not investment advice._
