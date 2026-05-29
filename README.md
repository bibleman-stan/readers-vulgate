# readers-vulgate — Latin Vulgate colometric reader

Sibling to readers-tanakh / readers-gnt / readers-bofm. Part of the ATU (Atomic Thought
Unit) colometry program. **Operated by the unified orchestrator-Claude at `C:\Users\bibleman\`.**

## Reader site — v1.5 DRAFT (deploy target: vulgate-reader.com, GitHub Pages)

A web reader ported from gnt-reader (same look / CSS / layout / UX). Latin Vulgate ATU lines
with the Douay-Rheims (1582 Rheims NT) English, and a **bilingual search** that matches either
layer (each result shows which layer hit).

- **Latin text + ATU segmentation:** the v1.5 mechanical generator (`scripts/vulgate_generate.py`)
  over the gold UD_Latin-PROIEL Text-Fabric at `data/tf/0.1`. This is a **pre-editorial draft**
  (segmentation pending a §7.3 audit). Known v1.5 bug: beatitudes Matt 5:3 & 5:10 are wrongly
  fused — *not* fixed in this build.
- **English:** Original Douay-Rheims (CC0), cloned to `private/original-douay-rheims/` (gitignored).
  Verse-level layer for this first build (whole DR verse under the verse's first ATU line).
- **Coverage:** the PROIEL Vulgate TF is gold but PARTIAL — Gospels/Acts/Revelation near-complete,
  Epistles sampled. 6,510 Latin verses emitted; 6,505 (99.9%) align with DR. Five versification
  mismatches (Matt 17:27, John 11:57, 2 Cor 1:24 & 7:18, 3 John 1:15). See `research/dr-coverage.json`.

**Build:** `scripts/build_content.py` (Latin + DR text-files) → `scripts/build_books.py`
(→ `books/*.html`). `index.html` + `sw.js` are the web app. Deferred: per-ATU English interleave,
a Latin lemma index for inflected-form search, an editorial v2/v3 pass, the empty interior
chapters of the few sampled epistles.

## Substrate doctrine (governs editorial refinement of the draft above)

Per the program's hard-won lesson (the BoFM over-merge ordeal, 2026-05-27): the v1.5 reader is
a **mechanical draft**, deployed-then-refined. Because the Latin fabric here is GOLD
(hand-tagged PROIEL syntax), the v1.5 mechanical layer is on solid substrate — but the ATU
boundaries are still a draft requiring an editorial pass before any "final" claim. Fabric
quality bounds the claims. See `~/repos/atu-method/docs/substrate.md` (the Textual Fabric Doctrine).

## Substrate plan (assemble + VERIFY before any colometry)

The Latin fabric is in **good shape** — assemble it; the leads below are from a 2026-05-27
resource sweep and are **UNVERIFIED until pulled** (confirm license/format/coverage on
acquisition — do not assume).

| Resource | Provides | License (verify) | Format | Status |
|---|---|---|---|---|
| **PROIEL Latin NT** | hand-tagged morph + dependency syntax, NT | CC BY-NC-SA | CoNLL-U (UD_Latin-PROIEL) | gold layer 1 |
| **Perseus AGDT — Jerome's Vulgate** | 2nd independent hand-tagged Vulgate sample (cross-validate gold-vs-gold) | check | AGDT XML | gold layer 2 |
| **LASLA** (~1.8M words Classical Latin) | manually-verified morph+syntax; the parser training base | CC BY-NC-SA 4.0 | CoNLL-U (Zenodo/CIRCSE) | training base |
| **ITTB** (Aquinas, medieval Latin) | parser models + valency lexicon transfer to Vulgate prose | check | UD_Latin-ITTB | aux |
| **LiLa Knowledge Base** | interop: every lemma a URI; SPARQL across LASLA/PROIEL/ITTB/Perseus | LOD | SPARQL | interop layer |
| LEMLAT3 / Frankfurt Latin Lexicon (medieval) | lexical verification (FLL bridges classical↔ecclesiastical) | check | — | lexical |
| Stanza Latin / LatinCy / Collatinus | mechanical parser (first pass) | open | CoNLL-U | parser |

**OT gap:** no Vulgate-OT equivalent to PROIEL exists. **Scope v1 to the NT**; treat the OT
as a separate substrate-building project.

## Hybrid annotation pipeline (substrate-build → v0/v1)

1. **Mechanical parse** (Stanza/LatinCy/Collatinus) — baseline on every token.
2. **Gold-check** where hand-tagged (PROIEL NT, Perseus-Jerome) — confidence map.
3. **Alignment-projection** (Vulgate↔Greek-NT via PROIEL) — **GIGO CAVEAT** (BoFM lesson): a
   source-language-anchored projection is a *candidate*, NOT target gold; each projected break
   must pass the Latin bidirectional ATU test before it's a boundary.
4. **LLM (Claude) adjudication** — adjudicate between layers, propose ATU breaks + justify;
   NEVER generate morph/syntax from scratch (confabulation = loss of Container-Not-Originator).
   Every token carries provenance (source + confidence).

## Methodology
Cross-corpus canon: `~/repos/atu-method/docs/`. The method is a **Container, not an Originator**
— it organizes what the fabric supports; fabric quality bounds the claims.
