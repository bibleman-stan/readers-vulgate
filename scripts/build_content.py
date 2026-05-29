#!/usr/bin/env python3
"""build_content.py - Emit the Vulgate v1.5 Latin ATU text-files AND the
Douay-Rheims (1582 Rheims NT) English verse-layer text-files that feed
build_books.py.

Latin source  : the v1.5 mechanical ATU generator (scripts/vulgate_generate.py)
                over the gold UD_Latin-PROIEL Text-Fabric at data/tf/0.1.
English source: the Original Douay-Rheims JSON dataset (CC0) cloned to
                private/original-douay-rheims/ - the Vulgate's own English.

Output (committed, public):
  data/text-files/v1.5/lat/<NN-slug>/<slug>-<CC>.txt   (Latin ATU lines)
  data/text-files/v1.5/eng-dr/<NN-slug>/<slug>-<CC>.txt (DR verse text)

The DR layer is VERSE-LEVEL for this first build: the whole DR verse is placed
on the first ATU line of its verse block; the remaining ATU lines of that verse
get a blank English line. A clean per-ATU interleave is deferred.

COVERAGE NOTE: the PROIEL Vulgate TF is a GOLD but PARTIAL NT - the Gospels,
Acts and Revelation are near-complete; the Epistles are sampled (select verses
only). This script emits ATU for exactly the verses present in the TF and
reports DR alignment over that set.

Usage:
  cd C:/Users/bibleman/repos/readers-vulgate
  PYTHONIOENCODING=utf-8 python scripts/build_content.py
  PYTHONIOENCODING=utf-8 python scripts/build_content.py --book MATT
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
LAT_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1.5", "lat")
ENG_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1.5", "eng-dr")
DR_DIR = os.path.join(REPO_ROOT, "private", "original-douay-rheims", "bible", "raw")

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import vulgate_generate as vg  # noqa: E402

# TF book_code -> (web slug, numbered-folder index, DR raw json filename)
# Order is canonical NT order; slugs match the GNT family convention.
BOOKS = [
    ("MATT",   "matt",    1,  "matthew.json"),
    ("MARK",   "mark",    2,  "mark.json"),
    ("LUKE",   "luke",    3,  "luke.json"),
    ("JOHN",   "john",    4,  "john.json"),
    ("ACTS",   "acts",    5,  "acts.json"),
    ("ROM",    "rom",     6,  "romans.json"),
    ("1COR",   "1cor",    7,  "1-corinthians.json"),
    ("2COR",   "2cor",    8,  "2-corinthians.json"),
    ("GAL",    "gal",     9,  "galatians.json"),
    ("EPH",    "eph",    10,  "ephesians.json"),
    ("PHIL",   "phil",   11,  "philippians.json"),
    ("COL",    "col",    12,  "colossians.json"),
    ("1THESS", "1thess", 13,  "1-thessalonians.json"),
    ("2THESS", "2thess", 14,  "2-thessalonians.json"),
    ("1TIM",   "1tim",   15,  "1-timothy.json"),
    ("2TIM",   "2tim",   16,  "2-timothy.json"),
    ("TIT",    "titus",  17,  "titus.json"),
    ("PHILEM", "phlm",   18,  "philemon.json"),
    ("HEB",    "heb",    19,  "hebrews.json"),
    ("JAS",    "jas",    20,  "james.json"),
    ("1PET",   "1pet",   21,  "1-peter.json"),
    ("2PET",   "2pet",   22,  "2-peter.json"),
    ("1JOHN",  "1john",  23,  "1-john.json"),
    ("2JOHN",  "2john",  24,  "2-john.json"),
    ("3JOHN",  "3john",  25,  "3-john.json"),
    ("JUDE",   "jude",   26,  "jude.json"),
    ("REV",    "rev",    27,  "apocalypse.json"),
]

# DR raw text still carries <sc>/<i> content markers; strip the tags, keep text.
_TAG_RE = re.compile(r"</?(sc|i)>")
_WS_RE = re.compile(r"\s+")


def clean_dr(text):
    text = _TAG_RE.sub("", text or "")
    text = _WS_RE.sub(" ", text).strip()
    return text


def load_dr(filename):
    """Return {(chapter, verse): text} for one DR book, or {} if missing."""
    path = os.path.join(DR_DIR, filename)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for ch in data.get("chapters", []):
        cnum = ch.get("chapter")
        for v in ch.get("verses", []):
            out[(cnum, v.get("verse"))] = clean_dr(v.get("text", ""))
    return out


def chapters_in_tf(api, book_code):
    F = api.F
    chs = set()
    for v in F.otype.s("verse"):
        if F.book_code.v(v) == book_code:
            chs.add(F.chapter.v(v))
    return sorted(chs)


def write_chapter(out_dir, slug, idx, chap, blocks):
    """blocks = list of (ref, [text_lines]). Writes the colometric file format
    (ref line, ATU lines, blank line between verses)."""
    folder = os.path.join(out_dir, f"{idx:02d}-{slug}")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{slug}-{chap:02d}.txt")
    parts = []
    for ref, lines in blocks:
        parts.append(ref)
        parts.extend(lines)
        parts.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default=None, help="TF book_code, e.g. MATT")
    args = ap.parse_args()

    api = vg.load_api()

    selected = BOOKS
    if args.book:
        selected = [b for b in BOOKS if b[0] == args.book.upper()]
        if not selected:
            print(f"Unknown book {args.book}", file=sys.stderr)
            sys.exit(1)

    # Coverage accounting
    cov = {
        "tf_verses": 0,        # Latin verses emitted (present in TF)
        "dr_aligned": 0,       # of those, DR has a matching (ch,verse)
        "dr_missing": defaultdict(list),  # slug -> [ "ch:v", ... ] no DR match
    }

    for book_code, slug, idx, dr_file in selected:
        dr = load_dr(dr_file)
        chs = chapters_in_tf(api, book_code)
        book_verses = 0
        book_aligned = 0
        for chap in chs:
            lines = vg.generate(book_code, chap)
            # group ATU lines by verse ref, preserving order
            by_verse = []
            seen_ref = {}
            for ln in lines:
                ref = ln["ref"]              # "5:3"
                txt = vg.render(api, ln)
                if ref not in seen_ref:
                    seen_ref[ref] = len(by_verse)
                    by_verse.append([ref, [], ln["verse"]])
                by_verse[seen_ref[ref]][1].append(txt)

            lat_blocks = []
            eng_blocks = []
            for ref, atu_lines, vnum in by_verse:
                lat_blocks.append((ref, atu_lines))
                # DR verse-level layer: whole DR verse on line 0, blanks after.
                dr_text = dr.get((chap, vnum), "")
                book_verses += 1
                cov["tf_verses"] += 1
                if dr_text:
                    book_aligned += 1
                    cov["dr_aligned"] += 1
                else:
                    cov["dr_missing"][slug].append(f"{chap}:{vnum}")
                en_lines = [dr_text] + [""] * (len(atu_lines) - 1)
                eng_blocks.append((ref, en_lines))

            write_chapter(LAT_DIR, slug, idx, chap, lat_blocks)
            write_chapter(ENG_DIR, slug, idx, chap, eng_blocks)

        pct = (100.0 * book_aligned / book_verses) if book_verses else 0.0
        print(f"  {slug:<8} {len(chs):>2} ch  {book_verses:>4} TF-vv  "
              f"DR-aligned {book_aligned:>4} ({pct:5.1f}%)")

    # Coverage report
    print("\n=== DR COVERAGE OVER TF-PRESENT VERSES ===")
    print(f"Latin (TF) verses emitted : {cov['tf_verses']}")
    print(f"DR-aligned                : {cov['dr_aligned']} "
          f"({100.0*cov['dr_aligned']/max(cov['tf_verses'],1):.1f}%)")
    total_missing = sum(len(v) for v in cov["dr_missing"].values())
    print(f"DR mismatches (no DR verse at TF ref): {total_missing}")
    for slug in sorted(cov["dr_missing"]):
        miss = cov["dr_missing"][slug]
        print(f"   {slug:<8} {len(miss):>3}  {', '.join(miss[:12])}"
              + (" ..." if len(miss) > 12 else ""))

    # Persist machine-readable coverage for the research record
    report = {
        "tf_verses": cov["tf_verses"],
        "dr_aligned": cov["dr_aligned"],
        "dr_mismatches_total": total_missing,
        "dr_mismatches_by_book": {k: v for k, v in cov["dr_missing"].items()},
    }
    os.makedirs(os.path.join(REPO_ROOT, "research"), exist_ok=True)
    with open(os.path.join(REPO_ROOT, "research", "dr-coverage.json"),
              "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\nWrote research/dr-coverage.json")


if __name__ == "__main__":
    main()
