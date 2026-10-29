# wordstat Specification

**Status:** Not Started
**Dependencies:** None
**Layer:** Domain / CLI utility
**Priority:** Required by the repository brief
**Estimated Complexity:** 2 tasks across 2 implementation phases

---

## 1. Executive Summary

Build a small Python 3.11+ standard-library command-line package at `wordstat/`. From the repository root, `python -m wordstat [--json] [--top N] FILE` reads exactly one UTF-8 file, computes the contract-defined line, word, and character counts, and prints either a four-line text summary or one-line JSON. Its bytes and errors must be deterministic across Windows, macOS, and Linux. The complete interface contract is [the authoritative repository contract](../../contract.md); this specification restates it for planning and does not supersede it.

Research found no existing application code, tests, packaging metadata, or CI configuration to extend. The contract is therefore the controlling design source. [A1]

## 2. Problem Statement

### Current State

The repository contains only `brief.md` and `contract.md`; the requested `wordstat` package and its pytest tests do not yet exist. [A1]

### Impact of Inaction

There is no executable implementation of the requested interface, so callers cannot obtain the contracted statistics or rely on its cross-platform output and error behavior.

## 3. Goals & Non-Goals

### Goals

- Provide the root-invoked module command and standard `--help` behavior.
- Read one named file as UTF-8 with an optional BOM; never read stdin.
- Compute exactly the counts and ranking defined by R3 and R4 below.
- Produce exactly the specified text or JSON output, with deterministic UTF-8 and LF output.
- Handle expected input and usage failures with the specified stderr and exit codes, without a traceback.
- Add pytest coverage of observable CLI behavior and run it on the available platform.

### Non-Goals

- Supporting stdin, multiple input files, configurable tokenization, Unicode word classification, alternate encodings, or recursive input discovery.
- Adding runtime dependencies, install/build metadata, a console-script entry point, persistent reports, or a CI workflow.
- Changing any requirement in `contract.md`.

## 4. Architecture

- Use a flat root package: `wordstat/__init__.py` as needed and `wordstat/__main__.py` for `python -m wordstat`.
- Keep command parsing, file loading, counting, and rendering small and explicit. The runtime uses only the Python 3.11+ standard library; pytest is test-only.
- Invoke through a subprocess in tests using the active interpreter and repository root as the working directory. Capture output as bytes to verify encoding and line endings. [A2]

## 5. Detailed Design

### Command and input

- Command: `python -m wordstat [--json] [--top N] FILE`.
- Configure argparse with `prog="wordstat"`, its normal help action, one positional `FILE`, and `--top` defaulting to 3.
- `--top` must parse as an integer >= 1. Missing `FILE`, unknown options, and invalid `--top` are usage errors with exit 2.
- Read only the path given by `FILE`, preserving that exact spelling in diagnostics. Decode with `utf-8-sig` so a leading UTF-8 BOM is accepted and excluded from counts. Do not read stdin.
- Count decoded code points as-is. In particular, do not normalize CRLF to LF before `chars = len(text)`; `lines = len(text.splitlines())` remains Python's specified splitlines count. Direct byte reading followed by `utf-8-sig` decoding is one way to make this behavior explicit. [A3]

### Counts and top words

- `lines = len(text.splitlines())`.
- `words` are exactly the non-overlapping `[a-z0-9]+` matches in `text.lower()`; `words` is their total count.
- `chars = len(text)`, counting Python string code points after optional BOM removal.
- `top` contains up to N distinct tokens, sorted by frequency descending and token ascending. Return all tokens when there are fewer than N.
- Preserve the literal regex and lowercase-before-matching rule. Unicode-aware `\w` or case-insensitive regex alternatives do not satisfy the contract. [A4]

### Output

- Reconfigure stdout with `encoding="utf-8"` and `newline="\n"` before writing.
- Default text output is exactly four lines, each terminated by LF: `lines: <n>`, `words: <n>`, `chars: <n>`, and `top: <word>=<count> ...`. With no tokens, output `top:\n` without a trailing space.
- With `--json`, emit one line from `json.dumps(obj)` using default separators, followed by LF. The object key order is `lines`, `words`, `chars`, `top`; each top element has key order `word`, `count`.
- Avoid locale-sensitive formatting or platform newline defaults. The required output configuration and default JSON separators are documented Python interfaces. [A5]

### Errors and exit codes

- Missing, directory, or unreadable input: exit 3; one stderr line `wordstat: error: <FILE>: cannot read file`.
- Invalid UTF-8: exit 3; one stderr line `wordstat: error: <FILE>: not valid UTF-8`.
- Usage errors: use argparse's default usage-error output and exit 2; the final stderr line must start `wordstat: error: `; stdout stays empty.
- Unexpected internal errors remain exit 1 and are not converted into expected input errors.
- Resolve the contract wording conflict by treating its specific requirement for argparse's default usage-error form as controlling over the general one-line error statement. Stock argparse may therefore emit both a usage line and an error line for usage failures; file and decoding failures remain exactly one line. [A6]

## 6. Cost Estimates

No external services, paid APIs, or runtime packages are required. Runtime cost is limited to reading and processing the selected file in memory; the contract does not require streaming.

## 7. Task Outline (Preliminary)

1. Implement the pure `analyze_text(text, top)` counting core and focused tests for R3/R4.
2. Add the `python -m wordstat` CLI boundary and subprocess pytest coverage for arguments, file decoding, output bytes, expected errors, and help. Validate the complete suite on the available platform; retain exact CLI output/exit evidence. A multi-OS CI setup is not in scope.

## 8. Risks & Mitigations

- **Newline translation changes character counts:** read bytes and decode explicitly; test CRLF input. [A3]
- **Unicode tokenization differs from the required ASCII classes:** use the exact lower-then-regex sequence and test non-ASCII boundaries. [A4]
- **Platform text streams introduce encoding or newline differences:** explicitly reconfigure stdout and assert captured bytes. [A2, A5]
- **Usage error wording can be interpreted as one-line-only:** retain default argparse behavior because the table specifically requires it; test the final diagnostic line and exit code. [A6]
- **Cross-platform behavior cannot be fully demonstrated on a single host:** verify byte-level behavior locally and note that no existing OS-matrix CI is present. [A1, A2]

## 9. Acceptance Criteria

The implementation is acceptable only when all of the following contract criteria pass:

- `python -m wordstat --help` exits 0 and identifies the program as `wordstat`.
- The command accepts exactly one file argument, optional `--json`, and optional positive integer `--top`; it never reads stdin.
- UTF-8 and UTF-8-with-BOM files are decoded correctly; invalid UTF-8 is a clean exit-3 error.
- Counts and top ordering match the exact definitions above, including empty files, line endings, and fewer than N distinct words.
- Default output is exactly four LF-terminated lines; JSON output is exactly the one-line default `json.dumps` representation plus LF, with required key ordering.
- Stdout is UTF-8/LF and remains empty on expected failures. File and decode failures have their exact one-line stderr messages and exit 3. Usage errors have argparse's default usage form, final error prefix, and exit 2.
- No expected bad input produces a traceback. Runtime imports use only the standard library.
- The pytest suite passes, including subprocess-level byte, stderr, and exit-code assertions.

## 10. Dependencies on Prior Features

None. Python 3.11+ is the environment prerequisite. pytest is required only to execute tests.

## 11. Delegation to Future Specs

None. Packaging for installation, a console-script alias, streaming large files, additional encodings, and CI OS matrices are explicitly deferred unless separately requested.

---

## Research Findings, Sources, and Assumptions

- **[A1] Repository context:** there is no existing Python code, test suite, packaging configuration, CI workflow, or integration surface. Source: repository file scan and `git status --short`; authoritative behavior: `brief.md` and `contract.md`.
- **[A2] CLI testing:** pytest `tmp_path` and parametrization support isolated byte-exact fixtures; Python subprocess capture without text mode supports platform-independent byte assertions. Sources: [pytest tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html), [pytest parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html), [Python subprocess](https://docs.python.org/3/library/subprocess.html). Assumption: tests run the module from the checkout root as the contract requires.
- **[A3] Decoding/newlines:** `utf-8-sig` removes a leading UTF-8 signature; universal-newline text reads can translate CRLF and alter `len(text)`. Sources: [Python codecs](https://docs.python.org/3/library/codecs.html#standard-encodings), [Python text I/O](https://docs.python.org/3/library/io.html#text-i-o). Decision: use decoded code points without newline normalization because R3 defines counts on decoded text; an alternative would normalize newlines, but that would change the decoded character count and conflict with the literal formula.
- **[A4] Tokenization:** Python's `re` defines the required character classes and matching behavior. Source: [Python regular expressions](https://docs.python.org/3/library/re.html). Decision: use `[a-z0-9]+` over `text.lower()` exactly; do not substitute Unicode `\w` or regex case-insensitivity.
- **[A5] Serialization and argument parsing:** argparse supports explicit `prog` and typed argument validation; `json.dumps` provides the specified default separators; Python text streams expose `reconfigure`. Sources: [argparse](https://docs.python.org/3/library/argparse.html), [JSON](https://docs.python.org/3/library/json.html#json.dumps), [Python standard streams](https://docs.python.org/3/library/sys.html#sys.stdout). Assumption: standard Python 3.11+ runtime behavior is sufficient; no third-party CLI layer is needed.
- **[A6] Error wording:** default argparse usage errors include usage text plus the final error diagnostic, whereas the general contract paragraph says errors are one line. Source: [argparse error behavior](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.error); contract.md's usage-error row is the authoritative exception. Decision: retain default argparse output for usage failures; alternative one-line custom formatting would no longer be argparse's default. This was the only material researcher disagreement/ambiguity; no external research conflicts with the contract.
