# private/ — layout and conventions

**This folder is gitignored; only this README is tracked.** It holds licensed
corpora and pre-publication material that must not reach the public repository.

This stub exists so the folder's purpose survives even though its contents
cannot be committed. A directory that is entirely ignored leaves nothing behind
when it goes missing — which is exactly how two Greek corpora disappeared from
`readers-gnt` unnoticed on 2026-08-10.

## Layout

| Dir | Holds | Scale |
|---|---|---|
| `substrate/` | Licensed corpora backing the Vulgate reader | ~1.4 GB |
| `original-douay-rheims/` | Douay-Rheims English text, per-chapter | ~35 MB |
| `lexham-exports/` | Lexham data export | ~576 KB |

## Rules

- **`substrate/` may never be committed.** Licensed third-party material, and at
  1.4 GB it would be unworkable in git history regardless.
- Our own analysis does not belong here — evidence goes in `2-evidence/`,
  scripts in `5-machinery/`, where git can diff and recover it.
- Third-party data that is freely redistributable belongs in `research/` with a
  tracked manifest naming its source, not here.
