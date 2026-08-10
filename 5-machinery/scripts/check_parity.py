#!/usr/bin/env python3
"""Parity gate: every verse's regenerated ATU lines must reassemble (alnum) to
the gold TF source text -- the generator may only ADD line breaks, never alter,
drop, or duplicate a word. Prints any mismatch."""
import re
from collections import defaultdict
import vulgate_generate as vg

api = vg.load_api()
F, L, T = api.F, api.L, api.T


def alnum(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


by_chap = defaultdict(list)
for v in F.otype.s("verse"):
    by_chap[(F.book_code.v(v), F.chapter.v(v))].append(v)

bad = []
nverses = 0
for (bc, ch), vs in sorted(by_chap.items()):
    lines = vg.generate(bc, ch)
    byv = defaultdict(list)
    for ln in lines:
        byv[(ln["chapter"], ln["verse"])].append(vg.render(api, ln))
    for v in vs:
        nverses += 1
        vn = (F.chapter.v(v), F.verse.v(v))
        if alnum(T.text(v)) != alnum(" ".join(byv.get(vn, []))):
            bad.append(f"{bc} {vn[0]}:{vn[1]}")

print(f"parity over {nverses} verses: {len(bad)} mismatches")
for b in bad[:25]:
    print("  ", b)
