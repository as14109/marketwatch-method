#!/usr/bin/env python3
"""Lint the MW wiki: orphans, unresolved links, link stats. Read-only."""
import os, re, glob, sys, collections
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

WIKI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MW", "wiki")
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MW", "raw")
ENTRY = {"index", "overview", "log", "portfolio-plan"}
LINK = re.compile(r"\[\[([^\]]+)\]\]")

files = glob.glob(os.path.join(WIKI, "**", "*.md"), recursive=True)
pages = {}        # name -> relpath
folder = {}       # name -> folder
for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    pages[name] = os.path.relpath(f, WIKI)
    folder[name] = os.path.basename(os.path.dirname(f))

inbound = collections.Counter()
unresolved = collections.Counter()
outbound = {}
for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    txt = open(f, encoding="utf-8").read()
    targets = set()
    for m in LINK.finditer(txt):
        t = m.group(1).split("|")[0].split("#")[0].strip().lower()
        if t: targets.add(t)
    outbound[name] = targets
    for t in targets:
        if t == name: continue
        if t in pages: inbound[t] += 1
        else: unresolved[t] += 1

print(f"PAGES: {len(pages)}  ({collections.Counter(folder.values())})\n")

orphans = sorted(p for p in pages if inbound[p] == 0 and p not in ENTRY)
print(f"ORPHANS (no inbound wikilinks) — {len(orphans)}:")
for p in orphans: print(f"  [{folder[p]}] {p}")

print(f"\nUNRESOLVED LINKS (target has no page) — {len(unresolved)} distinct, by inbound count:")
for t, c in unresolved.most_common():
    print(f"  {c:>2}x  [[{t}]]")

# raw key lists without a wiki source page
print("\nRAW key-lists vs wiki source pages:")
for rf in sorted(glob.glob(os.path.join(RAW, "*key-list*.md"))):
    d = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(rf))
    if not d: continue
    src = f"{d.group(1)}-key-list"
    print(f"  {d.group(1)}: source page {'OK' if src in pages else 'MISSING'}")
