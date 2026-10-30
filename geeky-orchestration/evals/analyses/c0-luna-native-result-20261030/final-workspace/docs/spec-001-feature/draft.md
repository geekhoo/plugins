# Coverage Matrix

| Requirement ID | Requirement Summary | Covered by Task(s) | Status |
|---|---|---|---|
| R1 | Help exits 0; argparse program is `wordstat`. | T2, T3 | Covered |
| R2 | Read exactly one UTF-8-sig file; optional flags; never read stdin. | T2, T3 | Covered |
| R3 | Exact line, ASCII-token word and decoded-code-point counts. | T1, T3 | Covered |
| R4 | Top N frequency order, lexical tie-break, default 3, N >= 1. | T1, T2, T3 | Covered |
| R5 | Exact default text and ordered one-line JSON formats. | T2, T3 | Covered |
| R6 | Successful stdout UTF-8/LF; locale-independent output. | T2, T3 | Covered |
| E1 | Missing/directory/unreadable path exits 3 with specified error and empty stdout. | T2, T3 | Covered |
| E2 | Invalid UTF-8 exits 3; optional BOM is consumed. | T2, T3 | Covered |
| E3 | Usage errors exit 2 with empty stdout and prefixed final stderr line. | T2, T3 | Covered |
