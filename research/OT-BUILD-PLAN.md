# Vulgate OT — substrate build plan (decisions settled 2026-05-27)

The NT fabric is done (gold UD_Latin-PROIEL → TF v0.1). The OT has **no gold treebank** — same shape
as BoFM (have text, no syntax), but the best-case version: our in-domain training data is the
Vulgate *NT* treebank we already hold (Jerome → Jerome, minimal register gap).

## DECISION — edition: **Clementine Vulgate** (public domain)

Rationale, in priority order:
1. **License (decisive).** The Clementine Text Project (2002–2005) released the Clementine Vulgate to
   the **public domain** (via vulsearch.sourceforge.net; GitHub converters exist). Stuttgart/Weber-Gryson
   (critical ed.) and Nova Vulgata are **copyright** — non-redistributable in our PUBLIC TF repos. Our
   whole program ships TFs publicly → the text must be PD → Clementine.
2. **Completeness.** Clementine carries the full OT incl. deuterocanonicals — a complete Vulgate fabric.
3. **Availability/tooling.** Clean PD digital text + converters already exist; best-supported PD Vulgate.
4. **NT-consistency caveat (managed, NOT blocking).** Our NT TF is PROIEL-based (its exact Vulgate base is
   unspecified in the PROIEL/UD docs — likely a critical text). Clementine-OT + PROIEL-NT is a mild
   edition seam, acceptable because: OT/NT don't overlap (nothing to be inconsistent *about*); the parser
   learns edition-agnostic Latin *syntax*; and edition is recorded as provenance (§9). A single-edition
   NT+OT could be re-derived later (re-parse a Clementine-NT) if ever wanted.

## DON'T-REINVENT SURVEY — result: no existing tagged/treebank Vulgate-OT to acquire

- **Text:** PD Clementine available (Clementine Text Project / vulsearch / jrichter converter). ACQUIRE.
- **Morphology:** no OPEN tagged Vulgate-OT exists. The Logos "Analytical Lexicon of the Vulgate" is
  **commercial** (unusable). LiLa (Linking Latin) does **not** yet include the Vulgate. → BUILD (tag ourselves).
- **Syntax:** no gold Vulgate-OT treebank (confirmed). → BUILD (parse ourselves).
So: acquire the PD text; build morph + syntax. Clean diligence — nothing to reinvent, nothing to acquire
beyond the raw text.

## BUILDING BLOCKS + PIPELINE (stages 4–5 are already built — reuse)

0. **Text (v0):** acquire PD Clementine OT, verse-keyed; record edition as provenance.
1. **Morph + lemma:** Stanza-Latin / CLTK (both trained on gold UD Latin) → UPOS, lemma, morph. (off-the-shelf RUN)
2. **Syntax:** Tier A = off-the-shelf **Stanza-Latin** (trained on PROIEL incl. the Vulgate NT) → parse OT.
   Tier B (only if the slice-audit needs it) = fine-tune on the **PROIEL Vulgate-NT subset** (Jerome register).
3. **Provenance + register-audit:** `syn_source` per token (stanza-latin / proiel-tuned, distinct from the
   NT's `proiel-gold`); hand-audit a gold OT slice (Genesis 1 / a Psalm) — no gold OT exists, so this is the
   GIGO gate before trusting the parse into the fabric (§8). Expected to pass easily (Jerome→Jerome).
4. **Serialize → TF:** REUSE `readers-vulgate/scripts/build_tf.py` (already §9-hardened: NFC, is_root, head
   edge, canonical upos/udrel, provenance, validation). The OT **extends the same Vulgate TF** — feed OT
   CoNLL-U with the `BOOK_CHAPTER.VERSE` ref scheme; OT books merge alongside the NT.
5. **Validate** (round-trip + edge-integrity), then sense-line (ATU) when the Vulgate reader is built.

So the real OT work is stages 0–3 (text → tag → parse → CoNLL-U); the fabric-build is plumbing we have.

Sources: Clementine Text Project (vulsearch.sourceforge.net); github.com/jrichter/ClementineVulgateConverter;
UD_Latin-PROIEL (universaldependencies.org/treebanks/la_proiel); LiLa (sighum / lila-erc.eu).
