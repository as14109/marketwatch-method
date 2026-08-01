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
    """Exit v3 (trend-hold): read against the ENTRY pivot and the 50-day SMA
    (the trailing exit). Watchlist names publish the evening before their trading
    day, so most are still un-triggered setups."""
    if r.get("last") is None:
        return "no data"
    last, entry, ma50 = r["last"], r["entry"], r.get("ma50")
    if last >= entry:  # triggered
        if ma50 and last < ma50:
            return f"✅ triggered, ⚠ below {uw.TREND_MA} SMA (exit watch)"
        return "✅ triggered — hold above " + (f"{uw.TREND_MA} SMA" if ma50 else "trend")
    pct = (last / entry - 1) * 100  # negative
    return f"… setup, {pct:.1f}% vs pivot (not triggered)"


def main():
    list_date, raw_path = uw.latest_key_list()
    tickers = uw.parse_entries(raw_path)
    rows, asof = uw.compute(tickers)
    overview = market_overview(raw_path)

    live = [r for r in rows if r.get("last")]
    # for un-triggered setups, who's closest to the pivot
    near = sorted([r for r in live if r["last"] < r["entry"]],
                  key=lambda r: r["last"] / r["entry"], reverse=True)
    near_txt = ", ".join(f"{r['tkr']} ({(r['last']/r['entry']-1)*100:.1f}%)" for r in near[:5])

    # ---- open book, read tonight for tomorrow's actions ----
    # The list publishes the evening BEFORE its trading day, so no watchlist name
    # can be triggered yet — the actionable reads come from the open positions.
    import math
    import open_positions, classify
    try:
        opos = open_positions.collect()
    except Exception:
        opos = []
    openset = {r["tkr"] for r in opos}
    near_stop = [r for r in opos if r["last"] / r["stop_now"] - 1 <= 0.025]
    # trend-exit watch: price within ~2% of the 50-SMA (a close below it exits)
    trail_watch = [r for r in opos if r.get("ma50") and r["last"] <= r["ma50"] * 1.02]
    near_t1 = []   # no fixed profit target under the trend-hold exit
    stale = [r for r in opos if r.get("stale")]
    held_on_list = [r["tkr"] for r in rows if r["tkr"] in openset]
    near_stop_txt = ", ".join(f"{r['tkr']} ({(r['last']/r['stop_now']-1)*100:.1f}% above stop {r['stop_now']:.2f})"
                              for r in near_stop)
    trail_txt = ", ".join(f"{r['tkr']} ({(r['last']/r['ma50']-1)*100:+.1f}% vs {uw.TREND_MA} SMA {r['ma50']:.2f})"
                          for r in trail_watch)
    near_t1_txt = ""
    stale_txt = ", ".join(f"{r['tkr']} ({r['ret']*100:+.1f}% after {r.get('days_held','?')} sessions)"
                          for r in stale)
    held_txt = ", ".join(held_on_list)

    # discipline flags on tomorrow's list (process-improvements-2026-07-09):
    # cooldown = recently stopped out at a loss; extended = trigger far above 21-day MA
    try:
        closed_book = open_positions.collect_closed(opos)
    except Exception:
        closed_book = []
    today = dt.date.today()
    cool = {}
    for r in closed_book:
        if r["ret"] <= 0 and "stop" in (r.get("exit_kind") or "") and r.get("exit_date"):
            xd = dt.date.fromisoformat(r["exit_date"])
            if (today - xd).days <= uw.COOLDOWN_DAYS:
                cool[r["tkr"]] = max(cool.get(r["tkr"], xd), xd)
    cooldown_rows = [r["tkr"] for r in rows if r["tkr"] in cool]
    cooldown_txt = ", ".join(f"{t} (stopped {cool[t]})" for t in cooldown_rows)

    def ext_pct(r):
        ma21 = r.get("ma21")
        if r.get("last") is None or ma21 is None or (isinstance(ma21, float) and math.isnan(ma21)):
            return None
        return r["entry"] / ma21 - 1
    extended_rows = [r for r in rows if (e := ext_pct(r)) is not None and e > uw.EXT_MAX_PCT]
    extended_txt = ", ".join(f"{r['tkr']} (+{ext_pct(r)*100:.1f}% vs 21MA)" for r in extended_rows)
    ext_set = {r["tkr"] for r in extended_rows}

    # earnings guard (B1): days to next report per name; "soon" = within EARN_GUARD_DAYS.
    # Names reporting soon are excluded from new buys and flagged as trim candidates.
    try:
        import earnings as earn_mod
        earn_days = {r["tkr"]: earn_mod.days_to_earnings(r["tkr"])
                     for r in rows if r.get("last") is not None}
    except Exception:
        earn_days = {}
    earn_soon = {t: d for t, d in earn_days.items() if d is not None and 0 <= d <= uw.EARN_GUARD_DAYS}
    earn_soon_txt = ", ".join(f"{t} ({d}d)" for t, d in sorted(earn_soon.items(), key=lambda x: x[1]))

    # portfolio equity (optional) for full-position share counts
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = None
    if eq_raw:
        try:
            equity = float(re.sub(r"[,$\s]", "", eq_raw))
        except ValueError:
            equity = None

    # ---- markdown / text ----
    md = []
    md.append(f"# Marketwatch — Key List Report ({list_date})")
    S, B, T = int(uw.STOP_PCT*100), int(uw.BE_PCT*100), int(uw.T1_PCT*100)
    F = int(uw.FULL_POSITION_PCT*100)
    D, M = int(uw.DISASTER_PCT*100), uw.TREND_MA   # exit v3: disaster stop %, trend SMA
    sm, bm, tm = 1-uw.STOP_PCT, 1+uw.BE_PCT, 1+uw.T1_PCT
    dm = 1 - uw.DISASTER_PCT
    md.append(f"_MAs as of close {asof}. Exit v3 (trend-hold): **hold to a daily close below the {M}-day SMA**; "
              f"disaster stop −{D}%. No target/breakeven. Full position = {F}% of portfolio._\n")
    # Period P&L (YTD/QTD/MTD, all three books) — cached; see tools/period_pnl.py
    period_md = period_html = ""
    try:
        import period_pnl
        period_md = period_pnl.report_block(equity=equity)
        period_html = period_pnl.report_block_html(equity=equity)
        md.append(period_md + "\n")
    except Exception as e:
        md.append(f"_Period P&L unavailable: {str(e)[:80]}_\n")
    try:
        import regime
        rscore, rverdict, rallowed, _rchecks = regime.compute()
    except Exception:
        rscore, rverdict, rallowed = "?", "unavailable", "?"
    pilot_mode = isinstance(rscore, int) and 4 <= rscore <= 6

    # three parallel books — computed once, reused throughout.
    import gated_book, ideal_book
    try:
        gpos, gclosed, _gskip, gdaily = gated_book.simulate()
    except Exception:
        gpos, gclosed, gdaily = [], [], []
    ghold = {p["tkr"] for p in gpos}
    try:
        ipos, iclosed, _iskip, idaily = ideal_book.simulate()
    except Exception:
        ipos, iclosed, idaily = [], [], []
    ihold = {p["tkr"] for p in ipos}

    # ---- shared helpers: sizing, brackets, per-book buy shortlist + manage lines ----
    try:
        import validate_list as vl
        spy = vl.series("SPY")
    except Exception:
        spy, vl = None, None

    def qty_for(entry, tkr):
        if not equity:
            return None
        w = uw.FULL_POSITION_PCT
        if pilot_mode: w *= uw.PILOT_FRACTION
        if classify.group(tkr)[1]: w *= uw.ETF_FRACTION
        return int(equity * w / entry)

    def bracket(r):
        q = qty_for(r["entry"], r["tkr"])
        dm = 1 - uw.DISASTER_PCT
        return (f"**{r['tkr']}** buy-stop {uw.fmt(r['entry'])} · disaster stop {uw.fmt(r['entry']*dm)} · "
                f"then hold to a close < {uw.TREND_MA} SMA" + (f" · {q} sh" if q else "")
                + (f" ({(r['last']/r['entry']-1)*100:+.1f}% to trigger)"))

    def cooldowns(closed):
        """Names that stopped out at a loss within COOLDOWN_DAYS (this book's own history)."""
        out = {}
        for r in closed:
            if r["ret"] <= 0 and "stop" in (r.get("exit_kind") or "") and r.get("exit_date"):
                xd = dt.date.fromisoformat(r["exit_date"])
                if (today - xd).days <= uw.COOLDOWN_DAYS:
                    out[r["tkr"]] = xd
        return out

    def buy_shortlist(held, ext_max, n, stocks_only, cool_set):
        """New-buy candidates: on the list, TT 8/8, not held in THIS book, not extended
        past ext_max vs the 21-MA, not on THIS book's cooldown. Closest-to-trigger first."""
        if not n or spy is None:
            return []
        out = []
        for r in rows:
            t = r["tkr"]
            if t in held or t in cool_set or t in earn_soon or r.get("last") is None:
                continue   # earn_soon: don't initiate a new position into earnings (B1)
            if stocks_only and classify.group(t)[1]:
                continue
            ma21 = r.get("ma21")
            if ma21 and not (isinstance(ma21, float) and math.isnan(ma21)) and (r["entry"]/ma21 - 1) > ext_max:
                continue
            try:
                passed, _ = vl.check(t, spy)
            except Exception:
                passed = None
            if passed == 8:
                out.append(r)
        out.sort(key=lambda r: r["last"] / r["entry"], reverse=True)
        return out[:n]

    def manage_lines(positions):
        """Exit / trend-trail / stale strings for a book's OWN open positions (v3)."""
        ns = [p for p in positions if p.get("stop_now") and p["last"]/p["stop_now"]-1 <= 0.025]
        tr = [p for p in positions if p.get("ma50") and p["last"] <= p["ma50"]*1.02]   # near 50-SMA exit
        st = [p for p in positions if p.get("days_held", 0) >= uw.STALE_DAYS and p["ret"] < uw.STALE_MIN_RET]
        return (", ".join(f"{p['tkr']} ({(p['last']/p['stop_now']-1)*100:.1f}% above stop {p['stop_now']:.2f})" for p in ns),
                "",
                ", ".join(f"{p['tkr']} ({(p['last']/p['ma50']-1)*100:+.1f}% vs {uw.TREND_MA}SMA)" for p in tr),
                ", ".join(f"{p['tkr']} ({p['ret']*100:+.1f}% after {p.get('days_held','?')}d)" for p in st))

    def action_md(title, n, pilot, buys, positions, held, note="", ready=None):
        ns_t, nt_t, tr_t, st_t = manage_lines(positions)
        out = [f"## {title} — regime {rscore}/8, up to {n} new "
               + ("pilot " if pilot else "") + "entr" + ("y" if n == 1 else "ies") + note]
        if n == 0:
            out.append("- 🚫 **No new buys** — regime gate closed (distribution/risk-off). Manage the open book only.")
            if ready:
                out.append(f"- 🟦 **Ready when the gate reopens** (top TT 8/8, nearest trigger — staged, "
                           f"blocked by regime today):")
                out += [f"   - {bracket(r)}" for r in ready]
        elif buys:
            out.append(f"- 🟢 **Buy (DAY stop-limit, up to {n}" + (", pilot ×½ size" if pilot else "") + "):**")
            out += [f"   - {bracket(r)}" for r in buys]
        else:
            out.append(f"- 🟢 **{n} new buy(s) allowed but none cleared the filters** (TT 8/8, not held/extended/cooldown). Watch the list.")
        out.append(f"- 🔴 **Exit / act:** near disaster stop → {ns_t or 'none'}" + (f" · ⏳ stale (rotate) → {st_t}" if st_t else ""))
        out.append(f"- 🟡 **Trend-exit watch:** near {uw.TREND_MA}-SMA (close below = exit) → {tr_t or 'none'}")
        out.append(f"- ➕ **Add-ons** (on the list & already held): {', '.join(r['tkr'] for r in rows if r['tkr'] in held) or 'none'}\n")
        return out

    def action_html_box(title, colour, n, pilot, buys, positions, held, note="", ready=None):
        ns_t, nt_t, tr_t, st_t = manage_lines(positions)
        if n == 0:
            buy_h = "🚫 <b>No new buys</b> — regime gate closed. Manage the open book only."
            if ready:
                buy_h += ("<br>🟦 <b>Ready when the gate reopens</b> (top TT 8/8, nearest trigger — staged):"
                          "<ul style='margin:4px 0'>" + "".join(f"<li>{bracket(r).replace('**','')}</li>" for r in ready) + "</ul>")
        elif buys:
            buy_h = (f"🟢 <b>Buy (up to {n}" + (", pilot &times;&frac12;" if pilot else "") + "):</b>"
                     "<ul style='margin:4px 0'>" + "".join(f"<li>{bracket(r).replace('**','')}</li>" for r in buys) + "</ul>")
        else:
            buy_h = f"🟢 <b>{n} buy(s) allowed but none cleared the filters.</b> Watch the list."
        return (f"<div style='border:2px solid {colour}; background:#f7fbff; padding:10px 14px; border-radius:6px; margin-bottom:8px'>"
                f"<h3 style='margin:0 0 6px'>{title} — regime {rscore}/8, up to {n} new "
                + ("pilot " if pilot else "") + f"entries{note}</h3>"
                f"<p style='margin:4px 0'>{buy_h}</p>"
                f"<p style='margin:4px 0'>🔴 <b>Exit / act:</b> near disaster stop &rarr; {ns_t or 'none'}"
                + (f" &middot; ⏳ stale &rarr; {st_t}" if st_t else "") + "</p>"
                f"<p style='margin:4px 0'>🟡 <b>Trend-exit watch:</b> near {uw.TREND_MA}-SMA (close below = exit) &rarr; {tr_t or 'none'}</p>"
                f"<p style='margin:4px 0'>➕ <b>Add-ons:</b> {', '.join(r['tkr'] for r in rows if r['tkr'] in held) or 'none'}</p></div>")

    # ---- ⚡ TOMORROW'S ACTION — book of record (gated), then the ideal-book alternative ----
    gcool = cooldowns(gclosed)
    icool = cooldowns(iclosed)
    n_gated = 5 if (isinstance(rscore, int) and rscore >= 7) else (2 if pilot_mode else 0)
    n_ideal = 4 if (isinstance(rscore, int) and rscore >= 7) else (2 if pilot_mode else 0)
    gated_buys = buy_shortlist(ghold, uw.EXT_MAX_PCT, n_gated, stocks_only=False, cool_set=gcool)
    ideal_buys = buy_shortlist(ihold, ideal_book.IDEAL_EXT_MAX, n_ideal, stocks_only=True, cool_set=icool)
    # "Ready when the gate reopens": staged shortlist shown even at 0 allowed entries
    gated_ready = buy_shortlist(ghold, uw.EXT_MAX_PCT, 5, stocks_only=False, cool_set=gcool) if n_gated == 0 else None
    ideal_ready = buy_shortlist(ihold, ideal_book.IDEAL_EXT_MAX, 4, stocks_only=True, cool_set=icool) if n_ideal == 0 else None

    md += action_md("⚡ Tomorrow's action — 📘 Book of record (gated)", n_gated, pilot_mode,
                    gated_buys, gpos, ghold, ready=gated_ready)
    md += action_md("🧪 Alternative — if you follow the Ideal book (paper v3)", n_ideal, pilot_mode,
                    ideal_buys, ipos, ihold, note=" · stocks-only, ≤5% ext, ≤8 names", ready=ideal_ready)
    md.append(f"> ⚠ **Earnings within {uw.EARN_GUARD_DAYS}d** (excluded from new buys; trim/‑½ held names before the report): "
              f"{earn_soon_txt or 'none'}\n")

    action_html = (action_html_box("⚡ Tomorrow's action — 📘 Book of record (gated)", "#2a7",
                                   n_gated, pilot_mode, gated_buys, gpos, ghold, ready=gated_ready)
                   + action_html_box("🧪 Alternative — Ideal book (paper v3)", "#69c",
                                     n_ideal, pilot_mode, ideal_buys, ipos, ihold,
                                     note=" · stocks-only", ready=ideal_ready)
                   + f"<p style='margin:4px 0'>⚠ <b>Earnings within {uw.EARN_GUARD_DAYS}d</b> "
                     f"(excluded from new buys; trim/&minus;&frac12; held names before the report): "
                     f"<b>{earn_soon_txt or 'none'}</b></p>")

    if overview:
        md.append("## Market overview")
        md.append(overview + "\n")
    md.append("## Watchlist")
    md.append(f"| Ticker | Gated | Ideal | Entry | Last | 9 EMA | 21 MA | {M} SMA ⟵exit | 200 MA | Disaster −{D}% | Shares ({F}%) | Status |")
    md.append("| --- | :-: | :-: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for r in rows:
        g = "✅" if r["tkr"] in ghold else ""
        i = "✅" if r["tkr"] in ihold else ""
        if r.get("last") is None:
            md.append(f"| {r['tkr']} | {g} | {i} | {uw.fmt(r['entry'])} | NO DATA |  |  |  |  | "
                      f"{uw.fmt(r['entry']*dm)} | {uw.shares(r['entry'], equity)} | no data |")
            continue
        md.append(f"| {r['tkr']} | {g} | {i} | {uw.fmt(r['entry'])} | {uw.fmt(r['last'])} | {uw.fmt(r['ema9'])} | "
                  f"{uw.fmt(r['ma21'])} | {uw.fmt(r['ma50'])} | {uw.fmt(r['ma200'])} | "
                  f"{uw.fmt(r['entry']*dm)} | {uw.shares(r['entry'], equity)} | {status(r)} |")
    # ---- order plan (thinkorswim brackets) ----
    # Sizing per process-improvements-2026-07-09: pilots ×PILOT_FRACTION in a
    # NEUTRAL regime, ETFs ×ETF_FRACTION; cooldown/extended names flagged.
    def qty_half(entry, tkr):
        if not equity: return None, None
        w = uw.FULL_POSITION_PCT
        if pilot_mode: w *= uw.PILOT_FRACTION
        if classify.group(tkr)[1]: w *= uw.ETF_FRACTION
        q = int(equity * w / entry); return q, q // 2
    def order_flags(tkr):
        f = []
        if tkr in cool: f.append("🧊 cooldown")
        if tkr in ext_set: f.append("📏 extended")
        if classify.group(tkr)[1]: f.append(f"ETF ×{uw.ETF_FRACTION}")
        return ", ".join(f)
    # size label per order, driven by the regime (pilot vs full) and ETF status
    def size_label(tkr):
        if not (isinstance(rscore, int) and rscore >= 4):
            return "🚫 gate closed"          # distribution ≤3 → no new buys today
        is_etf = classify.group(tkr)[1]
        base = "🟡 PILOT ½" if pilot_mode else "🟢 FULL"
        return base + (" · ETF ½" if is_etf else "")
    regime_size = ("PILOT (½ size)" if pilot_mode else "FULL size") if (isinstance(rscore, int) and rscore >= 4) \
                  else "— (regime gate closed: no new buys)"
    md.append("\n## Order plan — thinkorswim (buy-stop + disaster stop)")
    md.append(f"_Tickets to review and place yourself — not advice. Buy-STOP entry with a protective "
              f"STOP −{D}% (disaster). No profit target — **hold to a daily close below the {M}-day SMA**._ "
              f"**Regime {rscore}/8 → new buys are {regime_size}.** "
              + ("_Uptrend (7–8): FULL. NEUTRAL (4–6): PILOT ½, add the rest on confirmation. "
                 "Distribution (≤3): no new buys._"))
    md.append(f"| Ticker | Buy STOP | Size | Qty | Disaster STOP −{D}% | Exit rule | Flags |")
    md.append("| --- | ---: | :-- | ---: | ---: | --- | --- |")
    for r in rows:
        q, h = qty_half(r["entry"], r["tkr"])
        md.append(f"| {r['tkr']} | {uw.fmt(r['entry'])} | {size_label(r['tkr'])} | {q if q is not None else '—'} | "
                  f"{uw.fmt(r['entry']*dm)} | close < {M} SMA | {order_flags(r['tkr'])} |")

    # ---- Add-on plan: scale healthy pilots toward full when the regime confirms ----
    #  Advisory only (NOT in the book P&L until the pyramid add-on is validated):
    #  a pilot that is working (open, above its 50-SMA, in profit) should be topped up
    #  to full in a confirmed uptrend — otherwise winners stay under-sized.
    md.append(f"\n## Add-on plan — scale pilots toward full (advisory)")
    addons = []
    if isinstance(rscore, int) and rscore >= 7:
        for p in gpos:
            if p.get("etf"):                     # an ETF's "full" is already ½ by design — no top-up
                continue
            w = p.get("weight", uw.FULL_POSITION_PCT)
            if w >= uw.FULL_POSITION_PCT * 0.99:  # already full-size
                continue
            healthy = (p["status"].startswith("OPEN") and p.get("ma50") and p.get("last")
                       and p["last"] > p["ma50"] and p["ret"] > 0)
            if not healthy:
                continue
            gap = uw.FULL_POSITION_PCT - w
            add_sh = int(gap * equity / p["last"]) if (equity and p.get("last")) else None
            addons.append((p, w, gap, add_sh))
    if addons:
        md.append(f"_Regime {rscore}/8 confirms — top up these working pilots to full ({int(uw.FULL_POSITION_PCT*100)}% "
                  f"/ ${equity*uw.FULL_POSITION_PCT:,.0f}). Add on strength (buy-stop above a recent high or add on a "
                  f"strong session); the disaster stop / 50-SMA exit then apply to the whole position._")
        md.append("| Ticker | Now | → Target | Add shares | Add $ | Ret % | vs 50-SMA |")
        md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for p, w, gap, add_sh in sorted(addons, key=lambda x: -x[0]["ret"]):
            vs = f"+{(p['last']/p['ma50']-1)*100:.1f}%" if p.get("ma50") else "—"
            md.append(f"| {p['tkr']} | {w*100:.2f}% | {uw.FULL_POSITION_PCT*100:.2f}% | "
                      f"{add_sh if add_sh is not None else '—'} | ${gap*equity:,.0f} | {p['ret']*100:+.1f}% | {vs} |")
    elif isinstance(rscore, int) and rscore >= 7:
        md.append(f"_Regime {rscore}/8 confirms, but no held pilot currently qualifies (needs open, above its "
                  f"50-SMA, and in profit)._")
    else:
        md.append(f"_No add-ons — regime {rscore}/8 is not a confirmed uptrend (≥7). Pilots are topped up to full "
                  f"only when the market confirms; hold them at pilot size for now._")
    # ---- shared open-position table renderer — SAME columns for all 3 books ----
    defw = uw.FULL_POSITION_PCT
    def _lock_txt(p):
        return (f"🔒 +{int(uw.PROFIT_LOCK_PCT*100)}% @{p['lock_px']:.2f}" if p.get("locked")
                else f"arm {p.get('arm_px', p['fill']*(1+uw.PROFIT_ARM_PCT)):.2f} → +{int(uw.PROFIT_LOCK_PCT*100)}% {p.get('lock_px', p['fill']*(1+uw.PROFIT_LOCK_PCT)):.2f}")
    def book_md(positions):
        if not positions:
            return ["_no open positions_"]
        L = [f"| Ticker | From list | Size | Fill | {M}-SMA exit | Disaster −{D}% | "
             f"Lock +{int(uw.PROFIT_LOCK_PCT*100)}% (arm +{int(uw.PROFIT_ARM_PCT*100)}%) | Status | Ret % | Equity % |",
             "| --- | --- | ---: | ---: | ---: | ---: | :-- | --- | ---: | ---: |"]
        for p in sorted(positions, key=lambda x: -x["ret"]):
            w = p.get("weight", defw)
            size = f"{w*100:.2f}%" + (" pilot" if p.get("pilot") else "")
            ma50 = f"{p['ma50']:.2f}" if p.get("ma50") else "—"
            L.append(f"| {p['tkr']} | {p['list_date']} | {size} | {p['fill']:.2f} | {ma50} | {p['stop_now']:.2f} | "
                     f"{_lock_txt(p)} | {p['status']}{' ⏳stale' if p.get('stale') else ''} | "
                     f"{p['ret']*100:+.2f}% | {p['ret']*w*100:+.2f}% |")
        return L
    def book_html_tbl(positions):
        if not positions:
            return "<p><i>no open positions</i></p>"
        head = (f"<tr style='background:#f0f0f0'><th>Ticker</th><th>From list</th><th>Size</th><th>Fill</th>"
                f"<th>{M}-SMA exit</th><th>Disaster &minus;{D}%</th>"
                f"<th>Lock +{int(uw.PROFIT_LOCK_PCT*100)}% (arm +{int(uw.PROFIT_ARM_PCT*100)}%)</th>"
                f"<th>Status</th><th>Ret %</th><th>Equity %</th></tr>")
        rws = ""
        for p in sorted(positions, key=lambda x: -x["ret"]):
            w = p.get("weight", defw)
            size = f"{w*100:.2f}%" + (" pilot" if p.get("pilot") else "")
            ma50 = f"{p['ma50']:.2f}" if p.get("ma50") else "—"
            rws += (f"<tr><td style='padding:3px 8px'><b>{p['tkr']}</b></td><td style='padding:3px 8px'>{p['list_date']}</td>"
                    f"<td style='padding:3px 8px;text-align:right'>{size}</td><td style='padding:3px 8px;text-align:right'>{p['fill']:.2f}</td>"
                    f"<td style='padding:3px 8px;text-align:right'>{ma50}</td><td style='padding:3px 8px;text-align:right'>{p['stop_now']:.2f}</td>"
                    f"<td style='padding:3px 8px'>{_lock_txt(p)}</td>"
                    f"<td style='padding:3px 8px'>{p['status']}{' ⏳stale' if p.get('stale') else ''}</td>"
                    f"<td style='padding:3px 8px;text-align:right'>{p['ret']*100:+.1f}%</td>"
                    f"<td style='padding:3px 8px;text-align:right'>{p['ret']*w*100:+.2f}%</td></tr>")
        return f"<table style='border-collapse:collapse;font-size:13px' border='1'>{head}{rws}</table>"

    def capital_line(positions, max_names):
        """Capital deployed vs available for a book, in $ and % of equity. 'Available'
        = room to the book's max-deployed cap (max_names × full), i.e. empty slots
        PLUS pilot top-ups (a pilot could be scaled to full)."""
        dep = sum(p.get("weight", defw) for p in positions)     # fraction of equity deployed now
        n = len(positions); free = max(0, max_names - n)
        max_dep = max_names * defw                              # the book's max-deployed cap
        avail = max(0.0, max_dep - dep)                         # room to that cap
        if not equity:
            return f"{n}/{max_names} positions · {dep*100:.1f}% of equity deployed · {free} slot(s) free"
        topups = avail > free * defw + 1e-9                     # under-full pilots exist
        note = f"{free} free slot(s)" + (" + pilot top-ups" if topups else "")
        return (f"💰 **Deployed ${dep*equity:,.0f}** ({dep*100:.1f}% of ${equity:,.0f}) across **{n}/{max_names}** names "
                f"· **~${avail*equity:,.0f} still investable** to the {max_dep*100:.0f}% cap ({note})")
    def capital_html(positions, max_names):
        return capital_line(positions, max_names).replace("**", "").replace("💰 ", "💰 ")

    # Size legend (why some positions are 3.57% / 1.79%): full=7.14% ($100k); a NEUTRAL-regime
    # entry pilots at half (×0.5) and an ETF is half too, so pilot=3.57%, ETF-pilot=1.79% (¼).
    size_legend = (f"_Size: **{defw*100:.2f}%** = full (${equity*defw:,.0f}); "
                   f"**{defw*uw.PILOT_FRACTION*100:.2f}%** = pilot (NEUTRAL regime, ½ size) *or* ETF (½); "
                   f"**{defw*uw.PILOT_FRACTION*uw.ETF_FRACTION*100:.2f}%** = ETF pilot (¼). "
                   f"Pilots are deliberate half-size starts; **adding the rest on confirmation is not yet "
                   f"modeled**, so a pilot stays pilot-sized (it was not trimmed)._" if equity else "")

    # ---- BOOK OF RECORD: the gated (disciplined) book ----
    gport = sum(p["ret"] * p["weight"] for p in gpos + gclosed)
    greal = sum(p["ret"] * p["weight"] for p in gclosed)
    gunreal = sum(p["ret"] * p["weight"] for p in gpos)
    gdollar = f" ≈ ${gport*equity:+,.0f}" if equity else ""
    gsum = (f"{len(gpos)} open + {len(gclosed)} closed · realized {greal*100:+.2f}% eq · "
            f"unrealized {gunreal*100:+.2f}% eq · total {gport*100:+.2f}% of equity{gdollar}")
    gcap = capital_line(gpos, uw.MAX_POSITIONS)
    md.append("\n## Book of record — gated (disciplined) book")
    md.append(f"_The book we actually trade: regime-gated order count, Trend-Template only, "
              f"≤+{int(uw.EXT_MAX_PCT*100)}% extension, {uw.COOLDOWN_DAYS}d cooldown, ≤{uw.MAX_POSITIONS} names, "
              f"{int(uw.GROUP_CAP*100)}% group cap, pilots ×{uw.PILOT_FRACTION} in NEUTRAL, ETFs ×{uw.ETF_FRACTION}._")
    md.append(size_legend)
    md.append(gcap)
    md += book_md(gpos)
    md.append(f"\n**Book of record: {gsum}**")
    gated_html = (f"<h3>Book of record — gated (disciplined) book</h3>"
                  f"<p>{capital_html(gpos, uw.MAX_POSITIONS)}</p>"
                  f"<p style='color:#555;font-size:12px'>{size_legend.strip('_')}</p>"
                  f"<p><b>{gsum}</b></p>" + book_html_tbl(gpos))

    # ---- IDEAL: the leader-pullback swing paper book (v3 candidate) ----
    iport = sum(p["ret"] * p["weight"] for p in ipos + iclosed)
    ireal = sum(p["ret"] * p["weight"] for p in iclosed)
    iunreal = sum(p["ret"] * p["weight"] for p in ipos)
    idollar = f" ≈ ${iport*equity:+,.0f}" if equity else ""
    isum = (f"{len(ipos)} open + {len(iclosed)} closed · realized {ireal*100:+.2f}% eq · "
            f"unrealized {iunreal*100:+.2f}% eq · total {iport*100:+.2f}% of equity{idollar}")
    md.append("\n## Ideal book — leader-pullback swing (paper v3 candidate)")
    md.append(f"_Stocks only, trigger ≤{int(ideal_book.IDEAL_EXT_MAX*100)}% above the 21-SMA (near support), "
              f"≤{ideal_book.IDEAL_MAX_POS} names, orders 4/2/0 by regime. **In-sample / paper — not the book "
              f"of record** ([[ideal-swing-model-2026-07-15]]); shown for comparison._")
    md.append(capital_line(ipos, ideal_book.IDEAL_MAX_POS))
    md += book_md(ipos)
    md.append(f"\n**Ideal book: {isum}**")
    ideal_html = (f"<h3>Ideal book — leader-pullback swing (paper v3)</h3>"
                  f"<p><i>Stocks only, near-support entries, ≤{ideal_book.IDEAL_MAX_POS} names. In-sample paper — "
                  f"not the book of record.</i><br>{capital_html(ipos, ideal_book.IDEAL_MAX_POS)}<br><b>{isum}</b></p>"
                  + book_html_tbl(ipos))

    # ---- BENCHMARK: the every-signal book, capital-capped ----
    esig_open = sum(r["ret"] * uw.FULL_POSITION_PCT for r in opos)
    esig_closed = sum(r["ret"] * uw.FULL_POSITION_PCT for r in closed_book)
    bench_total = esig_open + esig_closed
    bdollar = f" ≈ ${bench_total*equity:+,.0f}" if equity else ""
    bsum = (f"{len(opos)} open ({esig_open*100:+.2f}% eq) + closed since inception {esig_closed*100:+.2f}% eq "
            f"= {bench_total*100:+.2f}% of equity{bdollar} — vs book of record {gport*100:+.2f}% eq")
    md.append(f"\n## Benchmark — every-signal book (no selection discipline, capital-capped ≤{open_positions.BENCH_CAP})")
    md.append(f"_Reference — takes every triggered signal (earliest entry per name) with NO Trend-Template / "
              f"regime gating, but still respects the capital rule: **≤{open_positions.BENCH_CAP} concurrent "
              f"positions** (max deployed), first-come; new triggers are dropped when full. The gap vs the "
              f"book of record isolates what the **selection discipline** is worth (both books are capital-capped)._")
    md.append(capital_line(opos, open_positions.BENCH_CAP))
    md += book_md(opos)
    md.append(f"\n**Benchmark: {bsum}**")
    bench_html = (f"<h3>Benchmark — every-signal book (no selection discipline, capital-capped ≤{open_positions.BENCH_CAP})</h3>"
                  f"<p><i>Every trigger, no TT/regime gating, ≤{open_positions.BENCH_CAP} concurrent (capital cap). "
                  f"The gap vs the book of record is the selection discipline's value.</i><br>{capital_html(opos, open_positions.BENCH_CAP)}<br><b>{bsum}</b></p>"
                  + book_html_tbl(opos))

    # ---- closed positions this month (winners vs stop-outs) ----
    full_pos = equity * uw.FULL_POSITION_PCT if equity else None
    month = dt.date.today().strftime("%Y-%m")
    try:
        closed_all = open_positions.collect_closed(opos)
    except Exception:
        closed_all = []
    closed_all = [r for r in closed_all if (r.get("exit_date") or "").startswith(month)]
    c_win = sorted([r for r in closed_all if r["ret"] > 0], key=lambda r: -r["ret"])
    c_loss = sorted([r for r in closed_all if r["ret"] <= 0], key=lambda r: r["ret"])

    def closed_row(r):
        d = f" | {r['ret']*full_pos:+,.0f}" if full_pos else ""
        px = f"{r['exit_px']:.2f}" if r.get("exit_px") else "—"
        return (f"| {r['tkr']} | {r['list_date']} | {r['entry_date']} | {r['fill']:.2f} | "
                f"{r.get('exit_date','—')} | {px} | {r.get('exit_kind','—')} | {r['ret']*100:+.2f}%{d} |")

    dollar_hdr = " $ P&L |" if full_pos else ""
    dollar_sep = " ---: |" if full_pos else ""
    md.append(f"\n## Closed positions — this month ({month})")
    md.append("_Trades exited this calendar month. Single-account view (one position per name at a "
              "time; adds not modeled). Net P&L per trade — full position exited on a close below the "
              f"{M}-day SMA or the −{D}% disaster stop._")
    md.append(f"\n### ✅ Closed with profit ({len(c_win)})")
    md.append(f"| Ticker | From list | Entered | Fill | Exited | Exit px | How | P&L % |{dollar_hdr}")
    md.append(f"| --- | --- | --- | ---: | --- | ---: | --- | ---: |{dollar_sep}")
    for r in c_win:
        md.append(closed_row(r))
    if not c_win:
        md.append("| _none yet_ | | | | | | | |" + (" |" if full_pos else ""))
    wr = sum(r["ret"] for r in c_win)
    md.append(f"\n**Subtotal: {wr*100:+.2f}% cum"
              + (f" · ${wr*full_pos:+,.0f}" if full_pos else "") + "**")
    md.append(f"\n### ❌ Closed with loss / stop-outs ({len(c_loss)})")
    md.append(f"| Ticker | From list | Entered | Fill | Exited | Exit px | How | P&L % |{dollar_hdr}")
    md.append(f"| --- | --- | --- | ---: | --- | ---: | --- | ---: |{dollar_sep}")
    for r in c_loss:
        md.append(closed_row(r))
    if not c_loss:
        md.append("| _none yet_ | | | | | | | |" + (" |" if full_pos else ""))
    lr_ = sum(r["ret"] for r in c_loss)
    md.append(f"\n**Subtotal: {lr_*100:+.2f}% cum"
              + (f" · ${lr_*full_pos:+,.0f}" if full_pos else "") + "**")
    n_closed = len(closed_all)
    net_closed = wr + lr_
    if n_closed:
        md.append(f"\n**Closed this month: {n_closed} trades · win rate {len(c_win)}/{n_closed} = "
                  f"{100*len(c_win)/n_closed:.0f}% · net realized "
                  + (f"${net_closed*full_pos:+,.0f}" if full_pos else f"{net_closed*100:+.2f}% cum") + "**")

    # (10-day per-list backtest removed 2026-07-27 — the YTD/QTD/MTD block at the top
    #  of the report is the strategy-performance view we track now.)

    # (P&L summary section removed 2026-07-27 — the YTD/QTD/MTD block at the TOP of
    #  the report is the single performance view; each book section carries its own
    #  since-inception total, so a duplicate summary at the bottom was redundant.)
    md.append("\n_Educational only — not investment advice. Do your own research._")
    md_text = "\n".join(md)

    # ---- html ----
    def cells(vals):
        return "".join(f"<td style='padding:4px 8px;text-align:right'>{v}</td>" for v in vals)
    trs = []
    for r in rows:
        gcell = "<td style='padding:4px 8px;text-align:center'>" + ("&#9989;" if r["tkr"] in ghold else "") + "</td>"
        icell = "<td style='padding:4px 8px;text-align:center'>" + ("&#9989;" if r["tkr"] in ihold else "") + "</td>"
        if r.get("last") is None:
            trs.append(f"<tr><td>{r['tkr']}</td>{gcell}{icell}{cells([uw.fmt(r['entry']),'NO DATA','','','','',uw.fmt(r['entry']*dm),uw.shares(r['entry'],equity)])}<td>no data</td></tr>")
            continue
        trs.append(f"<tr><td style='padding:4px 8px'><b>{r['tkr']}</b></td>{gcell}{icell}"
                   f"{cells([uw.fmt(r['entry']),uw.fmt(r['last']),uw.fmt(r['ema9']),uw.fmt(r['ma21']),uw.fmt(r['ma50']),uw.fmt(r['ma200']),uw.fmt(r['entry']*dm),uw.shares(r['entry'],equity)])}"
                   f"<td style='padding:4px 8px'>{status(r)}</td></tr>")
    html = f"""<html><body style="font-family:Arial,sans-serif;font-size:14px">
<h2>Marketwatch — Key List Report ({list_date})</h2>
<p style="color:#555">MAs as of close {asof}. Exit v3 (trend-hold): <b>hold to a daily close below the {M}-day SMA</b>; disaster stop &minus;{D}%. No target/breakeven. Full position = {F}% of portfolio.</p>
<div style="margin:8px 0">{period_html}</div>
<p><b>Regime gate: {rscore}/8 — {rverdict}</b> &middot; allowed new entries: <b>{rallowed}</b></p>
{action_html}
<p style="color:#555;font-size:12px">Cooldown (skip): {cooldown_txt or 'none'} &middot; Extended &gt;{int(uw.EXT_MAX_PCT*100)}% vs 21-MA (skip/reduce): {extended_txt or 'none'}</p>
<p>{overview}</p>
<table style="border-collapse:collapse" border="1">
<tr style="background:#f0f0f0"><th>Ticker</th><th>Gated</th><th>Ideal</th><th>Entry</th><th>Last</th><th>9 EMA</th><th>21 MA</th><th>{M} SMA &larr;exit</th><th>200 MA</th><th>Disaster &minus;{D}%</th><th>Shares ({F}%)</th><th>Status</th></tr>
{''.join(trs)}
</table>
<h3>Order plan — thinkorswim (buy-stop + disaster stop)</h3>
<p style="color:#555">Tickets to review and place yourself — not advice. Buy-STOP entry + STOP &minus;{D}% (disaster); no target — <b>hold to a close below the {M}-day SMA</b>. <b>Regime {rscore}/8 &rarr; new buys are {regime_size}.</b> (7–8: FULL · 4–6: PILOT &frac12;, add rest on confirmation · &le;3: none.)</p>
<table style="border-collapse:collapse" border="1">
<tr style="background:#f0f0f0"><th>Ticker</th><th>Buy STOP</th><th>Size</th><th>Qty</th><th>Disaster STOP &minus;{D}%</th><th>Exit rule</th><th>Flags</th></tr>
{''.join(f"<tr><td style='padding:4px 8px'><b>{r['tkr']}</b></td>" + cells([uw.fmt(r['entry']), size_label(r['tkr']), (qty_half(r['entry'], r['tkr'])[0] if equity else '—'), uw.fmt(r['entry']*dm)]) + f"<td style='padding:4px 8px'>close &lt; {M} SMA</td><td style='padding:4px 8px'>{order_flags(r['tkr'])}</td></tr>" for r in rows)}
</table>
<h3>Add-on plan — scale pilots toward full (advisory)</h3>
{("<p style='color:#555'>Regime "+str(rscore)+"/8 confirms — top up these working pilots to full. Add on strength; the disaster stop / 50-SMA exit then apply to the whole position.</p>"
  "<table style='border-collapse:collapse' border='1'><tr style='background:#f0f0f0'><th>Ticker</th><th>Now</th><th>&rarr; Target</th><th>Add shares</th><th>Add $</th><th>Ret %</th><th>vs 50-SMA</th></tr>"
  + "".join(f"<tr><td style='padding:4px 8px'><b>{p['tkr']}</b></td><td style='padding:4px 8px;text-align:right'>{w*100:.2f}%</td><td style='padding:4px 8px;text-align:right'>{uw.FULL_POSITION_PCT*100:.2f}%</td><td style='padding:4px 8px;text-align:right'>{add_sh if add_sh is not None else '—'}</td><td style='padding:4px 8px;text-align:right'>${gap*equity:,.0f}</td><td style='padding:4px 8px;text-align:right'>{p['ret']*100:+.1f}%</td><td style='padding:4px 8px;text-align:right'>{('+'+format((p['last']/p['ma50']-1)*100,'.1f')+'%') if p.get('ma50') else '—'}</td></tr>" for p, w, gap, add_sh in sorted(addons, key=lambda x:-x[0]['ret']))
  + "</table>") if addons else
 (f"<p style='color:#555'>No add-ons — regime {rscore}/8 is not a confirmed uptrend (&ge;7). Pilots are topped up to full only when the market confirms.</p>")}
{gated_html}
{ideal_html}
{bench_html}
<h3>Closed positions — this month ({month})</h3>
<p style="color:#555">Trades exited this calendar month. Single-account view (one position per name at a time; adds not modeled). Net P&amp;L per trade.</p>
<h4>&#9989; Closed with profit ({len(c_win)})</h4>
<table style="border-collapse:collapse" border="1">
<tr style="background:#eaf7ea"><th>Ticker</th><th>From list</th><th>Entered</th><th>Fill</th><th>Exited</th><th>Exit px</th><th>How</th><th>P&amp;L %</th>{'<th>$ P&amp;L</th>' if full_pos else ''}</tr>
{''.join(f"<tr><td style='padding:4px 8px'><b>{r['tkr']}</b></td><td style='padding:4px 8px'>{r['list_date']}</td><td style='padding:4px 8px'>{r['entry_date']}</td>" + cells([f"{r['fill']:.2f}", r.get('exit_date','—'), (f"{r['exit_px']:.2f}" if r.get('exit_px') else '—'), r.get('exit_kind','—'), f"{r['ret']*100:+.2f}%"] + ([f"{r['ret']*full_pos:+,.0f}"] if full_pos else [])) + "</tr>" for r in c_win) or "<tr><td colspan='9' style='padding:4px 8px'>none yet</td></tr>"}
</table>
<p><b>Subtotal: {wr*100:+.2f}% cum{f" · ${wr*full_pos:+,.0f}" if full_pos else ""}</b></p>
<h4>&#10060; Closed with loss / stop-outs ({len(c_loss)})</h4>
<table style="border-collapse:collapse" border="1">
<tr style="background:#fdeaea"><th>Ticker</th><th>From list</th><th>Entered</th><th>Fill</th><th>Exited</th><th>Exit px</th><th>How</th><th>P&amp;L %</th>{'<th>$ P&amp;L</th>' if full_pos else ''}</tr>
{''.join(f"<tr><td style='padding:4px 8px'><b>{r['tkr']}</b></td><td style='padding:4px 8px'>{r['list_date']}</td><td style='padding:4px 8px'>{r['entry_date']}</td>" + cells([f"{r['fill']:.2f}", r.get('exit_date','—'), (f"{r['exit_px']:.2f}" if r.get('exit_px') else '—'), r.get('exit_kind','—'), f"{r['ret']*100:+.2f}%"] + ([f"{r['ret']*full_pos:+,.0f}"] if full_pos else [])) + "</tr>" for r in c_loss) or "<tr><td colspan='9' style='padding:4px 8px'>none yet</td></tr>"}
</table>
<p><b>Subtotal: {lr_*100:+.2f}% cum{f" · ${lr_*full_pos:+,.0f}" if full_pos else ""}</b><br>
<b>Closed this month: {n_closed} trades · win rate {f"{100*len(c_win)/n_closed:.0f}%" if n_closed else "—"} · net realized {f"${net_closed*full_pos:+,.0f}" if full_pos and n_closed else f"{net_closed*100:+.2f}% cum"}</b></p>
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
