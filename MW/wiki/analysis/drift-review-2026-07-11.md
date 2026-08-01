---
type: analysis
tags: [review, drift, risk-management, expectancy, post-mortem]
created: 2026-07-11
---

# Strategy drift review — "market ok, book lagged" (2026-07-11)

**Question:** the indexes were fine but our book drifted — what could we have done differently to
maximize profit / reduce losses? Grounded in the measured single-account book, not theory.

## The numbers (window 2026-06-15 → 07-10)
- **Market:** SPY **+0.3%**, QQQ **−2.4%**, IWM **+0.5%** — index *levels* flat, but the *character* was
  hostile: 7 distribution days, failing breadth, QQQ actually down. Choppy, not trending.
- **Take-everything book** (deduped single account): 36 open + 43 closed = **−$35,914 (−3.59%)**
  - Open survivors marked to market: **+$42.8k** ← what the open-positions table shows
  - Closed trades: 43, **12% win rate, −$78,667 realized** ← the hidden drag
- **Gated (disciplined) book:** **−0.66% ≈ −$6,563** — a *third* of the drawdown, roughly matching the flat tape.

## Diagnosis — three findings
### 1. The "drift" is mostly a reporting illusion + a chop tax
The open-positions table shows only **survivors** (+$42.8k). The real single-account number, counting the
43 closed stop-outs, is **−$35.9k**. Winners are still open (unrealized); losers already closed. Nothing is
broken — a breakout system **structurally loses in a flat/choppy tape** (breakouts fail, −5% stops pile up).
QQQ was *down* 2.4%; this was not a breakout-friendly market despite the headline index level.

### 2. The discipline layer already fixes ~80% of it — we just weren't trading it
Gated book **−0.66%** vs take-everything **−3.59%**. The regime gate + TT-only + heat caps + cooldown we
built on 2026-07-09 ([[process-improvements-2026-07-09]]) would have avoided **~$29k** of the drawdown.
**The single biggest "what we could have done differently" is: run the gated book as the real book, not
the every-signal book.** The take-everything sim is a *benchmark*, not a trading plan.

### 3. The asymmetry is right; the frequency is wrong
- Avg win **+6.97%**, avg loss **−5.06%** → payoff **1.38** (healthy). Runners let to +10–14%. Cutting
  losers at −5% is working *per trade*.
- But closed **win rate is 12%** — in this chop, far too many breakouts were taken and failed. At 1.38
  payoff you need ~42% wins to break even. **The leak is entry frequency/selection, not stop width or
  target.** (The −5% stop is still optimal — [[stop-target-optimization-2026-07-02]].)

## What we'd do differently — prioritized, evidence-led
1. **Trade the gated book (not every signal).** Already built; adopt it as the book of record. −0.66% vs
   −3.59% is the measured value. *(No new work — a decision.)*
2. **Switch entry door in NEUTRAL/DISTRIBUTION regimes — breakout → pullback.** In a non-confirmed tape,
   buy strength *into support* (near the 21-EMA / prior pivot: Farley Dip Trip, Minervini low-cheat) rather
   than chasing the breakout that fails. Lower-risk entry, better R:R, far fewer whipsaws. *(strategy-review
   #2 relative; new — worth a backtest of pullback vs breakout fills in NEUTRAL.)*
3. **Pyramid the winners instead of starting new names.** When only a few names work (9 of 36 open >+5%),
   concentrating INTO them (add on the +7%/BE confirmation) compounds more than spreading into new
   breakouts. *(strategy-review #6, unmodeled upside.)*
4. **Group-correlation cap enforced live.** The 43 closed losers cluster on chop days and in the same
   groups (cyber/cloud ETFs/semis fade together). The gated book's ≤25%/group + ETF-½ already addresses
   this; the every-signal book ignored it.
5. **Breakout circuit-breaker.** When regime is NEUTRAL *and* the trailing breakout batting average is
   poor, take **zero new breakouts — adds to winners only.** A results-gated version of the regime gate.

## Bottom line
We didn't need a better stop or target. We needed **fewer, better-timed entries in a choppy tape** — which
is exactly what the discipline layer does. Adopt the gated book as the real book (item 1), add a
pullback-entry mode for NEUTRAL regimes (item 2), and let the winners compound via adds (item 3). The tape
will do the rest when it turns; a confirmed uptrend is where this system makes its money
([[cumulative-pnl-2026-06-30]] — positive in the rebound weeks, negative in the chop).

_Not financial advice. Educational analysis of our own simulated book._
