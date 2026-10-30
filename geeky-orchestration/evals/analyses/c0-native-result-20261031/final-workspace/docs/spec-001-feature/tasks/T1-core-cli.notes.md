# T1 Core CLI Notes

## Implementation

- Added `wordstat/__main__.py` with argparse help/arguments, UTF-8-sig input, contract counting and ranking, text/JSON output, and UTF-8/LF stdout configuration.
- Input is opened with `newline=""` so CR and LF code points are preserved for `len(text)` while `splitlines()` still determines logical line count.
- Added subprocess tests for help, exact example output, JSON output/key order, BOM handling, CRLF character/line counts, empty and no-token inputs, tie ordering, larger-than-distinct `--top`, and locale-independent output.
- Source inspection confirms the CLI does not import, query, or apply locale settings.

## Validation Evidence

- Command: `python -m pytest -q tests/test_wordstat.py`
- Result: exit 0; `8 passed in 1.65s`.
- Locale comparison: ran the same input through `python -m wordstat <fixture>` with `LC_ALL=C.UTF-8` and `LC_ALL=C`; both exited 0 with empty stderr and identical stdout bytes: `b'lines: 1\nwords: 5\nchars: 14\ntop: a=1 cat=1 dog=1\n'`.
- Environment: Python 3.13.15, pytest 9.0.3.
- Tested against HEAD `db45ad94d88abb4eb4c5fe389fc9d2262b0515b8`; implementation and test files were untracked at validation time (not committed).
- Previous parent verification passed before the CRLF fix: `python -m pytest -q tests/test_wordstat.py` -> exit 0, `8 passed in 1.58s`; `git diff --check` -> exit 0.
- Reviewer finding: default text-mode universal-newline conversion changed CRLF to LF before `len(text)`, violating R3. Fixed by passing `newline=""` to `open`; added a subprocess regression asserting CRLF input has two lines and six characters.
- Post-fix required validation: `python -m pytest -q tests/test_wordstat.py` -> exit 0, `9 passed in 1.74s`.
- Focused CRLF subprocess check using fixture bytes `41 0d 0a 42 0d 0a` -> exit 0, empty stderr, stdout `b'lines: 2\nwords: 2\nchars: 6\ntop: a=1 b=1\n'`.
- `git diff --check` -> exit 0 (Git emitted existing line-ending normalization warnings for parent-owned handoff/kanban files).
- Tested against HEAD `db45ad94d88abb4eb4c5fe389fc9d2262b0515b8`; post-fix changes remain uncommitted. SHA-256 after fix: `wordstat/__main__.py` `B646159F4B1756925E5A6183DC8831CB8DFEA307D6ACD9B88D1BDE4B218C3BC2`; `tests/test_wordstat.py` `DA4B77315D678FEC2259392108918A952B3755842724EA34D01F7F4DADA8795A`.

## Acceptance Evidence

- Help subprocess asserts return code 0 and `usage: wordstat` in stdout.
- Example text and `--json --top 2` assert exact stdout bytes and empty stderr.
- BOM input reports four decoded characters, excluding the BOM; empty file and punctuation-only input assert exact `top:\n` output.
- Tied counts assert lexical ordering, and `--top 8` returns all three distinct tokens.
- CRLF test verifies preserved decoded newline code points (`chars: 6`) alongside `splitlines()` counting (`lines: 2`).
- Source test asserts exact `sys.stdout.reconfigure(encoding="utf-8", newline="\\n")` call and absence of locale references.

## Review Findings and Resolution

- Initial phase review `/root/phase1_review`: NEEDS FIXES because default text-mode universal-newline conversion changed CRLF before `len(text)`, violating contract R3. Resolved in scope by opening with `newline=""` and adding the CRLF regression test.
- Focused re-review `/root/phase1_review`: T1 PASS; Phase 1 READY TO ADVANCE. AC-by-AC review confirmed help, UTF-8/BOM/counting (including CRLF), ranking, exact text/JSON output, UTF-8/LF output, and locale independence. `python -m pytest -q tests/test_wordstat.py` -> exit 0, 9 passed in 2.34s; `git diff --check` -> exit 0. No remaining findings; no deferred fixes.
- Resolution: the single required finding was fixed and re-reviewed. Touched files remain `wordstat/__main__.py` and `tests/test_wordstat.py`.
