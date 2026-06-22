---
type: concept
concept_kind: strategy
tags: [rules, risk-management, exits, stops]
created: 2026-06-14
updated: 2026-06-14
---

# Key List trade rules

**Definition:** The mechanical risk/exit rules applied to every [[2026-06-15-key-list]] name. Entries
come from the Key List **setup/pivot price** ("entry"); these rules turn an entry into a managed trade.

## The rules
1. **Hard stop −3%** — initial stop at `entry × 0.97`. If the stop is hit, exit the full position. This
   is the max risk per trade before any profit-taking.
2. **At +5% → move stop to breakeven** — once price reaches `entry × 1.05` (~1.7× the 3% risk), raise
   the stop to the entry price. This protects the gain so a winner can't round-trip into a loss
   (Eight Keys drawdown-key #4, "protect your breakeven point" — see [[eight-keys]]).
3. **At +7% → sell 50%** — at `entry × 1.07`, sell **half** the position to bank profit and de-risk
   (our [[selling-into-strength]] step; ~2.3× risk, inside Minervini's "sell into strength at 2–6×" band).
4. **Trail the remaining 50% under the 9-day EMA** — after the +7% sale, hold the rest and exit if
   price **closes below the 9-day EMA**. This lets winners run while protecting open profit.

## Worked example (entry = 100.00)
- Initial stop = **97.00** (−3%); risk ≈ 3% of the position.
- At **105.00** (+5%) → move stop up to **100.00** (breakeven). No more downside on the trade.
- At **107.00** (+7%) → sell 50%. Remaining 50% rides on house money.
- Trail the last 50% under the 9 EMA; exit on a close below it.

## How the MAs are used
- **9 EMA** — the trailing stop after the +7% sale (and a quick read of short-term trend).
- **21 MA** — near-term trend / first support reference.
- **50 MA** — intermediate trend; a common add/defend line.
- **200 MA** — long-term trend; above = healthy backdrop.
- Live values per ticker are in the [[overview]] watchlist, refreshed by `tools/update_watchlist.py`.

## Position sizing
- **A full position = 10% of the portfolio.** Up to **10 positions → fully invested** (no margin), à la
  David Ryan ([[momentum-masters-minervini]]). With the −3% stop, a full position risks **0.3% of equity**
  (10% × 3%); if all 10 were stopped at once, total risk ≈ 3%. Conservative by design.
- **Build into it ([[position-scaling]]):** start with a pilot and add as the trade proves itself —
  [[smart-add-on-strategy]] starts ~20–35% of full (≈2–3.5% of portfolio); [[pyramid-50-30-20-strategy]]
  builds 5% → 3% → 2% of portfolio to reach the 10% full size.
- **Share count** per name is shown in the [[overview]] watchlist when the portfolio value is set via
  the `MW_PORTFOLIO_EQUITY` env var: `full shares = floor(equity × 10% / entry)`.
- _Note:_ this fixed-10% scheme gives equal *dollar* exposure, not equal *risk*. To equalize risk
  instead (Minervini's frame: size so the stop = a fixed % of equity), see [[expectancy]] — flagged in
  [[overview]] as a possible later refinement.

## How it connects
- Sits on top of [[position-scaling]]: a "new buy" starts via [[smart-add-on-strategy]]; a confirmed
  add-on uses [[pyramid-50-30-20-strategy]]; the +7% trim and 9-EMA trail are [[selling-into-strength]].
- Triggers/ratings interpreted via [[can-slim]]; entry quality gated by [[trend-template]] + [[vcp]];
  the whole thing must produce positive [[expectancy]].

## Source trail
- Rule set specified by the user (2026-06-14) for the [[2026-06-15-key-list]] watchlist.
