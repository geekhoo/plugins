Task Name:
Complete wordstat edge and error contract tests

Context:
T1 provides successful CLI behavior. This task closes acceptance coverage for boundary semantics, argument failures, and input failures.

Scope:

In scope:
---
- Extend `tests/test_wordstat.py` with contract-edge, usage, and file/decode error subprocess tests.
- Correct `wordstat/__main__.py` only if these checks reveal a contract violation; implementation changes remain limited to fixing a verified contract defect.

## Out of scope:
- New requirements, contract edits, optional CLI features, or non-standard-library production dependencies.

Module/System:
Root-level `wordstat` Python package and pytest CLI suite.

## Dependencies:

* T1-core-cli

## Technical Notes:
- Preserve task T1 successful-output tests and all frozen behavior.
- For argparse errors, `contract.md` requires the last stderr line to match `^wordstat: error: ` and stdout to be empty.
- The file error suffix must be exactly `<path>: cannot read file`; decode error suffix exactly `<path>: not valid UTF-8`, where `<path>` is the argument exactly as given.
- See implementation-plan.md sections Design, Phase 2 and Validation Strategy.

## Acceptance Criteria:

* `--top` values that are not integers or are less than 1 fail with usage exit code 2, empty stdout, and a final stderr line matching `^wordstat: error: `.
* Missing FILE, unknown flags, and extra positional files fail with usage exit code 2, empty stdout, and a final stderr line matching `^wordstat: error: `.
* Missing-file, directory, and unreadable regular-file inputs fail with exit code 3, empty stdout, and exactly one stderr line `wordstat: error: <path>: cannot read file\n`, using the path argument exactly as given.
* Invalid UTF-8 input fails with exit code 3, empty stdout, and exactly one stderr line `wordstat: error: <path>: not valid UTF-8\n`, using the path argument exactly as given.
* Unicode lowercase/tokenization, code-point character counting, and `splitlines()` line-boundary behavior match the contract's specified Python expressions.
* Passing unused stdin data without a FILE does not cause stdin to be read and remains a usage error with exit code 2.
* No specified failure case emits a traceback or any stdout.

Definition of Done:

* Code reviewed
* Tested (manual/unit)
* No critical bugs

Tests/Validation Before Next Task:
- Run `python -m pytest -q tests/test_wordstat.py` from repository root and require exit 0.
- For every usage-failure case, assert exit code 2, `stdout == b""`, and `re.search(rb"^wordstat: error: ", stderr.splitlines()[-1])`.
- For missing path `missing.txt`, assert exit code 3, `stdout == b""`, and `stderr == b"wordstat: error: missing.txt: cannot read file\n"`.
- For a directory argument `sample-dir`, assert exit code 3, `stdout == b""`, and `stderr == b"wordstat: error: sample-dir: cannot read file\n"`.
- For an unreadable regular file `unreadable.txt`, remove read permission using a platform-appropriate fixture and assert exit code 3, `stdout == b""`, and `stderr == b"wordstat: error: unreadable.txt: cannot read file\n"`. Skip only when the host privilege/filesystem model cannot represent unreadability (for example an elevated Windows process); report the skip reason.
- For invalid UTF-8 file `invalid.txt`, assert exit code 3, `stdout == b""`, and `stderr == b"wordstat: error: invalid.txt: not valid UTF-8\n"`.
- For Unicode and line-boundary fixtures, independently calculate expected counts with the specified Python expressions and assert successful exact output bytes.
- Provide stdin bytes with a missing FILE and assert exit code 2, empty stdout, and the required final argparse error line.
- Require the test process itself to finish with no traceback in captured CLI stderr for these specified failures.

Estimate:
S (test-focused; implementation changes are conditional defect fixes only)

Priority:
P1
