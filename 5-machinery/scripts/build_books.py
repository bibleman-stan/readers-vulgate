"""
build_books.py - Generate HTML book files from the Vulgate colometric sources.

Reads chapter files from v1.5/lat/*/ (Latin ATU lines) and
v1.5/eng-dr/*/ (Douay-Rheims English, verse-level), and writes one HTML
fragment per book into books/.

Each .line span contains a .lat span (Latin) and a .en span (Douay-Rheims
English), enabling Latin / English / Both display modes in the web app, and a
bilingual search index that matches either layer.

Ported from readers-gnt/5-machinery/scripts/build_books.py. The Greek-specific pieces -
the SBLGNT word-order integrity check and the KJV archaic->modern swap engine -
are NOT applicable to Latin and have been removed.

Usage:
    py -3 5-machinery/scripts/build_books.py              # build all books
    py -3 5-machinery/scripts/build_books.py --book mark  # build one book
"""

import argparse
import glob
import html
import os
import re
from collections import defaultdict

def _find_repo_root():
    """Repo root by MARKER, not by counting parents.

    Counting encodes this file's depth in the tree, so moving the file silently
    breaks it and no text-based check notices. Anchoring on .git survives any
    move. Added 2026-08-10 after a reorg broke three different counted idioms.
    """
    from pathlib import Path as _P
    _here = _P(__file__).resolve()
    for _p in _here.parents:
        if (_p / ".git").exists():
            return _p
    return _here.parent


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = _find_repo_root()
LAT_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1.5", "lat")
INPUT_DIR = LAT_DIR
EN_DIR = os.path.join(REPO_ROOT, "data", "text-files", "v1.5", "eng-dr")
OUTPUT_DIR = os.path.join(REPO_ROOT, "books")

VERSE_REF_RE = re.compile(r"^\d+:\d+$")


def parse_chapter(filepath):
    """Parse a colometric chapter file into a list of verse dicts.

    Returns:
        chapter_num (int), verses (list of {"ref": "4:1", "lines": [...]})
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    verses = []
    current_verse = None
    chapter_num = None
    in_verse = False

    for raw in raw_lines:
        line = raw.rstrip("\n").rstrip("\r")

        if VERSE_REF_RE.match(line.strip()):
            if current_verse is not None:
                verses.append(current_verse)
            ref = line.strip()
            if chapter_num is None:
                chapter_num = int(ref.split(":")[0])
            current_verse = {"ref": ref, "lines": []}
            in_verse = True
            continue

        # Blank line ends current verse block. The DR English layer carries
        # intentional blank lines (one per extra ATU line beyond the first);
        # those are interior to a verse block and must NOT end it. We only end
        # a block on a blank line that is followed by a new verse ref or EOF,
        # which the ref-driven logic above already handles - so here we treat a
        # blank simply as an empty sense-line slot, preserving line alignment.
        if line.strip() == "":
            if current_verse is not None:
                current_verse["lines"].append("")
            continue

        if not in_verse:
            continue
        if current_verse is not None:
            current_verse["lines"].append(line)

    if current_verse is not None:
        verses.append(current_verse)

    # Trim trailing empty sense-lines from each verse (artifact of the
    # block-terminating blank line).
    for v in verses:
        while v["lines"] and v["lines"][-1] == "":
            v["lines"].pop()
    return chapter_num, verses


def build_lookup(en_verses):
    return {v["ref"]: v["lines"] for v in en_verses}


# Superscript digit map for inline verse markers (cross-verse continuation)
_SUPERSCRIPT_TO_DIGIT = {
    "²": "2", "³": "3",
    "⁰": "0", "¹": "1",
    "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7",
    "⁸": "8", "⁹": "9",
}
_SUPERSCRIPT_RE = re.compile("[" + "".join(_SUPERSCRIPT_TO_DIGIT.keys()) + "]+")


def _wrap_verse_markers(escaped_line, chapter_num):
    def repl(m):
        marker_text = m.group(0)
        digits = "".join(_SUPERSCRIPT_TO_DIGIT[c] for c in marker_text)
        inline_id = f"v-{chapter_num}-{digits}-inline"
        return f'<sup class="verse-marker" id="{inline_id}">{marker_text}</sup>'
    return _SUPERSCRIPT_RE.sub(repl, escaped_line)


def build_chapter_html(chapter_num, lat_verses, en_lookup=None):
    """Build HTML for one chapter with paired Latin/English lines."""
    parts = [f'<div class="chapter" id="ch-{chapter_num}">']

    for verse in lat_verses:
        ref = html.escape(verse["ref"])
        verse_id = "v-" + ref.replace(":", "-")
        parts.append(
            f'  <div class="verse" id="{verse_id}">'
            f'<span class="verse-num">{ref}</span>'
        )

        en_lines = []
        if en_lookup and verse["ref"] in en_lookup:
            en_lines = en_lookup[verse["ref"]]

        for i, lat_line in enumerate(verse["lines"]):
            lat_escaped = html.escape(lat_line)
            # Latin uses '.' ',' ';' ':' - wrap for the punctuation toggle.
            lat_escaped = re.sub(
                r'([,.;:?!])', r'<span class="punct">\1</span>', lat_escaped
            )
            lat_escaped = _wrap_verse_markers(lat_escaped, chapter_num)

            en_text = en_lines[i] if i < len(en_lines) else ""
            en_escaped = html.escape(en_text)
            en_escaped = re.sub(
                r'([,.;:!?\'"\-])', r'<span class="punct">\1</span>', en_escaped
            )
            en_escaped = _wrap_verse_markers(en_escaped, chapter_num)

            parts.append(
                f'    <span class="line">'
                f'<span class="lat">{lat_escaped}</span>'
                f'<span class="en">{en_escaped}</span></span>'
            )
        parts.append("  </div>")

    parts.append("</div>")
    return "\n".join(parts)


def discover_books(input_dir, book_filter=None):
    pattern = os.path.join(input_dir, "*", "*.txt")
    files = glob.glob(pattern)
    books = defaultdict(list)
    for fpath in files:
        stem = os.path.splitext(os.path.basename(fpath))[0]  # "1cor-03"
        dash_idx = stem.rfind("-")
        if dash_idx == -1:
            continue
        prefix = stem[:dash_idx]
        try:
            ch_num = int(stem[dash_idx + 1:])
        except ValueError:
            continue
        if book_filter and prefix != book_filter:
            continue
        books[prefix].append((ch_num, fpath))
    for prefix in books:
        books[prefix].sort(key=lambda x: x[0])
    return dict(books)


def _book_prefix(fpath):
    stem = os.path.splitext(os.path.basename(fpath))[0]
    dash_idx = stem.rfind("-")
    return stem[:dash_idx] if dash_idx != -1 else stem


def _find_book_subdir(base_dir, prefix):
    if not os.path.isdir(base_dir):
        return None
    for entry in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, entry)):
            parts = entry.split("-", 1)
            if len(parts) == 2 and parts[0].isdigit() and parts[1] == prefix:
                return entry
    if os.path.isdir(os.path.join(base_dir, prefix)):
        return prefix
    return None


def resolve_english_path(fpath):
    basename = os.path.basename(fpath)
    prefix = _book_prefix(fpath)
    subdir = _find_book_subdir(EN_DIR, prefix)
    if subdir:
        en_path = os.path.join(EN_DIR, subdir, basename)
        if os.path.isfile(en_path):
            return en_path
    return None


def build_book(prefix, chapter_files, output_dir):
    all_chapter_html = []
    total_verses = 0
    has_en = False

    for _ch_num, fpath in chapter_files:
        chapter_num, lat_verses = parse_chapter(fpath)
        if chapter_num is None:
            chapter_num = _ch_num

        en_lookup = None
        en_path = resolve_english_path(fpath)
        if en_path:
            _, en_verses = parse_chapter(en_path)
            en_lookup = build_lookup(en_verses)
            has_en = True

        total_verses += len(lat_verses)
        all_chapter_html.append(
            build_chapter_html(chapter_num, lat_verses, en_lookup)
        )

    output_path = os.path.join(output_dir, f"{prefix}.html")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_chapter_html) + "\n")

    return len(chapter_files), total_verses, output_path, has_en


def main():
    parser = argparse.ArgumentParser(
        description="Build HTML book files from Vulgate colometric sources."
    )
    parser.add_argument("--book", default=None, help="Build only this book.")
    args = parser.parse_args()

    if not os.path.isdir(INPUT_DIR):
        print(f"ERROR: Input directory not found: {INPUT_DIR}")
        raise SystemExit(1)

    books = discover_books(INPUT_DIR, book_filter=args.book)
    if not books:
        print(f"No .txt files found in {INPUT_DIR}")
        raise SystemExit(1)

    print(f"Building {len(books)} book(s)... [Latin + Douay-Rheims]\n")
    for prefix in sorted(books.keys()):
        num_ch, num_vv, out_path, has_en = build_book(
            prefix, books[prefix], OUTPUT_DIR
        )
        rel = os.path.relpath(out_path, REPO_ROOT)
        marker = " +DR" if has_en else ""
        print(f"  {prefix:<8} {num_ch:>3} ch, {num_vv:>4} vv  -> {rel}{marker}")

    print(f"\nDone. Output in {os.path.relpath(OUTPUT_DIR, REPO_ROOT)}/")


if __name__ == "__main__":
    main()
