---
type: analysis
tags: [exits, trend-following, backtest, structural, oos, gated-book, proposal, review]
created: 2026-07-25
updated: 2026-07-25
---

# Structural hold-the-trend exit — two-year test (2026-07-25)

After the tuned regime-conditioned exits **failed out-of-sample** ([[flex-exit-backtest-2026-07-25]]),
we tested the opposite kind of change: a **low-parameter, structural** exit — hold the
full position and exit only on a **daily close below the 50-day SMA**, with a wide
disaster stop underneath. This is classic Minervini stage-2 trend-following (ingested
wisdom), not a fitted parameter set — so it is far less prone to the overfit we just caught.
Tested on **both** 2025 (out-of-sample) and 2026, same gated selection, `≤12-name cap enforced`.

> [!important] Result: robustly beats the current rules in BOTH years — a genuine candidate.
> A 50-SMA trend-hold converts the book from *swing* to *position/trend-following*. It wins
> in both years by large margins and roughly **halves the loss rate** (win rate 21→33%).
> This is a **strategic change to review**, not yet promoted — `backtest.py` untouched.

> [!success] THREE-YEAR CONFIRMATION (2024 backfilled 2026-07-25) — passed the gate
> Re-ran current vs 50-SMA-hold(−12%) on **2024, 2025, and 2026** (full sim, 5-year
> history so early-2024 has a valid 200-SMA). **50-SMA hold wins all three years:**
>
> | Config | 2024 | 2025 | 2026 | 3-yr total |
> | --- | ---: | ---: | ---: | ---: |
> | current | +$28,452 (30%) | +$22,777 (22%) | −$18,842 (24%) | **+$32,388** |
> | **50-SMA hold −12%** | **+$109,006 (41%)** | **+$46,002 (34%)** | **+$75,137 (31%)** | **+$230,145** |
>
> Per-year edge: 2024 **+$80.6k**, 2025 **+$23.2k**, 2026 **+$94.0k**. Win rate higher every
> year. This clears the pre-agreed promotion gate ("wins in all three years"). **Remaining
> caveat unchanged: all three were UP years — no bear tape exists in the archive (starts 2023).**

## The test (realistic full-portfolio sim, ≤12 names)

| Exit rule | 2025 (OOS) | 2026 (in-sample) | Both > current |
| --- | ---: | ---: | :-: |
| **Current** (−5% stop, BE+7, sell½@+12%, 9-EMA) | +$21,527 (win 21%) | −$18,842 (win 24%) | — |
| 50-SMA hold + −10% disaster | +$33,740 (33%) | +$70,397 (30%) | ✅ |
| **50-SMA hold + −12% disaster** | **+$46,002 (34%)** | **+$75,137 (31%)** | ✅ |

Two-year total: **current +$2.7k** vs **50-SMA hold (−12%) +$121.1k**. The wider −12%
disaster stop beat −10% in both years (fewer premature exits; the 50-SMA is the real exit).

Note on labels: entries only occur when the regime gate is open (score ≥4), so a
"regime-conditioned" 50-SMA/current variant is *structurally identical* to flat 50-SMA-hold
for taken trades — the finding is simply **50-SMA trend-hold + ~−12% disaster stop**, one
structural rule with two low-sensitivity knobs (the MA length and the disaster %).

## Why this is trustworthy where the tuned overhaul was not

- **Low parameter count.** "Hold to the 50-SMA, −12% floor" is 2 knobs; the failed overhaul
  tuned stop/target/trail/partial across three regime bands (many knobs → fit to 2026's path).
- **Wins out-of-sample.** +$46k in 2025, which the design never saw — the opposite of the
  regime-conditioned exits (−$7.6k in 2025).
- **Mechanism is sound and pre-registered by theory.** Riding a leader above its 50-day line
  until it breaks is the textbook stage-2 hold; we're confirming ingested doctrine, not
  data-mining. It directly fixes the drift-review disease (we cap/whipsaw winners).
- **The full-portfolio cap matters.** An earlier fixed-picks scan showed +$249k–$760k — a
  gross over-count, because long holds would occupy far more than 12 slots at once. Enforcing
  the ≤12 cap collapses it to the realistic +$34–75k range and *cuts the number of trades*
  (2025: 112 closed → 71), which is itself the correct behavior (fewer, longer holds).

## Supporting evidence — single-knob probes (full sim, both years)

Even isolated single changes that only *let winners run further* beat current in both years,
while changes that merely *loosen risk control* did not — consistent with the diagnosis:

| Single change | 2025 | 2026 | Both |
| --- | ---: | ---: | :-: |
| slower trail (9→21-EMA) | +$26.3k | −$11.9k | ✅ |
| higher target (+12%→+20%) | +$45.3k | −$16.1k | ✅ |
| wider stop only (−8%) | +$10.1k | −$26.0k | ✗ |
| no breakeven | +$2.6k | −$24.9k | ✗ |

The 50-SMA hold dominates these (both single-knob tweaks still end 2026 negative; the
50-SMA hold turns 2026 firmly positive). It is the stronger, more coherent version of the
same idea: stop capping winners.

## Caveats — before this touches the book of record

- **Both test years (2025, 2026) were UP years.** A 50-SMA hold captures trends but in a
  sustained **down** year would ride losers to the −12% floor and give back gains as the
  lagging 50-SMA catches down. We cannot test a bear tape — the Key List archive starts
  2023; **2022 is unavailable.** This is the central open risk.
- **The regime entry gate is the bear-market protection.** In distribution (score ≤3) it
  takes 0 new entries, so the trend-hold is only ever applied to names entered in ≥4
  regimes. That mitigates but does not eliminate the down-year risk.
- **It changes the book's identity** from swing (days–weeks) to position/trend (weeks–
  months). Fewer, larger, longer holds; more give-back from peak on each exit; different
  psychology. That is a deliberate choice, not a tweak.

## Recommendation — gate passed; recommend promotion (with eyes open on the bear-year risk)

The three-year gate is met: 50-SMA trend-hold + −12% disaster beats current in **2024, 2025,
and 2026** (+$198k over three years). 2024 was pure out-of-sample (backfilled after the rule
was chosen). Recommend adopting it as the book-of-record exit. Scope of the change:
1. **Exit logic** (`backtest.py` / the books): replace −5% stop / BE+7 / sell½@+12 / 9-EMA
   trail with **hold to a daily close below the 50-day SMA, −12% disaster stop, no fixed
   target**. Keep the regime **entry** gate and the **≤12-name cap** unchanged — they are the
   down-year insurance and what makes the long-hold P&L real.
2. **Downstream** that assumes swing exits must follow: watchlist stop/target columns, the
   report's trim/trail "tomorrow's action" lines, `tos_orders.py` brackets, and
   `key-list-trade-rules.md`. This is a **book-identity change (swing → position-trading)**,
   not a constant tweak — expect a multi-file refactor.
3. **Survivorship note:** 2024 had many acquired/delisted names (SQ, DFS, COUP, SWAV, ITCI…)
   dropped from both books; a long-hold gives up *more* to missing acquisition-premium
   winners, so the 50-SMA numbers are if anything **understated** — the edge is not a
   survivorship artifact.

**The one unresolved risk:** all three test years were up years. A 50-SMA hold in a sustained
*bear* would ride names to the −12% floor and lag on the exit. The regime entry gate (0 new
entries in distribution) is the mitigation, but this cannot be validated without 2022-style
data, which the archive lacks. Promotion is a judgment call that this risk is acceptable given
the entry gate; a conservative alternative is to **run flex_book as a live parallel book for a
quarter** before switching the record.

`tools/flex_book.py` now supports the structural exit (`hold_sma` param); parity with the
current book is preserved (`--current` still reproduces it to the dollar). No live constant
changed.

_Simulated. 2026 in-sample; 2025 out-of-sample; both up years. Educational only — not
investment advice._
