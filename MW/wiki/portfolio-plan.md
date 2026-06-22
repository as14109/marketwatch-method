---
type: overview
tags: [plan, portfolio, risk-management, process]
created: 2026-06-18
updated: 2026-06-18
---

# $1M Portfolio Operating Plan

The everyday playbook for running a **$1,000,000** growth/momentum portfolio, synthesizing every source
ingested so far. This is a **process document, not financial advice** — it records the rules and reasoning;
all decisions and executions are the human's. (`MW_PORTFOLIO_EQUITY=1000000` drives the share counts in [[overview]].)

> Lineage: [[can-slim]] (O'Neil/IBD) · [[mark-minervini]] [[sepa]]/[[vcp]]/[[trend-template]]/[[expectancy]]/[[eight-keys]] ·
> [[momentum-masters-minervini]] (Minervini/Ryan/Zanger/Ritchie II) · [[alan-farley]] [[pattern-cycle]]/[[seven-bells]]/[[cross-verification]] ·
> [[peter-steidlmayer]] [[market-profile]]/[[auction-market-theory]]/[[value-area]] · [[chart-patterns]]/[[harmonic-patterns]] (Knight/Duddella).

## 1. Regime gate — *trade the market first*
Only press risk in a confirmed uptrend (CAN SLIM "M"; [[market-breadth]]). Scale exposure to results
([[eight-keys]] "trade small before you trade big"):
- **Healthy/broadening tape** → fully engaged, up to ~8–12 positions.
- **Distribution / risk-off** (e.g. the post-FOMC [[kevin-warsh]] higher-for-longer overhang) → fewer names,
  smaller size, raise cash; favor only the cleanest base breakouts.
- Current read in [[overview]] macro themes.

## 2. Universe & selection — *leading stocks in leading groups*
- **Funnel:** the daily [[2026-06-22-key-list|Key List]] is the candidate pool ([[semiconductors]]/[[cybersecurity]]/AI infra leadership now).
- **Quality filter:** [[trend-template]] (Stage 2: price > rising 150/200-day, 50 > 150 > 200, RS rank ≥ 70),
  [[can-slim]] ratings (composite, RS, A/D accumulation, group rank), clean [[vcp]] / [[chart-patterns]] bases.

## 3. Entry — *two doors, never chase*
- **Initiating (breakout):** buy the pivot on a volume-backed base breakout (3rd Watch / Coiled Spring /
  cup-with-handle). **Do NOT chase gap-ups** — per [[backtest-2026-06-18]], chasing Monday gaps was the main
  P&L drag; if price opens more than ~2% above the pivot, wait for a pullback or use a limit near the pivot.
- **Responsive (value):** buy pullbacks toward support/MA/value (Dip Trip / First Pullback [[seven-bells]];
  [[harmonic-patterns]] completion; near the [[value-area]]) — the lower-risk entry.
- **Edge booster:** prefer pivots with [[cross-verification]] (9/21/50/200 MAs + prior highs cluster).

## 4. Position sizing — *concentrate, risk-defined*
- **Full position = 10% of equity = $100,000** (share counts in [[overview]]). Max ~8–12 names; never > 25% in one name.
- **Build in ([[position-scaling]]):** pilot first ([[smart-add-on-strategy]], ~$20–35k), then add on confirmation
  ([[pyramid-50-30-20-strategy]]: ~$50k → $30k → $20k to reach the full $100k). Add *less* than the current position; don't lift the average too far.
- **Risk per full position** ≈ entry × 3% × $100k ≈ **$3,000 (0.3% of equity)**. Total open "heat" gated by results
  ([[expectancy]]): ~1% when struggling → 2–3% when working.

## 5. Exits & management — *never give back a big gain* ([[key-list-trade-rules]])
1. **Initial stop −3%** (full exit). 2. **+5% → stop to breakeven.** 3. **+7% → sell 50%.** 4. **Trail the
   remaining 50% under the 9-day EMA** (exit on a close below it). Sell into strength ([[selling-into-strength]]);
   cut early on violations (low-volume breakout + heavy-volume reversal, close below 20/50-day post-breakout).

## 6. Mindset & math
- **Positive [[expectancy]]:** keep losses a fraction of gains; accept a modest win rate ("build failure in").
- Compound singles/doubles; avoid revenge trading; protect capital *and* confidence ([[eight-keys]]).

## 7. Daily process (automated — see [[overview]] & `CLAUDE.md`)
1. Ingest the latest [[2026-06-22-key-list|Key List]] (member-gated; via browser). 2. `update_watchlist.py` → MAs,
   rule levels, $100k share counts. 3. `backtest.py` → how prior lists' triggered names are performing.
   4. `send_report.py` → emailed report. 5. Review: triggers, breakeven/+7% hits, trail-stop watch, regime.

## 8. Review cadence
Track win rate, avg win/avg loss, and expectancy via [[backtest-2026-06-18|the backtest]]; reallocate weak
holdings into stronger setups (Ryan's 2-for-1 rule); revisit this plan as new sources are ingested.

> **Not financial advice.** Educational synthesis of ingested sources; do your own research.
