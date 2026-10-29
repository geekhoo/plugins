Task Name:
Implement the deterministic counting core

Context:
The CLI must calculate line, word, character, and top-frequency results using the literal definitions in contract.md. Keeping this calculation as a pure core function makes the semantics independently testable before the CLI boundary is added.

Scope:

In scope:
---
- Add `wordstat/__init__.py` as needed and `wordstat/core.py` with `analyze_text(text, top)`, accepting decoded text and a positive top limit and returning a dict with `lines`, `words`, `chars`, and `top` (a list of `{word, count}` dicts).
- Add `tests/test_core.py` for exact R3/R4 behavior, including empty text, splitlines behavior, lower-then-regex tokenization, ties, and limits above/below the distinct word count.

## Out of scope:
- CLI parsing, file I/O, output formatting, and error messages; these belong to T2.
- Additional tokenization modes, stdin, streaming, packaging, or runtime dependencies.

Module/System:
Root Python package `wordstat/`; core unit tests in `tests/test_core.py`.

## Dependencies:

* None

## Technical Notes:
- Use `len(text.splitlines())`, `len(text)`, and matches of `[a-z0-9]+` over `text.lower()` exactly.
- Rank by count descending and then token ascending; default top is 3 at the CLI boundary, while the core accepts an explicit positive limit.
- Keep the function name and result shape stable for T2, which consumes this API.
- Do not normalize newlines or substitute Unicode `\w` / case-insensitive matching.
- See `implementation-plan.md` sections "Design" and "Phases and Tasks", and `feature-specification.md` R3/R4 and "Counts and top words".

## Acceptance Criteria:

* The core returns the exact line, total token, character, and top-token results for all input cases in its unit suite.
* Top results are stable and ordered by count descending, token ascending, capped at the requested positive limit.
* Runtime core code imports only the standard library.

Definition of Done:

* Code reviewed
* Tested (manual/unit)
* No critical bugs

Tests/Validation Before Next Task:
- `python -m compileall -q wordstat`
- `pytest tests/test_core.py -q`

Estimate:
S

Priority:
P0
