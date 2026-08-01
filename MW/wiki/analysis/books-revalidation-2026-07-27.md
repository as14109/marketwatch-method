---
type: analysis
tags: [review, books, strategy, validation, canon]
created: 2026-07-27
updated: 2026-07-27
---

# Strategy revalidation vs Pat Walker's book list (2026-07-27)

Cross-checked our current strategy against the trading canon on
[Pat Walker's book list](https://missionwinners.com/patrick-walkers-book-list/). New concept pages
synthesized (my own words, not book text): [[stage-analysis]] (Weinstein), [[trend-following]] (Covel),
[[box-theory]] (Darvas), [[market-timing-zweig]] (Zweig), [[trading-psychology]] (Schwager/Lefèvre/Koppel).
Already in the wiki: [[can-slim]] (O'Neil), [[sepa]]/[[trend-template]]/[[vcp]] (Minervini),
[[market-profile]] (Steidlmayer), [[pattern-cycle]] (Farley).

> **Headline:** the canon **strongly validates our recent v3 direction.** The 50-SMA trend-hold, "let
> winners run / cut losses," the profit-lock, and the regime gate are the mainstream of every trend book
> here. The July drift-review fix (removing the +12% winner-cap) corrected the *exact* mistake Covel,
> Darvas, and Livermore warn against. We are now aligned with the masters, not fighting them.

## Where we already match the canon

| Principle (source) | Our implementation |
| --- | --- |
| Stage-2 uptrend, exit below the trend MA (Weinstein) | 50-SMA trend-hold exit ([[key-list-trade-rules]] v3) |
| Cut losses short; let winners run (Covel, Livermore) | −12% disaster stop + no fixed target |
| Buy box/base breakouts, no chasing (Darvas, O'Neil) | Key List trigger, buy-at-pivot, no gap-up chase |
| "Don't fight the tape/Fed" (Zweig) | 8-point regime gate ([[regime]]) |
| Only Stage-2 leaders (Weinstein, CAN SLIM) | Trend-Template 8/8 filter |
| Follow the system, don't override (Schwager/Tharp) | Fully mechanical gated book |
| Survive to catch the trend; fixed-fractional risk | $100k full / 0.86% risk, heat caps, ≤12 names |

## Candidate adjustments — ranked (test before adopting; none change the book yet)

**A1 · Volume confirmation on entry — TESTED 2026-07-27 → REJECTED.** Weinstein, O'Neil, *and* Darvas all
weight **breakout volume**, so we tested requiring trigger-day volume ≥1.3× / ≥1.5× its 50-day average
(full sim, 2024/2025/2026, adopted v3 exit). It **hurt in all three years, monotonically** — 3-yr baseline
+$549k → **+$18k at 1.3× → −$32k at 1.5×** (−$531k / −$581k), dropping 213→146→115 trades. The removed
trades were net **winners**. Interpretation: the Key List already pre-selects quality (CAN SLIM
fundamentals + a clean pivot), and its biggest trend winners are often *steady* leaders that break out on
ordinary volume; a volume gate throws those away, and the trend-hold captures the move regardless of
entry-day volume. The validation gate did its job (as with the overfit exit). Volume filter kept only as a
default-off toggle in the research book (`flex_book.VOL_MULT`). **Do not adopt.**

**A2 · Relative-strength ranking for candidate selection (high value, low risk).** Weinstein's Mansfield RS
and O'Neil's RS rating both say: when you can't take every setup, take the **strongest**. We currently rank
candidates by **closeness to the pivot**; ranking by **RS vs SPY** (or a blend) may pick better leaders when
the regime allows fewer slots than triggers. Test the 3-year delta of RS-ranked vs pivot-ranked admission.

**A3 · Trend-MA length — test Weinstein's 30-week (150-day) (exit refinement).** Weinstein exits on the
**150-day**, we use the **50-day**. We know 50 beat 200 ([[structural-exit-test-2026-07-25]]); 150 is
untested. A slower trend line holds winners longer (more Weinstein-pure) but gives back more per exit. Test
a 150-day trend-hold and a dual 50/150 variant across 2024/2025/2026.

**A4 · Box / swing-low trailing stop for fast movers (Darvas) (exit refinement).** For the fastest names,
a break of the **prior consolidation low** may exit sooner and cleaner than the 50-SMA. Test as an
alternative trail; likely a small, name-dependent effect.

**A5 · Enrich the regime score with a monetary / breadth-thrust input (Zweig) (nice-to-have).** Add a
rates/liquidity tilt or an advance-decline thrust to the 8-point score. Lower priority — the current gate
already did its job (capped the July drawdown); don't over-engineer it.

**Not recommended:** anything that re-introduces a **fixed profit target** or a **tight give-back trail** —
the canon (and our own 3-year tests, [[profit-protection-2026-07-25]]) say these cap winners and destroy the
edge. The +30%→+15% one-way lock is the only profit-protection that survived; keep it.

## Recommendation

1. **No immediate change** — the strategy is well-aligned with the canon after the v3/profit-lock work.
2. **Build & test A1 (volume) and A2 (RS ranking) first** — highest value, and both target our known weak
   spot (false breakouts in chop). Run each through the **2024/2025/2026 validation gate**; promote only if
   it wins (or holds) in all three years — the same discipline that killed the overfit exit.
3. A3/A4 (exit-MA / box trail) and A5 (regime enrichment) are second-tier experiments.
4. The psychology canon ([[trading-psychology]]) adds no code change but one reminder: the live risk now is
   **human override** — selling a trend-hold winner early by hand, or forcing a trade past the regime gate.
   The system is built to prevent both; the job is to let it run.

_Concept pages are original synthesis of publicly-known methodologies, not reproductions of copyrighted
text. Simulated/educational — not investment advice._
