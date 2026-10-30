Task Name: Implement core word statistics

Context:
Calculate counts and top-word ranking independently of CLI parsing and file I/O.

Scope:

In scope:
---
- Create `wordstat/core.py` with `analyze(text, top_n)` returning `lines`, `words`, `chars`, `top`.
- Implement requirements R3/R4 from the feature specification.

## Out of scope:
- CLI, file reading, errors, serialization, and pytest suite.

Module/System:
Pure calculation module in `wordstat`.

## Dependencies:
* None

## Technical Notes:
- Match `[a-z0-9]+` in `text.lower()`; count chars from supplied decoded text.
- Top items are `{"word": ..., "count": ...}`; count desc, then word asc.
- Python 3.11+ stdlib only.

## Acceptance Criteria:
* Counts match contract definitions and include decoded code points.
* Top list honors N and orders ties lexically.

Definition of Done:
* Code reviewed and tested; no critical bugs.

Tests/Validation Before Next Task:
- `python -m compileall wordstat`
- `python -c "from wordstat.core import analyze; assert analyze('The cat cat. A', 3) == {'lines': 1, 'words': 4, 'chars': 14, 'top': [{'word': 'cat', 'count': 2}, {'word': 'a', 'count': 1}, {'word': 'the', 'count': 1}]}"`

Estimate:
S

Priority:
P1
