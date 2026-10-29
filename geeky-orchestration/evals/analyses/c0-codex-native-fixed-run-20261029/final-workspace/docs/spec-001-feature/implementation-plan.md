# wordstat Implementation Plan

## Objective

Implement the exact command-line contract in [`contract.md`](../../contract.md) as a flat Python 3.11+ standard-library package at `wordstat/`, with pytest-only tests. The approved requirements are R1-R6 and the exit/error contract in `contract.md`; no scope expansion is authorized by this plan.

## Design

- `wordstat/core.py` exposes `analyze_text(text, top)` for pure text analysis and returns keys `lines`, `words`, `chars`, and `top` (a list of `{word, count}` objects); it owns exact lower-then-`[a-z0-9]+` tokenization and deterministic ranking.
- `wordstat/__main__.py` owns argparse, path reading/UTF-8 BOM decoding, expected input error messages/exit codes, stdout configuration, and text/JSON rendering.
- `tests/` validates core calculations and invokes the module in subprocesses to assert exact byte output, stderr, and status.
- Runtime dependencies remain Python 3.11+ standard library only; pytest is test-only.

## Phases and Tasks

### Phase 1: Counting Core

| Task | Scope | Requirements | Depends on |
|---|---|---|---|
| T1 | Add the package core and focused unit tests for decoded text calculations and deterministic top ranking. | R3, R4 | None |

Phase 1 advances only after T1 meets its task contract and its required tests pass.

### Phase 2: CLI Contract

| Task | Scope | Requirements | Depends on |
|---|---|---|---|
| T2 | Add the `python -m wordstat` interface and subprocess tests for arguments, file decoding, output bytes, expected errors, and help. | R1, R2, R5, R6, exit/error contract; integration of R3/R4 | T1 |

Phase 2 advances only after T2 meets its task contract, its required tests pass, and the complete suite passes.

## Validation Strategy

- T1: `python -m compileall -q wordstat` and `pytest tests/test_core.py -q`.
- T2 and final: `python -m compileall -q wordstat` and `pytest -q`; additionally verify representative `python -m wordstat --help` and JSON output from the repository root.
- Subprocess tests capture stdout/stderr as bytes and assert LF output, exact JSON serialization/key order, empty stdout on errors, exit codes, and final argparse error prefix.
- Required edge coverage includes empty input, BOM, invalid UTF-8, CRLF decoded character count, tied ranking, `--top` default and limits, stdin independence, missing/directory paths, and usage errors. Cover unreadable-file handling deterministically with a test that monkeypatches the file-read operation to raise `OSError`; do not rely on OS permission behavior.
- Cross-platform behavior is contractually required. This repository has no CI setup, so record the current host's evidence and do not claim Windows/macOS/Linux execution unless observed.

## Contract Decisions

- `chars` uses decoded code points without newline normalization; CRLF contributes two characters. This follows R3's `len(text)` formula.
- Usage errors use argparse's default output because the specific usage row requires it, even though the general error paragraph says one line. Tests assert exit 2, empty stdout, and the final error prefix.
- `FILE` is treated as an exact argument string in diagnostics. File and UTF-8 decode errors are distinct exit-3 cases.

## Completion Conditions

- Every R1-R6 and error-table condition has traceable task coverage and passing evidence.
- Planning gates pass, both implementation phases are reviewed and accepted, and the final implementation review returns PASS.
- No release/deployment approval is implied.
