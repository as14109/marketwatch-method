#!/usr/bin/env python3
"""
Open positions — every Key List signal that triggered and is still live under
the trade rules (v3: 50-SMA trend-hold, disaster stop -12%).

Scans ALL ingested Key Lists through the backtest engine and collects positions
whose sim state is still OPEN (held above the 50-day SMA).
A name that triggered from multiple lists is held ONCE — the earliest trigger
wins (later signals would be adds, which we don't model).

Writes the table between the OPENPOS markers in MW/wiki/overview.md and prints
it. Also importable: collect() returns the deduped open-position rows for the
emailed report.

Usage: python tools/open_positions.py
"""
import sys, glob, os, re, datetime as dt
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import update_watchlist as uw
import backtest

START, END = "<!-- OPENPOS:START -->", "<!-- OPENPOS:END -->"


def all_dates():
    return sorted({m.group(1) for f in glob.glob(os.path.join(uw.RAW, "*key-list*.md"))
                   if (m := re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(f)))
                   and m.group(1) >= uw.MODEL_START})   # book inception (July 1); June excluded


# Benchmark capital cap: the every-signal book still can't invest more than the
# account holds. Max concurrent full positions = max-deployed / full size = 12
# ($1.2M / $100k), i.e. uw.MAX_POSITIONS. Once full, new triggers are DROPPED
# (first-come chronological); a slot frees only when a held position exits.
BENCH_CAP = uw.MAX_POSITIONS

_adm_cache = {}

def _admitted(asof=None):
    """Capacity-aware admission of every triggered signal (one position per name,
    earliest trigger), chronological: a candidate enters only if fewer than
    BENCH_CAP admitted positions are still open on its entry day. Returns the full
    admitted set (open + closed), point-in-time at `asof`."""
    key = asof.isoformat() if asof else "now"
    if key in _adm_cache:
        return _adm_cache[key]
    best = {}
    for d in all_dates():
        if asof is not None and dt.date.fromisoformat(d) > asof:
            continue
        try:
            rows, _ = backtest.sim_list(d, asof=asof)
        except Exception:
            continue
        for r in rows:
            if r.get("ret") is None or r["status"] == "not triggered" or not r.get("entry_date"):
                continue
            r2 = dict(r, list_date=d)
            k = r["tkr"]
            if k not in best or r2["entry_date"] < best[k]["entry_date"]:
                best[k] = r2
    cands = sorted(best.values(), key=lambda r: (r["entry_date"], r["list_date"]))
    admitted = []
    for r in cands:
        e = r["entry_date"]
        concurrent = sum(1 for a in admitted if (not a.get("exit_date")) or a["exit_date"] > e)
        if concurrent < BENCH_CAP:          # capital available -> take it; else drop (maxed out)
            admitted.append(r)
    _adm_cache[key] = admitted
    return admitted


def collect(asof=None):
    """Open positions in the capacity-capped every-signal book, sorted by unrealized %."""
    op = [dict(r) for r in _admitted(asof) if r["status"].startswith("OPEN")]
    for r in op:                             # time-stop flag (v2.1 #6): dead money after N sessions
        r["stale"] = (r.get("days_held", 0) >= uw.STALE_DAYS and r["ret"] < uw.STALE_MIN_RET)
    return sorted(op, key=lambda r: r["ret"], reverse=True)


def collect_closed(open_pos=None, asof=None):
    """Closed trades in the capacity-capped every-signal book (same admitted set as
    collect(), so open + closed reconcile to one account). Sorted by exit date."""
    cl = [dict(r) for r in _admitted(asof) if r["status"] == "closed"]
    return sorted(cl, key=lambda r: (r.get("exit_date") or "", r["tkr"]))


def next_sell(r):
    """Exit v3: the position is held until a daily CLOSE below the 50-day SMA
    (or the −12% disaster stop). The 'next sell' is that trailing 50-SMA level."""
    ma = r.get("ma50")
    return (f"<{ma:.2f} close ({uw.TREND_MA}SMA)" if ma else f"close<{uw.TREND_MA}SMA")


def build_table(pos, equity=None):
    full = equity * uw.FULL_POSITION_PCT if equity else None
    lines = [f"_Simulated book per [[key-list-trade-rules]] v3: every triggered signal, earliest entry "
             f"per name, still open. {len(pos)} positions"
             + (f" · full = ${int(full):,}" if full else "") + "._", ""]
    lines.append(f"| Ticker | From list | Entered | Fill | Last | Disaster stop | Exit (< {uw.TREND_MA}SMA) | Status | Unreal. % |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |")
    tot = 0.0
    for r in pos:
        flag = " ⏳stale" if r.get("stale") else ""
        lines.append(f"| [[{r['tkr'].lower()}]] | {r['list_date']} | {r['entry_date']} | "
                     f"{r['fill']:.2f} | {r['last']:.2f} | {r['stop_now']:.2f} | {next_sell(r)} | "
                     f"{r['status']}{flag} | {r['ret']*100:+.2f}% |")
        tot += r["ret"]
    if pos:
        port = sum(r["ret"] * uw.FULL_POSITION_PCT for r in pos)
        lines.append(f"\n**Open P&L: avg {tot/len(pos)*100:+.2f}%/position · "
                     f"{port*100:+.2f}% of equity at {int(uw.FULL_POSITION_PCT*100)}%/name"
                     + (f" · ≈ ${sum(r['ret']*full for r in pos):,.0f}" if full else "") + "**")
    return "\n".join(lines)


def main():
    eq_raw = uw.env("MW_PORTFOLIO_EQUITY")
    equity = float(re.sub(r"[,$\s]", "", eq_raw)) if eq_raw else None
    pos = collect()
    table = build_table(pos, equity)
    print(table.replace("[[", "").replace("]]", ""))

    ov = os.path.join(uw.WIKI, "overview.md")
    text = open(ov, encoding="utf-8").read()
    block = f"{START}\n{table}\n{END}"
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.DOTALL)
        open(ov, "w", encoding="utf-8").write(text)
        print(f"\n[updated open-positions table in {ov}]")
    else:
        print(f"\n[OPENPOS markers not found in {ov} — table not spliced]")


if __name__ == "__main__":
    main()
