# T2 Contract Edge Cases Notes

## Implementation

- Extended `tests/test_wordstat.py` with usage failures for invalid `--top` values, missing/unknown/extra arguments, and stdin supplied without a FILE.
- Added exact file/decode failure tests for missing paths, directory paths, invalid UTF-8, and unreadable files where the host can represent unreadability.
- Added Unicode lowercase/tokenization, code-point character count, and `splitlines()` boundary coverage computed from the contract expressions.
- Contract defects found and corrected in `wordstat/__main__.py`: Windows translated stderr LF to CRLF, so stderr is now reconfigured to UTF-8 with `newline="\n"` to satisfy the exact error-line contract. The existing stdout configuration is unchanged.

## Validation Evidence

- Required command: `python -m pytest -q tests/test_wordstat.py`
- Result: exit 0; `21 passed, 1 skipped in 3.77s`.
- Parent verification against unchanged post-worker files: `python -m pytest -q tests/test_wordstat.py` -> exit 0, `21 passed, 1 skipped in 4.32s`.
- Skip detail from `python -m pytest -q -rs tests/test_wordstat.py`: unreadable-file test skipped because the host process/filesystem can still read a mode-000 file.
- `git diff --check` -> exit 0; Git reported line-ending normalization warnings for changed working files.
- Environment: Python 3.13.15, pytest 9.0.3.
- Tested against HEAD `19f20a3833592d71d2b789d02750da9365b75c7d`; task changes are uncommitted. SHA-256: `wordstat/__main__.py` `306DCE515806E444B7F1736182C20EDA889CDB691C30AB4FF2CD1AFF88F5AF03`; `tests/test_wordstat.py` `680836D1211F872BE715F24F02409F97E4892392700991720F76F0C36F32D904`.

## Acceptance Evidence

- Usage cases assert exit 2, empty stdout, final stderr prefix, and no traceback.
- Missing path, directory, and invalid UTF-8 cases assert exit 3, empty stdout, exact path-preserving stderr bytes, and no traceback.
- Stdin with no FILE is supplied and remains an argparse usage error.
- Unicode and line boundary expected output is derived independently from `text.lower()`, `[a-z0-9]+`, `len(text.splitlines())`, and `len(text)`.
- Unreadability could not be represented on this host: after removing all file permission bits, both the test process and child process still read the file. The regression is retained and will assert exact behavior on hosts that can enforce the permission change.

## Review Findings and Resolution

- Phase 2 reviewer `/root/phase1_review`: T2 PASS; Phase 2 READY TO ADVANCE. AC-by-AC review confirmed usage, file/decode, stdin, Unicode and line semantics, plus no stdout/tracebacks on specified failures. Exact stderr byte assertions exercise the Windows UTF-8/LF stderr reconfiguration. Sole permitted skip is unreadable-file behavior because this host can read a mode-000 file; reviewer independently confirmed via `pytest -q -rs`.
- Reviewer validation: `python -m pytest -q tests/test_wordstat.py` -> exit 0, 21 passed, 1 skipped in 3.96s; `python -m pytest -q -rs tests/test_wordstat.py` confirms the sole permitted skip; `git diff --check` -> exit 0. Parent full suite: `python -m pytest -q` -> exit 0, 21 passed, 1 skipped in 3.95s.
- Required finding resolution: the verified Windows stderr newline translation defect was fixed by configuring stderr UTF-8/LF. No remaining required findings. Unreadable-file test skip is a host limitation, not deferred product work.
