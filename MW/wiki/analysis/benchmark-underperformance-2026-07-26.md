---
type: analysis
tags: [benchmark, spx, underperformance, cash-drag, pyramid, research]
created: 2026-07-26
updated: 2026-07-26
---

# Why the book lagged the S&P 500 in 2024–2025 — deep research (2026-07-26)

Full-year 2024 and 2025 the book of record made money but **underperformed the S&P 500**. This is the
root-cause study. Short version: **we did not truly underperform the market — we beat the *equal-weight*
S&P and small-caps every year; we lagged the *cap-weighted* SPX for two specific, understood reasons —
(1) we hold a large cash buffer by design (the biggest factor), and (2) 2024–25 SPX returns were
concentrated in a handful of mega-caps we don't chase.**

## The scoreboard (simulated book vs indices, calendar returns)

| Year | 📘 Book of record | SPY (cap-wt) | QQQ | **RSP (equal-wt)** | IWM (small-cap) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2024 | **+15.6%** | +25.6% | +27.7% | **+12.8%** | +12.0% |
| 2025 | **+12.5%** | +18.0% | +21.0% | **+11.5%** | +12.6% |
| 2026 YTD | **+11.2%** | +8.7% | +11.9% | +11.6% | +17.5% |

- vs **RSP (equal-weight S&P)** — the "average stock" — the book **won all three years** (+2.8 / +1.0 /
  −0.4 pts; ahead cumulatively).
- vs **IWM (small-caps)** — won 2024, ~matched 2025, lagged 2026.
- vs **cap-weighted SPY/QQQ** — lagged 2024–25 (the years in question), then **beat SPY in 2026 YTD**.

So the "underperformance" is specifically **versus the cap-weighted SPX/Nasdaq in 2024–25**, not versus the
broad market. Against the fair benchmark for a diversified, risk-managed, equal-ish-weighted book — RSP —
we outperformed.

## Cause 1 (dominant): we are deliberately under-invested — cash drag

The book deploys only **~41% of capital** on average (regime gate keeps us in cash during distribution;
neutral-regime entries are half-size pilots; ≤12 names). **SPY is 100% invested.** In a +25% year, holding
~60% cash is a huge drag on *return-on-equity* even when the stocks we own do well.

**Evidence — the pyramid add-on test.** We modeled scaling healthy pilots to full when the regime confirms
(deploying the idle capital) and measured it across 2024/2025/2026:

| Year | Book (baseline) | + pyramid (more invested) | Δ |
| --- | ---: | ---: | ---: |
| 2024 | +$218k (+15.6%) | **+$310k (+22.2%)** | +$92k |
| 2025 | +$175k (+12.5%) | +$129k (+9.2%) | −$46k |
| 2026 YTD | +$157k (+11.2%) | +$211k (+15.1%) | +$55k |
| 3-yr | +$549k | +$651k | +$101k |

Deploying more capital **closed ~2/3 of the 2024 gap to SPY** (+15.6% → +22.2% vs SPY +25.6%) — confirming
under-investment is the main driver. **But it is not a free fix:** the same extra capital *lost* −$46k in
2025 (adds made into "confirmed" uptrends that then reversed). Net +$101k over three years, but it **loses
one of the three years**, so it fails our promotion gate as-is (see Recommendations).

## Cause 2: 2024–25 SPX returns were mega-cap-concentrated

SPY +25.6% (2024) vs **RSP +12.8%** means the cap-weighted index nearly *doubled* the equal-weight — the
gain was carried by a small number of mega-caps (the "Magnificent Seven" complex). Our book is diversified,
capital-capped (≤25%/group), and takes Key-List leaders across sectors — it structurally **cannot match a
cap-weighted index in a year of extreme mega-cap concentration**, and it shouldn't try (that's
concentration risk). The right read: RSP is the honest benchmark, and we beat it.

## Cause 3: risk management costs bull-market upside (by design)

The −12% disaster stop, the 50-SMA trend exit, the regime gate, and the ≤12-name cap all exist to cut
*drawdowns*. The premium for that insurance is giving up some upside in a straight-up bull — whipsaw exits,
being flat during rallies the regime hadn't yet confirmed. That is the intended trade-off ([[ytd-review-2026-07-25]]:
the same discipline cut the July-2026 drawdown ~4.5× vs taking every signal). You cannot have both minimum
drawdown *and* maximum bull-market capture.

## What would actually close the SPX gap (ranked candidates — test before adopting)

1. **Deploy more capital in confirmed uptrends (the pyramid) — REFINED & REJECTED 2026-07-26.** Tested six
   stricter add-conditions (peak regime 8/8; proven-winner gate gain≥8% / ≥15%; not-extended ≤12% above the
   50-SMA; combos). **None wins all three years.** Every variant that adds meaningful capital still *loses
   2025* (base +$129k / gain≥8% +$146k / gain≥15% +$150k / not-extended +$163k vs baseline +$174.8k); the
   8/8-only variants avoid 2025 adds (tie) but then their few adds hurt 2024/2026. 3-yr totals rise +$22k–$73k
   but always at the cost of one year. **Root cause: 2025's "confirmed uptrend" days reversed**, so
   add-on-confirmation gives back regardless of the gate — no signal inside "add on strength" separates 2025's
   false confirmations from the real ones. **The half-size pilots / cash buffer are the risk control doing its
   job in the choppy year — not adopted.** It remains a *risk-preference fork*: if the goal is raw return over
   drawdown, the proven-winner "gain≥8%" add nets +$52k/3yr for a worse 2025; the book of record keeps the
   discipline.
2. **Loosen the regime gate's cash bias in strong uptrends** (allow more/near-full deployment at score 7–8).
   Same idea from the entry side; validate it doesn't reintroduce drawdown.
3. **Report against the right benchmark.** Show **RSP (equal-weight)** alongside SPY so the comparison is
   apples-to-apples; we beat RSP every year. (Presentation, not strategy.)
4. **Accept the trade-off explicitly.** If the goal is risk-adjusted return / low drawdown, lagging a
   mega-cap-led cap-weighted index in a bull year is *expected and acceptable* — our Sharpe/drawdown profile
   is the selling point, not raw return vs SPX.

## Bottom line

We beat the average stock (RSP) all three years; the SPX gap in 2024–25 is **~⅔ cash drag** (fixable, but
the fix costs in choppier years) and **~⅓ mega-cap concentration + the cost of risk management** (largely
by design). The pyramid quantifies the cash-drag piece and is worth **refining, not adopting as-is** (it
fails the 2025 year). For marketing, benchmark against **RSP**, not SPY, and lead with **risk-adjusted**
performance — that's the honest and stronger story.

_Simulated / backtested. Educational only — not investment advice._
