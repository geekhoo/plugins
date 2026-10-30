Task Name:
Implement the wordstat module CLI and successful output

Context:
The repository has no implementation. This task establishes the package entry point and the successful CLI contract.

Scope:

In scope:
---
- Create `wordstat/__main__.py` implementing the contract's command, counting, ranking, text/JSON formatting, and deterministic stdout.
- Create initial `tests/test_wordstat.py` with subprocess tests for help and successful inputs.

## Out of scope:
- Detailed negative-input and usage-error regression coverage, assigned to T2.
- Any behavior not present in root `contract.md`.

Module/System:
Root-level `wordstat` Python package and pytest CLI suite.

## Dependencies:

* None

## Technical Notes:
- Production stack is Python >=3.11 standard library only; pytest is test-only.
- Follow `contract.md` exactly for `splitlines()`, regex tokenization, ordering, output layout and JSON key ordering.
- Configure stdout with `encoding="utf-8", newline="\n"`.
- See implementation-plan.md sections Design, Phase 1 and Validation Strategy.

## Acceptance Criteria:

* `python -m wordstat --help` exits 0 and displays a usage interface with program name `wordstat`.
* A named UTF-8 file with optional BOM is decoded, and `lines`, `words`, and `chars` match `len(text.splitlines())`, the number of `[a-z0-9]+` matches in `text.lower()`, and `len(text)` respectively.
* Top words use count descending then word ascending; default top count is 3 and output includes fewer than N distinct words when fewer exist.
* Default output is exactly four LF-terminated lines in the contract's text format, including `top:` with no trailing space when there are no words.
* `--json` emits exactly one LF-terminated `json.dumps(obj)` line with default separators and keys ordered `lines`, `words`, `chars`, `top`, and top objects ordered `word`, `count`.
* Standard output is reconfigured exactly with `encoding="utf-8", newline="\n"`, and successful output uses LF line endings.
* Counting and output do not consult locale settings; the same input produces identical bytes regardless of the active locale.

Definition of Done:

* Code reviewed
* Tested (manual/unit)
* No critical bugs

Tests/Validation Before Next Task:
- Run `python -m pytest -q tests/test_wordstat.py` from repository root and require exit 0.
- The tests must invoke `sys.executable -m wordstat --help`; assert return code 0 and that stdout contains `usage: wordstat`.
- For the contract example, assert exit 0, stderr is empty, and stdout bytes are exactly `b"lines: 3\nwords: 8\nchars: 33\ntop: cat=2 the=2 a=1\n"`.
- For `--json --top 2`, assert exit 0, stderr is empty, and stdout bytes are exactly `b'{"lines": 3, "words": 8, "chars": 33, "top": [{"word": "cat", "count": 2}, {"word": "the", "count": 2}]}\n'`.
- Include a BOM input and assert the BOM is excluded from `chars`; include an empty/no-token input and assert the fourth text line is exactly `top:\n`.
- Include a truly empty file and assert exit 0, empty stderr, and stdout bytes exactly `b"lines: 0\nwords: 0\nchars: 0\ntop:\n"`.
- Inspect `wordstat/__main__.py` and assert it calls `sys.stdout.reconfigure(encoding="utf-8", newline="\n")` exactly as required by `contract.md`; retain exact stdout byte assertions proving LF line endings. The contract's output alphabet is ASCII, so output fixtures cannot distinguish UTF-8 from other encodings.
- Include a tied-frequency case and assert lexical ascending tie order, plus a `--top` value larger than distinct-word count and assert all available words are listed.
- Inspect the implementation to verify it does not query or apply locale settings; run the same fixture under two available locale environments where supported and assert identical stdout bytes. If the host lacks switchable locales, the source check remains required and record the limitation.

Estimate:
M

Priority:
P1
