# C0 — wordstat: Reference Spec

| Field | Value |
|---|---|
| id | `c0-wordstat` |
| tier | C0 (harness smoke test) |
| budget ceiling | $3 |
| expected size | 3 tasks, 2 implementation phases |
| stack | Python >=3.11, standard library only; pytest for tests only |
| package location | `wordstat/` at repo root (flat layout, no `src/`) |
| entry point | `python -m wordstat ...` run from repo root |

## Purpose

C0 is the smallest problem that still drives the whole geeky-orchestration lifecycle through the canonical prompt. Use it to check that a harness and model reach every point we trace (see "Harness points") before spending on C1-C3. The problem is deliberately easy, so a failure points at the harness, the model or the workflow rather than the domain. It has two phases because one phase would skip phase-to-phase sequencing and the dependency hand-off. Its interface is exact because a loose one would give the reviewers and the final review loop nothing to check.

## Contestant brief

Build `wordstat`, a tiny Python command-line tool that reads one UTF-8 text file and prints its line, word and character counts plus its most frequent words. It must run as `python -m wordstat FILE` from the repository root using only the Python 3.11+ standard library. Output is a short text summary by default or one line of JSON with `--json`; `--top N` sets how many frequent words to show. Output must be byte-for-byte deterministic on Windows, macOS and Linux. Bad input must fail cleanly with a clear message on stderr and a specific exit code, never a traceback. The full interface contract is in `contract.md`; include pytest tests for your implementation.

## Scope

- Reading and decoding one file; counting lines, words and characters; ranking frequent words.
- Text and JSON output; argument validation and file error handling.

## Out of scope

- Multiple files, stdin, encodings other than UTF-8, Unicode word segmentation, stemming, stop words, packaging metadata beyond what `python -m` needs.

## Functional requirements

R1-R6 as in `contract.md`, which is authoritative.

## Acceptance criteria

- **AC1 (R1)** `python -m wordstat --help` → exit 0.
- **AC2 (R2-R5)** The contract example → stdout equals the example text exactly, exit 0.
- **AC3 (R4, R5)** `--json --top 2` on the example → the example JSON line exactly.
- **AC4 (R4)** Ties order by word ascending; `--top` larger than the distinct word count lists every word.
- **AC5 (R3)** Empty file → `lines: 0`, `words: 0`, `chars: 0`, `top:`; JSON `"top": []`.
- **AC6 (R2, R3)** A BOM is not counted; `\r\n` line endings count as one line break each.
- **AC7 (errors)** Missing file and directory → exit 3, `<path>: cannot read file`; invalid UTF-8 → exit 3, `<path>: not valid UTF-8`; stdout empty, no traceback.
- **AC8 (errors)** `--top 0`, `--top x` and a missing FILE → exit 2 with the argparse usage contract.
- **AC9 (R6)** Output contains no `\r` and is identical across two runs.

## Hidden oracle outline

`oracle/oracle_wordstat.py`, run through `python -m wordstat` as a subprocess with `cwd` set to `ORACLE_TARGET`:

- **W1** help exits 0. **W2** example text. **W3** example JSON `--top 2`. **W4** default top is 3.
- **W5** tie order and `--top` above the distinct count. **W6** digits and mixed case tokenize per R3.
- **W7** empty file, text and JSON. **W8** BOM and CRLF.
- **W9** missing file, directory, invalid UTF-8 (exit 3, exact stderr, empty stdout).
- **W10** usage errors (`--top 0`, `--top x`, no FILE). **W11** no `\r`, deterministic bytes.

## Suggested decomposition

Reference only; contestants plan their own.

- **Phase 1 — core**
  - T1 `wordstat/stats.py`: `analyze(text, top)` returning the counts and the ranked list; unit tests.
- **Phase 2 — interface** (depends on T1)
  - T2 Text and JSON renderers; unit tests.
  - T3 `__main__.py`: argparse, file reading and decoding, error mapping to exit codes, UTF-8/LF stdout; subprocess tests.

## Harness points

A complete C0 run is expected to show each of these in the trace. `evals/telemetry/langfuse-coverage.py` checks them from the Langfuse session.

| Point | Where it comes from |
|---|---|
| All five skills | the canonical prompt: `spec-research`, `geeky-plan`, `plan-review`, `geeky-implement`, `impl-review` |
| Subagents | researchers (`spec-research`), plan reviewers, coders and phase reviewers |
| Nested subagents | `geeky-implement` delegated to its orchestrator, which dispatches coders and reviewers |
| Coder and reviewer roles | `geeky-coder` per task; `code-reviewer` per phase and in `impl-review` |
| Planning gates | `validate-planning-folder`, `validate-task-schema`, `validate-kanban`, `check-dod`, `check-commit` (scripts or `geeky` MCP tools) |
| Tests run | the contestant's own pytest runs |
| Commits | one per task or phase, through `check-commit` |
| File edits | specs, tasks, kanban, source and tests |
| Reasoning | thinking or reasoning summaries on generations (with telemetry on) |
| Token usage | usage on every generation |

## Quality signals

- **Minimal code:** roughly 40-70 LOC of source in 2-3 modules; one tokenizer used for counts and ranking; no classes beyond an optional dataclass; no third-party imports.
- **No defects:** every oracle case passes; no traceback reaches the user; no trailing whitespace or `\r`; JSON key order exact.
- **Tests:** about 60-120 LOC of pytest using `tmp_path` and subprocess calls.

## Running

```powershell
pwsh -File evals/scripts/run-mock-matrix.ps1 -Case c0-wordstat                 # model-free check of both harnesses
pwsh -File evals/scripts/run-baseline.ps1 -Case c0-wordstat -Model <model>    # Claude Code, paid
pwsh -File evals/scripts/run-codex-baseline.ps1 -Case c0-wordstat -Model <model> -Launch ...   # Codex, paid (see adapters/codex/README.md)
```

With `TRACE_TO_LANGFUSE=true`, each run folder gets `langfuse.json` and `langfuse-coverage.json`, and `run.json` records `telemetry.coverage_complete`.
