# Vulgate Latin — Text-Fabric

A queryable [Text-Fabric](https://annotation.github.io/text-fabric/) representation of the
gold UD_Latin-PROIEL dependency treebank (Jerome's Vulgate NT + classical Latin companion texts),
in the same ecosystem format as BHSA (Hebrew) and the BoFM fabric — enabling cross-corpus
structural comparison (the ATU-convergence thesis).

Built by [`scripts/build_tf.py`](../../scripts/build_tf.py).
Regenerate: `python scripts/build_tf.py` (from repo root).
Validate: `python scripts/validate_tf.py 0.1`

## Load

```python
from tf.fabric import Fabric
api = Fabric(locations="data/tf", modules="0.1").load(
    "form lemma upos udrel is_root syn_source ref "
    "book_code chapter verse book_name text_source sent_text head"
)
F, L, E = api.F, api.L, api.E
```

## Source

UD_Latin-PROIEL (CC BY-NC-SA 3.0). Gold hand-annotated; converted to UD by Dag Haug.
Train/dev/test splits merged in canonical order: train first, then dev, then test.

Five source works in the treebank:

| `text_source` key | Work | Sentences | Words |
|---|---|---|---|
| `vulgate` | Jerome's Vulgate NT (all 27 books) | 11,784 | 109,517 |
| `cicero-att` | Epistulae ad Atticum (Cicero) | 3,895 | 47,090 |
| `caesar-bg` | Commentarii belli Gallici (Caesar) | 1,446 | 26,558 |
| `palladius` | Opus agriculturae (Palladius) | 955 | 14,882 |
| `cicero-off` | De officiis (Cicero) | 609 | 7,519 |

## Structure (version 0.1)

| node type | count | what |
|---|---|---|
| `document` | 5 | one per source work (`title`, `text_source`) |
| `book` | 27 | NT book (`book_code`, `book_name`) — Vulgate only |
| `chapter` | 243 | chapter (`chapter` int) — Vulgate only |
| `verse` | 6,510 | verse (`ref` = "BOOKCODE_CHAPTER.VERSE") — Vulgate only |
| `sentence` | 18,689 | one UD sentence (`sent_id`, `sent_text`, `ref`, `text_source`) |
| `word` (slot) | 205,566 | token + dependency layer |

Hierarchy:
- **Vulgate NT**: `document` > `book` > `chapter` > `verse` > `sentence` > `word`
- **Classical texts**: `document` > `sentence` > `word`

## Slot (word) features

| feature | description |
|---|---|
| `form` | NFC-normalized surface form |
| `lemma` | lemma (PROIEL; NFC-normalized) |
| `upos` | **UD universal POS** — canonical cross-corpus feature |
| `xpos` | PROIEL native POS tag |
| `morph` | UD FEATS string (e.g. `Case=Nom\|Gender=Masc\|Number=Sing`) |
| `udrel` | **UD dependency relation** — canonical cross-corpus feature |
| `is_root` | 1 if sentence root (head==0), 0 otherwise |
| `syn_source` | `"proiel-gold"` (provenance; gold hand-annotation) |
| `text_source` | work key (see table above) |
| `head` | EDGE dep->governor within sentence (absent for roots) |

## Biblical references

Vulgate token refs follow the scheme `BOOKCODE_CHAPTER.VERSE` (e.g. `MATT_1.1`, `REV_22.21`).
Book codes are standard abbreviations (MATT, MARK, LUKE, JOHN, ACTS, ROM, 1COR, ..., REV).
Classical token refs are the raw PROIEL Ref= values (e.g. `1.1.1` for Caesar Gall. 1.1.1).

## Cross-corpus harmonization

`upos` and `udrel` are the two canonical harmonized features shared across all corpora
in this project. A single cross-corpus query like `upos=VERB udrel=nsubj` returns
comparable hits in Vulgate Latin, BoFM English, and (future) GNT Greek.

This TF is the **reference implementation** of that harmonization layer: its annotations
are gold (PROIEL hand-annotated, UD-converted), so it is the calibration target for the
weaker substrates (BoFM Stanza parse; LXX partial syntax).
