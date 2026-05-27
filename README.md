# readers-vulgate — Latin Vulgate colometric reader (SUBSTRATE-FIRST; not yet started)

Sibling to readers-tanakh / readers-gnt / readers-bofm. Part of the ATU (Atomic Thought
Unit) colometry program. **Operated by the unified orchestrator-Claude at `C:\Users\bibleman\`.**

## STATUS: substrate-assembly phase — NO ATU/sense-line work yet

Per the program's hard-won lesson (the BoFM over-merge ordeal, 2026-05-27): **do not draw
a single ATU boundary until the textual fabric reaches a parity threshold.** Sense-lining on
a thin/noisy parse produces systematic over-merges. Fabric first; superstructure second.
See `~/repos/atu-method/docs/substrate.md` (the Textual Fabric Doctrine) when written.

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
