Task Name:
Implement and test the wordstat CLI

Context:
This is the only delivery phase for the CLI described by the root contract. There is no existing application code. The supplied `contract.md` is authoritative.

Scope:

In scope:
---
- Create the flat `wordstat/` package and its `python -m wordstat` implementation.
- Create pytest black-box coverage for every requirement and error contract, invoking the module as a subprocess and checking exact stream bytes and statuses.
- Run the validation commands below from the repository root.

## Out of scope:
- Packaging or installation metadata, runtime third-party dependencies, stdin support, other input formats, localization, or changing the contract.
- Claiming other operating systems were executed when they were not.

Module/System:
Python 3.11+ standard-library CLI package at repository root; pytest-only test suite.

## Dependencies:
* None

## Technical Notes:
- Follow root `contract.md` literally. `feature-specification.md` sections 4-5 describe newline preservation and CLI design; `implementation-plan.md` Phase 1 defines the delivery gate.
- Preserve original newline code points when reading (`encoding="utf-8-sig", newline=""` or equivalent); R3 counts `len(text)`.
- Sort ties explicitly by word. Reconfigure stdout before writing. Never read stdin.
- Error tests must assert exactly the source contract's messages/prefixes, exit codes, empty stdout and path argument behavior, not paraphrases.

## Acceptance Criteria:
* The package command matches R1-R6 and all exact command, text/JSON, and error/exit requirements in root `contract.md`, using only Python's standard library at runtime.
* Pytest verifies all success and failure behavior by subprocess, including exact stdout bytes (UTF-8/LF/trailing newline/key order), stderr predicates, and exit codes; every required contract case is checked before this task advances.

Definition of Done:
* Code reviewed against this task and its defined tests.
* Tests/Validation commands pass and their tested revision is recorded.
* `tasks/T1-implement-wordstat-cli.notes.md` records evidence and review.
* No critical contract mismatch remains.

Tests/Validation Before Next Task:
- `python -m pytest -q` exits 0 and reports every collected test passing. The tests must exercise these exact source assertions:
  - R1: `python -m wordstat --help` exits 0.
  - Example input is exactly `The cat sat.\nThe cat ran!\nA dog.\n`; text stdout is exactly `lines: 3\nwords: 8\nchars: 33\ntop: cat=2 the=2 a=1\n`.
  - Example JSON stdout is exactly `{"lines": 3, "words": 8, "chars": 33, "top": [{"word": "cat", "count": 2}, {"word": "the", "count": 2}]}\n` for `--json --top 2`.
  - Contract text format: `Exactly four lines, each ending in \`\n\`.`; for no words `top:` has no trailing space.
  - Contract JSON format: `One line: the result of \`json.dumps(obj)\` with default separators, followed by \`\n\`.` and the exact ordered keys `lines`, `words`, `chars`, `top`.
  - `--top` defaults to 3; `--top N` must be an integer >= 1. Explicitly test `--top 0` and non-integer `--top nope` as usage errors; ties order by count descending then word ascending.
  - Input uses UTF-8 `utf-8-sig`; include BOM, invalid UTF-8 and mixed newline cases; counts use exact R3 formulas and stdin is not read.
  - stdout is `encoding="utf-8", newline="\n"`; assert exact bytes include LF rather than platform CRLF.
  - Missing file, directory, or unreadable: exit 3 and stderr after prefix is `<path>: cannot read file`. Test missing file and directory as subprocesses. For the unreadable-I/O branch (not reliably reproducible with OS permissions on Windows or elevated accounts), unit-test the CLI's read/error handling with an injected `open` that raises `PermissionError`; assert the exact same path error and exit 3.
  - Invalid UTF-8: exit 3 and stderr after prefix is `<path>: not valid UTF-8`.
  - Usage errors return 2 and `the last stderr line must match \`^wordstat: error: \`` for missing FILE, unknown flag and bad `--top`.
  - All errors print one line to stderr, prefix `wordstat: error: `, and leave stdout empty. `<path>` is the FILE argument exactly as given.
  - Empty file is success (exit 0) with exact four-line text `lines: 0\nwords: 0\nchars: 0\ntop:\n` and JSON `{"lines": 0, "words": 0, "chars": 0, "top": []}\n`.
  - Verify `sys.stdout.reconfigure` is invoked before output with exactly `encoding="utf-8", newline="\n"` (for example through a controlled unit-level stdout wrapper); subprocess byte assertions separately verify LF output.
- `python -m wordstat --help` exits 0.
- The test suite creates its exact sample input `The cat sat.\nThe cat ran!\nA dog.\n` in `tmp_path`, then runs `python -m wordstat --json --top 2 <that-created-path>`; the result is exactly `{"lines": 3, "words": 8, "chars": 33, "top": [{"word": "cat", "count": 2}, {"word": "the", "count": 2}]}\n`.

Estimate:
M

Priority:
P1
