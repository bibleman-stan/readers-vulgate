#!/usr/bin/env python3
"""Vulgate-native ATU generator: ports the readers-gnt nesting-based engine
(scripts/sblgnt_generate.py) onto the gold UD_Latin-PROIEL Text-Fabric at
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
  PYTHONIOENCODING=utf-8 python scripts/vulgate_generate.py MATT 5
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
    for w in clause_heads:
        rel = F.udrel.v(w)
        if F.is_root.v(w) == 1:
            bind[w] = False
            continue
        if rel == "parataxis":
            bind[w] = False
            continue
        if rel == "conj":
            # R2: a conj member stands only if its subtree carries a finite verb.
            bind[w] = not subtree_has_finite(api, w, children_of)
            continue
        if rel in ("advcl", "advcl:cmp"):
            if is_finite(api, w):
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
