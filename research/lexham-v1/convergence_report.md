# Genesis convergence analysis — Vulgate, Tanakh, LXX

Cross-corpus comparison of atomic-text-unit (ATU) counts across the Hebrew Masoretic Text, the Septuagint, and the Latin Vulgate for Genesis, mediated against a published Latin discourse segmentation. Source: `vulgate_convergence_genesis.json` (1,525 verses).

---

## 1. Headline aggregates

| Metric | Value |
|---|---|
| Verses compared | **1,525** |
| Full agreement (T = L = V) | **372 (24.4%)** |
| Vulgate-finer-but-predictable | **111 (7.3%)** |
| Genuine Vulgate divergence | **355 (23.3%)** |
| Tanakh-vs-LXX source-side disagreement | **612 (40.1%)** |
| LXX projection fallback | **75 (4.9%)** |

A **convergent baseline of 31.7%** is set by full agreement plus predictable Vulgate-finer cases. The largest single bucket is not Vulgate divergence at all — it is source-text disagreement between MT and LXX, which sets a hard upper bound on three-way convergence.

---

## 2. Methodology

**T** — Tanakh reader's mechanical segmentation of BHSA clause-atoms with binding rules. **L** — LXX colometric reader's segmentation, projected onto MT numbering via a CATSS-style alignment table; where projection fails (75 verses) the verse is flagged `lxx_fallback`, L = 1. **V_raw** — proposition count from the Lexham Latin Discourse Genesis edition, one line per ATU; finer than Hebrew/Greek granularity because it splits fronted topic-NPs from predicating clauses and explodes coordinated lists into one line per coordinand. **V_merged** — applies one mechanical rule:

> **Topic-merge:** When proposition *n* is a fronted topic/subject and *n+1* carries the predicating verb attached to it, merge.

This recovers the clause-as-atom granularity used by the Hebrew and Greek pipelines.

**Classification statuses:** `full_agreement` (T = L = V_merged); `vulgate_finer_predictable` (V_raw > T = L, V_merged = T = L); `vulgate_diverges` (V_merged ≠ T = L); `tanakh_lxx_diverge` (T ≠ L); `lxx_fallback` (projection failed; comparison reduces to T-vs-V).

---

## 3. Patterns observed in the convergence

- **Topic + predicate pairs are the dominant predictable split.** The Latin edition routinely separates a fronted nominal topic ("Terra autem…", "spiritus Dei…") from its predicating verb. 81 of 111 predictable cases close on one such pair (ratio 2:1); 28 more close on two pairs.
- **Speech-frame + speech-content does not need merge.** Hebrew, Greek, and Latin pipelines all treat "Dixitque Deus:" as one ATU and the quoted content as the next. Full agreement dominates the speech-heavy chapters (Gen 18, 24, 27, 31).
- **Short narrative event-chains converge cleanly** — one ATU per finite clause across all three.
- **Genealogies converge at the highest rate of any genre.** Gen 10, 11, 36 show T-vs-L agreement at 94%, 84%, 93%, with most Vulgate-finer cases absorbed by the same Topic-merge.

---

## 4. Patterns observed in the divergence

The 355 genuine-divergence verses cluster on a small number of features.

- **Coordinand-list explosion is the single largest class.** ~70% of high-magnitude divergences (|V_merged − T| ≥ 5) are verses where one Hebrew/Greek clause governs a long Latin list of coordinated NPs, each rendered as its own line. 13 of the top 15 fit this shape.
- **Embedded apposition in covenantal language** — Vulgate expands Hebrew construct chains into multiple coordinated Latin relative clauses (Gen 9, 15, 17, 28).
- **Place-name and proper-noun list-explosion.** Gen 10:10 is one MT/LXX atom and six Latin lines.
- **Stacked background-temporal frames at verse-head** — adverbial preambles get their own proposition; Topic-merge does not cover this (the relation is not subject–predicate).
- **Speech-attribution chains** — speech-verb + embedded subject + vocative + quoted content can produce three or four Latin lines where Hebrew has one frame.

A future binding rule keyed on *consecutive Latin propositions sharing one governing finite verb, all but the first being bare NPs joined by* et would close the bulk of this class.

---

## 5. Named-residual — top 10 genuinely-divergent verses

Ordered by |V_merged − T|. Latin proposition lines slashed; one-line structural note follows.

| Verse | T | L | V | Latin propositions / structural note |
|---|---|---|---|---|
| **36:6** | 2 | 2 | 10 | *Tulit autem Esau / uxores suas / et filios / et filias / et omnem animam domus suæ / et substantiam / et pecora / et cuncta / quæ habere poterat in terra Chanaan / et abiit in alteram regionem.* — eight-element household list under one MT clause |
| **50:23** | 2 | 2 | 10 | *locutus est fratribus suis / Post / mortem / meam / Deus / visitabit vos / et ascendere vos faciet / de terra ista / ad terram quam juravit / Abraham / Isaac / et Jacob.* — fronted temporal phrase + relative oath-clause + three-name patriarchal list |
| **7:13** | 1 | 1 | 7 | *In articulo diei illius / ingressus est Noë / et Sem, et Cham, et Japheth filii ejus / uxor illius / et tres uxores filiorum ejus / cum eis / in arcam.* — temporal frame + five-element family list |
| **12:16** | 2 | 2 | 8 | *Abram vero / bene usi sunt propter illam / fueruntque ei / oves et boves / et asini / et servi et famulæ / et asinæ / et cameli.* — five-coordinand possession list |
| **19:16** | 2 | 2 | 8 | *Dissimulante illo / apprehenderunt / manum ejus / et manum uxoris / ac duarum filiarum ejus / eo quod parceret Dominus illi / Eduxeruntque eum / et posuerunt extra civitatem.* — three coordinated objects + causal subordinate |
| **45:10** | 2 | 2 | 8 | *…habitabis in terra Gessen / erisque juxta me / tu / et filii tui / et filii filiorum tuorum / oves tuæ / et armenta tua / et universa quæ possides.* — six-element invitation list |
| **46:5** | 2 | 2 | 8 | *Surrexit autem Jacob a Puteo juramenti / tuleruntque / eum / filii / cum parvulis / et uxoribus suis / in plaustris / quæ miserat Pharao.* — agent + object + accompaniment + instrument + relative |
| **1:26** | 3 | 3 | 8 | *et ait / Faciamus hominem ad imaginem et similitudinem nostram / et præsit / piscibus maris / et volatilibus cæli / et bestiis / universæque terræ / omnique reptili, quod movetur in terra.* — speech-frame + image-clause + dominion governing five-element domain list |
| **6:18** | 2 | 2 | 7 | *Ponamque fœdus meum tecum / et ingredieris arcam / tu / et filii tui / uxor tua / et uxores filiorum ejus / tecum.* — covenant + ark-entry with four family categories |
| **7:7** | 1 | 1 | 6 | *Et ingressus est Noë / et filii ejus / uxor ejus / et uxores filiorum ejus / cum eo in arcam / propter aquas diluvii.* — agent + three coordinated subjects + accompaniment + reason |

Common signature: **coordinand-list explosion inside a single source-clause is the principal residual divergence class.**

---

## 6. Tanakh-vs-LXX byproduct

40.1% of Genesis verses (612 of 1,525) show source-side disagreement before the Vulgate is consulted — the largest bucket and a sanity-check on LXX deploy quality.

- **MT finer in 61% (372); LXX finer in 39% (240).** Consistent with the LXX translator's tendency to compress Hebrew nominal predications into Greek participials.
- **Vulgate splits its allegiance.** V_merged matches MT in 180, LXX in 171, neither in 261 — expected for a tradition working from a Hebrew Vorlage with Old Latin consultation.
- **Dense but shallow.** 73% of cases differ by one atom; only 7% by three or more.
- **Clusters in dialogue chapters.** Top T-vs-L rates: Gen 43 (74%), 32 (69%), 48 (64%), 44 (59%), 31 (58%) — speech-heavy reconciliation/negotiation passages.
- **Genealogies converge cleanly.** Gen 10 (6%), 36 (7%), 11 (16%) — lowest in the book.
- **75 fallback verses** concentrate in Gen 31, 7, 23, 27, 49 — chapters with known LXX additions or numbering offsets; expected residual.

---

## 7. Methodology note — Path B, and why role labels are private

**Path B** is the working name for the track represented here: *use a published third-party segmentation of the Latin (the Lexham Discourse Latin Bible) as an independent witness against which the mechanically-derived Hebrew and Greek ATUs can be cross-validated.* **Path A**, the standard track, derives the Latin segmentation mechanically from the UD_Latin-PROIEL treebank using the binding-rule machinery used for the other corpora — and is the deployed track for the Vulgate New Testament. Path B runs on Genesis as a convergence check: if the Lexham segmentation and a mechanical pipeline converge on most verses after a single Topic-merge rule, that is independent evidence the analytical instrument is measuring something real and reproducible across methods. The 31.7% baseline plus the 23.3% well-characterized residual is the answer.

**Role labels are private.** The Lexham edition assigns one of approximately forty discourse-functional categories to each proposition; these are the proprietary analytical product of the Lexham editors and are not redistributed here. This report describes patterns in our own vocabulary — *coordinand-list explosion, topic-predicate split, speech-frame, embedded apposition* — and uses Lexham labels only as internal parser landmarks. Proposition text itself is quoted under fair-use scholarly comment. The Lexham source lives in `private/lexham-exports/` (gitignored); per-chapter extracts in `research/lexham-v1/01-genesis/` carry Latin lines only.
