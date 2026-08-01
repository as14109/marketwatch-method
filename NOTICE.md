# Notice — scope, third-party material, and disclaimers

## Scope of the licence

The [MIT licence](LICENSE) covers the **method documentation and tooling in this repository**.

It does **not** grant rights to any third-party material this tooling is designed to consume —
in particular:

- **Paid or member-gated watchlist services.** The daily watchlist this system was built against is a
  paid subscription product. Nothing from it is included here: no raw lists, no source pages, no
  per-ticker pages, no dated run artifacts, and no per-name trade ledgers. Supply your own, under your
  own subscription.
- **Copyrighted books.** The concept pages in `MW/wiki/concepts/` are **original syntheses** written to
  document a method — they are not reproductions, excerpts, or summaries offered as substitutes for the
  works they reference. Buy your own copies of the source books.

If you fork or adapt this repository, these exclusions travel with it. Do not redistribute gated or
copyrighted content through it.

## Not investment advice

All performance figures in this repository are **simulated / backtested**. No live capital was traded
and no real client accounts are represented. Hypothetical results have inherent limitations, including
hindsight bias and the absence of real execution, slippage, and fees.

Nothing here is investment advice, a recommendation, or an offer to buy or sell any security. This is
not a registered investment adviser or broker-dealer. Past or hypothetical performance is **not**
indicative of future results. Do your own research and consult a licensed professional before trading.
**Trade at your own risk.**

## Automation boundary

The agent in this system **never places trades**. `tools/tos_orders.py` prints order tickets for a human
to review and place. If a data source is unavailable, the pipeline **halts and notifies rather than
fabricating data** — a synthetic watchlist would silently corrupt every downstream book, backtest,
and report. Credentials are read from environment variables and are never handled by the agent.
