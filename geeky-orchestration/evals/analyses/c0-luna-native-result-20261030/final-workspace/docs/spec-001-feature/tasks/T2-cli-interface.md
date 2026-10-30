Task Name: Implement wordstat CLI and file boundary

Context:
Expose the core statistics through the contracted `python -m wordstat` interface.

Scope:

In scope:
---
- Create `wordstat/__main__.py` with argparse, one input file, `--json`, and `--top`.
- Implement file decoding, clean error exits, deterministic stdout and both output formats.
- Add `tests/fixtures/cli-smoke.txt` containing `A cat.` plus a final LF for a simple output check.

## Out of scope:
- Changes to pure statistics, pytest suite, installation or packaging.

Module/System:
Root `wordstat` CLI; integrates `wordstat/core.py`.

## Dependencies:
* T1-core-statistics

## Technical Notes:
- Follow R1/R2/R5/R6 and E1-E3 exactly; `prog` is `wordstat` and `--top >= 1`.
- Decode `utf-8-sig`, preserve decoded newline characters, never read stdin.
- Convert file `OSError`/decode errors to contract messages; failures leave stdout empty.
- Reconfigure stdout before output to UTF-8 and LF. Python 3.11+ stdlib only.

## Acceptance Criteria:
* `python -m wordstat --help` exits 0 and parser usage names `wordstat`.
* Output and usage/read/decode error status, streams and wording match contract.

Definition of Done:
* Code reviewed and tested; no critical bugs.

Tests/Validation Before Next Task:
- `python -m compileall wordstat`
- `python -m wordstat --help`
- `python -m wordstat tests/fixtures/cli-smoke.txt` must print `lines: 1`, `words: 2`, `chars: 7`, `top: a=1 cat=1`, each on its own LF-terminated line.
- `python -m wordstat --top 0 tests/fixtures/cli-smoke.txt` must exit 2, leave stdout empty, and end stderr with `wordstat: error: `.

Estimate:
S

Priority:
P1
