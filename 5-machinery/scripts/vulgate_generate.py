#!/usr/bin/env python3
"""Vulgate-native ATU generator: ports the readers-gnt nesting-based engine
(5-machinery/scripts/sblgnt_generate.py) onto the gold UD_Latin-PROIEL Text-Fabric at
data/tf/0.1.

ARCHITECTURE (ported, not re-invented)
--------------------------------------
Each word is assigned to the innermost clause-head in its governor chain that
is an ATU-ROOT. A clause-head STANDS (is its own ATU root) unless it BINDS to
its governor:

  STAND  = is_root, OR udrel in {conj, parataxis}, OR a FINITE advcl.
  BIND   = acl / acl:relcl (relative + other adnominal), ccomp, xcomp,
           csubj/csubj:pass, and a NON-FINITE advcl (participle / infinitive /
           gerund frame). These ride with their governor's ATU.

  finite(w) = "VerbForm=Fin" in morph, OR (upos in {VERB,AUX} and no
              VerbForm=Part/Inf/Ger/Gdv in morph).

The UD treebank's `head` edge (dep -> governor) gives each word a chain to the
sentence root; the innermost STANDING clause-head on that chain is the word's
ATU. Function/connective words ride their surface-adjacent content word's ATU.

TWO REFINEMENT RULES (ports of validated sibling-corpus rules, applied over the
naive baseline above)
----------------------------------------------------------------------------
R1  FINITE FRAME -> directional bind. A finite advcl is a frame, not a free
    clause. If it PRECEDES its governing main clause in surface order
    (temporal/conditional/concessive: "cum sedisset...", "si...") it BINDS
    FORWARD into the main clause's ATU. If it FOLLOWS its head
    (causal/result/purpose: "quoniam...", "ut...") it keeps its own ATU.
    => fixes the naive over-split of "cum sedisset" as a 1-word line.

R2  conj-FRAGMENT vs conj-CLAUSE. A conj member STANDS only if it carries its
    OWN predication (a finite verb anywhere in its subtree). A conj member with
    NO finite verb in its subtree (a gapped coordinate PP/NP sharing the prior
    predicate: "neque ex sanguinibus / neque ex voluntate carnis / sed ex Deo")
    BINDS BACK into the prior ATU.
    => fixes the naive over-split of John 1:13.

This is a FIRST-PASS measurement draft. Not deployed, not committed.

Usage:
  cd C:/Users/bibleman/repos/readers-vulgate
  PYTHONIOENCODING=utf-8 python 5-machinery/scripts/vulgate_generate.py MATT 5
"""
import sys
from tf.fabric import Fabric

TF_LOCATION = "C:/Users/bibleman/repos/readers-vulgate/data/tf"
TF_MODULE = "0.1"

# Clause-head relations whose head sits OUTSIDE the clause it heads (i.e. the
# word at that relation is the top of a sub-clause).
BIND_RELS = {"acl", "acl:relcl", "ccomp", "xcomp", "csubj", "csubj:pass"}
STAND_RELS = {"root", "conj", "parataxis"}
# advcl is conditional: finite advcl STANDS (then R1 may redirect); non-finite
# advcl BINDS. advcl:cmp (comparative) is treated like advcl.

_NONFINITE_VF = ("VerbForm=Part", "VerbForm=Inf", "VerbForm=Ger", "VerbForm=Gdv")

_api = None  # cached TF api


def load_api():
    global _api
    if _api is None:
        TF = Fabric(locations=TF_LOCATION, modules=TF_MODULE, silent="deep")
        _api = TF.load(
            "form lemma upos udrel morph is_root verse chapter "
            "book_code book_name ref sent_id head",
            silent="deep",
        )
    return _api


def _morph(api, w):
    return api.F.morph.v(w) or ""


def _person_num(api, w):
    """(Person, Number) feature pair from a word's morph, for detecting whether a
    coordinate shares its conjunct's subject."""
    p = n = ""
    for tok in _morph(api, w).split("|"):
        if tok.startswith("Person="):
            p = tok
        elif tok.startswith("Number="):
            n = tok
    return (p, n)


def is_finite(api, w):
    """A word is a finite predicate if its FEATS carry VerbForm=Fin, or it is a
    VERB/AUX with no non-finite VerbForm tag (defensive: a finite verb missing
    the explicit tag still counts; a participle/infinitive never does)."""
    m = _morph(api, w)
    if "VerbForm=Fin" in m:
        return True
    if api.F.upos.v(w) in ("VERB", "AUX"):
        return not any(t in m for t in _NONFINITE_VF)
    return False


def is_clause_head(api, w):
    """A word that heads its own clause: the sentence root, a coordinate/
    parataxis member, an adverbial clause, a relative/adnominal clause, or a
    complement/open-complement/clausal-subject. These are the nodes that can be
    ATU roots or bind to a governor."""
    rel = api.F.udrel.v(w)
    if api.F.is_root.v(w) == 1:
        return True
    if rel in STAND_RELS or rel in BIND_RELS:
        return True
    if rel in ("advcl", "advcl:cmp"):
        return True
    return False


def governor_chain(api, w):
    """List of governors from w up to the sentence root: [gov1, gov2, ... root].
    Follows the UD `head` edge (dep -> governor). Cycle-guarded."""
    chain = []
    seen = {w}
    cur = w
    while True:
        gov = api.E.head.f(cur)
        if not gov:
            break
        g = gov[0]
        if g in seen:
            break
        chain.append(g)
        seen.add(g)
        cur = g
    return chain


def subtree_has_finite(api, head, children_of):
    """True if `head` or any descendant is a finite predicate (for R2 gap test)."""
    stack = [head]
    seen = set()
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        if is_finite(api, n):
            return True
        stack.extend(children_of.get(n, ()))
    return False


def _has_own_subject(api, w, children_of):
    """True if clause-head w has its own overt subject child (nsubj/csubj) -- a
    full parallel clause, not a shared-subject coordinate continuation."""
    for c in children_of.get(w, ()):
        if api.F.udrel.v(c) in ("nsubj", "nsubj:pass", "csubj", "csubj:pass"):
            return True
    return False


def _coordinate_is_new_assertion(api, w):
    """Veto on the inheritance-bind: a coordinate whose subject person/number
    SHIFTS vs its conjunct, inside a content/relative (ccomp/acl) frame, is a NEW
    independent assertion flattened into a speech/relative line -- the over-merge
    the gate flagged (John 3:11 "quod scimus loquimur ... et ... non accipitis",
    we->you; Matt 17:12 "Helias venit et non cognoverunt", sing->plur). Standing
    it is the safe under-merge side. Same-subject coordinates (John 3:11's
    "testamur", Person=1 like "loquimur") are NOT vetoed -> stay bound."""
    gov = api.E.head.f(w)
    if not gov:
        return False
    if _person_num(api, w) == _person_num(api, gov[0]):
        return False
    seen, c = {w}, w
    while True:
        g = api.E.head.f(c)
        if not g:
            return False
        g = g[0]
        if g in seen:
            return False
        seen.add(g)
        if api.F.udrel.v(g) == "conj":
            c = g
            continue
        return api.F.udrel.v(g) in ("ccomp", "acl", "acl:relcl")


# Content-taking matrix verbs (speech / cognition / perception / emotion). When
# one of these governs a quod/quoniam clause, PROIEL sometimes tags that clause
# advcl though it is really an OBJECT (content-"that") clause -- binding it
# over-merges. Suppressing the bind for these governors errs to STAND (the safe,
# under-merge side of the red line). Closed list set by the 2026-05-29 over-merge
# adversarial gate.
_CONTENT_VERBS = {
    "dico", "ago", "loquor", "narro", "confiteor", "fateor", "nuntio",
    "respondeo", "clamo", "praedico", "testor", "scribo", "moneo", "inquam",
    "scio", "nescio", "cognosco", "nosco", "intellego", "existimo", "puto",
    "credo", "arbitror", "reor", "memini", "recordor", "ignoro", "cogito",
    "iudico", "spero", "confido",
    "video", "audio", "sentio", "animadverto",
    "gaudeo", "laudo", "gratulor", "glorior", "miror", "doleo", "queror",
    "gratias",
}


def _causal_ground_marks(api, w, children_of):
    """The `mark` children of advcl-head w whose lemma is a true causal
    subordinator (quia/quoniam/quod). enim/nam are discourse ADVs (not marks)
    and are excluded; declarative/recitative quoniam after a verb of
    knowing/saying is parsed ccomp (not advcl) and never reaches here."""
    out = []
    for c in children_of.get(w, ()):
        if api.F.udrel.v(c) == "mark":
            if (api.F.lemma.v(c) or "").lower() in ("quia", "quoniam", "quod"):
                out.append(c)
    return out


def _is_causal_anaphoric_ground(api, w, children_of):
    """Audited SAFE sub-class of the causal-bind rule: a FOLLOWING causal advcl
    binds BACKWARD into its main clause (one ATU) ONLY when it is a short, flat,
    anaphoric ground -- the Beatitudes pattern ("beati mites / quoniam ipsi
    possidebunt terram" -> one line). The four guards keep it off the over-merge
    red line the adversarial audit drew (a blanket following-causal-bind
    over-merges 50-70%: discourse enim/nam, recitative quoniam, and long or
    new-referent grounds are self-standing ATUs):
      1. marker is a true causal subordinator (quia/quoniam/quod);
      2. no NEW proper-noun referent in the subtree (anaphoric ground only);
      3. flat: no nested finite clause-head in the subtree;
      4. short: subtree <= 8 words.
    """
    if not _causal_ground_marks(api, w, children_of):
        return False
    # content-clause guard: a content-taking matrix verb means the quod/quoniam
    # clause is an object clause mis-tagged advcl, not a causal ground -> stand.
    gov = api.E.head.f(w)
    if gov and (api.F.lemma.v(gov[0]) or "").lower() in _CONTENT_VERBS:
        return False
    stack, sub, seen = [w], [], set()
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        sub.append(n)
        stack.extend(children_of.get(n, ()))
    if len(sub) > 8:
        return False
    if any(api.F.upos.v(n) == "PROPN" for n in sub):
        return False
    if any((api.F.lemma.v(n) or "").lower() == "inquam" for n in sub):
        return False  # recitative parenthetical (inquit/inquiunt), not a ground
    _NESTED = {"advcl", "advcl:cmp", "ccomp", "acl", "acl:relcl",
               "conj", "csubj", "csubj:pass", "parataxis"}
    for n in sub:
        if n is w:
            continue
        if api.F.udrel.v(n) in _NESTED and is_finite(api, n):
            return False
    return True


def _clause_head_of(api, w):
    """The clause-head that directly governs w's clause membership: w itself if
    it is a clause-head, else the nearest clause-head among its governors."""
    if is_clause_head(api, w):
        return w
    for g in governor_chain(api, w):
        if is_clause_head(api, g):
            return g
    return w


def generate(book_code, chap):
    """Return ATU lines for one chapter as a list of {"ref","words"} dicts, where
    words is a surface-ordered list of word nodes. Each verse is segmented into
    ATU lines; lines preserve word order (only line breaks added)."""
    api = load_api()
    F, E, L = api.F, api.E, api.L

    verses = [
        v for v in F.otype.s("verse")
        if F.book_code.v(v) == book_code and F.chapter.v(v) == chap
    ]
    verses.sort()

    # Build a children map over the WHOLE chapter's words (subtree tests).
    chap_words = []
    for v in verses:
        chap_words.extend(L.d(v, "word"))
    chap_words = sorted(set(chap_words))
    children_of = {}
    for w in chap_words:
        gov = E.head.f(w)
        if gov:
            children_of.setdefault(gov[0], []).append(w)

    # --- classify each clause-head as ROOT (stands) or BIND (rides governor) ---
    clause_heads = {w for w in chap_words if is_clause_head(api, w)}

    def precedes_governor(w):
        """R1: does finite advcl w (surface) precede the main clause it governs?
        Its governor node is its head; compare slot order (word nodes are
        monotone == surface order)."""
        gov = E.head.f(w)
        if not gov:
            return False
        return w < gov[0]

    bind = {}  # clause_head -> bool (True = binds to governor, not its own ATU)
    _conj_pending = []  # conj members resolved in a 2nd pass (coord inheritance)
    for w in clause_heads:
        rel = F.udrel.v(w)
        if F.is_root.v(w) == 1:
            bind[w] = False
            continue
        if rel == "parataxis":
            bind[w] = False
            continue
        if rel == "conj":
            _conj_pending.append(w)  # coordination inheritance, resolved below
            continue
        if rel in ("advcl", "advcl:cmp"):
            if not precedes_governor(w) and _is_causal_anaphoric_ground(api, w, children_of):
                # R3: a short, flat, anaphoric causal ground FOLLOWING its main
                # clause binds BACKWARD into it (one ATU) -- the Beatitudes
                # pattern ("beati mites / quoniam ipsi possidebunt terram").
                # Guarded sub-class only (see _is_causal_anaphoric_ground); the
                # general following-causal class over-merges and is left to
                # stand (-> v2 adjudication, not a blanket rule).
                bind[w] = True
            elif is_finite(api, w):
                # R1: finite frame preceding its governor binds FORWARD (rides
                # the main clause); finite advcl following its head stands.
                bind[w] = precedes_governor(w)
            else:
                bind[w] = True  # non-finite participle/infinitive frame binds
            continue
        if rel in BIND_RELS:
            bind[w] = True
            continue
        bind[w] = False

    # --- 2nd pass: COORDINATION INHERITANCE. A coordinate (conj) member segments
    # like the conjunct it attaches to. If the conjunct BINDS (a verb inside a
    # relative/complement/non-finite clause -- "qui esuriunt ET sitiunt") the
    # coordinate binds too, keeping the coordination in one ATU. If the conjunct
    # STANDS (coordinate MAIN clauses / sequential event-chains -- "venit ET vidit
    # ET dixit") the coordinate stands, so each predication is its own ATU. A
    # gapped coordinate (no finite verb of its own) always binds (shared predicate
    # -- "neque ex sanguinibus / neque ex voluntate carnis"). Replaces the rejected
    # broad rule (bind-if-no-own-subject), which over-merged 2552 coordinates
    # corpus-wide (event-chains, parallel cola, rhetorical series). ---
    def _conjunct_bind(w):
        # A conj member STANDS only if its coordination head is itself a standing
        # ATU root (coordinate MAIN clauses / event-chains -- "venit ET vidit").
        # If that head BINDS, or is NOT a clause-head of its own (a clausal-subject
        # or relative verb that rides a governor -- "qui esuriunt ET sitiunt",
        # where esuriunt is nsubj of beati), the coordinate binds too.
        seen = {w}
        c = w
        while True:
            gov = E.head.f(c)
            if not gov:
                return False
            g = gov[0]
            if g in seen:
                return False
            seen.add(g)
            if F.udrel.v(g) == "conj":
                c = g
                continue
            stands_alone = is_clause_head(api, g) and not bind.get(g, False)
            return not stands_alone

    # Combined guard: a coordinate with its OWN subject is a full parallel clause
    # / colon ("omnes...fuerunt ET omnes...transierunt", 1Cor 10:1) and STANDS even
    # when its conjunct binds; only a SHARED-subject coordinate follows the
    # conjunct. (Pure inheritance alone over-bound ~721 such parallel clauses.)
    for w in _conj_pending:
        if not subtree_has_finite(api, w, children_of):
            bind[w] = True
        elif _has_own_subject(api, w, children_of):
            bind[w] = False
        else:
            bind[w] = _conjunct_bind(w) and not _coordinate_is_new_assertion(api, w)

    def atu_root(w):
        """Innermost STANDING clause-head on w's chain (w's clause-head first,
        then up through governors). The ATU id for w."""
        ch = _clause_head_of(api, w)
        # walk: ch, then its clause-head governors, until one stands
        node = ch
        seen = {node}
        while True:
            if node in clause_heads and not bind.get(node, False):
                return node
            # climb to the clause-head that governs `node`
            nxt = None
            for g in governor_chain(api, node):
                if is_clause_head(api, g):
                    nxt = g
                    break
            if nxt is None or nxt in seen:
                return node
            seen.add(nxt)
            node = nxt

    # --- assign every word to an ATU id (forward bind for R1 frames handled by
    # atu_root via the governor relation: a forward-binding finite advcl's words
    # resolve up to the governing main clause root). ---
    atu_of = {}
    for w in chap_words:
        atu_of[w] = atu_root(w)

    # --- emit display lines as maximal SURFACE-CONTIGUOUS runs sharing one ATU
    # id (ported from the GNT emit_v4). A discontinuous ATU (its words split by
    # an embedded clause) renders as two contiguous segments -- the only word-
    # order-preserving rendering, and what the token-exact parity check expects.
    # A verse-boundary inside a run also cuts the line, so each line is one verse.
    verse_of_word = {}
    for w in chap_words:
        vn = L.u(w, "verse")[0]
        verse_of_word[w] = (F.chapter.v(vn), F.verse.v(vn))

    seq = sorted(chap_words)
    out = []
    run, run_atu, run_v = [], None, None
    for w in seq:
        a = atu_of[w]
        vref = verse_of_word[w]
        if run and (a != run_atu or vref != run_v):
            out.append((min(run), run_v, run))
            run = []
        run.append(w)
        run_atu, run_v = a, vref
    if run:
        out.append((min(run), run_v, run))

    out.sort(key=lambda x: x[0])

    # --- contentless-line merge: a line of pure function words (no content
    # lemma) folds into a neighbor (postpositive-ish -> back, else forward). ---
    lines = _merge_contentless(api, [(v, ws) for _, v, ws in out])

    return [
        {"ref": f"{chap}:{v[1]}", "chapter": v[0], "verse": v[1], "words": ws}
        for v, ws in lines
    ]


_FUNC_UPOS = {"ADP", "CCONJ", "SCONJ", "DET", "PART", "AUX", "PUNCT"}


def _has_content(api, ws):
    """A line bears content if it has any word that is not a pure function word.
    AUX standing alone (e.g. a copula 'est') counts as content for ATU purposes
    only when there is no other verb -- but here we treat AUX as function; a
    bare copular predicate keeps its nominal, which is content."""
    for w in ws:
        if api.F.upos.v(w) not in _FUNC_UPOS:
            return True
    return False


def _merge_contentless(api, lines):
    """Fold any function-word-only line into a neighbor so every ATU line carries
    a thought. Coordinators/postpositives (et/autem/enim/-que/sed) fold backward;
    everything else folds forward."""
    _BACKWARD = {"autem", "enim", "vero", "igitur", "ergo", "que", "-que"}
    out = []
    pend = []
    for v, ws in lines:
        if not _has_content(api, ws):
            lemmas = {api.F.lemma.v(w) for w in ws}
            if lemmas & _BACKWARD and out:
                ov, ows = out[-1]
                out[-1] = (ov, sorted(ows + ws))
            else:
                pend.extend(ws)
            continue
        merged = sorted(pend + ws) if pend else ws
        out.append((v, merged))
        pend = []
    if pend:
        if out:
            ov, ows = out[-1]
            out[-1] = (ov, sorted(ows + pend))
        else:
            out.append((lines[0][0], pend))
    return out


def render(api, line):
    """Surface text of an ATU line (space-joined, trimmed)."""
    return " ".join(api.T.text(w).strip() for w in line["words"]).strip()


def verse_word_sequence(api, book_code, chap, verse):
    api_ = api
    F, L = api_.F, api_.L
    for v in F.otype.s("verse"):
        if F.book_code.v(v) == book_code and F.chapter.v(v) == chap and F.verse.v(v) == verse:
            return list(L.d(v, "word"))
    return []


def main():
    book = sys.argv[1] if len(sys.argv) > 1 else "MATT"
    chap = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    api = load_api()
    lines = generate(book, chap)
    print(f"=== {book} {chap}: Vulgate v1.5 draft (PROIEL-gold TF) ===\n")
    cur = None
    for ln in lines:
        if ln["ref"] != cur:
            if cur is not None:
                print()
            print(ln["ref"])
            cur = ln["ref"]
        print("  " + render(api, ln))


if __name__ == "__main__":
    main()
