# Wordstat Feature Specification

**Status:** Spec written — not yet planned  
**Dependencies:** None  
**Layer:** CLI utility  
**Priority:** Important  
**Estimated Complexity:** 1 task across 1 implementation phase

---

## 1. Executive Summary

Add a small Python command-line utility that reads one named UTF-8 text file and reports line, word, and character counts plus the most frequent words. The flat `wordstat/` package must run as `python -m wordstat` from the repository root, use only the Python 3.11+ standard library at runtime, and provide deterministic text and JSON output with contract-defined error behavior.

**Authority and decision:** Root `contract.md` is authoritative; the brief is consistent with it. Research found no repository implementation or convention to preserve. Scope therefore stays limited to the exact contract: no stdin mode, dependencies, packaging metadata, or extra features. This is intentionally a one-task, one-phase utility rather than a larger architecture. No researcher proposed a conflicting behavior; the alternative of adding general-purpose word/statistics features was rejected because it would exceed the contract without evidence of need.

## 2. Problem Statement

### Current State

The repository contains only `brief.md` and `contract.md`; it has no implementation, tests, project configuration, or existing integration pattern. The requested `wordstat` command is not yet available.

### Impact of Inaction

Users cannot obtain the requested counts through a portable command, and none of the exact output/error guarantees can be exercised or maintained.

**Evidence:** Repository inventory and codebase analysis found only the two root input files. The required behavior is specified by `contract.md` (R1-R6 and interface/error sections).

## 3. Goals & Non-Goals

### Goals

- Provide `python -m wordstat [--json] [--top N] FILE` from the repository root.
- Match all counting, ordering, formatting, encoding, and error semantics in `contract.md` exactly.
- Include pytest coverage of successful, boundary, and error paths at the process interface.
- Keep runtime dependencies to Python 3.11+ standard library modules.

### Non-Goals

- Reading from stdin, accepting multiple files, or recursively scanning directories.
- Locale-aware tokenization, Unicode word classes, configurable output schemas, or extra statistics.
- Installing/packaging the project, adding third-party runtime dependencies, or creating a general library API.

**Assumption:** The repository-root module invocation is the only supported launch mode because the contract explicitly names it.

## 4. Architecture

Use a flat `wordstat/` Python package with a module entry point. Keep responsibilities small: parse the CLI contract, read/decode the named file, compute counts/top words, serialize the requested output, and map expected input/usage failures to specified diagnostics and exit codes. The implementation may keep these pieces in one module if that remains clear; no abstraction or framework is required.

**Evidence:** There is no existing architecture or integration point. This minimal design follows the package and entry-point constraints in `contract.md`. The official Python documentation confirms the relevant standard-library APIs: [argparse](https://docs.python.org/3.11/library/argparse.html), [codecs](https://docs.python.org/3.11/library/codecs.html#encodings-and-unicode), [string methods](https://docs.python.org/3.11/library/stdtypes.html#str.splitlines), [JSON](https://docs.python.org/3.11/library/json.html#json.dumps), and [text stream reconfiguration](https://docs.python.org/3.11/library/io.html#io.TextIOBase.reconfigure).

## 5. Detailed Design

### Command and input

- `argparse` program name is exactly `wordstat`; accept one `FILE`, optional `--json`, and optional integer `--top N` (default 3).
- Reject missing/extra positional arguments, unknown flags, non-integer `N`, and `N < 1` as usage errors (exit 2).
- Read exactly the supplied path; never read stdin. Decode using `utf-8-sig`, which accepts and removes an optional leading UTF-8 BOM.
- A missing file, directory, or unreadable file exits 3 with `<path>: cannot read file`; invalid UTF-8 exits 3 with `<path>: not valid UTF-8`. `<path>` is exactly the CLI argument.

### Computation

- `lines = len(text.splitlines())`.
- Find tokens using `[a-z0-9]+` over `text.lower()`; `words` is the token count.
- `chars = len(text)`, counting decoded Python string code points, excluding a consumed BOM.
- Sort distinct tokens by frequency descending, then token ascending; include up to N, or all when fewer exist.

### Output and errors

- Before output, reconfigure stdout with UTF-8 encoding and `newline="\n"`; avoid locale-dependent formatting.
- Every success ends with exactly one LF. Text mode emits exactly four lines: `lines`, `words`, `chars`, and `top`; an empty token set emits `top:` without a trailing space.
- JSON mode emits one line from `json.dumps(obj)` using default separators and ordered keys `lines`, `words`, `chars`, `top`; top entries have ordered keys `word`, `count`.
- Errors emit one stderr line prefixed `wordstat: error: ` and leave stdout empty. Usage diagnostics otherwise follow argparse defaults. Expected input failures never produce tracebacks; exit 1 remains reserved for unexpected internal errors.

**Clarification from research:** argparse's normal usage-error exit is 2, but its default diagnostic does not meet the required prefix. A narrow error-handler customization is needed to preserve the argparse usage text and prepend the contract prefix. This does not alter the CLI semantics. [Python argparse error/exiting behavior](https://docs.python.org/3.11/library/argparse.html#exiting-methods).

## 6. Cost Estimates

No infrastructure, hosted service, license, or recurring runtime cost is introduced. Runtime uses the Python standard library; pytest is test-only as allowed by the contract.

## 7. Task Outline (Preliminary)

1. Implement the `wordstat` module and pytest process-level tests for counts, ordering, formats, encoding, deterministic newline/output behavior, help, usage errors, and expected file errors.

The task is independent and fits one implementation phase. No separate integration task is justified by the repository evidence.

## 8. Risks & Mitigations

- **Cross-platform newline or encoding drift:** reconfigure stdout explicitly and assert raw process output bytes/newlines in tests.
- **Ambiguous error handling between argparse and file input:** test exit code, exact prefix/path, and empty stdout separately for usage, I/O, and decode failures.
- **Accidental tokenization drift:** test ASCII-only `[a-z0-9]+` behavior, lowercasing, frequency ties, and punctuation/non-ASCII boundaries.
- **Platform-specific unreadable-file tests:** use deterministic missing-file and directory cases everywhere; test permissions only where the platform reliably supports them.

## 9. Acceptance Criteria

Acceptance is measured against root `contract.md` and includes:

1. `python -m wordstat --help` exits 0; the module runs from the repository root on Python 3.11+.
2. Exactly one named file is read as UTF-8 with optional BOM; stdin is not read.
3. Counts use precisely `splitlines()`, `[a-z0-9]+` over `text.lower()`, and `len(text)`.
4. Top words use count-descending/word-ascending order, with default N=3 and `N >= 1`.
5. Text and JSON formats, property/key order, trailing LF, stdout encoding and newline behavior match the contract byte-for-byte.
6. Missing/directory/unreadable and invalid-UTF-8 inputs exit 3 with their exact required message suffix; usage errors exit 2 with the required prefix; all expected errors leave stdout empty and do not traceback.
7. Pytest tests exercise the public module CLI and pass on the tested Python 3.11+ environment without any runtime dependency beyond the standard library.

## 10. Dependencies on Prior Features

None. There are no prior specs or repository modules to integrate.

## 11. Delegation to Future Specs

None. Additional statistics, stdin, multi-file processing, installation, or alternate tokenization would be separate future requirements and are deliberately not part of this delivery.

## Sources and Assumptions

- **Authoritative local source:** repository-root `contract.md`, which defines the package path, CLI, exact computation/output semantics, and exit behavior; `brief.md` supplies the concise product goal and requires pytest coverage.
- **Research source:** official Python 3.11 documentation links in Section 4 and the argparse error-handling link in Section 5. Research verified API compatibility; it did not change or extend requirements.
- **Codebase finding:** no prior implementation, test suite, or conventions existed, so there were no codebase integration claims to assume.
- **Decision record:** contract precedence resolves any possible conflicts. Researchers found no factual disagreement; standard-library-only runtime and no added scope are retained. No unresolved requirement question remains.
