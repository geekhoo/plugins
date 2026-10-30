Task Name: Add contract-level CLI tests

Context:
Prove the implemented command meets the public contract at the real process boundary.

Scope:

In scope:
---
- Create `tests/test_cli.py` using pytest and subprocesses invoking `sys.executable -m wordstat` from the repository root.
- Cover successful text/JSON bytes, counting/token rules, top defaults/ties, BOM, input errors, usage, streams, and stdin isolation.

## Out of scope:
- New features, third-party runtime dependencies, or weakening contract assertions to fit implementation behavior.
- Product code changes; report a defect against T1/T2 with failing evidence for remediation.

Module/System:
Root `tests/` integration tests for the `wordstat` CLI.

## Dependencies:
* T1-core-statistics
* T2-cli-interface

## Technical Notes:
- Assert exact stdout bytes and LF endings, exit codes, and stderr independently.
- Include empty input, Unicode/code-point and CRLF cases, invalid UTF-8, missing path, directory, invalid arguments, JSON key order, and ties.
- Permission-denial tests are conditional where the platform/privilege makes unreadability reliable; E1 handling remains tested through portable read failures.
- See spec sections 5, 8 and 9.

## Acceptance Criteria:
* The pytest suite covers every R1-R6 and E1-E3 condition with portable assertions.
* The suite passes on the delivered implementation without network access or non-stdlib runtime packages.

Definition of Done:
* Tests reviewed and pass; no critical bugs.

Tests/Validation Before Next Task:
- `python -m pytest -q`

Estimate:
M

Priority:
P1
