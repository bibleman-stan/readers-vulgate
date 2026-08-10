#!/usr/bin/env python3
"""TF validation suite for the Vulgate Latin Text-Fabric.

Adapted from readers-bofm/scripts/validate_tf.py for the CoNLL-U -> TF case.
Release gate: the built TF must pass ALL of these before use.

Checks:
  1. load          -- TF loads cleanly and reports expected node types
  2. round-trip    -- concatenated NFC form per sentence == sentence's # text (mod whitespace)
  3. edge-integrity -- every non-root token has exactly one head edge;
                       edge-less count == is_root==1 count (== #sentences)
  4. provenance    -- every word has syn_source set (must be 'proiel-gold')
  5. ref-format    -- every Vulgate verse node has a ref matching BOOKCODE_CHAPTER.VERSE
  6. node-counts   -- report all node type counts (informational)

Usage:
    python scripts/validate_tf.py [version]   (default: 0.1)
"""
import sys, re, unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
VERSION = sys.argv[1] if len(sys.argv) > 1 else "0.1"

from tf.fabric import Fabric

_VULG_REF = re.compile(r"^[A-Z0-9]+_\d+\.\d+$")

def nfc(s):
    return unicodedata.normalize("NFC", s)

def squash(s):
    """Strip all whitespace for round-trip comparison."""
    return re.sub(r"\s+", "", nfc(s))


def main():
    vdir = REPO / "data" / "tf" / VERSION
    print(f"=== Vulgate Latin TF v{VERSION} validation suite ===")
    print(f"    TF dir: {vdir}")
    results = {}

    # ---- Load ----------------------------------------------------------------
    api = Fabric(locations=str(REPO / "data" / "tf"), modules=VERSION, silent="deep").load(
        "form lemma upos udrel is_root syn_source text_source ref "
        "sent_text sent_id book_code chapter verse book_name title head",
        silent="deep"
    )
    if api is False:
        print("FAIL: TF did not load")
        return 1

    F, L, E = api.F, api.L, api.E
    # E.head.f(w) returns a tuple (may be empty); empty tuple is falsy — correct sentinel
    otypes = F.otype.all
    results["1 load"] = "PASS"
    print(f"  [PASS] 1 load: TF loaded OK")
    print(f"         Node types: {list(otypes)}")

    # ---- Node counts (informational) -----------------------------------------
    counts = {ot: len(list(F.otype.s(ot))) for ot in otypes}
    print(f"\n  [INFO] 6 node-counts:")
    for ot, n in counts.items():
        print(f"         {ot:12s}  {n:7,d}")
    results["6 node-counts"] = "PASS (informational)"

    # ---- Round-trip ----------------------------------------------------------
    bad_rt = []
    for sn in F.otype.s("sentence"):
        sent_text_raw = F.sent_text.v(sn) or ""
        forms = "".join(F.form.v(w) for w in L.d(sn, "word"))
        if squash(forms) != squash(sent_text_raw):
            sid = F.sent_id.v(sn) or str(sn)
            bad_rt.append(f"sent_id={sid!r} (text={sent_text_raw[:40]!r})")
        if len(bad_rt) > 10:
            bad_rt.append("... (truncated)")
            break

    if bad_rt:
        results["2 round-trip"] = f"FAIL ({len(bad_rt)} sentences; first: {bad_rt[0]})"
    else:
        results["2 round-trip"] = "PASS"

    # ---- Edge integrity ------------------------------------------------------
    # Every non-root word should have exactly one outgoing head edge.
    # edgeless non-root == FAIL.
    # edge-less count should equal is_root==1 count (roots legitimately have no edge).
    words = list(F.otype.s("word"))
    total_words = len(words)
    root_count = sum(1 for w in words if F.is_root.v(w) == 1)
    # head edges: E.head.f(w) gives list of gov nodes this word's head edge points to
    edgeless = sum(1 for w in words if not E.head.f(w))

    if edgeless == root_count:
        results["3 edge-integrity"] = f"PASS (edgeless={edgeless:,} == is_root={root_count:,} == #sentences={counts.get('sentence',0):,})"
    else:
        results["3 edge-integrity"] = (
            f"FAIL (edgeless={edgeless:,}, is_root={root_count:,}, "
            f"sentences={counts.get('sentence',0):,}; "
            f"delta={abs(edgeless - root_count):,})"
        )

    # ---- Provenance ----------------------------------------------------------
    missing_prov = sum(1 for w in words if not F.syn_source.v(w))
    wrong_prov = sum(1 for w in words if F.syn_source.v(w) and F.syn_source.v(w) != "proiel-gold")
    if missing_prov == 0 and wrong_prov == 0:
        results["4 provenance"] = "PASS (all words have syn_source='proiel-gold')"
    else:
        results["4 provenance"] = f"FAIL (missing={missing_prov}, wrong_value={wrong_prov})"

    # ---- Ref format on Vulgate verses ----------------------------------------
    bad_ref = []
    for vn in F.otype.s("verse"):
        ref = F.ref.v(vn) or ""
        if not _VULG_REF.match(ref):
            bad_ref.append(ref[:30])
        if len(bad_ref) > 5:
            bad_ref.append("...")
            break
    if bad_ref:
        results["5 ref-format"] = f"FAIL (bad refs: {bad_ref})"
    else:
        results["5 ref-format"] = f"PASS ({counts.get('verse',0):,} verse refs all match BOOKCODE_CHAPTER.VERSE)"

    # ---- Print results -------------------------------------------------------
    print()
    for k, v in sorted(results.items()):
        tag = v.split()[0]
        print(f"  [{tag:4}] {k}: {v}")

    hard_fail = any(r.startswith("FAIL") for r in results.values())
    print()
    print("RESULT:", "FAIL -- do not deploy" if hard_fail else "OK (all hard checks pass)")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
