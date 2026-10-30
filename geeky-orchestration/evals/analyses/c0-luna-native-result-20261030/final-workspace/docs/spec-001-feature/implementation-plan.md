# wordstat Implementation Plan

## Objective

Implement the root `contract.md` exactly as specified by `feature-specification.md`: a Python 3.11+ standard-library package runnable with `python -m wordstat FILE`, deterministic text/JSON output, and clean error exits. Pytest is allowed for tests only.

## Scope and constraints

- Package location is root `wordstat/`; tests live in root `tests/`.
- Keep the contract's tokenization, counting, ordering, byte output and error behavior unchanged.
- Read exactly one file as UTF-8 with optional BOM; preserve decoded newline code points when counting characters.
- No stdin, third-party runtime libraries, installation/packaging work, or extra features.

## Task sequence

| Phase | Task | Purpose | Dependencies |
|---|---|---|---|
| 1 - Core and CLI | T1 | Implement pure statistics/top-word calculation in `wordstat/core.py`. | None |
| 1 - Core and CLI | T2 | Implement module CLI, file decoding/errors, deterministic text/JSON output in `wordstat/__main__.py`. | T1 |
| 2 - Contract verification | T3 | Add subprocess pytest coverage for all requirements; send product defects back through T1/T2 remediation and revalidation. | T1, T2 |

Tasks T1 then T2 are sequential because the CLI consumes the core result. T3 depends on the completed public interface. No safe independent task group is available; all three are small and share the same behavior contract.

## Phase gates

### Phase 1 - Core and CLI

T1 and T2 must each pass their own validation, satisfy their task acceptance criteria and reach `In Review`. The phase reviewer checks both task contracts and the integrated command. Do not start Phase 2 until a code-reviewer returns `READY TO ADVANCE`.

### Phase 2 - Contract verification

T3 must pass pytest and exact-byte subprocess checks. Any product defect returns to its owning T1/T2 task for remediation and revalidation before T3 resumes. A separate phase review is required after T3 is in review, including the final phase. The reviewer must return `READY TO ADVANCE` before tasks move to Done.

## Completion conditions

- Every contract requirement R1-R6 and error condition E1-E3 is traced in `draft.md` and exercised by T3 tests, with environment-dependent permission denial reported accurately.
- Required schema, kanban and planning-folder validators pass.
- Both phase reviews and each task's validation evidence are recorded before commit.
