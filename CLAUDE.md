# Latin Vulgate Reader — Claude Code Instructions (thin stub)

Operated by the **unified orchestrator-Claude** at `C:\Users\bibleman\`. If you spawned in
this workspace, hand off to the user-home Claude (it has full cross-repo + substrate context).

**STATUS: substrate-assembly phase. NO ATU/sense-line work until the Latin textual fabric
reaches parity** (see `README.md` + `~/repos/atu-method/docs/03-implementation/substrate.md` — the Textual Fabric Doctrine). Fabric first.

**Substrate ACQUIRED 2026-05-27:** `UD_Latin-PROIEL` = **gold dependency treebank for the entire Vulgate NT** (all 27 books, Jerome's Vulgate, 11,784 sentences) — local at `readers-vulgate/private/substrate/` (this repo's gitignored folder — relocated 2026-05-27 from the shared `biblical-corpora/` container, "each project gets its intuitive data"). Plus Perseus-AGDT Revelation (2nd gold layer), LASLA/ITTB/LLCT (parser diversity). Vulgate-OT: no gold treebank exists (NT-first confirmed). **Only build step = a ~1-day CoNLL-U→Text-Fabric converter.** Full inventory: `research/SUBSTRATE-INVENTORY.md`.

- What this is: a colometric ATU reading edition of the Latin Vulgate (NT first; OT deferred —
  no gold OT substrate). Sibling to readers-tanakh/gnt/bofm.
- Substrate plan + resource inventory + the hybrid pipeline: `README.md`.
- Cross-corpus methodology canon: `~/repos/atu-method/docs/`. The method is a **Container, not
  an Originator** — it organizes what the fabric supports; fabric quality bounds the claims.
- GIGO guardrail (BoFM-2026-05-27 lesson): a source-language-anchored projection is a candidate,
  NOT target gold; validate each projected break on the Latin bidirectional ATU test.
