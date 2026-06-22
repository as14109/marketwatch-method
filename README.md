# Marketwatch — Method & Tools

A shareable, LLM-maintained **trading knowledge base** and operating playbook: the methodology synthesis,
concept pages, the $1M portfolio plan, and the Python tooling. Built with the LLM Wiki pattern (the LLM is
the wiki maintainer; you curate sources and ask questions).

> **Not financial advice.** This documents a *method* — rules, reasoning, and tooling. All trading
> decisions and executions are yours.

## What's here
- **`CLAUDE.md`** — the schema: how the wiki is structured and the workflows (ingest / query / lint / daily routine).
- **`MW/wiki/portfolio-plan.md`** — the everyday operating playbook (regime → selection → entry → sizing → exits).
- **`MW/wiki/concepts/`** — the methodology: CAN SLIM, SEPA/VCP/Trend Template, expectancy, the Eight Keys,
  position scaling, selling into strength, Market Profile / auction-market theory / value area, the Pattern
  Cycle / 7-Bells / cross-verification, chart & harmonic patterns, the Key List trade rules.
- **`MW/wiki/entities/`** — bios of the traders/educators behind the method.
- **`MW/wiki/templates/`** — page templates for extending the wiki.
- **`tools/`** — `update_watchlist.py` (MAs + rule levels), `build_report.py`, `send_report.py`, `backtest.py`.

## What's intentionally NOT here (bring your own)
This bundle **excludes copyrighted and paid material**:
- The source books (Minervini, Farley, Steidlmayer, Knight, Duddella) — buy your own copies.
- The member-gated **Mission Winners Key Lists** and anything derived from them (the live watchlist,
  dated snapshots, per-ticker pages, backtests). The tooling expects *you* to supply a Key List in
  `raw/<YYYY-MM-DD>-key-list.md` from your own subscription.

So unresolved `[[wikilinks]]` to sources/tickers are expected — they point to material you add yourself.

## Quick start
1. Open the **`MW/`** folder as an [Obsidian](https://obsidian.md) vault to browse the wiki (graph view, links).
2. Python tools need `yfinance`: `pip install --user yfinance`.
3. Add your own Key List to `raw/`, then run `python tools/update_watchlist.py` and `python tools/backtest.py <date>`.
4. Read `CLAUDE.md` to drive it with an LLM agent (Claude Code, etc.).

## Config (your own, never committed)
- `MW_PORTFOLIO_EQUITY` — portfolio value for share counts (e.g. `1000000`).
- `MW_SMTP_USER` / `MW_SMTP_PASS` — Gmail app password for the emailed report (optional).

## License / use
Share and adapt the **method and tools** freely. Do **not** redistribute the excluded books or any
member-gated content. Trade at your own risk.
