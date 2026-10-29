# Coverage Matrix

| Requirement ID | Requirement Summary | Covered by Task(s) | Status |
|---|---|---|---|
| B1 | Build the wordstat CLI described by the brief and include pytest tests. | T1, T2 | Covered |
| C1 | Use Python >=3.11 and the standard library at runtime; pytest is test-only. | T1, T2 | Covered |
| C2 | Place the package at repository-root `wordstat/` (flat layout). | T1, T2 | Covered |
| C3 | Support `python -m wordstat ...` from the repository root. | T2 | Covered |
| R1 | `python -m wordstat --help` exits 0. | T2 | Covered |
| R2 | Parse optional flags and one FILE; read it as UTF-8 with optional BOM; never read stdin. | T2 | Covered |
| R3 | Compute lines with `splitlines()`, words from `[a-z0-9]+` in lowercased text, and chars with `len(text)`. | T1, T2 | Covered |
| R4 | Select up to N frequent words, sorted by descending count then ascending word; default N is 3. | T1, T2 | Covered |
| R5 | Produce default text output or one-line JSON selected by `--json`. | T2 | Covered |
| R6 | Produce deterministic UTF-8/LF stdout without locale-dependent formatting. | T2 | Covered |
| E1 | Missing, directory, or unreadable file exits 3 with exact-path cannot-read diagnostic and empty stdout. | T2 | Covered |
| E2 | Invalid UTF-8 exits 3 with exact-path decoding diagnostic and empty stdout. | T2 | Covered |
| E3 | Missing FILE, unknown flags, and invalid `--top` are argparse usage errors, exit 2, with final prefixed stderr line and empty stdout. | T2 | Covered |
| E4 | Successful input, including an empty file, exits 0; unexpected internal errors are reserved for exit 1. | T2 | Covered |
