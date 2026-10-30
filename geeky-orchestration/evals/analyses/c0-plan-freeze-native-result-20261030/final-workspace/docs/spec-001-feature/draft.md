# Coverage Matrix

| Requirement ID | Requirement Summary | Covered by Task(s) | Status |
|---|---|---|---|
| Brief | Build a Python command-line tool with deterministic summary output and pytest coverage. | T1 | Covered |
| R1 | `python -m wordstat --help` exits 0. | T1 | Covered |
| R2 | Accept one named file, optional BOM UTF-8, never read stdin. | T1 | Covered |
| R3 | Compute line, word, and character counts using the exact specified formulas. | T1 | Covered |
| R4 | Return top N words with defaults and deterministic tie ordering. | T1 | Covered |
| R5 | Support exact text output and one-line JSON output. | T1 | Covered |
| R6 | Produce cross-platform deterministic UTF-8/LF output. | T1 | Covered |
| Command contract | Set `prog`, accept only specified arguments, enforce `N >= 1` as usage error. | T1 | Covered |
| Text format | Emit exactly four LF-terminated lines, including empty `top:` form. | T1 | Covered |
| JSON format | Use default `json.dumps` separators and prescribed key order. | T1 | Covered |
| Error contract | Use exit 3 for file/decode errors, exit 2 for usage, exact messages, no stdout/traceback. | T1 | Covered |
| Stack/package | Python >=3.11, flat root package, standard library runtime, pytest tests only. | T1 | Covered |

Completeness check: each brief/contract requirement and interface constraint maps to T1, and T1's ACs trace back to the brief or a contract requirement/section. T1's validation block includes a check for each AC before any successor could start. Expected output and error predicates are quoted from `contract.md` without loosening their line, prefix, or suffix positions.
