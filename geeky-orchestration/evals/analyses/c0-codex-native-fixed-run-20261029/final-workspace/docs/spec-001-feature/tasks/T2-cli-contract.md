Task Name:
Implement and verify the command-line contract

Context:
The wordstat module must expose the full user-facing contract after the counting core is accepted. This phase connects core results to file input, argparse, deterministic output, and clean expected failures.

Scope:

In scope:
---
- Add `wordstat/__main__.py` so `python -m wordstat [--json] [--top N] FILE` runs from the repository root.
- Read exactly the given file as UTF-8 with optional BOM, preserve decoded newline code points, and never read stdin.
- Implement help/argument validation, exact output formats, stdout UTF-8/LF configuration, required stderr messages, and exit codes.
- Add `tests/test_cli.py` using subprocesses and byte assertions for success and error behaviors, including the contract edge cases.
- Add a deterministic test that monkeypatches the file-read operation to raise `OSError` and verifies the unreadable-file exit-3 diagnostic; do not rely on filesystem permission changes.

## Out of scope:
- Changing the accepted R3/R4 counting rules implemented in T1.
- Adding CI, packaging/install metadata, alternate encodings, multi-file input, or runtime dependencies.

Module/System:
Root Python CLI `wordstat/__main__.py`; subprocess contract tests in `tests/test_cli.py`.

## Dependencies:

* T1-counting-core

## Technical Notes:
- Import and call T1's `analyze_text(text, top)` and render the returned `lines`, `words`, `chars`, and `top` fields; do not duplicate counting logic in the CLI.
- Set argparse `prog="wordstat"`; `--top` defaults to 3 and must be integer >= 1. Use argparse default usage-error output and status 2.
- Decode bytes with `utf-8-sig`; catch file `OSError` and `UnicodeDecodeError` separately. The diagnostic includes the exact FILE argument.
- Reconfigure stdout to UTF-8 and LF. Text output has exactly four LF-terminated lines. JSON is one `json.dumps(obj)` line with the specified insertion/key order.
- Missing, directory, and unreadable-file errors exit 3 with one prefixed line and empty stdout. Decode errors exit 3 with their distinct one-line message and empty stdout. Usage errors exit 2 with empty stdout and a final prefixed error line. Do not emit tracebacks for expected errors.
- Cover empty and BOM inputs, invalid UTF-8, CRLF character counts, no words, tied ranking, `--top` limits, stdin independence, missing/directory paths, simulated unreadable-file `OSError`, and usage failures.
- See `implementation-plan.md` sections "Design", "Validation Strategy", and "Contract Decisions"; see `feature-specification.md` R1/R2/R5/R6 and "Errors and exit codes".

## Acceptance Criteria:

* Help, valid commands, and all argument combinations follow the command contract and exit codes.
* Captured stdout bytes exactly match the prescribed UTF-8/LF text or JSON format; stdout is empty for expected failures.
* File and decoding failures have their exact one-line messages; usage errors use argparse defaults with the required final error prefix.
* The subprocess suite covers the required contract cases, and the complete test suite passes.

Definition of Done:

* Code reviewed
* Tested (manual/unit)
* No critical bugs

Tests/Validation Before Next Task:
- `python -m compileall -q wordstat`
- `pytest -q`
- From the repository root, `python -m wordstat --help`

Estimate:
M

Priority:
P0
