# wordstat Implementation Plan

## Objective

Implement the exact root `contract.md` interface as a Python 3.11+ flat package, runnable with `python -m wordstat FILE`, using only the standard library at runtime and pytest for tests. `contract.md` is authoritative; neither this plan nor research may weaken its requirements.

## Requirements

- R1: `python -m wordstat --help` exits 0.
- R2: accept exactly one file, decode UTF-8 with optional BOM via `utf-8-sig`, and never read stdin.
- R3: use `len(text.splitlines())`, matches of `[a-z0-9]+` in `text.lower()`, and `len(text)`.
- R4: default `--top` to 3; reject N < 1; order by count descending then word ascending; return at most N distinct words.
- R5: text by default; JSON with `--json`.
- R6: reconfigure stdout with UTF-8 and LF newline behavior; output must be deterministic across Windows, macOS and Linux.
- Preserve every exact text/JSON layout, usage/error wording, stream condition and exit code in root `contract.md`.

## Phase 1: Complete CLI and Contract Tests

### T1 — Implement and test wordstat

Create `wordstat/` and tests. Keep the runtime implementation standard-library-only. Use newline-preserving UTF-8-with-BOM decoding so `chars` counts decoded code points including original line endings. Produce stable top-word ties explicitly. Exercise the public module command via subprocess tests and assert exact stdout bytes, stderr, and exit codes.

**Dependencies:** None. **Parallelization:** Not applicable; one cohesive task. **Exit gate:** T1 ACs and Tests/Validation pass; phase reviewer returns READY TO ADVANCE.

## Delivery and Review

The single phase contains T1. The implementation worker validates all T1 acceptance criteria before returning. The orchestrator verifies tested revision, commands and output; a code-reviewer subagent then returns separate AC/test verdicts and the phase verdict. T1 moves to Done only after that verdict, `check-dod`, and kanban integrity pass. Commit the tested code and pytest tests together. Package-wide final acceptance additionally requires all three `impl-review` reviewer lanes and an overall PASS.

## Constraints

- No runtime dependencies or additional product scope.
- Do not consume stdin.
- Do not normalize input newlines before `chars` is computed.
- Do not paraphrase required output/error strings in tests; assert contract literals and positional predicates.
- Do not claim cross-platform execution from a single-host run; byte determinism follows explicit stream configuration and portable tests.

## Sources

- Root `contract.md` (authoritative interface, R1-R6, command and output/error contract).
- `feature-specification.md` (research synthesis and design notes).
- `tasks/T1-implement-wordstat-cli.md` (frozen task contract and executable validation).
