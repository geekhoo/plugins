# Implementation Review — docs/spec-001-feature/ (wordstat)

Reviewed revision: `96604d3` (tree at end of geeky-implement; suite 56 passed).
Authoritative requirement: `contract.md` at the repository root. Prior task/phase
reviews (T1–T4 PASS; phase verdicts READY TO ADVANCE, agents a2f5942290fa1144d and
aee9018e6ba0b5b8d) are inputs, not re-litigated here.

## Reviewers Deployed

1. Counting Core & Output Formats — `wordstat/counts.py` semantics and format bytes
2. CLI Surface, I/O & Error Contract — `wordstat/cli.py`, `wordstat/__main__.py`
3. Contract Coverage & Cross-Phase Integration — `tests/*` vs contract + AC1–AC13

---

## Counting Core & Output Formats Review

<!-- reviewer-complete: counting-core -->
(reviewed revision `96604d3`; files: `wordstat/counts.py`, `wordstat/__init__.py`, `tests/test_counts.py`)

### Critical Issues (must fix)
- None found

### Warnings (should fix)
- None found

### Evidence summary
- R3 exact (`counts.py:9,13-15`): `words` = `len(re.findall(r"[a-z0-9]+", text.lower()))` —
  literal class on `str.lower()`, not `\w`, no `IGNORECASE`/`casefold`;
  `lines=len(text.splitlines())`; `chars=len(text)` code points.
- R4 (`counts.py:11,16`): explicit `sorted(..., key=lambda kv: (-kv[1], kv[0]))[:top_n]`;
  `Counter.most_common()` never used for ordering; items shaped `{"word","count"}`.
- R5 text (`counts.py:20-31`): exactly four `\n` lines; empty top yields bare `top:`
  (no trailing space); non-empty `word=count` join matches the worked example.
- R5 JSON (`counts.py:34-41`): `json.dumps(obj) + "\n"` default separators; key order
  `lines, words, chars, top` rebuilt explicitly; no `sort_keys`/custom separators.
- Purity: no I/O, no locale, total order well-defined on ASCII tokens.
- Integration: `cli.py:6,39-40` calls `counts.analyze`/`render_text`/`render_json` as
  module attributes; shapes and signatures match.

### Suggestions (nice to have)
- `analyze` does not guard `top_n >= 1` (`counts.py:11`) — unreachable via CLI; a
  `ValueError` guard would make the pure API self-defending.
- `test_empty_text` asserts via `endswith`/`in` rather than full byte-exact strings
  (already covered end-to-end by `tests/test_contract.py:142`).

### Verdict: PASS

---

## CLI Surface, I/O & Error Contract Review

<!-- reviewer-complete: cli-contract -->
(reviewed revision `96604d3`; files: `wordstat/cli.py`, `wordstat/__main__.py`, call-site spot-check of `wordstat/counts.py`)

### Critical Issues (must fix)
- None found by the reviewer

### Warnings (should fix)
- **Exit-1 / "never a traceback" hole on stdout write** (reviewer confidence 80) —
  `wordstat/cli.py:47`: `sys.stdout.write(output)` sits outside the `try` that maps
  exceptions. A stdout failure (e.g. `BrokenPipeError` from `python -m wordstat big.txt | head`)
  escapes `main()` uncaught: large output yields a raw traceback (exit 1), buffered
  output fails at interpreter shutdown ("Exception ignored", exit 120) — neither the
  contract's reserved exit-1 `wordstat: error: internal error` path nor any in-table
  exit code. Smallest correction: wrap only the write
  (`try: sys.stdout.write(output); sys.stdout.flush() except Exception: -> exit 1
  wordstat: error: internal error`); it must NOT fall into the existing
  `except OSError` read-failure mapping, which would mislabel a write failure as
  `<path>: cannot read file`.

### Verified exact
Invocation surface (`prog="wordstat"` hardcoded, `--json`/`--top`/one FILE,
`ArgumentTypeError` converter for non-int or `<1`, argparse defaults otherwise —
`cli.py:32-35,9-16`); R2 read path (`open(path,"rb")` + `decode("utf-8-sig")`, no
newline translation, stdin never read, `-` is an ordinary positional — `cli.py:19-21,38`);
error table (one `wordstat: error: ` stderr line, stdout empty on error, raw argv path
echo, exits 3/3/2/0/1 — `cli.py:24-26,41-48`); R6 (`reconfigure(encoding="utf-8",
newline="\n")` for stdout and stderr first in `main()` per D4 — `cli.py:30-31`); exit
path (`raise SystemExit(main())`, `main() -> int`, no `sys.exit` in helpers);
exception order `UnicodeDecodeError` → `OSError` → bare `Exception` with time-of-call
attribute lookup so the `counts.analyze` monkeypatch seam works.

### Suggestions (nice to have)
- `cli.py:14-15`: `n < 1` message `invalid int value: '{value}'` is misleading for
  numeric-but-out-of-range input (contract does not pin usage-error wording).
- A broken-pipe/write-failure regression test is absent (covered by fix below).

### Verdict: PASS WITH WARNINGS

---

## Contract Coverage & Cross-Phase Integration Review

<!-- reviewer-complete: test-coverage -->
(reviewed revision `96604d3`; files: `tests/conftest.py`, `tests/test_counts.py`, `tests/test_cli.py`, `tests/test_contract.py`, seams in `wordstat/*`, `draft.md`, T4 notes)

### Critical Issues (must fix)
- None found

### Warnings (should fix)
- **Internal-error body over-pin** — `tests/test_contract.py:231` asserts exactly
  `b"wordstat: error: internal error\n"`. The contract fixes only exit 1, one stderr
  line, and the `wordstat: error: ` prefix (the exit-1 body is unspecified); a
  compliant implementation printing another body fails this test. Smallest correction:
  assert `code == 1`, empty stdout, `err.startswith("wordstat: error: ")`, single line,
  `b"Traceback" not in err`.

### Coverage confirmation
Every contract rule asserted byte-exact where the contract is literal: R1
(`test_cli.py:10-14`), R2 (`test_cli.py:41-58`; BOM `test_contract.py:19-34`;
stdin-never-read `:165-196`), R3 (`test_counts.py:8-24`; CRLF/lone-CR
`test_contract.py:37-58`; splitlines extras `:61-72`; İ/K/é `:92-125`), R4 (worked
example cuts through a 4-way tie over 6 distinct words — `test_cli.py:38` and
`test_contract.py:211-215` genuinely pin default 3 and boundary tie selection), R5, R6
(byte asserts + `PYTHONIOENCODING=ascii` gate `test_contract.py:199-208`), full error
table (missing/dir/unreadable/invalid-UTF-8/raw-path echo/usage rows) and exits 0/1/2/3.
Worked example replayed both formats (`test_contract.py:211-219`). All enumerated
regression classes discriminate: `most_common()`, `open()` text mode, missing
`reconfigure`, locale-default encoding, `Path` normalization (`:157-162`),
`sys.exit("msg")`, `json.dumps` separators/`sort_keys`, `\w`/IGNORECASE, Traceback
leaks. Seams live (`cli.py:19` `_read_bytes`, `counts.py:8` `analyze`); `run_wordstat`
drives the real `python -m wordstat` entry; all fixture writes go to `tmp_path`.

### Suggestions (nice to have)
- R6 stdout `reconfigure` is only observable on Windows; an in-process spy on
  `sys.stdout.reconfigure` would close the Linux gap (existing `b"\r" not in` asserts
  are the black-box proxies).
- `tests/test_counts.py:20-24` pins `analyze()`'s in-memory dict key order (not
  contract-required; `render_json` rebuilds the dict).
- `tests/test_contract.py:157-162` assumes `./missing.txt` / `./a/../missing.txt` do
  not exist under `cwd=REPO_ROOT`.
- `draft.md:10-21` matrix Status column still says "Planned" (frozen planning artifact;
  not editable during implementation — accepted as-is).

### Verdict: PASS WITH WARNINGS

---

## Consolidated findings

### Critical Issues (across all reviewers)
- **C-impl-1** (elevated from CLI warning; AC11 "never a traceback" + contract exit
  table): uncaught stdout write failure bypasses the reserved exit-1 path
  (`wordstat/cli.py:47`) — traceback (exit 1) or interpreter-shutdown exit 120 on
  `BrokenPipeError`. Contract violation path; elevated to Critical at consolidation
  because it demonstrably defeats AC11.

### Warnings
- **W-impl-1** (test over-pin): `tests/test_contract.py:231` pins the unspecified
  exit-1 message body (`tests/test_contract.py` internal-error case).

### Top Suggestions (follow-ups only — do not block acceptance)
1. Guard `top_n >= 1` in `counts.analyze` (self-defending pure API).
2. In-process spy asserting `sys.stdout.reconfigure(encoding="utf-8", newline="\n")`.
3. Friendlier `--top` out-of-range usage message (contract wording unpinned).
4. Byte-exact assertion style in `test_empty_text`.
5. `draft.md` matrix Status column refresh (frozen artifact — record only).

### Per-Reviewer Verdicts
| Reviewer | Verdict |
|----------|---------|
| Counting Core & Output Formats | PASS |
| CLI Surface, I/O & Error Contract | PASS WITH WARNINGS |
| Contract Coverage & Cross-Phase Integration | PASS WITH WARNINGS |

### Overall: NEEDS FIXES (1 critical)

Remediation (pre-authorized): fix C-impl-1 via `geeky-coder`; apply W-impl-1 as the
option closest to `contract.md` (see handoff decision log); then re-review the affected
scope and record the final verdict below.

## Final verdict (post-remediation)

_Pending re-review of affected scope._
