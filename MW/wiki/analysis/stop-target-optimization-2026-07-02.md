---
type: analysis
tags: [backtest, optimization, stops, targets, expectancy]
created: 2026-07-02
---

# Stop/target optimization — run 2026-07-02
Grid sweep over 11 Key Lists (2026-06-15 → 2026-07-02), ~119 signals per combo. Engine: corrected gap fills + vendor-data guards; BE arms at ~70% of target; trailing 9-EMA unchanged. Entries identical across combos — only exits differ.

| Stop | Target | N | Win% | Avg/trade | Cum P&L (10%/name) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| −5% | +15% | 119 | 46% | -0.05% | -0.64% |
| −5% | +7% | 119 | 45% | -0.19% | -2.21% |
| −5% | +12% | 119 | 46% | -0.22% | -2.61% |
| −4% | +15% | 119 | 41% | -0.30% | -3.60% |
| −4% | +5% | 119 | 42% | -0.34% | -4.07% |
| −4% | +7% | 119 | 41% | -0.35% | -4.14% |
| −5% | +9% | 119 | 45% | -0.41% | -4.93% |
| −3% | +15% | 119 | 36% | -0.46% | -5.50% |
| −4% | +12% | 119 | 41% | -0.46% | -5.52% |
| −3% | +5% | 119 | 38% | -0.52% | -6.21% |
| −3% | +7% | 119 | 36% | -0.54% | -6.45% |
| −4% | +9% | 119 | 41% | -0.55% | -6.57% |
| −3% | +12% | 119 | 36% | -0.61% | -7.28% |
| −3% | +9% | 119 | 36% | -0.70% | -8.38% |
| −2% | +5% | 119 | 29% | -0.96% | -11.38% |
| −2% | +7% | 119 | 28% | -0.97% | -11.49% |
| −2% | +15% | 119 | 26% | -0.99% | -11.79% |
| −2% | +12% | 119 | 27% | -1.00% | -11.84% |
| −2% | +9% | 119 | 27% | -1.07% | -12.68% |

## Interpretation
1. **The stop is the robust finding — and −3% is too tight.** Results improve *monotonically* with stop
   width across every target column: −2% ≈ −12% cumulative (whipsawed to death, 27% win rate), −3% ≈ −6.5%,
   −4% ≈ −4.5%, **−5% ≈ −2.5% (best row, 45–46% win rate)**. This month's semi-heavy names moved ±3%
   as *noise*; a −3% stop kept selling the noise. Matches [[momentum-masters-minervini]] practice —
   Minervini's *average* loss is 5–6% (max 10%); our −3% was tighter than the masters actually trade.
2. **The target finding is weaker but directional: let winners run.** +15% beats +7% in every stop row,
   but the spread is small (−0.05% vs −0.19%/trade at a −5% stop) — within noise. Confound: BE arming
   scales with the target in this sweep, so part of the wide-target edge is really *later breakeven
   arming* (fewer premature BE-stopouts), not the target itself.
3. **Reconciling with [[expectancy]]:** this does *not* contradict "don't widen stops for volatility."
   Minervini's frame is **risk = size × stop**. Moving −3%→−5% raises risk per full $100k position from
   $3k to $5k (0.5% of equity) — still inside his 1.25–2.5% band, but if adopted, trim size or pilot
   smaller to hold dollar risk constant. −5% stop with +15% first trim = 3R — squarely his
   "sell into strength at 2–6× risk."

## Suggested revision (pending user decision — rules unchanged until then)
`stop −5% → BE at +7% → sell 50% at +10–15% → trail 9-EMA`, with pilot sizing to hold dollar risk near
the current $3k/position. Re-run this sweep monthly; one regime cycle is not proof.

## Caveats
- ~3 weeks of data, one regime cycle (chop → selloff → rebound → whipsaw); lists overlap; most positions open (marked to last close); daily bars.
- Per [[expectancy]]: don't loosen stops for volatility; the tighter the stop, the more timing accuracy required. Cross-check any change against [[key-list-trade-rules]] and re-run monthly.
