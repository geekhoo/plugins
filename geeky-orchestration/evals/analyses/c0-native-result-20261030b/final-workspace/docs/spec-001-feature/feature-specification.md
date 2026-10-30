# wordstat Specification

**Status:** Specification written; planning not yet reviewed
**Dependencies:** None
**Layer:** Developer tooling / Python CLI
**Priority:** Required by the root contract
**Estimated Complexity:** Small, one implementation phase

## 1. Executive Summary

Implement `wordstat`, a flat-layout Python 3.11+ package runnable from the repository root as `python -m wordstat FILE`. It reads one UTF-8 text file, counts lines, ASCII word tokens and decoded code points, and reports the most frequent tokens as deterministic text or JSON. Runtime dependencies are limited to the standard library; pytest is used only for tests. The root `contract.md` is authoritative for the complete interface, exact output, errors, and exit codes.

## 2. Problem Statement

### Current State

The repository contains the brief and interface contract, but no application package, tests, or project configuration. There is no existing CLI convention to preserve.

### Impact of Inaction

The requested module command and contract-defined statistics are unavailable.

## 3. Goals and Non-Goals

### Goals

- Satisfy every requirement and exact string in root `contract.md`.
- Provide predictable cross-platform stdout bytes and deterministic top-word ordering.
- Test the command through its public module interface, including failure codes and streams.

### Non-Goals

- Packaging, installation, stdin input, recursive processing, configurable tokenization, localization, or runtime third-party dependencies.
- Changing or relaxing the root interface contract.

## 4. Architecture

Create `wordstat/` at repository root with `__main__.py` for argument parsing, input/error handling, statistics and output. Keep any reusable logic in this package only if it makes behavior clearer. Add pytest tests at repository root (or a conventional `tests/` directory); pytest is test-only. No build metadata is needed for `python -m wordstat` from the repository root.

The input must be opened with UTF-8-with-optional-BOM decoding and newline preservation (for example `encoding="utf-8-sig", newline=""`): universal-newline translation would alter `len(text)` for CRLF or CR files. Then compute the exact expressions in the contract: `len(text.splitlines())`, token matches `[a-z0-9]+` in `text.lower()`, and `len(text)`. Sort top words by descending count and ascending word, rather than relying on encounter-order tie behavior. Reconfigure stdout to UTF-8 and LF before writing.

## 5. Detailed Design

- Use `argparse.ArgumentParser(prog="wordstat")`; expose `--help`, `--json`, `--top N`, and one required positional `FILE`.
- Validate `--top` as an integer of at least 1 and route invalid values through argparse's usage-error behavior.
- Read only the supplied file; never inspect or consume stdin.
- Decode with `utf-8-sig`. Map file-not-found, directory, other read failures to the contract's read error; map `UnicodeDecodeError` to its distinct invalid-UTF-8 error. Both return 3, write exactly the required prefixed line to stderr, and write nothing to stdout.
- Preserve the given FILE argument text in the error message.
- Emit the exact four-line text layout or one-line default `json.dumps` object in specified key order, with trailing LF and no locale-sensitive behavior.

## 6. Runtime and Test Dependencies

Runtime: Python standard library only. Compatibility floor: Python 3.11. Tests: pytest only. The current research environment has Python 3.13.15 and pytest 9.0.3; implementation validation must run the repository's available Python/pytest and make no claim of testing other operating systems unless actually done.

## 7. Preliminary Task Outline

1. Implement the package CLI and its contract-defined output/error handling.
2. Add black-box pytest coverage for successful formats/counts and deterministic bytes.
3. Add black-box pytest coverage for argument, file, and encoding failures; run the complete suite and module smoke checks.

These are preliminary and may be grouped into one bounded implementation task after planning, provided all contract requirements have local acceptance evidence.

## 8. Risks and Mitigations

- **Newline normalization changes character counts:** open with newline translation disabled and include CRLF/CR/LF assertions.
- **Platform encoding or newline conversion changes output bytes:** reconfigure stdout as required and assert subprocess stdout bytes.
- **Ties vary with input encounter order:** sort explicitly on `(-count, word)` and test tied words.
- **Argparse defaults use the wrong program label or wording:** set `prog="wordstat"`; assert exit code and final error prefix for usage errors.
- **Windows permission tests are not portable:** reliably test missing path and directory; use controlled error injection if explicitly testing other unreadable conditions.

## 9. Acceptance Criteria

The authoritative acceptance criteria are R1-R6 and the full command, text/JSON output, and error/exit-code tables in root `contract.md`. Implementation is accepted only when each is traceably tested, including exact output bytes, stream emptiness on errors, error prefix/path, usage behavior, UTF-8 BOM handling, and deterministic tie order. No alternate or weaker interpretation is introduced here.

## 10. Dependencies on Prior Features

None.

## 11. Delegation to Future Specs

None.

## Research Decisions and Sources

- `contract.md` takes precedence over `brief.md` and all research. Research found no requirement conflict and did not alter the interface.
- The codebase report found no existing package, tests, project metadata or conventions; therefore use the requested flat package and focused pytest tests.
- Official Python documentation confirms that `utf-8-sig` removes an optional BOM; `splitlines()` recognizes the specified line boundaries; explicit ASCII ranges avoid broader Unicode token matching; and text streams support the required reconfiguration. Cross-platform research additionally found that default text input newline translation would change character counts, so preserve newlines while decoding.
- Sources: `brief.md`; root `contract.md`; Python codecs: utf-8-sig (https://docs.python.org/3/library/codecs.html#encodings.utf_8_sig); str.splitlines (https://docs.python.org/3/library/stdtypes.html#str.splitlines); re (https://docs.python.org/3/library/re.html); open (https://docs.python.org/3/library/functions.html#open); TextIOWrapper.reconfigure (https://docs.python.org/3/library/io.html#io.TextIOWrapper.reconfigure); argparse (https://docs.python.org/3/library/argparse.html).
