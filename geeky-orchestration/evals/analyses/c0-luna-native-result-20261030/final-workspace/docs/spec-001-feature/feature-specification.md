# wordstat Specification

**Status:** Spec written - not yet planned  
**Dependencies:** None  
**Layer:** Domain / CLI  
**Priority:** Required  
**Estimated Complexity:** Small; one flat Python package and a pytest suite

## 1. Executive Summary

Build `wordstat`, a Python command-line tool invoked as `python -m wordstat FILE` from the repository root. It reads one UTF-8 text file (optional BOM), counts lines, ASCII-pattern words and decoded-text code points, and prints a four-line text summary or one-line JSON. Runtime code uses only the Python 3.11+ standard library; pytest is permitted for tests. Root `contract.md` is authoritative.

## 2. Problem Statement

### Current State

The repository contains the requirements brief and interface contract, but no implementation, tests, packaging configuration, or prior project conventions. Research found no integration point that should alter the flat root-package layout.

### Impact of Inaction

Without an implementation, users cannot run the contracted module or rely on its counts, deterministic output, and documented errors.

## 3. Goals and Non-Goals

### Goals

- Provide `python -m wordstat [--json] [--top N] FILE` from the repository root.
- Implement every R1-R6 and E1-E3 requirement below without changing its semantics.
- Keep successful stdout UTF-8 and LF-delimited on Windows, macOS, and Linux.
- Include pytest coverage of the public command, including exact output and error behavior.

### Non-Goals

- Reading stdin, processing multiple files, recursive traversal, configurable tokenization, locale-aware behavior, or additional output formats.
- Third-party runtime dependencies, a console-script installer, or packaging beyond the required `wordstat/` flat package.
- Performance benchmarking or analytics beyond the contract.

## 4. Architecture

Use a flat `wordstat/` package at the repository root with a module entry point supporting `python -m wordstat`. Keep CLI and calculation behavior in the standard library. Put pytest tests in `tests/` and invoke the module through subprocesses where process behavior is part of the contract. No external service or additional architecture is needed.

## 5. Detailed Design and Requirements

The requirements below are transcribed from root `contract.md`; identifiers and observable behavior remain binding.

| ID | Requirement |
|---|---|
| R1 | `python -m wordstat --help` exits 0. `argparse` uses `prog=wordstat`. |
| R2 | Accept one `FILE`, optional `--json`, and optional `--top N`; read only that file as `utf-8-sig`; never read stdin. |
| R3 | On decoded text: `lines = len(text.splitlines())`; `words` counts `[a-z0-9]+` matches in `text.lower()`; `chars = len(text)` in code points, excluding a consumed BOM. |
| R4 | List at most N distinct words, ordered by count descending then word ascending. `--top` defaults to 3 and must be an integer >= 1. |
| R5 | Default output is four lines: `lines: <int>`, `words: <int>`, `chars: <int>`, `top: <word>=<count> ...`; each ends LF. No words means final line `top:\n`. JSON emits one line from `json.dumps(obj)` with default separators and key order `lines`, `words`, `chars`, `top`; top items use `word`, `count`. |
| R6 | Reconfigure successful stdout as UTF-8 with a line-feed newline; output is deterministic across Windows, macOS and Linux without locale dependence. |
| E1 | Missing, directory or unreadable file: exit 3, empty stdout, one stderr error whose content after `wordstat: error: ` is `<path>: cannot read file`; reproduce `<path>` exactly as given. |
| E2 | Invalid UTF-8: exit 3, empty stdout, stderr content after the prefix is `<path>: not valid UTF-8`. Accept an optional leading UTF-8 BOM and exclude it from counts. |
| E3 | Usage error (missing FILE, unknown flag, non-integer or less-than-one `--top`): exit 2, empty stdout, argparse-style diagnostic with final stderr line matching `^wordstat: error: `. Unexpected errors are reserved for exit 1. |

**Assumption:** Preserve CR, LF and CRLF code points when reading. The contract defines `chars` on decoded text and does not authorize newline normalization; `splitlines()` independently defines the line count. Lock this reading in tests.

## 6. Cost Estimates

Not applicable; there is no service, deployment or recurring infrastructure cost.

## 7. Preliminary Task Outline

1. Create the flat package and CLI with required parsing, input, counting, output and error behavior.
2. Add pytest subprocess tests for success, ordering, decoding, usage, read failures and exact output.
3. Run validation on the finished package and reconcile evidence with every R/E requirement.

Planning may split or combine these tasks while preserving complete R/E coverage.

## 8. Risks and Mitigations

- **Newline translation changes `chars`:** preserve decoded line-ending code points and test CRLF/lone CR.
- **Platform output defaults differ:** configure UTF-8/LF and assert stdout bytes through subprocesses.
- **Permission tests vary by platform or privilege:** missing paths and directories are portable; make unreadable-file tests conditional where denial is reliable. E1 handling of read `OSError` remains required.
- **Usage diagnostics have multiple lines:** verify exit 2, empty stdout and required last-line prefix; do not impose a single-line format.

## 9. Acceptance Criteria

- R1-R6 and E1-E3 pass as observable CLI behavior.
- The root command works on Python 3.11+ with no third-party runtime dependency.
- Pytest covers exact stdout bytes, stream separation, BOM/malformed UTF-8, ordering/ties, empty input, usage failures and portable read errors.
- Where all target OSes are unavailable, report unexecuted platform checks rather than implying they ran.

## 10. Dependencies on Prior Features

None.

## 11. Delegation to Future Specs

None; all brief requirements belong to this feature.

## Research Sources and Decisions

`contract.md` is authoritative; `brief.md` is a summary. Research found no existing codebase conventions or disagreement. Python's official Python 3.11 argparse, io and codecs documentation confirms the specified stdlib APIs. WebSearch/WebFetch was unavailable. Preserve CR/LF for `chars`: the contract counts decoded characters and does not authorize newline normalization; test this assumption.
