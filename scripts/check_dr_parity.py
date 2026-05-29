#!/usr/bin/env python3
"""Token-exact gate for the LLM-realigned eng-dr: every verse's spans, concatenated
and alnum-normalized, must equal the COMMITTED (HEAD) eng-dr for that verse -- i.e.
the realignment moved only line breaks, never altered/dropped/added a DR word."""
import glob
import os
import re
import subprocess

REPO = "C:/Users/bibleman/repos/readers-vulgate"
os.chdir(REPO)


def alnum(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def parse(text):
    out, ref, buf = {}, None, []
    for ln in text.splitlines():
        s = ln.strip()
        if re.match(r"^\d+:\d+$", s):
            if ref is not None:
                out[ref] = alnum(" ".join(buf))
            ref, buf = s, []
        elif s:
            buf.append(s)
    if ref is not None:
        out[ref] = alnum(" ".join(buf))
    return out


bad, checked = [], 0
for f in glob.glob("data/text-files/v1.5/eng-dr/*/*.txt"):
    rel = f.replace("\\", "/")
    cur = parse(open(f, encoding="utf-8").read())
    head = subprocess.run(["git", "show", f"HEAD:{rel}"],
                          capture_output=True, text=True, encoding="utf-8")
    if head.returncode != 0:
        continue
    old = parse(head.stdout)
    for ref in set(cur) | set(old):
        checked += 1
        if cur.get(ref, "") != old.get(ref, ""):
            bad.append(f"{rel} {ref}")

print(f"DR parity: {len(bad)} mismatches across {checked} verses (new eng-dr vs HEAD)")
for b in bad[:25]:
    print("  ", b)
