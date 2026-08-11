#!/usr/bin/env python3
"""Build the Vulgate-Latin Text-Fabric from the gold UD_Latin-PROIEL CoNLL-U treebank.

Node types (coarsest -> finest):
  document -> [book -> chapter -> verse ->] sentence -> word(slot)

The `document` node groups each source work in the treebank:
  - Jerome's Vulgate (all 27 NT books, gold hand-annotated)
  - Commentarii belli Gallici (Caesar's Gallic War)
  - Epistulae ad Atticum (Cicero's Letters)
  - Opus agriculturae (Palladius)
  - De officiis (Cicero)

For the Vulgate NT the full biblical section hierarchy is emitted:
  book -> chapter -> verse -> sentence -> word

For classical texts the hierarchy is:
  document -> sentence -> word
(No chapter/verse — they have their own numeric Ref schemes but those are not
biblical verse refs; they are collapsed into the sentence's `ref_raw` feature.)

Slot (word) features:
  form        NFC-normalised surface form
  lemma       lemma
  upos        UD universal POS (the canonical cross-corpus feature)
  xpos        PROIEL native POS
  morph       FEATS column (UD morphological features string)
  udrel       UD dependency relation (the canonical cross-corpus feature)
  is_root     1 where head == 0 (sentence root)
  syn_source  "proiel-gold" for all tokens (provenance mandate §9 of substrate.md)
  text_source work key: vulgate | caesar-bg | cicero-att | palladius | cicero-off

  head        EDGE dep->governor within sentence (absent for roots)

Sentence features:
  sent_id     original PROIEL/UD sent_id
  sent_text   the # text line
  text_source work key (same as slot feature)
  ref         canonical reference for Vulgate: BOOK_CHAPTER.VERSE  (first token's Ref)
              raw reference for classical: the Ref= value of the first token

Book/chapter/verse features (Vulgate only):
  book_code   e.g. MATT
  book_name   e.g. Matthew
  chapter     int
  verse       int (for verse nodes)
  ref         BOOKCODE_CHAPTER.VERSE (for verse nodes)

Document features (all source works):
  text_source  work key
  title        human-readable title

Output: data/tf/0.1/  (load with Fabric(locations='data/tf', modules='0.1'))
"""
import re, sys, unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

from tf.convert.walker import CV
from tf.fabric import Fabric

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


REPO = _find_repo_root()
CONLLU_DIR = REPO / "private" / "substrate" / "UD_Latin-PROIEL"
TF_DIR = REPO / "data" / "tf"
VERSION = "0.1"

# ---- source-text key mapping -------------------------------------------------

def source_to_key(source_str):
    """Map the '# source' line value to a short work key."""
    s = source_str.strip()
    if s.startswith("Jerome's Vulgate"):
        return "vulgate"
    if s.startswith("Commentarii belli Gallici"):
        return "caesar-bg"
    if s.startswith("Epistulae ad Atticum"):
        return "cicero-att"
    if s.startswith("Opus agriculturae"):
        return "palladius"
    if s.startswith("De officiis"):
        return "cicero-off"
    return "unknown"

TEXT_SOURCE_TITLE = {
    "vulgate":    "Jerome's Vulgate (New Testament)",
    "caesar-bg":  "Commentarii belli Gallici (Caesar)",
    "cicero-att": "Epistulae ad Atticum (Cicero)",
    "palladius":  "Opus agriculturae (Palladius)",
    "cicero-off": "De officiis (Cicero)",
}

# ---- NT book ordering and display names -------------------------------------

# Standard canonical NT order
NT_BOOK_ORDER = [
    "MATT", "MARK", "LUKE", "JOHN", "ACTS",
    "ROM", "1COR", "2COR", "GAL", "EPH", "PHIL", "COL",
    "1THESS", "2THESS", "1TIM", "2TIM", "TIT", "PHILEM",
    "HEB", "JAS", "1PET", "2PET",
    "1JOHN", "2JOHN", "3JOHN", "JUDE", "REV",
]

NT_BOOK_NAME = {
    "MATT": "Matthew", "MARK": "Mark", "LUKE": "Luke", "JOHN": "John",
    "ACTS": "Acts", "ROM": "Romans", "1COR": "1 Corinthians",
    "2COR": "2 Corinthians", "GAL": "Galatians", "EPH": "Ephesians",
    "PHIL": "Philippians", "COL": "Colossians", "1THESS": "1 Thessalonians",
    "2THESS": "2 Thessalonians", "1TIM": "1 Timothy", "2TIM": "2 Timothy",
    "TIT": "Titus", "PHILEM": "Philemon", "HEB": "Hebrews", "JAS": "James",
    "1PET": "1 Peter", "2PET": "2 Peter", "1JOHN": "1 John",
    "2JOHN": "2 John", "3JOHN": "3 John", "JUDE": "Jude", "REV": "Revelation",
}

# ---- CoNLL-U parsing --------------------------------------------------------

def nfc(s):
    return unicodedata.normalize("NFC", s)

def parse_conllu_files(paths):
    """
    Yield sentence dicts in document order across train/dev/test.
    Each dict:
      {
        'source_key': str,      # work key
        'source_line': str,     # raw '# source' value
        'sent_id': str,
        'text': str,            # '# text' line value
        'tokens': [             # only regular tokens (no MWT, no empty)
          {
            'id': int, 'form': str, 'lemma': str,
            'upos': str, 'xpos': str, 'morph': str,
            'head': int, 'udrel': str, 'ref_raw': str,
          }
        ]
      }
    """
    # Canonical ordering: train first (preserves original document order),
    # then dev, then test.  Within-train order already reflects the PROIEL
    # source ordering (Vulgate books are mostly consecutive per book/chapter).
    for path in paths:
        cur_source = None
        cur_source_key = None
        cur_sent_id = None
        cur_text = None
        cur_tokens = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.startswith("# source"):
                    cur_source = line.split(" = ", 1)[1] if " = " in line else ""
                    cur_source_key = source_to_key(cur_source)
                elif line.startswith("# sent_id"):
                    cur_sent_id = line.split(" = ", 1)[1].strip() if " = " in line else line
                elif line.startswith("# text"):
                    cur_text = line.split(" = ", 1)[1] if " = " in line else ""
                elif line == "":
                    if cur_tokens:
                        yield {
                            "source_key": cur_source_key,
                            "source_line": cur_source,
                            "sent_id": cur_sent_id,
                            "text": cur_text or "",
                            "tokens": cur_tokens,
                        }
                    cur_tokens = []
                    cur_sent_id = None
                    cur_text = None
                elif line.startswith("#"):
                    pass  # other comment lines ignored
                else:
                    parts = line.split("\t")
                    if len(parts) < 10:
                        continue
                    idx = parts[0]
                    # Skip multiword and empty-node lines
                    if "-" in idx or "." in idx:
                        continue
                    misc = parts[9]
                    ref_m = re.search(r"Ref=([^\|\s]+)", misc)
                    ref_raw = ref_m.group(1) if ref_m else ""
                    cur_tokens.append({
                        "id": int(idx),
                        "form": nfc(parts[1]),
                        "lemma": nfc(parts[2]) if parts[2] != "_" else nfc(parts[1]),
                        "upos": parts[3] if parts[3] != "_" else "X",
                        "xpos": parts[4] if parts[4] != "_" else "_",
                        "morph": parts[5] if parts[5] != "_" else "",
                        "head": int(parts[6]) if parts[6] != "_" else 0,
                        "udrel": parts[7] if parts[7] != "_" else "_",
                        "ref_raw": ref_raw,
                    })
            # handle final sentence if file doesn't end with blank line
            if cur_tokens:
                yield {
                    "source_key": cur_source_key,
                    "source_line": cur_source,
                    "sent_id": cur_sent_id,
                    "text": cur_text or "",
                    "tokens": cur_tokens,
                }

# ---- Vulgate ref parsing ----------------------------------------------------

_VULG_REF_RE = re.compile(r"^([A-Z0-9]+)_(\d+)\.(\d+)$")

def parse_vulgate_ref(ref_raw):
    """Parse 'MATT_1.1' -> ('MATT', 1, 1).  Returns None if not Vulgate format."""
    m = _VULG_REF_RE.match(ref_raw)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))
    return None

# ---- grouping ---------------------------------------------------------------

def group_sentences(conllu_paths):
    """
    Group sentences by (source_key, [book, chapter, verse for vulgate]).
    Returns a list of groups in encounter order.

    Each group is one of:
      - For Vulgate:
          {'type': 'verse', 'source_key': 'vulgate', 'book': str, 'chapter': int, 'verse': int,
           'sentences': [sent_dict, ...]}
      - For classical:
          {'type': 'classical', 'source_key': str, 'sentences': [sent_dict, ...]}
        (sentences are collected per-document-source)

    The Vulgate groups are assembled book -> chapter -> verse.
    Classical texts are one group per source_key (all their sentences together).
    """
    # We want to preserve canonical NT book order for Vulgate.
    # Collect: vulgate_data[book_code][chapter][verse] = [sentences]
    # classical_data[source_key] = [sentences]

    vulgate_data = {}   # {book_code: {chapter: {verse: [sent]}}}
    classical_data = {}  # {source_key: [sent]}

    for sent in parse_conllu_files(conllu_paths):
        sk = sent["source_key"]
        if sk == "vulgate":
            # Use the Ref from the FIRST token to establish the verse key.
            # (All tokens in a sentence have the same Ref in PROIEL data —
            # verified above.)
            first_ref = sent["tokens"][0]["ref_raw"] if sent["tokens"] else ""
            parsed = parse_vulgate_ref(first_ref)
            if parsed is None:
                # Fallback: shouldn't happen with this data, but be safe
                classical_data.setdefault("vulgate-other", []).append(sent)
                continue
            book, chap, verse = parsed
            if book not in vulgate_data:
                vulgate_data[book] = {}
            if chap not in vulgate_data[book]:
                vulgate_data[book][chap] = {}
            vulgate_data[book][chap].setdefault(verse, []).append(sent)
        else:
            classical_data.setdefault(sk, []).append(sent)

    return vulgate_data, classical_data

# ---- Walker (director) ------------------------------------------------------

def director(cv):
    stats = {
        "documents": 0,
        "books": 0,
        "chapters": 0,
        "verses": 0,
        "sentences": 0,
        "words": 0,
        "root_words": 0,
        "edge_pairs": 0,
    }

    conllu_paths = [
        CONLLU_DIR / "la_proiel-ud-train.conllu",
        CONLLU_DIR / "la_proiel-ud-dev.conllu",
        CONLLU_DIR / "la_proiel-ud-test.conllu",
    ]

    vulgate_data, classical_data = group_sentences(conllu_paths)

    # ---- 1. Vulgate NT document + book/chapter/verse/sentence/word ----------
    doc_node = cv.node("document")
    cv.feature(doc_node,
               text_source="vulgate",
               title=TEXT_SOURCE_TITLE["vulgate"])
    stats["documents"] += 1

    for book_code in NT_BOOK_ORDER:
        if book_code not in vulgate_data:
            continue
        bk = cv.node("book")
        cv.feature(bk,
                   book_code=book_code,
                   book_name=NT_BOOK_NAME.get(book_code, book_code),
                   text_source="vulgate")
        stats["books"] += 1

        for chap_num in sorted(vulgate_data[book_code]):
            ch = cv.node("chapter")
            cv.feature(ch,
                       book_code=book_code,
                       chapter=chap_num,
                       text_source="vulgate")
            stats["chapters"] += 1

            for verse_num in sorted(vulgate_data[book_code][chap_num]):
                vs = cv.node("verse")
                cv.feature(vs,
                           book_code=book_code,
                           chapter=chap_num,
                           verse=verse_num,
                           ref=f"{book_code}_{chap_num}.{verse_num}",
                           text_source="vulgate")
                stats["verses"] += 1

                verse_edge_pairs = []
                for sent in vulgate_data[book_code][chap_num][verse_num]:
                    sn = cv.node("sentence")
                    cv.feature(sn,
                               sent_id=sent["sent_id"],
                               sent_text=sent["text"],
                               text_source="vulgate",
                               ref=sent["tokens"][0]["ref_raw"] if sent["tokens"] else "")
                    stats["sentences"] += 1

                    local_map = {}
                    for tok in sent["tokens"]:
                        w = cv.slot()
                        is_root = 1 if tok["head"] == 0 else 0
                        cv.feature(w,
                                   form=tok["form"],
                                   lemma=tok["lemma"],
                                   upos=tok["upos"],
                                   xpos=tok["xpos"],
                                   morph=tok["morph"],
                                   udrel=tok["udrel"],
                                   is_root=is_root,
                                   syn_source="proiel-gold",
                                   text_source="vulgate")
                        local_map[tok["id"]] = w
                        stats["words"] += 1
                        if is_root:
                            stats["root_words"] += 1

                    for tok in sent["tokens"]:
                        if tok["head"] != 0 and tok["head"] in local_map and tok["id"] in local_map:
                            verse_edge_pairs.append((local_map[tok["id"]], local_map[tok["head"]]))

                    cv.terminate(sn)

                # Emit edges AFTER all sentence nodes are terminated
                for dep, gov in verse_edge_pairs:
                    cv.edge(dep, gov, head=None)
                    stats["edge_pairs"] += 1

                cv.terminate(vs)
            cv.terminate(ch)
        cv.terminate(bk)

    cv.terminate(doc_node)

    # ---- 2. Classical documents (sentence -> word only) ---------------------
    for source_key in ["caesar-bg", "cicero-att", "palladius", "cicero-off"]:
        if source_key not in classical_data:
            continue
        doc_node = cv.node("document")
        cv.feature(doc_node,
                   text_source=source_key,
                   title=TEXT_SOURCE_TITLE.get(source_key, source_key))
        stats["documents"] += 1

        doc_edge_pairs = []
        for sent in classical_data[source_key]:
            sn = cv.node("sentence")
            first_ref = sent["tokens"][0]["ref_raw"] if sent["tokens"] else ""
            cv.feature(sn,
                       sent_id=sent["sent_id"],
                       sent_text=sent["text"],
                       text_source=source_key,
                       ref=first_ref)
            stats["sentences"] += 1

            local_map = {}
            for tok in sent["tokens"]:
                w = cv.slot()
                is_root = 1 if tok["head"] == 0 else 0
                cv.feature(w,
                           form=tok["form"],
                           lemma=tok["lemma"],
                           upos=tok["upos"],
                           xpos=tok["xpos"],
                           morph=tok["morph"],
                           udrel=tok["udrel"],
                           is_root=is_root,
                           syn_source="proiel-gold",
                           text_source=source_key)
                local_map[tok["id"]] = w
                stats["words"] += 1
                if is_root:
                    stats["root_words"] += 1

            for tok in sent["tokens"]:
                if tok["head"] != 0 and tok["head"] in local_map and tok["id"] in local_map:
                    doc_edge_pairs.append((local_map[tok["id"]], local_map[tok["head"]]))

            cv.terminate(sn)

        for dep, gov in doc_edge_pairs:
            cv.edge(dep, gov, head=None)
            stats["edge_pairs"] += 1

        cv.terminate(doc_node)
        print(f"  {source_key}: done", flush=True)

    print(f"\nNODE COUNTS:")
    print(f"  document  {stats['documents']}")
    print(f"  book      {stats['books']}")
    print(f"  chapter   {stats['chapters']}")
    print(f"  verse     {stats['verses']}")
    print(f"  sentence  {stats['sentences']}")
    print(f"  word      {stats['words']}  (slots)")
    print(f"  is_root=1 {stats['root_words']}")
    print(f"  head edges {stats['edge_pairs']}")


# ---- Feature metadata -------------------------------------------------------

VERSION_STR = VERSION
GENERIC_META = dict(
    name="vulgate-latin",
    version=VERSION_STR,
    purpose=(
        "Latin Vulgate NT + classical Latin Text-Fabric "
        "(gold UD_Latin-PROIEL dependency treebank serialized to BHSA-ecosystem format; "
        "reference implementation of the harmonized upos/udrel cross-corpus layer)"
    ),
    source="UD_Latin-PROIEL (gold hand-annotated; CC BY-NC-SA 3.0)",
    writtenBy="readers-vulgate/5-machinery/scripts/build_tf.py",
)

OTEXT = {
    "fmt:text-orig-full": "{form} ",
    # Vulgate NT section hierarchy
    "sectionTypes": "book,chapter,verse",
    "sectionFeatures": "book_name,chapter,verse",
    # Structure: document > book/sentence
    "structureTypes": "document,book,chapter,verse,sentence",
    "structureFeatures": "title,book_name,chapter,verse,ref",
}

FEATURE_META = {
    # slot features
    "form": {"description": "surface form (NFC-normalized Unicode)"},
    "lemma": {"description": "lemma (PROIEL; NFC-normalized); falls back to form if absent"},
    "upos": {
        "description": (
            "UD universal POS — CANONICAL CROSS-CORPUS FEATURE. "
            "Same name/schema as BHSA (via mapping) and GNT Macula. "
            "Source: PROIEL manual annotation, converted to UD by Dag Haug."
        )
    },
    "xpos": {"description": "PROIEL native POS tag (language-specific; see PROIEL guidelines)"},
    "morph": {"description": "UD FEATS string (morphological features; '_' absent → stored as empty string)"},
    "udrel": {
        "description": (
            "UD dependency relation — CANONICAL CROSS-CORPUS FEATURE. "
            "Same name/schema as BoFM and GNT. "
            "Source: PROIEL manual annotation, converted to UD."
        )
    },
    "is_root": {"description": "1 if this token is the syntactic root of its sentence (head==0); 0 otherwise"},
    "syn_source": {"description": "provenance of syntactic annotation; always 'proiel-gold' for this corpus"},
    "text_source": {
        "description": (
            "source work key: vulgate | caesar-bg | cicero-att | palladius | cicero-off"
        )
    },
    # edge
    "head": {
        "description": (
            "dependency head edge (dep -> governor); absent for roots (is_root=1). "
            "Edge direction: dependent points TO governor (same as BHSA `mother` convention). "
            "Source: PROIEL gold annotation."
        )
    },
    # sentence features
    "sent_id": {"description": "original UD/PROIEL sent_id"},
    "sent_text": {"description": "original sentence text (# text comment)"},
    "ref": {
        "description": (
            "canonical reference: BOOKCODE_CHAPTER.VERSE for Vulgate (e.g. MATT_1.1); "
            "raw PROIEL Ref= value for classical texts"
        )
    },
    # book features
    "book_code": {"description": "NT book abbreviation code (e.g. MATT, JOHN, REV)"},
    "book_name": {"description": "NT book display name (e.g. Matthew, John, Revelation)"},
    "chapter": {"description": "chapter number (integer)"},
    "verse": {"description": "verse number (integer)"},
    # document features
    "title": {"description": "human-readable title of the source work"},
}

INT_FEATURES = {"chapter", "verse", "is_root"}


# ---- main -------------------------------------------------------------------

def main():
    out = TF_DIR / VERSION
    out.mkdir(parents=True, exist_ok=True)
    print(f"Building Vulgate Latin TF v{VERSION} -> {out}", flush=True)

    cv = CV(Fabric(locations=str(out), silent="deep"))
    ok = cv.walk(
        director,
        slotType="word",
        otext=OTEXT,
        generic=GENERIC_META,
        intFeatures=INT_FEATURES,
        featureMeta=FEATURE_META,
        # warn=None: suppress the "slot outside sections" warning that fires for classical
        # corpus tokens which are intentionally outside the Vulgate book/chapter/verse
        # section hierarchy.  The warning is expected: classical texts have no biblical
        # section refs; they live under document->sentence->word only.
        warn=None,
    )
    print("\nBUILD", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
