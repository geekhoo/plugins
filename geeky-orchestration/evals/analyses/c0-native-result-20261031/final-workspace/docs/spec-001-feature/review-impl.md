# Implementation Review: wordstat

Reviewed implementation revision: `c9d55883f644fe0c85ef963610e9f66d15438891`.
Review range: `db45ad94d88abb4eb4c5fe389fc9d2262b0515b8..c9d55883f644fe0c85ef963610e9f66d15438891`.
Validation evidence: `python -m pytest -q` -> exit 0, 21 passed, 1 skipped. The unreadable-file test was skipped because this host can still read a mode-000 file; the task contract allows this host limitation.

## CLI Semantics

Reviewer: `/root/impl_cli_review`.
Reviewed HEAD: `c9d55883f644fe0c85ef963610e9f66d15438891`.

### Required Findings

- None.

### Nonblocking Warnings

- The unreadable-file test was skipped because this host can still read a mode-000 file, an allowed limitation.

### Suggestions

- None.

### Verdict: PASS

<!-- reviewer-complete: cli-semantics -->

## File Errors and Platform I/O

Reviewer: `/root/impl_io_review`.
Reviewed range: `db45ad94d88abb4eb4c5fe389fc9d2262b0515b8..c9d55883f644fe0c85ef963610e9f66d15438891`.
Reviewed HEAD: `c9d55883f644fe0c85ef963610e9f66d15438891`.

### Required Findings

- None.

### Nonblocking Warnings

- None.

### Suggestions

- None.

### Verdict: PASS

The reviewer verified `UnicodeDecodeError` handling before `OSError`, exact supplied-path errors with status 3 and no stdout, UTF-8-sig plus `newline=""` behavior, UTF-8/LF stdout and stderr, and argparse diagnostics after stderr configuration. Full suite: 21 passed, 1 permitted unreadability skip.

<!-- reviewer-complete: file-errors-platform-io -->

## Acceptance Test Coverage

Reviewer: `/root/impl_test_review`.
Reviewed range: `db45ad94d88abb4eb4c5fe389fc9d2262b0515b8..c9d55883f644fe0c85ef963610e9f66d15438891`.
Reviewed HEAD: `c9d55883f644fe0c85ef963610e9f66d15438891`.

### Required Findings

- None.

### Nonblocking Warnings

- [tests/test_wordstat.py:113] uses a CWD-relative path to inspect `wordstat/__main__.py`; invoking pytest from `docs/spec-001-feature` fails with `FileNotFoundError`. The contract and task validation run pytest from the repository root, where the suite passes. Deferred as an optional portability improvement; no acceptance requirement is unmet.

### Suggestions

- The help test checks `usage: wordstat`, not exact help bytes. This meets the contract; exact help output is not specified.

### Verdict: PASS WITH WARNINGS

The reviewer confirmed success-output coverage for example/JSON/BOM/CRLF/empty/no-token/tie-top cases, expression-derived Unicode results, required failure codes/streams/paths, traceback absence, and the permitted unreadability skip. Independent focused run: 21 passed, 1 skipped.

<!-- reviewer-complete: acceptance-test-coverage -->

## Consolidated Verdict

### Reviewers Deployed

1. CLI Semantics — interface, counting, ranking and deterministic output.
2. File Errors and Platform I/O — read/decode failures, path preservation and stream portability.
3. Acceptance Test Coverage — test evidence completeness and portability.

### Required Findings

- None.

### Warnings

- The unreadable-file test is skipped on this host because mode-000 permissions do not prevent reads; this is an explicitly permitted host limitation.
- [tests/test_wordstat.py:113] uses a CWD-relative source-inspection path and would fail when pytest is run from a nested directory. The required root-directory validation passes; defer as optional portability work.

### Top Suggestions

- Resolve the inspected source path from `REPO_ROOT` if nested-directory pytest invocation becomes a supported workflow.
- Exact help bytes are unspecified; the current usage-line assertion is sufficient.

### Per-Reviewer Verdicts

| Reviewer | Verdict |
| --- | --- |
| `/root/impl_cli_review` — CLI Semantics | PASS |
| `/root/impl_io_review` — File Errors and Platform I/O | PASS |
| `/root/impl_test_review` — Acceptance Test Coverage | PASS WITH WARNINGS |

### Overall: PASS
