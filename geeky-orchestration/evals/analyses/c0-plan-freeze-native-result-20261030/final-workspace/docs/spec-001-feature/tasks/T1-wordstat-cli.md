Task Name:
Implement wordstat CLI and contract tests

Context:
The package is greenfield. This task implements the full public command and tests its observable behavior against root `contract.md` and `feature-specification.md`.

Scope:

In scope:
---
- Add a flat `wordstat/` package at repository root with the `python -m wordstat` entry point.
- Implement argument parsing, UTF-8-sig file reading, counting, stable sorting, text/JSON formatting, stdout configuration, and expected error handling exactly as contracted.
- Add pytest process-level tests under `tests/` for successful and expected-error behavior.

## Out of scope:
- stdin, multiple files, recursive processing, third-party runtime packages, installation metadata, and behavior not required by `contract.md`.

Module/System:
Python CLI package and pytest test suite.

## Dependencies:

* None

## Technical Notes:
- Root `contract.md` is authoritative; do not normalize or broaden its observable details.
- Requirements R1-R6 and exact formats/errors are recorded in `implementation-plan.md` and `feature-specification.md`.
- Use `argparse` with `prog="wordstat"`; customize usage error formatting to guarantee its required prefix.
- Process-level tests should invoke the current interpreter with `-m wordstat` from the repository root and assert output bytes when checking LF determinism. Add one direct `main()` unit test with a recording stdout spy because output is ASCII and process bytes alone cannot prove the required reconfiguration call.
- For all expected errors, separately assert the exit code, required stderr text/prefix, and empty stdout. Do not accept a traceback.
- Expected file error text copied verbatim from `contract.md`: `<path>: cannot read file`; `<path>: not valid UTF-8`.
- Usage stderr's last line must match the verbatim predicate from `contract.md`: `^wordstat: error: `.
- Text success contract (exact shape, with values substituted):
  ```text
  lines: <lines>
  words: <words>
  chars: <chars>
  top: <word>=<count> <word>=<count> ...
  ```
  Each of the four lines ends in `\n`; if there are no words, the last line is exactly `top:` with no trailing space.
- JSON success is one line from `json.dumps(obj)` with default separators and ordered keys `lines`, `words`, `chars`, `top`; each top entry has ordered keys `word`, `count`.
- Supported runtime is Python >=3.11 and the standard library only; pytest is test-only.

## Acceptance Criteria:

* AC1: `python -m wordstat --help` from repository root exits 0; normal invocation accepts the contract's single `FILE` and optional `--json`/`--top N`, and rejects a second `FILE` as usage error 2.
* AC2: The command reads only `FILE`, decodes UTF-8 with optional BOM, does not read stdin, and counts with exactly the R3 formulas.
* AC3: `--top` defaults to 3; valid `N >= 1` returns up to N terms ordered count descending then word ascending; fewer distinct terms all appear; invalid integer or `N < 1` is usage error 2.
* AC4: Default text output exactly matches the four-line contract format, including a final LF and `top:` for no words; `--json` emits exactly one LF-terminated JSON line with required values, default separators, and key order.
* AC5: `sys.stdout.reconfigure(encoding="utf-8", newline="\n")` is called before output; stdout has byte-for-byte deterministic UTF-8/LF output on the tested platform.
* AC6: Missing file, directory, and unreadable-file conditions exit 3 with stderr suffix `<path>: cannot read file`; invalid UTF-8 exits 3 with `<path>: not valid UTF-8`; `<path>` is the argument exactly as given.
* AC7: Missing FILE, unknown flag, non-integer `--top`, and `--top` below 1 exit 2, have no stdout, and the last stderr line matches `^wordstat: error: `; expected errors do not traceback.
* AC8: Tests use pytest and the runtime imports only Python 3.11+ standard-library modules.

Definition of Done:

* Code reviewed
* Tested (manual/unit)
* No critical bugs

Tests/Validation Before Next Task:
- `python -m pytest -q` from repository root. The tests must contain at least one check for each AC below; this single task has no successor task.
- AC1: subprocess `python -m wordstat --help` returns 0; successful invocation with one file and each option form proves the accepted arguments; pass a valid first FILE and a second FILE and assert usage exit 2, empty stdout, and last stderr line matching `^wordstat: error: `.
- AC2: compare a BOM-prefixed UTF-8 file and a no-BOM file against `len(text.splitlines())`, `len(re.findall(r"[a-z0-9]+", text.lower()))`, and `len(text)`; start the CLI with a valid FILE and an open `stdin=PIPE` to which no bytes are written, then require it to exit within a short timeout with the file result. On timeout, fail the test (the child attempted a blocking stdin read), terminate it, and collect streams.
- AC3: assert default top count 3, `--top 1`, `--top` larger than distinct count, tied counts in ascending word order; test non-integer and `0` as exit 2, empty stdout, and last stderr line matching `^wordstat: error: `.
- AC4: assert exact four-line output bytes with `\n`, final LF, empty-input `top:\n`; assert JSON equals `json.dumps(expected_object).encode("utf-8") + b"\n"`, using ordered dict construction matching `lines`, `words`, `chars`, `top` and nested `word`, `count`.
- AC5: patch the module's `sys.stdout` to a recording spy, invoke `main()` with a valid file, and assert exactly one call `reconfigure(encoding="utf-8", newline="\n")` before `write`; also assert subprocess stdout bytes contain no `\r` and are stable under a locale/environment variation where available.
- AC6: for a missing path and a directory, assert process exit 3, stdout is empty, and stderr's content after `wordstat: error: ` is exactly `<path>: cannot read file` with `<path>` equal to the exact argument; deterministically unit-test an unreadable file by making `open()` raise `PermissionError`, invoking the CLI handler, and asserting `SystemExit.code == 3`, empty captured stdout, and stderr suffix `<path>: cannot read file`; for malformed bytes assert process exit 3 and exact suffix `<path>: not valid UTF-8`, empty stdout, no traceback. An actual OS-level permission test may supplement but does not replace the simulated case.
- AC7: test missing FILE, unknown flag, and a second positional FILE in addition to the AC3 bad-top cases; assert return code 2, `stdout == b""`, and the last stderr line matches the source predicate `^wordstat: error: `.
- AC8: inspect imports for runtime standard-library-only use; `python -m compileall -q wordstat tests` succeeds and pytest is invoked as `python -m pytest -q`.
- Manual contract example: create the exact example text from `contract.md`; assert text output is `lines: 3\nwords: 8\nchars: 33\ntop: cat=2 the=2 a=1\n` and JSON output is `{"lines": 3, "words": 8, "chars": 33, "top": [{"word": "cat", "count": 2}, {"word": "the", "count": 2}]}\n`.
- `git diff --check` exits 0.

Estimate:
M

Priority:
P1
