# Implementation References

## Authoritative requirements

- `../../contract.md` - binding CLI, counting, output, determinism, argument and error contract. Preserve exact IDs and observable behavior; do not reinterpret to suit implementation.
- `../../brief.md` - concise product goal; use only where it does not conflict with the contract.
- `feature-specification.md` - synthesized requirements, assumptions, decisions, risks and acceptance criteria. It supports but does not supersede `contract.md`.

## Plan and task contracts

- `implementation-plan.md` - phase order, gates and completion conditions.
- `draft.md` - requirement-to-task coverage matrix. Keep every R/E row covered when planning changes.
- `tasks/T1-core-statistics.md` - owns pure counting/top-word algorithm in `wordstat/core.py`.
- `tasks/T2-cli-interface.md` - owns `wordstat/__main__.py` and the CLI smoke fixture; depends on T1.
- `tasks/T3-contract-tests.md` - owns contract-level subprocess tests in `tests/test_cli.py`; depends on T1/T2. Report product defects back to their owner rather than changing frozen scopes.
- `review-development-project-manager.md` - PM-style semantic findings and how required gaps were corrected.

## Tracking and validation

- `kanban.md` - task status source of truth. Run the kanban validator after each individual lane move.
- `handoff.md` - decisions, review results, validation evidence, blockers and next-step instructions.
- `tests/fixtures/cli-smoke.txt` - one-line smoke fixture created by T2; expected output is recorded in T2.
- `tests/test_cli.py` - created by T3; must exercise R1-R6 and E1-E3, including byte-exact stdout, independent stderr, stdin isolation, BOM and newline semantics. The unreadable-permission case is conditional when the host cannot reliably enforce it.

## Execution instructions

Use a `geeky-coder` worker for each bounded task. Preserve the task's declared dependencies and file ownership. Validate each task before moving it to In Review, then use one code-reviewer per phase for separate task verdicts and a phase verdict. Do not advance until the reviewer returns `READY TO ADVANCE`, including after the final phase. Save task evidence in `tasks/Tx-*.notes.md`; update `handoff.md` whenever another task is affected. Never edit the frozen requirements, plan, coverage matrix, references, or task bodies during implementation.
