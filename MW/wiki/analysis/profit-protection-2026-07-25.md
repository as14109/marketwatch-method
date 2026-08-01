---
type: analysis
tags: [exits, profit-taking, trend-hold, backtest, oos, review]
created: 2026-07-25
updated: 2026-07-25
---

# Profit-protection for the trend-hold — 3-year test (2026-07-25)

The v3 exit ([[structural-exit-test-2026-07-25]]) holds the full position to a close below the
50-day SMA. The open risk: the 50-SMA **lags**, so a big winner can give back 15–25% from its peak
before the exit triggers. We tested ways to protect accumulated profit **without capping upside**,
across **2024 / 2025 / 2026** (full-portfolio sim, ≤12-name cap, $1.4M). Adopted from this:
**profit-lock +30% → +15%.**

## Results ($ at $1.4M equity)

| Rule (on top of 50-SMA hold, −12% disaster) | 2024 | 2025 | 2026 | 3-yr | vs pure |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Pure hold (no protection)** | +$218k | +$92k | +$150k | +$460k | — |
| **✅ Profit-lock +30% → +15%** | +$218k | **+$175k** | **+$157k** | **+$549k** | **+$89k** |
| BE-lock @ +15% | +$171k | +$44k | +$125k | +$339k | −$121k |
| Give-back trail (arm +25%, 15% from peak) | +$211k | +$94k | +$52k | +$357k | −$103k |
| High partial (⅓ @ +30%) | +$187k | +$100k | +$119k | +$406k | −$54k |
| Sell 50% @ +25%, lock rest +20% | +$208k | +$158k | **+$24k** | +$390k | −$70k |

## What worked, and the rule behind it

**Only the +30% → +15% one-way lock helped** — and it helped in all three years (+$89k over three,
never worse than pure). Every other protection rule **hurt**. The rule: once the high reaches **+30%**,
raise the disaster stop from −12% up to **+15%** above entry. No shares sold; the position still rides
to the 50-SMA on the upside; it simply can't round-trip a big gain back below +15%.

**Why the others failed — all the same disease (capping winners):**
- **BE-lock @ +15%** and **sell-50%/lock-+20%**: their trigger/floor sit *too low and too close* to
  normal price, so routine pullbacks eject decent winners before they run — worst of all in 2026
  (strong trends with deep pullbacks): the sell-50/lock-20 rule collapsed to +$24k vs pure's +$150k.
- **Give-back trail (15% from peak)**: once armed, normal volatility (>15% intraday-to-close swings on
  momentum names) triggered exits mid-trend — cut −$103k.
- **High partial (⅓ @ +30%)**: selling a third caps a third of every big winner — a steady −$54k drag.

The edge is specifically a **high (+30%), one-directional (stop-only, no sale) lock**. Anything that
fires on smaller moves, sells shares, or exits on give-back re-creates the exact winner-capping problem
the v3 trend-hold was built to fix ([[drift-review-2026-07-25]]).

## Adopted

`PROFIT_ARM_PCT = 0.30`, `PROFIT_LOCK_PCT = 0.15` in `tools/update_watchlist.py`; the ratchet lives in
`backtest.sim_one` (all books inherit it). The emailed report shows each open position's **50-SMA exit,
−12% disaster stop, and profit-lock state** (`arms @<+30% price>` → `🔒 +15% @<price>` once armed).
Verified: the gated book of record reproduces the validated 2026 figure **+$156,622 (+11.19% of equity)**.

_Simulated. 2024 is out-of-sample; all three test years were up years (no bear tape in the archive).
Educational only — not investment advice._
