# Marketwatch — LLM Wiki Schema

This repo is a **personal markets/trading knowledge base** built with the LLM Wiki pattern.
You (the LLM) are the **wiki maintainer**. The human curates sources, directs analysis, and
asks questions. You do all the reading, summarizing, cross-referencing, filing, and bookkeeping.

> The wiki is a **persistent, compounding artifact**. Don't re-derive knowledge on every query —
> read what's already been compiled, extend it, and keep it consistent.

## Layers

1. **Raw sources** — `MW/raw/`. Immutable. Articles, transcripts, reports, filings, notes, images
   (`MW/raw/assets/`). You read from here but **never edit these files**. This is the source of truth.
2. **The wiki** — `MW/wiki/`. LLM-owned markdown. You create, update, cross-link, and maintain it.
3. **The schema** — this file. How the wiki is structured and the workflows to follow. Co-evolve it.

Everything lives inside the Obsidian vault `MW/` so the human can browse it (links, graph view) live.

## Wiki layout (`MW/wiki/`)

| Folder | Purpose | Page = |
| --- | --- | --- |
| `index.md` | Catalog of every page — link + one-line summary, by category. **Update on every ingest.** | — |
| `log.md` | Append-only chronological record of ingests / queries / lints. | — |
| `overview.md` | The dashboard: watchlist, active theses, key macro themes, open questions. | — |
| `sources/` | One summary page per ingested source. | a source |
| `entities/` | Tickers/companies, people (execs, fund managers, analysts), institutions (funds, central banks). | a thing |
| `concepts/` | Macro themes, sectors, strategies, technical/fundamental indicators, mechanisms. | an idea |
| `theses/` | Investment theses — claim + evidence + conviction + disconfirmers. | a bet |
| `analysis/` | Filed-back answers to queries (comparisons, deep dives, screens). | an exploration |
| `templates/` | Page templates. Copy these when creating new pages. | — |

## Conventions

- **Links:** use Obsidian wikilinks `[[page-name]]` (no path, no `.md`). Link liberally — a link to a
  page that doesn't exist yet is fine; it marks something worth writing later.
- **Filenames:** kebab-case. Tickers as `entities/aapl.md`. People as `entities/jerome-powell.md`.
  Source pages prefixed by date: `sources/2026-06-14-q1-earnings-call.md`.
- **Frontmatter (YAML):** every wiki page starts with frontmatter so Obsidian Dataview can query it:
  ```yaml
  ---
  type: source | entity | concept | thesis | analysis
  tags: [equities, semis, macro]
  created: 2026-06-14
  updated: 2026-06-14
  ---
  ```
  Entity/thesis pages add domain fields (see templates): `ticker`, `sector`, `conviction`, `direction`.
- **Citations:** when a wiki claim comes from a source, cite it inline as `[[2026-06-14-source-name]]`.
- **Contradictions:** when a new source contradicts an existing claim, do NOT silently overwrite.
  Flag it with a `> [!warning] Contradiction` callout, keep both with dates, and note which is newer.
- **Not financial advice:** record claims, evidence, and reasoning. Never place trades, move money,
  or tell the human to buy/sell — surface the analysis and let them decide.

## Operations

### Ingest (human drops a source in `MW/raw/` and says "ingest X")
1. Read the source fully. For markdown with inline images, read text first, then view key images.
2. Discuss the key takeaways with the human before writing.
3. Create `sources/<date>-<slug>.md` from `templates/source-template.md` — summary, key facts, quotes,
   and links to every entity/concept/thesis it touches.
4. Update affected `entities/`, `concepts/`, and `theses/` pages (create missing ones). A single source
   often touches 10–15 pages — that's expected.
5. Update `index.md` (add/refresh entries) and `overview.md` if it shifts a thesis or watchlist item.
6. Append a line to `log.md`.

### Query (human asks a question)
1. Read `index.md` first to find relevant pages, then drill in. (Add a search tool later if it grows.)
2. Synthesize an answer **with `[[wikilink]]` citations**.
3. If the answer is durable (a comparison, screen, deep dive, discovered connection), **file it back**
   as a page in `analysis/`, add it to `index.md`, and log it. Explorations should compound.

### Lint (human says "lint" / "health check")
Scan for: contradictions between pages, stale claims newer sources superseded, orphan pages (no inbound
links), important concepts mentioned but lacking a page, missing cross-references, and data gaps a web
search could fill. Report findings + suggest new questions and sources. Apply fixes the human approves.

## Log format
Append-only, one line per event, consistent prefix so it's greppable
(`grep "^## \[" MW/wiki/log.md | tail -5`):

```
## [2026-06-14] ingest | Q1 Earnings Call — NVDA
## [2026-06-14] query  | Compare semis capex exposure
## [2026-06-14] lint   | 3 contradictions, 2 orphans
```

## Daily watchlist routine (EOD, weekdays)
The routine assumes a **daily watchlist source** that publishes each evening after the close, for the
next trading day (this repo was built against a paid, member-gated service — **bring your own**; nothing
from it ships here). A scheduled task can fire **Sunday–Thursday at 9 PM** local (cron `0 21 * * 0-4`).
Runs are idempotent: if the day's list is already saved in `MW/raw/` the run no-ops; if the list isn't
published yet (or the source is unreachable), it **stops and notifies rather than fabricating**.
Each successful run:
1. **Find the latest list.** Fetch it from your own subscription — via an authenticated browser session
   if the page is member-gated, or any source you have the rights to read. **Never handle credentials in
   the agent, and never invent data:** if the list isn't available, **stop and notify**. This is the
   single most important rule in the pipeline — a fabricated watchlist silently poisons every
   downstream book, backtest and report.
2. **Save raw** to `MW/raw/<YYYY-MM-DD>-key-list.md` (verbatim), where the date is the trading day.
3. **Ingest** per the normal flow: source page, entity pages (with stop/T1), index, log.
4. **Refresh the watchlist:** run `python tools/update_watchlist.py`. It auto-selects the **latest**
   `MW/raw/*key-list*.md` by date, pulls MAs via `yfinance`, applies [[key-list-trade-rules]], and
   rewrites the table between the `WATCHLIST` markers in `overview.md` + writes a dated snapshot to
   `wiki/analysis/watchlist-<date>.md`.
5. **Validate the list against the wiki:** run `python tools/validate_list.py <date>`. It scores each name
   against Minervini's [[trend-template]] (8 Stage-2 criteria, computable from price; RS is an SPY proxy).
   Report which names **pass the full Trend Template** vs. fail and why. Combine with the **regime gate**
   ([[portfolio-plan]] §1 — only press in a confirmed uptrend) and "don't chase gap-ups." The fundamental
   CAN SLIM bits (composite/EPS/accumulation/group) come from the Key List itself.
   **Also run `python tools/regime.py`** — the computed 8-point regime score (SPY/QQQ/IWM trend, RSP/SPY
   breadth, VIX level+trend, distribution days) that rewrites the REGIME block in `overview.md` and maps
   to allowed new entries: 7–8 → 3–5 · 4–6 → 1–2 pilots · ≤3 → 0 (manage exits). The emailed report
   includes the score. This is the gate on how many of the day's triggers to actually take.
6. **Refresh open positions:** run `python tools/open_positions.py`. It scans every ingested list through
   the backtest engine, collects **triggered signals still live** under the rules (earliest entry per name;
   later re-triggers = adds, not modeled), and rewrites the table between the `OPENPOS` markers in
   `overview.md`. The emailed report includes the same table. Flag names near their stop or 9-EMA trail;
   positions **<+2% after 10 sessions** are auto-flagged **⏳stale** (rotation candidates).
   **Also run `python tools/gated_book.py`** — the disciplined parallel sim (v2.1 layer: point-in-time
   regime-gated order count, Trend-Template-only, ≤+8% extension, 5-session cooldown after a losing stop,
   ≤12 names / 25% group cap / ETFs ×½, pilots ×½ in NEUTRAL). It rewrites the `GATED` block in
   `overview.md`; the report shows it next to the every-signal book — the gap measures the discipline's value. **The gated
   book is the book of record (adopted 2026-07-11, [[drift-review-2026-07-11]]); the every-signal book is a
   benchmark. The watchlist carries a Gated column (✅ = held in the book of record).** The **benchmark is now
   capital-capped** (`open_positions.BENCH_CAP` = `MAX_POSITIONS` = 12 concurrent = max-deployed $1.2M): it takes
   every trigger with no TT/regime gating but **cannot exceed the account's capital** — new triggers are dropped
   when full. So the benchmark↔gated gap now isolates *selection* discipline (both are capital-capped).
7. **Ad-hoc backtest (optional):** `python tools/backtest.py <dates…>` still exists for spot-checks and writes
   `wiki/analysis/backtest-<rundate>.md`, but the **10-day per-list table was removed from the emailed report**
   (2026-07-27) — the **YTD/QTD/MTD strategy-performance block at the top of the report** (step 9b) is the
   performance view we track now.
8. **Email the report:** run `python tools/send_report.py`. It builds `reports/key-list-report-<date>`
   (`.md` + `.html`) — including the regime gate, watchlist (Gated/Ideal columns), the three parallel books
   (gated book of record, paper ideal swing, every-signal benchmark), order plan, open positions, **closed
   positions for the current calendar month** (two tables — closed-with-profit and stop-outs/losses —
   each trade with entry/exit dates+prices, exit kind, and P&L % and $; filtered by exit date, deduped
   single-account view via `open_positions.collect_closed()`), and a closing **P&L
   summary** (realized + unrealized, incl. the month's closed net) — and emails it to `MW_MAIL_TO`
   (optional CC via `MW_MAIL_CC`) via SMTP. **Credentials are user-set env
   vars** (`MW_SMTP_USER`, `MW_SMTP_PASS` — a Gmail/Google **app password**, never the real password;
   never handled by Claude). If they aren't set the script still writes the report files and exits
   with a clear message — that's expected until the user configures them. Do not send email any other
   way (e.g. browser UI) unless the user explicitly asks.
9. **Update the MTD P&L table:** run `python tools/mtd_pnl.py`. It re-simulates all three books
   (gated book of record, paper [[ideal_book]] swing, every-signal benchmark) point-in-time at each
   trading-day close this month and rewrites `wiki/analysis/mtd-pnl-<YYYY-MM>.md` — the running
   month-to-date scoreboard. Re-run daily to extend the table.
9b. **Refresh the YTD/QTD/MTD scoreboard:** run `python tools/period_pnl.py`. It computes each book's
   P&L since inception (**2026-01-01**, `MODEL_START`) at the latest close and at the prior month-/quarter-
   /year-end boundaries, giving **YTD / QTD / MTD** per book, and caches to `tools/.period_pnl_cache.json`
   keyed by the close date (the report reads the cache instantly; recompute only when the date rolls or
   with `--force`). Writes `wiki/analysis/period-pnl-<rundate>.md`; `build_report.py` shows the block at
   the **top of the report** (`period_pnl.report_block[_html]`). Full-year context: [[ytd-review-2026-07-25]].
   **Price cache:** all point-in-time tools (backtest / validate_list / regime) fetch 3-year daily history
   via `tools/pricecache.py`, a shared **daily on-disk cache** (`tools/.price_cache/`, gitignored) — the
   first tool of the day downloads ~440 tickers, the rest read from disk (routine ~8× faster). The 3-year
   window is required so even January entries have a valid 200-day SMA for the Trend Template.
10. **Generate the order plan:** run `python tools/tos_orders.py`. It prints a thinkorswim "1st Triggers
   OCO" bracket per name (buy-stop entry, −3% stop, +7% sell-half, $100k share counts) for the latest
   list. These are tickets for the user to review/place — Claude never places trades. Pair with the
   `tools/keylist_levels.ts` chart study for alerts.

**Month/quarter-end review:** run `python tools/cumulative_pnl.py`. It backtests *every* ingested Key
List and aggregates (per-list + across all triggered signals), writing `wiki/analysis/cumulative-pnl-<rundate>.md`.
Read it as strategy expectancy (lists overlap; it over-commits capital), and note the regime split
(mechanical trading loses in choppy/distribution weeks, gains in confirmed uptrends).

**Trigger validity:** a Key List trigger is only valid on its list's trading day (entry = DAY order,
not GTC); names still valid re-appear on the next list. **No gap-up entries:** buy only at the trigger price (stop-limit at the trigger) — never chase a gap-up
open; but if price **revisits the trigger intraday, the resting DAY limit fills at the trigger**; only
gap-and-go days (low stays above the trigger) go unfilled.
Enforced in `tools/backtest.py` (TRIGGER_DAYS=1, no-gap fills); `tos_orders.py` prints DAY stop-limits.
**Gap-down exits:** a session opening below the stop closes the position immediately at the open — the
protective sell is a STOP-MARKET, never a stop-limit (modeled as `min(open, stop)` in the backtest).

**Trade rules v3, 2026-07-25 — 50-SMA TREND-HOLD + PROFIT-LOCK** (see `wiki/concepts/key-list-trade-rules.md`):
hold the **full** position until a **daily close below the 50-day SMA**, then sell; **disaster stop
−12%**; **profit-lock — once the stock trades +30% above entry, ratchet the stop up to +15%** (protects
big winners without capping upside, no shares sold). No breakeven, no fixed target, no partial —
position/trend-following, not swing. Basis: `structural-exit-test-2026-07-25.md` (3-year OOS test: +$230k
vs +$32k) and `profit-protection-2026-07-25.md` (the +30→+15 lock beat pure hold +$89k/3yr; lower locks,
give-back trails, and partial sales all tested worse). Constants `PROFIT_ARM_PCT`/`PROFIT_LOCK_PCT`. The **entry** rules, the **regime gate**, and the
**heat caps** are unchanged. Watchlist MAs: 9 EMA, 21/50/200 SMA (50-SMA = the exit line). **Sizing
(updated 2026-07-25):** set your own book size via `MW_PORTFOLIO_EQUITY`; a full position =
**`FULL_POSITION_PCT` ≈ 7.14% of equity**; **≤12 names → max deployed ≈ 85.7%**, the rest held as cash.
Risk per full position ≈ **0.86% of equity** at the −12% disaster stop. Exit constants live in
`tools/update_watchlist.py` (`DISASTER_PCT`, `TREND_MA`); legacy `STOP_PCT/BE_PCT/T1_PCT` retained only
for old backtests/labels. Prior swing rule (v2, −5%/BE+7/sell½+12/9-EMA): `stop-target-optimization-2026-07-02.md`.
**Book inception (2026-07-22):** all three books (gated / ideal / benchmark) start **2026-07-01**
(`MODEL_START` in `tools/update_watchlist.py`) — June lists stay for backtests but are excluded from the
live books, so MTD == since-inception with a clean $0 start. The emailed report leads with a
**⚡ Tomorrow's action** block: regime-capped buy shortlist (Trend-Template 8/8, not held/extended/cooldown,
closest to trigger, with brackets) + prioritized exit/trim/trail/add-on lists.

The full operating playbook is `wiki/portfolio-plan.md`.

**Discipline layer v2.1, 2026-07-09** (basis: `wiki/analysis/process-improvements-2026-07-09.md`;
constants also in `update_watchlist.py`): regime-gated order count (7–8 → 5 · 4–6 → 2 pilots ×½ ·
≤3 → 0); Trend-Template 8/8 only; skip triggers >8% above the 21-day SMA (`EXT_MAX_PCT`); ~5-session
cooldown after a losing stop-out (`COOLDOWN_DAYS`, calendar 7); gated book ≤12 names (`MAX_POSITIONS`),
≤25%/group (`GROUP_CAP`), ETFs ×½ (`ETF_FRACTION`, classified via `tools/classify.py` + cache);
open positions <+2% after 10 sessions flagged ⏳stale (`STALE_DAYS`/`STALE_MIN_RET`, flag-only).
`tools/gated_book.py` simulates the disciplined book (GATED block in overview + report section);
the report's Action read and `tos_orders.py` carry the cooldown/extension flags and pilot/ETF sizing.

## Tooling notes
- **`tools/update_watchlist.py`** — recomputes MAs + rule levels for the latest Key List. Requires
  `yfinance` (`pip install --user yfinance`). Run after every ingest. Edit `STOP_PCT`/`T1_PCT` there
  to change the rules (keep `key-list-trade-rules.md` in sync).
- **YouTube ingests:** captions via `yt-dlp` — `python -m yt_dlp --skip-download --write-auto-subs
  --sub-langs en --extractor-args "youtube:player_client=android_vr" <url>`, then strip the VTT.
- **Member-gated pages** (Key List): read via the Claude-for-Chrome extension from the user's
  authenticated session; never handle credentials.
- Obsidian is the IDE; you are the programmer; `MW/wiki/` is the codebase.
- At this scale `index.md` is the navigation system — no embedding/RAG needed. If the wiki grows past
  a few hundred pages, consider a local markdown search tool (e.g. `qmd`) and document it here.
- The vault is a plain folder of markdown — `git init` it for version history when ready.
