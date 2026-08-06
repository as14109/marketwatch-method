---
type: concept
concept_kind: mechanism
tags: [data-quality, tooling, pricecache, backtest]
created: 2026-08-04
updated: 2026-08-04
---

# Data exclusions registry

**Definition:** `tools/excluded_tickers.json` — a tracked registry of Key List tickers whose price
history is permanently unusable (vendor 404 / delisted-symbol response, or a >60% single-bar-jump
that trips `backtest.sim_one`'s corrupted-history guard). Every book (gated, ideal, benchmark)
silently `continue`s past a signal it can't simulate; this registry lets that silent drop be
classified as **known** (already catalogued here) vs **NEW** (uncatalogued — investigate), so a gap
can't go unnoticed the way [[aaoi]]'s benchmark entry briefly did.

## Why it matters
- Before 2026-08-04, `tools/pricecache.py` cached whatever `yf.download()` returned — including an
  empty/failed response — with no validation, and every consumer (`open_positions.py`,
  `gated_book.py`, `ideal_book.py`) dropped a `ret is None` signal with zero logging. A ticker's
  entire contribution to a book's YTD total could vanish for a day (or longer) with no trace.
- The fix (2026-08-04) has two parts: (1) `pricecache.get()` now refuses to cache an empty/invalid
  download, so a transient failure gets retried rather than poisoning the rest of the calendar day;
  (2) all three books now accumulate a `dropped` list of every `(list_date, ticker, reason)` signal
  they couldn't simulate, printed on every run and surfaced in the emailed report's **Data quality**
  line — loudly, if the ticker isn't in this registry yet.

## Current state (as of the 2026-08-04 audit)
16 tickers are currently excluded from all three books. None are believed to represent missing P&L
of the scale AAOI briefly was — a full fresh-cache re-download and trade-by-trade diff against all
three books' existing totals found no other AAOI-class gap (see [[drift-review-2026-07-11]]-style
verification in the 2026-08-04 session log). These are structural, not transient:

**No price data at all** (Yahoo 404, reproducible on repeated calls):
| Ticker | First list | Trigger | Appearances | Note |
| --- | --- | ---: | ---: | --- |
| COMM | 2026-01-05 | 18.40 | 3 | Large active real-world ticker (CommScope) — symbol/exchange mapping suspected |
| TERN | 2026-01-08 | 41.00 | 3 | |
| BK | 2026-01-30 | 121.60 | 3 | Large active real-world ticker (BNY Mellon) — symbol collision suspected |
| ARMN | 2026-02-17 | 20.40 | 1 | |
| X | 2026-04-16 | 54.92 | 1 | Plausibly a real 2025 delisting (US Steel / Nippon Steel acquisition) |

**"Data suspect"** (the >60% single-bar-jump guard trips — possibly an unadjusted split, not
necessarily bad data):
| Ticker | First list | Trigger | Appearances |
| --- | --- | ---: | ---: |
| MXL | 2026-04-13 | 21.10 | **7** — re-appeared often, worth a manual look |
| DAVE | 2026-06-01 | 287.10 | 3 |
| APLD | 2026-01-26 | 39.60 | 3 |
| AGL | 2026-07-14 | 122.00 | 2 |
| AXTI | 2026-01-14 | 22.30 | 2 |
| UMAC | 2026-06-15 | 26.40 | 2 |
| VISN | 2026-02-09 | 19.15 | 2 |
| DEC | 2026-03-23 | 16.60 | 1 |
| FSLY | 2026-04-01 | 29.20 | 1 |
| GME | 2026-03-06 | 24.30 | 1 |
| USAR | 2026-05-29 | 28.70 | 1 |

Dollar impact is **unquantifiable, not zero** — there's no valid price series to simulate these
against, so no fabricated number is given. MXL's 7 recurring appearances make it the most worth a
manual second look (a real, actively-traded ticker with an unusual price series is more likely to
be a split-adjustment glitch than a genuine data void).

## How it connects
- Mechanism: [[key-list-trade-rules]] (the exit engine all three books share, `backtest.sim_one`)
- Entities affected: [[gated_book]], [[ideal_book]], watchlist tickers listed above
- Source trail: the AAOI benchmark-book anomaly (2026-08-04) that triggered this audit and fix.

## Maintenance
Re-run the audit periodically (see the 2026-08-04 session's methodology: snapshot all 3 books,
force a full price-cache refresh, re-snapshot, diff trade-by-trade) if a book's totals move in a way
that isn't explained by known open positions. Add any newly-discovered permanent exclusion to
`tools/excluded_tickers.json` with `reason`, `first_list`, `trigger`, `appearances`, and a `note`.
