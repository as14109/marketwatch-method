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

STOP_PCT = 0.03   # hard stop below entry
BE_PCT   = 0.05   # at +5% move stop to breakeven
T1_PCT   = 0.07   # first target; sell 50% here, trail the rest on the 9 EMA
FULL_POSITION_PCT = 0.10  # a full position = 10% of the portfolio

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
            asof = df.index[-1].date()
            last = float(c.iloc[-1])
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
    return f"{x:,.2f}" if isinstance(x, (int, float)) else "—"


def shares(entry, equity):
    """Full-position (10% of portfolio) share count, or '—' if equity unknown."""
    if not equity:
        return "—"
    return f"{math.floor(equity * FULL_POSITION_PCT / entry):,}"


def build_table(rows, list_date, asof, equity=None):
    lines = []
    size_note = (f"full position = {int(FULL_POSITION_PCT*100)}% of "
                 f"${equity:,.0f}" if equity else
                 f"full position = {int(FULL_POSITION_PCT*100)}% of portfolio "
                 f"(set MW_PORTFOLIO_EQUITY for share counts)")
    lines.append(f"_Latest list: **{list_date}** · MAs as of close **{asof}** · 9 EMA (exp.), 21/50/200 SMA. "
                 f"Rules ([[key-list-trade-rules]]): stop −{int(STOP_PCT*100)}%, "
                 f"breakeven at +{int(BE_PCT*100)}%, sell 50% at +{int(T1_PCT*100)}%, trail rest under 9 EMA. "
                 f"Sizing: {size_note}._")
    lines.append("")
    lines.append("| Ticker | Entry | Last | 9 EMA | 21 MA | 50 MA | 200 MA | Stop −3% | BE +5% | T1 +7% (sell ½) | Shares (10%) |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in rows:
        if r.get("last") is None:
            lines.append(f"| [[{r['tkr'].lower()}]] | {fmt(r['entry'])} | NO DATA | — | — | — | — | "
                         f"{fmt(r['entry']*(1-STOP_PCT))} | {fmt(r['entry']*(1+BE_PCT))} | "
                         f"{fmt(r['entry']*(1+T1_PCT))} | {shares(r['entry'], equity)} |")
            continue
        lines.append(
            f"| [[{r['tkr'].lower()}]] | {fmt(r['entry'])} | {fmt(r['last'])} | "
            f"{fmt(r['ema9'])} | {fmt(r['ma21'])} | {fmt(r['ma50'])} | {fmt(r['ma200'])} | "
            f"{fmt(r['stop'])} | {fmt(r['be'])} | {fmt(r['t1'])} | {shares(r['entry'], equity)} |")
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
