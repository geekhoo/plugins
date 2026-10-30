# wordstat Specification

**Status:** Spec written - not yet planned  
**Dependencies:** None  
**Layer:** Domain / CLI utility  
**Priority:** Important  
**Estimated Complexity:** 2 tasks across 1 implementation phase

## 1. Executive Summary

Build `wordstat`, a root-level Python package invoked as `python -m wordstat FILE`. It reads exactly one named UTF-8 text file, reports line, word, and character counts, and lists the most frequent words. Its text and JSON output, error messages, exit codes, and output bytes are fixed by the authoritative repository-root `contract.md`.

## 2. Problem Statement

### Current State

The repository contains only `brief.md`, `contract.md`, and `.gitignore`; no implementation, tests, packaging configuration, or existing application conventions are present.

### Impact of Inaction

Without the package, the required module command and deterministic summary/error interface do not exist.

## 3. Goals & Non-Goals

### Goals

- Provide `python -m wordstat [--json] [--top N] FILE` from the repository root using Python >=3.11 and production standard-library modules only.
- Match all definitions and observable behavior in root `contract.md`, including UTF-8 with optional BOM, exact counting semantics, stable sort order, exact output formats, stdout encoding/newlines, and error exit/stream behavior.
- Include pytest coverage of the CLI, including byte-exact output and error behavior.

### Non-Goals

- Stdin input, multiple input files, recursive or directory processing, locale-sensitive counting, configurable tokenization, extra output formats, dependencies beyond the standard library at runtime, installation/packaging work, or changing the contract.

## 4. Architecture

Use a flat `wordstat/` package at repository root and its `__main__.py` module entry point. Keep argument parsing, reading, counting, formatting, and exit behavior small and local. Tests live under `tests/` and invoke the real module using the active Python interpreter; pytest is test-only.

## 5. Detailed Design

### Input and counting

- Parse one positional `FILE`, optional `--json`, and optional `--top N` (default 3). `argparse` program name is `wordstat`; `--top` accepts integers >=1 only. No stdin is read.
- Read/decode the named file as `utf-8-sig`, which consumes an initial UTF-8 BOM. On a file missing, directory, or unreadable error, report the exact argument string; on invalid UTF-8, use the separate specified message.
- Compute `lines = len(text.splitlines())`; `words` is the number of `[a-z0-9]+` matches in `text.lower()`; `chars = len(text)` (Unicode code points in decoded text, BOM excluded).
- Rank tokens by descending frequency then ascending word; return at most N, or all distinct tokens if fewer.

### Output and errors

- Reconfigure `sys.stdout` with `encoding="utf-8", newline="\n"`.
- Default to exactly the contract's four text lines, each terminated by LF; when there are no words render the last line as `top:` with no trailing space.
- `--json` emits one line from `json.dumps(obj)` with default separators and prescribed key order `lines`, `words`, `chars`, `top`; each top item has `word`, then `count`.
- On failures, write one error line to stderr with prefix `wordstat: error: ` and no stdout. File and decode errors exit 3; argparse usage errors (including missing FILE, unknown option, invalid/nonpositive `--top`) exit 2; unexpected internal errors are reserved exit 1.

## 6. Cost Estimates

No runtime service or external package is required. Runtime cost is local file I/O and in-memory tokenization proportional to input size; no numeric service cost applies.

## 7. Task Outline (Preliminary)

1. Add the module CLI implementing the frozen contract and verify help, usage and file-error behavior.
2. Add comprehensive pytest subprocess tests for counts, ordering, output bytes, BOM/Unicode, and all specified error cases; close any contract gaps found before acceptance.

These preliminary work units will become the implementation tasks; tests are included in the implementation work rather than left as a future feature.

## 8. Risks & Mitigations

- **Cross-platform newline/encoding drift:** explicitly configure stdout and assert captured byte streams with LF and UTF-8.
- **Ambiguous natural-language meanings of words/lines/chars:** use the exact Python operations in the contract and include Unicode and line-break edge cases.
- **Partial stdout on failed input:** read and decode before emitting any summary; test error streams and exact empty stdout.
- **Input-path message drift:** preserve the original positional argument in error text and verify the complete stderr line.

## 9. Acceptance Criteria

The implementation is accepted only when all R1-R6 and the complete Command, Text format, JSON format, and Exit codes and errors clauses in root `contract.md` are satisfied. The CLI must pass pytest tests covering the above; no traceback may replace any specified input/usage failure.

## 10. Dependencies on Prior Features

None. Python >=3.11 is the execution prerequisite; pytest is needed only for the test suite.

## 11. Delegation to Future Specs

None. Additional input modes or output features require a separate contract/specification and are not part of this deliverable.

## Research Evidence and Decisions

- Repository inspection: there is no existing package or project convention to preserve (`git ls-files`, initial tree; root files `brief.md`, `contract.md`, `.gitignore`). The root contract is authoritative; the brief is a summary, not a competing specification.
- Python's `utf-8-sig` codec consumes an initial UTF-8 BOM; `argparse.ArgumentParser(prog="wordstat").error()` writes usage followed by the `wordstat: error:` line and exits 2; `TextIOWrapper.reconfigure(encoding="utf-8", newline="\n")` is supported. Sources: https://docs.python.org/3.11/library/codecs.html#encodings-and-unicode, https://docs.python.org/3.11/library/argparse.html#argparse.ArgumentParser.error, https://docs.python.org/3.11/library/io.html#io.TextIOWrapper.reconfigure.
- `str.splitlines()` recognizes defined Unicode line boundaries and does not add a line for a terminal separator; `str.lower()` is Unicode-aware before the required ASCII token regex; `len(str)` counts Python string code points/elements, not encoded bytes. Sources: https://docs.python.org/3.11/library/stdtypes.html#str.splitlines, https://docs.python.org/3.11/library/stdtypes.html#str.lower, https://docs.python.org/3.11/library/re.html#regular-expression-syntax, https://docs.python.org/3.11/library/stdtypes.html#text-sequence-type-str.
- Tests should invoke the active interpreter with subprocess byte capture to verify the exact portable CLI interface. Sources: https://docs.python.org/3/library/subprocess.html#subprocess.run, https://docs.pytest.org/en/stable/how-to/parametrize.html.
- Researchers agreed that no material uncertainty or repository convention changes the contract. An alternative of generalizing this into a configurable tokenizer or stdin-capable utility was rejected because neither is specified and stdin is explicitly forbidden.
- Assumption: execution and tests run from repository root as the contract requires; no packaging/install path is needed.
