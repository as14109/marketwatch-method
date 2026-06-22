#!/usr/bin/env python3
"""
Build the daily Key List report (text + HTML) from the latest Key List + live MAs.

Reuses update_watchlist.py for finding the latest list, parsing entries, and
computing MAs / rule levels. Adds a per-ticker STATUS read against the rules and
writes:
    reports/key-list-report-<date>.md   (markdown/plain text, for the email body)
    reports/key-list-report-<date>.html (simple HTML, for a richer email)

Usage:  python tools/build_report.py
"""
import os, re, sys, datetime as dt
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import update_watchlist as uw

BASE = uw.BASE
REPORTS = os.path.join(BASE, "reports")


def market_overview(raw_path):
    text = open(raw_path, encoding="utf-8").read()
    m = re.search(r"## Market Overview\s*\n(.+?)\n\s*\n", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def status(r):
    """Status is read against the ENTRY pivot. The −3% stop / +7% target only
    apply once a position is triggered (last >= entry); for un-triggered setups
    we just report distance below the pivot."""
    if r.get("last") is None:
        return "no data"
    last, entry, ema9 = r["last"], r["entry"], r["ema9"]
    if last >= entry:  # triggered
        if last >= r["t1"]:
            return "🎯 +7%+ — sell 50%, trail rest"
        if last >= r["be"]:
            return "✅ +5%+ — move stop to breakeven"
        if last < ema9:
            return "✅ triggered, ⚠ below 9 EMA (trail watch)"
        return "✅ triggered (above entry)"
    pct = (last / entry - 1) * 100  # negative
    return f"… setup, {pct:.1f}% vs pivot (not triggered)"


def main():
    list_date, raw_path = uw.latest_key_list()
    tickers = uw.parse_entries(raw_path)
    rows, asof = uw.compute(tickers)
    overview = market_overview(raw_path)

    live = [r for r in rows if r.get("last")]
    triggered = [r["tkr"] for r in live if r["last"] >= r["entry"]]
    at_t1 = [r["tkr"] for r in live if r["last"] >= r["t1"]]
    trail_watch = [r["tkr"] for r in live if r["last"] >= r["entry"] and r["last"] < r["ema9"]]
    # for un-triggered setups, who's closest to the pivot
    near = sorted([r for r in live if r["last"] < r["entry"]],
                  key=lambda r: r["last"] / r["entry"], reverse=True)
    near_txt = ", ".join(f"{r['tkr']} ({(r['last']/r['entry']-1)*100:.1f}%)" for r in near[:5])

    # portfolio equity (optional) for full-position share counts
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = None
    if eq_raw:
        try:
            equity = float(re.sub(r"[,$\s]", "", eq_raw))
        except ValueError:
            equity = None
    at_be = [r["tkr"] for r in live if r["entry"] <= r["last"] < r["t1"] and r["last"] >= r["be"]]

    # ---- markdown / text ----
    md = []
    md.append(f"# Marketwatch — Key List Report ({list_date})")
    md.append(f"_MAs as of close {asof}. Rules: stop −3%, breakeven at +5%, sell 50% at +7%, "
              f"trail rest under 9 EMA. Full position = 10% of portfolio._\n")
    if overview:
        md.append("## Market overview")
        md.append(overview + "\n")
    md.append("## Action read")
    md.append(f"- 🎯 At/over +7% target (sell 50%): {', '.join(at_t1) or 'none'}")
    md.append(f"- ✅ +5%+ (move stop to breakeven): {', '.join(at_be) or 'none'}")
    md.append(f"- ✅ Triggered (above entry pivot): {', '.join(triggered) or 'none'}")
    md.append(f"- ⚠ Triggered but below 9 EMA (trail watch): {', '.join(trail_watch) or 'none'}")
    md.append(f"- … Closest setups to triggering: {near_txt or 'none'}\n")
    md.append("## Watchlist")
    md.append("| Ticker | Entry | Last | 9 EMA | 21 MA | 50 MA | 200 MA | Stop −3% | BE +5% | T1 +7% | Shares (10%) | Status |")
    md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for r in rows:
        if r.get("last") is None:
            md.append(f"| {r['tkr']} | {uw.fmt(r['entry'])} | NO DATA |  |  |  |  | "
                      f"{uw.fmt(r['entry']*0.97)} | {uw.fmt(r['entry']*1.05)} | {uw.fmt(r['entry']*1.07)} | "
                      f"{uw.shares(r['entry'], equity)} | no data |")
            continue
        md.append(f"| {r['tkr']} | {uw.fmt(r['entry'])} | {uw.fmt(r['last'])} | {uw.fmt(r['ema9'])} | "
                  f"{uw.fmt(r['ma21'])} | {uw.fmt(r['ma50'])} | {uw.fmt(r['ma200'])} | "
                  f"{uw.fmt(r['stop'])} | {uw.fmt(r['be'])} | {uw.fmt(r['t1'])} | "
                  f"{uw.shares(r['entry'], equity)} | {status(r)} |")
    md.append("\n_Educational only — not investment advice. Do your own research._")
    md_text = "\n".join(md)

    # ---- html ----
    def cells(vals):
        return "".join(f"<td style='padding:4px 8px;text-align:right'>{v}</td>" for v in vals)
    trs = []
    for r in rows:
        if r.get("last") is None:
            trs.append(f"<tr><td>{r['tkr']}</td>{cells([uw.fmt(r['entry']),'NO DATA','','','','',uw.fmt(r['entry']*0.97),uw.fmt(r['entry']*1.05),uw.fmt(r['entry']*1.07),uw.shares(r['entry'],equity)])}<td>no data</td></tr>")
            continue
        trs.append(f"<tr><td style='padding:4px 8px'><b>{r['tkr']}</b></td>"
                   f"{cells([uw.fmt(r['entry']),uw.fmt(r['last']),uw.fmt(r['ema9']),uw.fmt(r['ma21']),uw.fmt(r['ma50']),uw.fmt(r['ma200']),uw.fmt(r['stop']),uw.fmt(r['be']),uw.fmt(r['t1']),uw.shares(r['entry'],equity)])}"
                   f"<td style='padding:4px 8px'>{status(r)}</td></tr>")
    html = f"""<html><body style="font-family:Arial,sans-serif;font-size:14px">
<h2>Marketwatch — Key List Report ({list_date})</h2>
<p style="color:#555">MAs as of close {asof}. Rules: stop −3%, breakeven at +5%, sell 50% at +7%, trail rest under 9&nbsp;EMA. Full position = 10% of portfolio.</p>
<p>{overview}</p>
<p><b>At/over +7% (sell 50%):</b> {', '.join(at_t1) or 'none'} &nbsp;|&nbsp; <b>+5%+ (breakeven):</b> {', '.join(at_be) or 'none'} &nbsp;|&nbsp; <b>Triggered:</b> {', '.join(triggered) or 'none'}<br>
<b>Triggered but below 9 EMA:</b> {', '.join(trail_watch) or 'none'} &nbsp;|&nbsp; <b>Closest setups:</b> {near_txt or 'none'}</p>
<table style="border-collapse:collapse" border="1">
<tr style="background:#f0f0f0"><th>Ticker</th><th>Entry</th><th>Last</th><th>9 EMA</th><th>21 MA</th><th>50 MA</th><th>200 MA</th><th>Stop −3%</th><th>BE +5%</th><th>T1 +7%</th><th>Shares (10%)</th><th>Status</th></tr>
{''.join(trs)}
</table>
<p style="color:#888;font-size:12px">Educational only — not investment advice. Do your own research.</p>
</body></html>"""

    os.makedirs(REPORTS, exist_ok=True)
    md_path = os.path.join(REPORTS, f"key-list-report-{list_date}.md")
    html_path = os.path.join(REPORTS, f"key-list-report-{list_date}.html")
    open(md_path, "w", encoding="utf-8").write(md_text)
    open(html_path, "w", encoding="utf-8").write(html)
    print(md_text)
    print(f"\n[wrote {md_path}]\n[wrote {html_path}]")
    return md_path, html_path


if __name__ == "__main__":
    main()
