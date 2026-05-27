# Latin Substrate Inventory — Vulgate Reader Acquisition Report

**Date acquired:** 2026-05-27
**Scope:** Latin NT treebanks for Vulgate reader substrate. Scope v1 = NT only (no gold Vulgate-OT treebank is known to exist — confirmed by survey of all current UD Latin treebanks; none contain OT material).
**Landing directory:** `C:\Users\bibleman\repos\biblical-corpora\latin-substrate\`

---

## Resource Table

| Name | Verified? | License (quoted) | Format | Size on disk | Coverage — Vulgate content | WHERE IT LANDED / ACQUIRE STEPS | Gold / Projected / Raw |
|------|-----------|-----------------|--------|-------------|---------------------------|----------------------------------|------------------------|
| **UD_Latin-PROIEL** | YES | "CC BY-NC-SA 3.0" | CoNLL-U (.conllu) — 3 splits (train/dev/test) | 22 MB | GOLD. 27 NT books (all Pauline epistles, Gospels, Acts, Hebrews, Catholic epistles, Revelation — the entire NT). 11,784 sentences explicitly sourced as "Jerome's Vulgate, [Book] [ch]". Stats.xml: 18,689 sentences / 205,566 tokens total treebank; majority is Vulgate NT. Full morph + Universal Dependencies syntax. Source: University of Oslo PROIEL project, converted to UD by Dag Haug (April 2018 release). | `C:\Users\bibleman\repos\biblical-corpora\latin-substrate\UD_Latin-PROIEL` (ACQUIRED) | **GOLD** — hand-tagged morph + dependency syntax |
| **treebank_data (Perseus AGDT v2.1 Latin)** | YES | "Creative Commons Attribution-ShareAlike 3.0 United States License" | XML treebank format (v2.1 .tb.xml); parallel CoNLL-U in UD_Latin-Perseus (see below) | 399 MB (full repo incl. Greek + all versions) | GOLD (independent annotation layer). Contains `tlg0031.tlg027.perseus-lat1.tb.xml` = Vulgate **Revelation** (Jerome). 618 sentences / ~9,309 words, annotated by Tufts students + Anastasia Mellano (released 2015-04-07), supervised by Celano/Crane/Leipzig. **This is a second independent gold annotation of Revelation, cross-validatable against PROIEL.** Other NT books: NOT present in this treebank. | `C:\Users\bibleman\repos\biblical-corpora\latin-substrate\treebank_data` (ACQUIRED) | **GOLD** — hand-tagged morph + dependency syntax (different annotation school from PROIEL) |
| **UD_Latin-Perseus** | YES | "CC BY-NC-SA 2.5" | CoNLL-U (.conllu) — 2 splits | 3.5 MB | GOLD (UD conversion of Perseus AGDT). 155 sentences from Vulgate Revelation (subset of the 618 in raw XML, split into train only). 29,138 tokens total across 11 texts including Jerome's Vulgata. No other NT books. | `C:\Users\bibleman\repos\biblical-corpora\latin-substrate\UD_Latin-Perseus` (ACQUIRED) | **GOLD** (UD conversion of hand-tagged AGDT) |
| **UD_Latin-ITTB** | YES | "CC BY-NC-SA 3.0" | CoNLL-U (.conllu) — 3 splits | 52 MB | NO Vulgate or NT content. Medieval Latin: Thomas Aquinas (Summa contra gentiles, Books 1-4) + 61 related authors. 450,515 tokens. Value: parser-training base for ecclesiastical Latin syntax (Medieval Latin prose style closest to Jerome's Vulgate register). | `C:\Users\bibleman\repos\biblical-corpora\latin-substrate\UD_Latin-ITTB` (ACQUIRED) | **GOLD** — hand-tagged morph + syntax (Index Thomisticus) |
| **UD_Latin-LLCT** | YES | "CC BY-SA 4.0" | CoNLL-U (.conllu) — 3 splits | 26 MB | NO Vulgate or NT content. Early Medieval Latin: 521 legal charters from Tuscany, 774-897 AD. 242,411 tokens. Value: sub-classical Latin period coverage; parser-model diversity for non-CRF Latin. | `C:\Users\bibleman\repos\biblical-corpora\latin-substrate\UD_Latin-LLCT` (ACQUIRED) | **GOLD** — hand-tagged |
| **LASLA (CIRCSE/LASLA)** | YES | "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" | CoNLL-U Plus (.conllup), Turtle RDF (.ttl), TSV; 242 conllup files + complete_lasla.ttl.gz | 889 MB | NO Vulgate or NT content. Classical pagan Latin only: Caesar, Cato, Catullus, Cicero (60+ works), Curtius, and others. IMPORTANT: The GitHub repo contains the LASLA-LiLa **linkage layer** (morph annotation + LiLa KB links). The underlying raw LASLA corpus texts themselves "are available through data-sharing agreements" at lasla.be — but the CoNLL-U Plus annotation files in this repo are directly downloadable and usable. Value: the LASLA annotation layer is the standard classical Latin morph-tag schema (manually verified, ~1.8M words); the conllup files provide that annotation in a usable format. No sign-up gate for the GitHub repo itself. | `C:\Users\bibleman\repos\biblical-corpora\latin-substrate\LASLA` (ACQUIRED — 889 MB, just under 1 GB threshold) | **GOLD** — manually verified morph annotation (no dependency syntax) |
| **LiLa Knowledge Base** | YES (verified as live LOD service) | Open Linked Data (CC); endpoint publicly queryable | SPARQL / RDF — NOT a downloadable file corpus | N/A — online service | Registers and links LASLA, PROIEL, ITTB, Perseus, and other Latin corpora at the lemma level. Allows cross-corpus lemma lookup and interoperability queries. NO bulk download. | REPORT-DON'T-ACQUIRE. SPARQL endpoint: `https://lila-erc.eu/sparql` (Virtuoso endpoint; also accessible via `https://lila-erc.eu/query/` UI). Example query: find all occurrences of a lemma across LASLA + PROIEL. | N/A — interoperability layer |

---

## Notes

### OT coverage question
**Confirmed: no gold Vulgate-OT treebank is known to exist.** The survey of all six current Universal Dependencies Latin treebanks (PROIEL, ITTB, LLCT, Perseus, UDante, Latin) plus the Perseus AGDT v2.1 finds zero OT Vulgate annotations. The LASLA corpus (pure classical) and ITTB (Aquinas) also have no OT content. Scope v1 = NT only is correct and fully supported by what exists.

### PROIEL is the primary Vulgate substrate
UD_Latin-PROIEL is the only resource with full-NT coverage. It covers all 27 NT books with sentence-level attribution ("Jerome's Vulgate, [Book] [ch]"). 11,784 of the 18,689 total sentences are Vulgate NT. CoNLL-U format provides: word form, lemma, UPOS, XPOS (PROIEL tags), morph features, dependency head, dependency relation. This is the direct pipeline input for ATU work.

### Perseus AGDT Revelation = independent cross-validation layer
The Perseus treebank annotates Revelation using a different annotation school (Perseus/Leipzig guidelines v1.3, 2015) vs. PROIEL (Oslo PROIEL guidelines, 2018). 618 sentences of Revelation in XML, 155 in UD CoNLL-U. Use for cross-validation on the Revelation subset; do not expect identical dependency labels.

### LASLA note
LASLA in this repo is the **linkage layer** (lemma IDs, morph tags, LiLa KB URIs) — not the original running text. The running text requires a data-sharing agreement with LASLA (Liège). The CoNLL-U Plus files are usable for morph-tag schema reference and lemma interop but should not be treated as a standalone corpus for training without reading the LASLA data-sharing terms.

### LiLa SPARQL access
- UI: `https://lila-erc.eu/query/`
- Endpoint (direct): `https://lila-erc.eu/sparql`
- Example query (find lemma form cross all corpora): query for `lila:LemmaBank` URIs with owl:sameAs links to LASLA + PROIEL lemma entries
- No bulk download available or needed; use for lemma-ID interop between the locally-acquired corpora.

### What is NOT here
- No Vulgate OT treebank (does not exist as of 2026-05-27)
- No projected annotation (Greek-to-Latin projection) — none was found in the surveyed resources; all annotation here is gold or gold-converted
- PROIEL upstream (full XML, richer features than UD conversion): available at `https://github.com/proiel/proiel-treebank` — not acquired but the UD conversion captures all fields needed for ATU substrate work
- UDante (Dante's Latin works, not relevant): skipped as out-of-scope

---

## Acquisition summary

| Repo | Path | Size |
|------|------|------|
| UD_Latin-PROIEL | `latin-substrate\UD_Latin-PROIEL` | 22 MB |
| treebank_data (Perseus AGDT) | `latin-substrate\treebank_data` | 399 MB |
| UD_Latin-Perseus | `latin-substrate\UD_Latin-Perseus` | 3.5 MB |
| UD_Latin-ITTB | `latin-substrate\UD_Latin-ITTB` | 52 MB |
| UD_Latin-LLCT | `latin-substrate\UD_Latin-LLCT` | 26 MB |
| LASLA | `latin-substrate\LASLA` | 889 MB |
| **Total** | | **~1.39 GB** |

All are depth-1 git clones. All licenses are non-commercial (CC BY-NC-SA 3.0/4.0 or CC BY-SA 3.0/4.0) — compatible with non-commercial research use.
