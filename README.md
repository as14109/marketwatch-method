# Marketwatch — Method & Tools

An **agent-maintained systematic trading research system**: a rules-based swing/position-trading method,
the Python tooling that runs it end-to-end every evening, and an LLM-maintained knowledge wiki that
compounds instead of being re-derived on every query.

Built on the **LLM Wiki pattern** — the LLM is the *maintainer*, not the chat window. It reads the
sources, files the knowledge, runs the validation, and enforces the rules a human abandons under pressure.

> **Not investment advice.** Every performance figure here is **simulated / backtested** — no live
> capital, ever. This documents a *method*: rules, reasoning, tooling, and the evidence behind each
> decision. All trading decisions and executions are yours.

---

## Why this exists

Retail systematic-trading tooling splits into two camps:

- **Black-box signal services** — you get picks, not a process, and no way to test whether the process holds up.
- **Heavyweight quant frameworks** (backtrader, zipline, QuantConnect) — powerful, but they assume you
  already have a strategy, a data pipeline, and the discipline to follow them.

Nothing occupies the middle: a **research loop** where an agent maintains the knowledge base, runs
point-in-time validation on every proposed change, and gates the trading rules on evidence.
That's what this is.

## The discipline that matters most

Every proposed strategy change must **win across three independent years (2024 / 2025 / 2026) or it's
rejected.** No exceptions for good stories or strong in-sample results.

That gate has killed several ideas that looked good — each written up as a dated analysis in
[`MW/wiki/analysis/`](MW/wiki/analysis):

| Idea | Result | Verdict |
| --- | --- | --- |
| Pyramiding add-ons on regime confirmation | +$101k over 3 years — but **lost 2025** (−$46k) | ❌ rejected; 6 refined variants also failed |
| Volume-confirmation filter on entry | Hurt **all three years** (−$531k at 1.3× avg volume) | ❌ rejected |
| Regime-conditioned exits | +$67.7k in-sample 2026, **−$29k out-of-sample 2025** | ❌ rejected as overfit |
| 50-day-SMA trend-hold exit | Beat the prior swing exit in **all three years** (+$230k vs +$32k) | ✅ adopted |
| +30% → +15% profit lock | +$89k over 3 years, won every year | ✅ adopted |

The system's most valuable output is the changes it **stopped** its operator from shipping.

## The method (v3 — trend-hold)

- **Regime gate** — an 8-point score (index trend, breadth, VIX level & direction, distribution days)
  decides *how much risk to press*: 7–8 → full size, 4–6 → half-size pilots, ≤3 → **no new buys**.
- **Selection** — candidates must pass all 8 criteria of a computable Stage-2 trend template, sit within
  8% of the 21-day SMA (no chasing), and clear an earnings-proximity and cooldown check.
- **Entry** — buy-stop at the trigger, **DAY order only** (no gap-up chasing; a stop-limit at the trigger
  fills only if price actually trades there).
- **Exit** — hold the **full** position until a **daily close below the 50-day SMA**. A **−12% disaster
  stop** underneath (stop-market, so gap-downs exit at the open). Once a position trades **+30%** above
  entry, ratchet the stop to **+15%** — protecting big winners without capping upside.
- **No** fixed profit target, no breakeven stop, no partial sales. All three tested worse.
- **Sizing** — a full position ≈ **7.14% of equity**, ≤12 names (≈86% max deployed), ≤25% per industry
  group, ETFs and neutral-regime pilots at half size.

Full playbook: [`MW/wiki/portfolio-plan.md`](MW/wiki/portfolio-plan.md) ·
rules: [`MW/wiki/concepts/key-list-trade-rules.md`](MW/wiki/concepts/key-list-trade-rules.md)

## Three parallel books

Every run simulates three portfolios side by side, so the value of discipline stays visible:

1. **Gated (book of record)** — the full discipline layer: regime gating, trend-template-only, extension
   and cooldown limits, position/group caps.
2. **Ideal (paper)** — a leader-pullback variant, tracked but not traded.
3. **Benchmark (every-signal)** — takes *every* trigger with no selection discipline, but under the
   **same capital cap**, so the gap isolates what selection is worth rather than just measuring leverage.

## What's here

```
CLAUDE.md              the schema — wiki structure + agent workflows (ingest / query / lint / daily run)
MW/wiki/portfolio-plan.md   the everyday operating playbook
MW/wiki/concepts/      the methodology: CAN SLIM, SEPA/VCP/Trend Template, stage analysis,
                       trend following, box theory, market timing, expectancy, psychology, …
MW/wiki/analysis/      dated research — every adopted and rejected strategy change, with evidence
MW/wiki/entities/      bios of the traders/educators behind the method
MW/wiki/templates/     page templates for extending the wiki
tools/                 20 Python tools (see below)
```

**Key tools**

| Tool | Does |
| --- | --- |
| `regime.py` | the 8-point market-regime gate |
| `validate_list.py` | scores candidates against the 8-criterion trend template |
| `update_watchlist.py` | moving averages + rule levels for the current list |
| `backtest.py` | point-in-time simulation of the exit engine |
| `gated_book.py` / `ideal_book.py` / `open_positions.py` | the three parallel books |
| `period_pnl.py` / `mtd_pnl.py` / `cumulative_pnl.py` | YTD/QTD/MTD and since-inception scoreboards |
| `build_report.py` / `send_report.py` | the daily report (markdown + HTML + email) |
| `tos_orders.py` | broker order tickets (buy-stop + protective stop) for **you** to review and place |
| `pricecache.py` | shared on-disk daily price cache (makes the routine ~8× faster) |
| `lint_wiki.py` | wiki health check — contradictions, orphans, stale claims |

The agent **never places trades.** `tos_orders.py` prints tickets; a human reviews and places them.

## What's intentionally NOT here (bring your own)

This repo **excludes copyrighted and paid material**:

- **The source books** (Minervini, Weinstein, Farley, Steidlmayer, Darvas, Zweig, …) — buy your own copies.
  The concept pages are original syntheses, not reproductions.
- **The member-gated daily watchlists** the tooling was built against, and anything that would redistribute
  them — the live watchlist, dated snapshots, per-ticker pages, and per-name trade ledgers.

The tooling expects **you** to supply a watchlist in `MW/raw/<YYYY-MM-DD>-key-list.md` from your own
subscription. Unresolved `[[wikilinks]]` to sources and tickers are expected — they point at material you add.

## Quick start

```bash
pip install --user yfinance
```

1. Open **`MW/`** as an [Obsidian](https://obsidian.md) vault to browse the wiki (backlinks, graph view).
2. Drop your own watchlist into `MW/raw/<YYYY-MM-DD>-key-list.md` (format: `- **TICKER 123.45**` per line,
   or a `Ticker,Trigger Price` CSV block).
3. Run the routine:

```bash
python tools/update_watchlist.py && python tools/validate_list.py <YYYY-MM-DD> && python tools/regime.py
```

4. Read [`CLAUDE.md`](CLAUDE.md) to drive the whole thing with an agent (Claude Code or similar).

## Config (yours, never committed)

| Var | Purpose |
| --- | --- |
| `MW_PORTFOLIO_EQUITY` | your book size, for share counts (e.g. `1000000`) |
| `MW_SMTP_USER` / `MW_SMTP_PASS` | sending account + **app password** for the emailed report (optional) |
| `MW_MAIL_TO` / `MW_MAIL_CC` | report recipients (optional) |

Credentials are read from your environment and never handled by the agent.

## Licence

[MIT](LICENSE) for the method documentation and tooling. It does **not** grant rights to the excluded
books or any member-gated content — supply those under your own subscription. Trade at your own risk.
