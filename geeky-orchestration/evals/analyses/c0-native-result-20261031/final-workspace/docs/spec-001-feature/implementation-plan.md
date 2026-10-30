# wordstat Implementation Plan

## Outcome

Implement the root-level Python 3.11+ `wordstat` package and pytest suite exactly as required by `../../contract.md` (repository root). The contract is authoritative over the summary brief and this plan. Production code uses only the standard library; pytest is test-only.

## Design

- Put the module entry point at `wordstat/__main__.py` so `python -m wordstat` works from the repository root.
- Parse the contract's positional `FILE`, `--json`, and `--top N` interface with `argparse` and `prog="wordstat"`.
- Decode one named path using UTF-8 with optional BOM; compute line, token, character, and top-word values with the exact contract expressions/order.
- Fully read and validate before writing output. Format text or default `json.dumps` output in insertion order and configure stdout as UTF-8/LF.
- Keep black-box CLI tests in `tests/`, invoke `sys.executable` with subprocess byte capture, and assert return code plus both streams.

## Task Sequence and Phases

### Phase 1: Core CLI (T1)

Create `wordstat/__main__.py` and initial `tests/test_wordstat.py`. Deliver help and successful text/JSON outputs, required counting/ranking behavior, BOM handling, and exact UTF-8/LF bytes. Validate T1 before moving it to In Review. Phase review must return READY TO ADVANCE before Phase 2.

### Phase 2: Contract edge and error coverage (T2)

Extend tests for Unicode and line semantics, stdin/argument restrictions, and all specified usage and input failures; correct implementation defects only as necessary to meet the frozen contract. Validate T2 before review. Final phase review must return READY TO ADVANCE before Done; final `impl-review` follows implementation completion.

The order is intentionally serial: T2's regression cases exercise the CLI assembled in T1. There are no independent tasks to parallelize without conflicting ownership of the module and shared test file.

## Validation Strategy

- Each task runs its own pytest node before advancing. All tests invoke the CLI as subprocesses and assert exact bytes, streams, and exit codes.
- The final suite must cover every R1-R6 clause and the detailed command, text, JSON, and error clauses in root `contract.md`.
- Full validation command: `python -m pytest -q` from repository root.
- Run `python -m wordstat --help` and contract example comparisons as supplementary smoke checks; the pytest suite is the acceptance evidence.

## Scope Decisions

- No stdin, installation metadata, external runtime dependencies, configurable tokenization, or new output formats are added. These were rejected as out of scope, and stdin is explicitly prohibited by the contract.
- Tests use the active Python interpreter and the repository-root working directory, matching the documented invocation. No other project or test conventions exist.

## Requirements Traceability

See `draft.md` for the complete requirement-to-task matrix. Task bodies are the frozen execution contracts once plan review accepts this package.
