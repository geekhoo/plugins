# Wordstat Implementation Plan

## Outcome

Deliver the repository-root `wordstat/` package so `python -m wordstat [--json] [--top N] FILE` satisfies the complete observable interface in root `contract.md`, with pytest coverage. `contract.md` takes precedence over the brief and this plan; the feature specification adds no product behavior.

## Requirements and design

- **R1:** `python -m wordstat --help` exits 0.
- **R2:** Parse at most the defined options and exactly one `FILE`, read only that path, decode via UTF-8 with optional BOM (`utf-8-sig`), and never read stdin.
- **R3:** Implement `lines = len(text.splitlines())`, `words` as matches of `[a-z0-9]+` in `text.lower()`, and `chars = len(text)` after BOM removal.
- **R4:** Default `--top` to 3; accept only integers >= 1; sort by count descending then word ascending and include all words when fewer than N distinct words exist.
- **R5:** Use the exact four-line text format unless `--json` is selected. Text and JSON outputs end with one LF; JSON uses `json.dumps(obj)` default separators and the specified key order.
- **R6:** Force stdout UTF-8 and `\n`, independent of platform/locale. Expected errors use exact contract exit codes and stderr wording and leave stdout empty.
- **Brief:** Include pytest tests; runtime must use only Python 3.11+ standard library.

## Architecture and scope

Implement a flat `wordstat/` package, likely `wordstat/__init__.py` and `wordstat/__main__.py`, with a small CLI and private counting/formatting helpers. Use `argparse` with `prog="wordstat"`; customize its error path only as needed to satisfy the required `wordstat: error: ` prefix. Open the named file explicitly as UTF-8-sig, catch expected OS and decoding errors, and return 3 with the specified message. Build JSON keys in contract order and keep formatters deterministic. No packaging metadata, external runtime dependencies, stdin path, or unrelated reusable library API is in scope.

Add process-level tests under `tests/` invoking the public module command with the current interpreter. Assert return code and stdout/stderr bytes for success and error cases. Use a subprocess environment with a stable working directory (repository root) and temporary files. Deterministically simulate an unreadable file by making `open()` raise `PermissionError` and assert the specified exit and diagnostic; an actual OS permission-denied test is supplementary because platform behavior differs. Missing path and directory cases are mandatory cross-platform coverage.

## Implementation phase

### Phase 1 — CLI and contract tests

Task T1 implements the complete CLI and its tests. It has no dependencies. Keep it in Ready. No later task is allowed to supply evidence missing from T1.

## Task mapping

See `draft.md` for the requirement-to-task coverage matrix. All requirements map to T1.

## Validation and acceptance

T1 validation must run `python -m pytest -q` from repository root and `python -m wordstat --help`; the task file enumerates individual assertions and exact expected text/messages. Before acceptance, also run `python -m compileall -q wordstat tests`, inspect `git diff --check`, and manually verify the example in `contract.md` byte-for-byte. Record the tested revision, exact commands, exit statuses, and results in T1 notes and `handoff.md`. A passing pytest run alone is not a substitute for checking each task AC or the full contract.

## Decisions and assumptions

- The root contract is the source of truth; research is supporting evidence and cannot alter it.
- Empty file succeeds with zero counts and `top:`; no input bytes are sourced from stdin.
- `unreadable` maps to the contract's exit-3 `cannot read file` message; a deterministic simulated `PermissionError` test is mandatory, with actual filesystem permission denial supplementary.
- The repository has no existing test or packaging convention. Use pytest and Python's standard library only, as authorized.
- One task/phase is the smallest schedule that covers the specification without inventing dependencies.
