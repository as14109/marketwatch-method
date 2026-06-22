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

## Daily Key List routine (EOD, weekdays)
Mission Winners publishes a new **Key List** each evening after the close, for the next trading day.
The scheduled task `daily-key-list` (in `~/.claude/scheduled-tasks/`) fires weekday evenings. Each run:
1. **Find the latest list.** Connect the Claude-for-Chrome extension (`list_connected_browsers` →
   `select_browser`), then open the newest Key List. URL pattern:
   `https://missionwinners.com/key-list-<dow>-<mon>-<dd>-<yyyy>/`. If unsure of the exact slug,
   open `https://missionwinners.com/` and follow the newest Key List link. **The page is member-gated**
   — it must be read from the user's authenticated session via `get_page_text`. If no authenticated
   browser is available, **stop and notify** — do not fabricate.
2. **Save raw** to `MW/raw/<YYYY-MM-DD>-key-list.md` (verbatim), where the date is the trading day.
3. **Ingest** per the normal flow: source page, entity pages (with stop/T1), index, log.
4. **Refresh the watchlist:** run `python tools/update_watchlist.py`. It auto-selects the **latest**
   `MW/raw/*key-list*.md` by date, pulls MAs via `yfinance`, applies [[key-list-trade-rules]], and
   rewrites the table between the `WATCHLIST` markers in `overview.md` + writes a dated snapshot to
   `wiki/analysis/watchlist-<date>.md`.
5. **Backtest recent lists:** run `python tools/backtest.py <date>` for the **2–3 most recent prior** Key
   List dates (use `MW/raw/*key-list*.md` filenames). It applies the rules to real prices and reports which
   names triggered and the running P&L (each full position = 10% of equity). Include a one-line
   trigger/P&L summary per list in the report/summary.
6. **Email the report:** run `python tools/send_report.py`. It builds `reports/key-list-report-<date>`
   (`.md` + `.html`) and emails it to `as14109@nyu.edu` via SMTP. **Credentials are user-set env
   vars** (`MW_SMTP_USER`, `MW_SMTP_PASS` — a Gmail/Google **app password**, never the real password;
   never handled by Claude). If they aren't set the script still writes the report files and exits
   with a clear message — that's expected until the user configures them. Do not send email any other
   way (e.g. browser UI) unless the user explicitly asks.

**Trade rules** (see `wiki/concepts/key-list-trade-rules.md`): stop = entry −3%; **at +5% move stop to
breakeven**; at +7% sell 50%; trail the remaining 50% under the 9-day EMA. Watchlist MAs: 9 EMA,
21/50/200 SMA. **Sizing:** a full position = **10% of the portfolio**; `MW_PORTFOLIO_EQUITY` is set to
**1000000** (env var) so the watchlist/report show $100k full-position share counts. The full operating
playbook is `wiki/portfolio-plan.md`.

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
