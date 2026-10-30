# Coverage Matrix

| Requirement ID | Requirement Summary | Covered by Task(s) | Status |
|---|---|---|---|
| R1 | `python -m wordstat --help` exits 0. | T1 | Covered |
| R2 | `python -m wordstat [--json] [--top N] FILE` reads one `utf-8-sig` file; stdin is never read. | T1 | Covered |
| R3 | Counts are `len(text.splitlines())`, matches of `[a-z0-9]+` in `text.lower()`, and `len(text)`. | T1 | Covered |
| R4 | `top` is count-descending/word-ascending, defaults to 3, limits to N, lists fewer when needed; `--top` integer must be >= 1. | T1 | Covered |
| R5 | Text is default; `--json` selects JSON. | T1 | Covered |
| R6 | stdout reconfigured to UTF-8 and `newline="\n"`; UTF-8 output and LF endings are deterministic across platforms. | T1 | Covered |
| Interface: argparse | `prog` is `wordstat`; exactly one required FILE; missing FILE, unknown flag, and invalid `--top` are usage errors. | T1 | Covered |
| Interface: text output | Exactly four lines, each ending in `\n`; empty top list renders `top:` with no trailing space. | T1 | Covered |
| Interface: JSON output | One line from default `json.dumps(obj)` plus `\n`; ordered keys `lines`, `words`, `chars`, `top`; top item keys `word`, `count`. | T1 | Covered |
| Errors and exits | Read failures and invalid UTF-8 return 3 with their exact distinct message; usage failures return 2 and last stderr line has the required prefix; errors leave stdout empty; FILE text is preserved. Success including empty file returns 0; unexpected errors reserve 1. | T1 | Covered |
| Stack and location | Python >=3.11, standard library only at runtime, pytest only for tests, flat `wordstat/`, root module command. | T1 | Covered |

## Task Self-Check

Every task criterion is validated in T1's own test block using the public command and pytest tests added by T1. Error predicates preserve exact prefixes, status codes, empty stdout, supplied path, and final-line position from the source contract. No AC relies on tests added by a later task.
