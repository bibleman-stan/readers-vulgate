# research/ — third-party corpora (payloads untracked, this manifest tracked)

**Currently empty.** This file exists so the folder is safe by default: without
the `research/*` ignore rule, anything dropped here would be tracked into a
public repo automatically.

## What belongs here

Third-party corpora that are freely redistributable but bulky — clone them and
record each one in the table below with its upstream URL and pinned commit. The
payload stays local; upstream owns it, and a pinned clone is more recoverable
than a copy vendored into our history.

| Directory | Source | Pinned |
|---|---|---|
| *(none yet)* | | |

## What does NOT belong here

- **Our own analysis.** It goes in the numbered tiers — `2-evidence/` for
  findings, `5-machinery/` for scripts — where git can diff and recover it.
- **Licensed or restricted material.** That goes in `private/`, which is where
  this repo's substrate already lives.

## Why the manifest is tracked when the payloads are not

A blanket ignore leaves nothing behind when a directory's contents disappear. On
2026-08-10 two Greek corpora were found missing from `readers-gnt` with no
deletion trace: fifteen validators had been returning zero and reporting
success, and one rule had been emitting roughly ten times its baseline in false
candidates. Nothing failed loudly. A tracked manifest makes absence detectable.
