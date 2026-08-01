#!/usr/bin/env python3
"""
Update the Marketwatch watchlist with moving averages and trade-rule levels.

What it does
------------
1. Finds the LATEST Key List raw file by date  (MW/raw/<YYYY-MM-DD>-key-list.md).
2. Parses each ticker and its Key List entry/setup price.
3. Pulls daily prices via yfinance and computes:
     - 9-day EMA (used for the trailing stop)
     - 21 / 50 / 200-day simple MAs
4. Applies the trade rules off the Key List entry:
     - hard stop  = entry * (1 - STOP_PCT)        (default 3%)
     - target 1   = entry * (1 + T1_PCT)          (default 7%, sell 50% there)
     - trail the remaining 50% under the 9-day EMA
5. Rewrites the table between the WATCHLIST markers in MW/wiki/overview.md
   and writes a dated snapshot to MW/wiki/analysis/watchlist-<date>.md.

Usage:  python tools/update_watchlist.py
Rules defined once here and in wiki/concepts/key-list-trade-rules.md.
"""
import re, sys, glob, os, math, datetime as dt


def env(name, default=None):
    """Read env var; on Windows fall back to the User-scope registry so the
    scheduled routine sees vars set via setx even if the shell didn't inherit them."""
    v = os.environ.get(name)
    if not v and sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                v = winreg.QueryValueEx(k, name)[0]
        except OSError:
            v = None
    return v if v else default

# --- EXIT MODEL v3 — 50-day-SMA TREND-HOLD (adopted 2026-07-25) ---
# Validated across 2024/2025/2026 (all three years beat the old swing exit; +$230k
# vs +$32k over three years): hold the FULL position until a daily CLOSE below the
# 50-day SMA, with a wide disaster stop underneath. No breakeven move, no fixed
# target, no partial. Converts the book from swing to position/trend-following.
# Basis: [[structural-exit-test-2026-07-25]]. The regime ENTRY gate and the 12-name
# cap are unchanged — they are the down-year insurance.
DISASTER_PCT = 0.12   # hard disaster stop below entry (the only hard stop)
TREND_MA     = 50     # exit on a daily close below this SMA (stage-2 trail)
# Profit-lock (added 2026-07-25, validated 2024/2025/2026 vs pure hold: +$89k/3yr):
# once a name trades PROFIT_ARM above entry, ratchet the stop up to PROFIT_LOCK above
# entry — protects accumulated profit on big winners without capping the upside (still
# rides to the 50-SMA). High one-way lock: no shares sold, only fires on ≥+30% winners.
PROFIT_ARM_PCT  = 0.30
PROFIT_LOCK_PCT = 0.15

# Legacy swing constants — retained only for historical backtests/labels that still
# reference them; the live exit engine uses DISASTER_PCT / TREND_MA above.
STOP_PCT = 0.05
BE_PCT   = 0.07
T1_PCT   = 0.12
# A full position as a fraction of equity. ~7.14% => 12 concurrent names ≈ 86% deployed,
# leaving a cash buffer. Set MW_PORTFOLIO_EQUITY to your own book size; this ratio is
# what the sizing, heat caps and share counts are derived from.
FULL_POSITION_PCT = 0.0714

# Discipline layer v2.1 (process-improvements-2026-07-09) — used by the gated
# book simulation and the report/order-plan flags.
COOLDOWN_DAYS  = 7     # calendar days after a losing stop-out before re-entry (~5 sessions)
EXT_MAX_PCT    = 0.08  # skip triggers more than 8% above the 21-day SMA (extended)
PILOT_FRACTION = 0.5   # NEUTRAL regime (score 4-6): enter at half size
STALE_DAYS     = 10    # flag open positions still below STALE_MIN_RET after N sessions
STALE_MIN_RET  = 0.02
MAX_POSITIONS  = 12    # gated book concentration cap (masters' 8-12)
GROUP_CAP      = 0.25  # max fraction of gated-book positions in one sector/group
ETF_FRACTION   = 0.5   # ETFs at half size in the gated book

# Model inception — all three books (gated / ideal / benchmark) start here.
# June lists were the pre-discipline warm-up; the tracked book begins 2026-07-01
# (adopted 2026-07-22). Raw June lists are kept for backtests but excluded from
# the live books, so MTD == since-inception and the P&L has a clean $0 start.
MODEL_START = "2026-01-01"

# Earnings guard (backlog B1): don't initiate a new position if the stock reports
# within this many days; flag held names reporting soon as trim candidates.
EARN_GUARD_DAYS = 7

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(BASE, "MW", "raw")
WIKI = os.path.join(BASE, "MW", "wiki")
START, END = "<!-- WATCHLIST:START -->", "<!-- WATCHLIST:END -->"

ENTRY_RE = re.compile(r"\*\*([A-Z]{1,6})\s+([\d,]+\.\d+)\*\*")
DATE_RE  = re.compile(r"(\d{4}-\d{2}-\d{2})")


def latest_key_list():
    files = glob.glob(os.path.join(RAW, "*key-list*.md"))
    dated = []
    for f in files:
        m = DATE_RE.search(os.path.basename(f))
        if m:
            dated.append((m.group(1), f))
    if not dated:
        sys.exit(f"No dated key-list files found in {RAW}")
    dated.sort()
    return dated[-1]  # (date_str, path)


def parse_entries(path):
    text = open(path, encoding="utf-8").read()
    out = []
    seen = set()
    for m in ENTRY_RE.finditer(text):
        tkr = m.group(1)
        if tkr in seen:
            continue
        seen.add(tkr)
        out.append((tkr, float(m.group(2).replace(",", ""))))
    return out


def compute(tickers):
    import yfinance as yf
    rows, asof = [], None
    for tkr, entry in tickers:
        try:
            df = yf.download(tkr, period="1y", interval="1d",
                             progress=False, auto_adjust=True)
            c = df["Close"].squeeze()
            # Data-sanity guard: auto-adjusted daily closes should never jump >60%
            # in one bar; if they do, the vendor series is corrupted (bad split /
            # adjustment seam) and MAs across it are garbage — blank them.
            if len(c) > 1 and c.pct_change().abs().max() > 0.60:
                print(f"warning: {tkr} price history looks corrupted "
                      f"(>60% one-day jump) — MAs suppressed")
                nan = float("nan")
                asof = df.index[-1].date()
                rows.append(dict(tkr=tkr, entry=entry, last=float(c.iloc[-1]),
                                 ema9=nan, ma21=nan, ma50=nan, ma200=nan,
                                 stop=entry * (1 - STOP_PCT), be=entry * (1 + BE_PCT),
                                 t1=entry * (1 + T1_PCT)))
                continue
            asof = df.index[-1].date()
            last = float(c.iloc[-1])
            # Split check: the Key List entry is a fresh price anchor; if last is
            # wildly far from it, a split/adjustment likely happened — flag loudly.
            if last > 0 and not (0.6 < entry / last < 1.67):
                print(f"warning: {tkr} last ({last:.2f}) is far from the Key List entry "
                      f"({entry:.2f}) — check for a stock split and adjust the raw entry")
            ema9 = float(c.ewm(span=9, adjust=False).mean().iloc[-1])
            ma21 = float(c.rolling(21).mean().iloc[-1])
            ma50 = float(c.rolling(50).mean().iloc[-1])
            ma200 = float(c.rolling(200).mean().iloc[-1])
            rows.append(dict(tkr=tkr, entry=entry, last=last, ema9=ema9,
                             ma21=ma21, ma50=ma50, ma200=ma200,
                             stop=entry * (1 - STOP_PCT), be=entry * (1 + BE_PCT),
                             t1=entry * (1 + T1_PCT)))
        except Exception as e:
            rows.append(dict(tkr=tkr, entry=entry, last=None, err=str(e)[:60]))
    return rows, asof


def fmt(x):
    if isinstance(x, (int, float)):
        return "—" if (isinstance(x, float) and math.isnan(x)) else f"{x:,.2f}"
    return "—"


def shares(entry, equity):
    """Full-position (10% of portfolio) share count, or '—' if equity unknown."""
    if not equity:
        return "—"
    return f"{math.floor(equity * FULL_POSITION_PCT / entry):,}"


def gated_held():
    """Tickers currently held in the gated book of record (empty set on error).
    Lazy import avoids a circular dependency (gated_book imports this module)."""
    try:
        import gated_book
        return gated_book.held_tickers()
    except Exception:
        return set()


def ideal_held():
    """Tickers currently held in the paper 'ideal' swing book (empty set on error)."""
    try:
        import ideal_book
        return ideal_book.held_tickers()
    except Exception:
        return set()


def build_table(rows, list_date, asof, equity=None):
    lines = []
    held = gated_held()
    iheld = ideal_held()
    size_note = (f"full position = {int(FULL_POSITION_PCT*100)}% of "
                 f"${equity:,.0f}" if equity else
                 f"full position = {int(FULL_POSITION_PCT*100)}% of portfolio "
                 f"(set MW_PORTFOLIO_EQUITY for share counts)")
    lines.append(f"_Latest list: **{list_date}** · MAs as of close **{asof}** · 9 EMA (exp.), 21/50/200 SMA. "
                 f"Exit v3 ([[key-list-trade-rules]]): **hold to a daily close below the {TREND_MA}-day SMA**; "
                 f"disaster stop −{int(DISASTER_PCT*100)}%. No target/breakeven — position/trend-hold. "
                 f"Sizing: {size_note}. **Gated** = held in the book of record ([[gated_book]]); "
                 f"**Ideal** = held in the paper swing book ([[ideal_book]])._")
    lines.append("")
    lines.append(f"| Ticker | Gated | Ideal | Entry | Last | 9 EMA | 21 MA | {TREND_MA} SMA ⟵exit | 200 MA | "
                 f"Disaster −{int(DISASTER_PCT*100)}% | Shares ({int(FULL_POSITION_PCT*100)}%) |")
    lines.append("| --- | :-: | :-: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in rows:
        g = "✅" if r["tkr"] in held else ""
        i = "✅" if r["tkr"] in iheld else ""
        if r.get("last") is None:
            lines.append(f"| [[{r['tkr'].lower()}]] | {g} | {i} | {fmt(r['entry'])} | NO DATA | — | — | — | — | "
                         f"{fmt(r['entry']*(1-DISASTER_PCT))} | {shares(r['entry'], equity)} |")
            continue
        lines.append(
            f"| [[{r['tkr'].lower()}]] | {g} | {i} | {fmt(r['entry'])} | {fmt(r['last'])} | "
            f"{fmt(r['ema9'])} | {fmt(r['ma21'])} | {fmt(r['ma50'])} | {fmt(r['ma200'])} | "
            f"{fmt(r['entry']*(1-DISASTER_PCT))} | {shares(r['entry'], equity)} |")
    return "\n".join(lines)


def splice(overview_path, table_md):
    text = open(overview_path, encoding="utf-8").read()
    block = f"{START}\n{table_md}\n{END}"
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), block,
                      text, flags=re.DOTALL)
    else:
        sys.exit("WATCHLIST markers not found in overview.md — add them once first.")
    open(overview_path, "w", encoding="utf-8").write(text)


def main():
    list_date, path = latest_key_list()
    print(f"Latest Key List: {list_date}  ({os.path.basename(path)})")
    tickers = parse_entries(path)
    print(f"Parsed {len(tickers)} tickers")
    rows, asof = compute(tickers)
    eq_raw = env("MW_PORTFOLIO_EQUITY")
    equity = None
    if eq_raw:
        try:
            equity = float(re.sub(r"[,$\s]", "", eq_raw))
        except ValueError:
            print(f"warning: MW_PORTFOLIO_EQUITY='{eq_raw}' not numeric — skipping share counts")
    table = build_table(rows, list_date, asof, equity)

    overview = os.path.join(WIKI, "overview.md")
    splice(overview, table)
    print(f"Updated watchlist in {overview}")

    snap_dir = os.path.join(WIKI, "analysis")
    os.makedirs(snap_dir, exist_ok=True)
    snap = os.path.join(snap_dir, f"watchlist-{list_date}.md")
    with open(snap, "w", encoding="utf-8") as f:
        f.write(f"---\ntype: analysis\ntags: [watchlist, snapshot]\n"
                f"created: {dt.date.today()}\nlist_date: {list_date}\n---\n\n"
                f"# Watchlist snapshot — {list_date}\n\n"
                f"Auto-generated by `tools/update_watchlist.py` from [[{list_date}-key-list]].\n\n"
                + table + "\n")
    print(f"Wrote snapshot {snap}")


if __name__ == "__main__":
    main()
