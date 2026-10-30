# Coverage Matrix

| Requirement ID | Requirement Summary | Covered by Task(s) | Status |
|---|---|---|---|
| B1 | Build a tiny CLI reading one UTF-8 file and reporting counts and frequent words. | T1, T2 | Covered |
| B2 | Run with `python -m wordstat FILE` using Python 3.11+ standard library only. | T1, T2 | Covered |
| B3 | Default text output, `--json`, and `--top N` behavior. | T1, T2 | Covered |
| B4 | Byte-for-byte deterministic output across Windows, macOS, and Linux. | T1, T2 | Covered |
| B5 | Clean errors with clear stderr and specific exit code; never traceback. | T2 | Covered |
| B6 | Include pytest tests. | T1, T2 | Covered |
| R1 | `python -m wordstat --help` exits 0. | T1 | Covered |
| R2 | Parse exactly one file, optional `--json`/`--top`, decode UTF-8 BOM, never read stdin. | T1, T2 | Covered |
| R3 | Count lines with `splitlines()`, words with `[a-z0-9]+` over `text.lower()`, chars with `len(text)`. | T1, T2 | Covered |
| R4 | Rank top words by count descending then word ascending; default 3 and cap by available distinct words. | T1 | Covered |
| R5 | Default text output and optional JSON output. | T1 | Covered |
| R6 | UTF-8 output, LF line endings, no locale use, configured stdout. | T1, T2 | Covered |
| C1 | `argparse` program name is `wordstat`; `--top` integer >=1; usage errors exit 2. | T1, T2 | Covered |
| C2 | Text format is exactly four LF-terminated lines and empty `top:` has no trailing space. | T1 | Covered |
| C3 | JSON is one default `json.dumps` line, with prescribed key and top-item ordering. | T1 | Covered |
| C4 | File missing/directory/unreadable and invalid UTF-8 errors use exact paths/messages, exit 3, empty stdout. | T2 | Covered |
| C5 | Usage errors print argparse default; final stderr line matches `^wordstat: error: `, stdout empty. | T2 | Covered |
