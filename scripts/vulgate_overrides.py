"""Render-stage ATU-line override layer for the Vulgate reader.

Sibling to scripts/bofm_generate.py _overrides() / _apply_override() in BoFM,
but architected around Vulgate's TF-node-list pipeline: overrides are applied
on the rendered List[str] for each verse INSIDE build_content.py, AFTER
vg.render(api, ln) materializes the strings — never inside vg.generate().

Override file: data/text-files/v1.5-adjudicated/overrides.json
  Schema: {"<book> <chapter>:<verse>": ["ATU line 1", "ATU line 2", ...]}
  Keys use lowercase singular book names (matthew, mark, 1john, 2corinthians).

Parity gate: the override's joined alnum (NFD-normalized, combining-marks
stripped, lowercased, [a-z0-9]-filtered) MUST equal the v0 verse_text's same
normalization. Mismatch -> override REJECTED, mechanical kept, warning to stderr.

Env bypass: VULGATE_BYPASS_OVERRIDES=1 short-circuits to mechanical for
validators that want to measure raw mechanical output.
"""
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ADJUDICATED = REPO_ROOT / "data" / "text-files" / "v1.5-adjudicated" / "overrides.json"
BYPASS_ENV = "VULGATE_BYPASS_OVERRIDES"

# TF book_code -> override-key book token. Lowercase singular, matches the
# BoFM convention ("1nephi 1:1", "alma 5:6") so the same JSON shape transfers
# across readers.
BOOK_KEY = {
    "MATT":   "matthew",
    "MARK":   "mark",
    "LUKE":   "luke",
    "JOHN":   "john",
    "ACTS":   "acts",
    "ROM":    "romans",
    "1COR":   "1corinthians",
    "2COR":   "2corinthians",
    "GAL":    "galatians",
    "EPH":    "ephesians",
    "PHIL":   "philippians",
    "COL":    "colossians",
    "1THESS": "1thessalonians",
    "2THESS": "2thessalonians",
    "1TIM":   "1timothy",
    "2TIM":   "2timothy",
    "TIT":    "titus",
    "PHILEM": "philemon",
    "HEB":    "hebrews",
    "JAS":    "james",
    "1PET":   "1peter",
    "2PET":   "2peter",
    "1JOHN":  "1john",
    "2JOHN":  "2john",
    "3JOHN":  "3john",
    "JUDE":   "jude",
    "REV":    "revelation",
}

_OVERRIDES = None


def _overrides():
    """Cached singleton loader. Honors VULGATE_BYPASS_OVERRIDES."""
    global _OVERRIDES
    if os.environ.get(BYPASS_ENV):
        return {}
    if _OVERRIDES is None:
        if ADJUDICATED.exists():
            _OVERRIDES = json.loads(ADJUDICATED.read_text(encoding="utf-8"))
        else:
            _OVERRIDES = {}
    return _OVERRIDES


_ALNUM_KEEP = re.compile(r"[^a-z0-9]")


def _alnum_latin(s):
    """NFD-normalized, combining-marks-stripped, lowercased, [a-z0-9]-filtered.

    Latin Vulgate surface forms are typically unaccented (Iesus, not Iesus),
    but LLM-authored override JSON may carry macrons / precomposed accents.
    NFD + strip combining marks (Unicode category Mn) collapses those to bare
    Latin letters, preserving strict-but-diacritic-tolerant parity. The TF
    surface form is canonical; an override that disagrees on i/j or u/v IS
    a real text change and is correctly rejected by the simple [a-z0-9] gate.
    """
    nfd = unicodedata.normalize("NFD", s).lower()
    stripped = "".join(ch for ch in nfd
                       if unicodedata.category(ch) != "Mn")
    return _ALNUM_KEEP.sub("", stripped)


def ref_for(book_code, chap, verse):
    """Build the override-lookup key for a verse, e.g. 'matthew 5:3'."""
    book = BOOK_KEY.get(book_code)
    if book is None:
        return None
    return f"{book} {chap}:{verse}"


def apply_override(verse_text, ref):
    """Return adjudicated ATU lines for `ref` iff:
      (a) an override exists, and
      (b) the override's lines reassemble to verse_text alnum-for-alnum.
    Returns None otherwise; on parity mismatch prints a stderr warning
    matching the BoFM contract.
    """
    if ref is None:
        return None
    ov = _overrides().get(ref)
    if not ov:
        return None
    if _alnum_latin(" ".join(ov)) != _alnum_latin(verse_text):
        print(f"  !! adjudication override REJECTED (text mismatch): {ref}",
              file=sys.stderr, flush=True)
        return None
    return ov


# NB: cross-verse merges (BoFM bofm_generate.py:1031-1090, Tanakh Rule H10
# analog) have NO Latin Vulgate analogue yet. No rule in vulgate_generate.py
# moves an ATU across a verse boundary. If a Latin cross-verse phenomenon is
# later identified, port the BoFM schema; do not pre-build dead code.
