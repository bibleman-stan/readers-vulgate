# Vulgate v1.5 adjudication overrides

Render-stage ATU-line overrides for residual cases the mechanical v1.5 binding
fabric (`scripts/vulgate_generate.py`) cannot reach: judgment-residuals where
the parse is structurally sound but the line-break needs editorial finesse.

## File

`overrides.json` — keyed `"<book> <chapter>:<verse>"` (lowercase singular
book names: `matthew`, `mark`, `1corinthians`, `2john`, `revelation`),
values are arrays of strings, one ATU line per element.

```json
{
  "matthew 5:3": [
    "Beati pauperes spiritu,",
    "quoniam ipsorum est regnum caelorum."
  ]
}
```

## Parity gate

Every override entry must reassemble to the underlying Vulgate verse text
alphabetically. The check is NFD-normalized, combining-marks-stripped,
lowercased `[a-z0-9]` comparison — so macrons / precomposed accents are
tolerated, but every word in the verse must appear in the override (and
no extra words). A mismatch is silently REJECTED with a stderr warning;
mechanical output is kept.

This means **an override can re-segment, never re-word**. To change a word
is a separate concern (textual-criticism, not colometry).

## When to use an override

- The mechanical fabric over-splits or over-merges a specific verse where
  no general binding rule can be added without regressing elsewhere
- A scholarly editorial choice (e.g. parallel cola in Pauline doxologies)
  the binding rules cannot make from UD features alone

## When NOT to use an override

- A class of verses needs the same fix → add a binding rule in
  `vulgate_generate.is_clause_head` instead
- The underlying parse is wrong → fix the UD substrate (gold PROIEL is rare
  to defect against, but if found, file upstream)

## Bypass

For validators or raw-mechanical-measurement runs:

```
VULGATE_BYPASS_OVERRIDES=1 python scripts/build_content.py
```

## Architecture

Overrides apply at the **render stage** inside `scripts/build_content.py`
(post `vg.render(api, ln)`, pre Douay-Rheims interleave). The Vulgate generate
pipeline returns TF-word-node dicts, not strings, so overrides cannot drop in
at generate-stage the way BoFM's do. The render-stage injection is the
architecturally clean answer; mirrors the Tanakh + GNT solutions and is
documented in the cross-corpus port redesign work (session 2026-06-02).
