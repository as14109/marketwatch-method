---
type: analysis
tags: [rules, risk-management, expectancy, review]
created: 2026-06-14
---

# Rules review — do stops / targets need to change? (2026-06-14)

Checking the current [[key-list-trade-rules]] (stop **−3%**, sell **50% at +7%**, trail rest under the
**9 EMA**) against [[expectancy]], [[eight-keys]], and the sizing/exit rules from
[[think-and-trade-like-a-champion-minervini]] and [[momentum-masters-minervini]].

## Verdict
**The two *levels* (−3% and +7%) are sound and don't need to change. Two things around them do:**

### 1. Stop −3% — KEEP the level ✅
- Minervini's [[expectancy]] math says **smaller absolute losses win** (losses compound geometrically)
  and he **explicitly opposes widening stops for volatility/ATR**. So a tight −3% is *philosophically
  correct*, not too tight. Earlier doubt (Momentum Masters used 3–10% chart stops) is resolved: those
  are sized so risk = position × stop ≈ 1–2.5% of equity, not a license to loosen.
- Caveat: −3% is *below* his 5–6% average-loss / 10% "uncle" max, so it will **whipsaw more** on names
  whose natural base low is >3% away. His fix is **not** a wider stop — it's a **smaller position** (or
  skipping the trade). That's rule change #3 below.

### 2. Target +7% sell-50% — KEEP ✅
- +7% on a −3% stop = **~2.3× risk (R)**, inside Minervini's "sell into strength at **2–6× risk**" band
  and comfortably ≥2:1 reward/risk. Trimming half early is textbook [[selling-into-strength]] / Eight
  Keys drawdown-key #1 ("better to sell early than late"). The trailed half keeps the upside open.
- No change. (If anything, in a *strong* tape you could let the first trim run toward the 3–4×R end, but
  the fixed +7% is a fine default.)

### 3. ADD a breakeven step — the real gap ⚠️ (recommended)
- Current rules jump from a −3% hard stop straight to a 9-EMA trail **only after +7%**. That leaves a
  window: a name up **+5%** can reverse and still be exited at **−3%**, turning a decent gain into a loss
  — which violates Eight Keys drawdown-key #4 ("**Protect your breakeven point**") and Minervini's "never
  let a decent gain turn into a loss; move the stop to at least breakeven once up a multiple of risk."
- **Fix:** once a position is up **≈ +5% (~1.7R)**, move the stop to **breakeven**. Progression becomes:
  `−3% hard stop → (at +5%) breakeven → (at +7%) sell 50% + trail rest under 9 EMA.`

### 4. ADD risk-based sizing — structural upgrade ⚠️ (recommended)
- A flat −3% stop only equals equal *dollar* risk if positions are equal size. Minervini: **size so the
  stop = a fixed % of equity** (1.25–2.5%). With a −3% stop and a 1% risk budget → position ≈ 33% of
  equity → **cap at the 20–25% max** (so effective risk on big names is ~0.6–0.75%). This makes every
  name's risk comparable and ties size to the stop instead of guessing.

## Suggested revised rule set
1. **Entry:** Key List pivot (ideally also passing the [[trend-template]]).
2. **Initial stop −3%** (or the nearest base low if tighter); **size so −3% risks ~1% of equity, capped at a 20–25% position.**
3. **At +5% (~1.7R): move stop to breakeven.**
4. **At +7% (~2.3R): sell 50%** ([[selling-into-strength]]).
5. **Trail the remaining 50% under the 9-day EMA**; exit on a close below it.

## So what
- Levels stay; we **add a breakeven trigger** (closes a real give-back gap) and **risk-based sizing**
  (needs a portfolio-equity input in `tools/update_watchlist.py`). Both flow straight from [[expectancy]]
  and [[eight-keys]]. See [[key-list-trade-rules]].

## Update (implemented 2026-06-14)
- ✅ **Breakeven step added**: at +5% move stop to breakeven (rules + `BE +5%` watchlist/report column + report status).
- ✅ **Sizing decided/implemented**: full position = **10% of portfolio** (user preference, not risk-equalized).
  Watchlist/report show full-position share counts when `MW_PORTFOLIO_EQUITY` is set. Risk-equalized
  sizing left as an optional future refinement in [[overview]].
