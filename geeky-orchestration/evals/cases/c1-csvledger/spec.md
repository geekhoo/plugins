# C1 — csvledger: Reference Spec

| Field | Value |
|---|---|
| id | `c1-csvledger` |
| tier | C1 |
| budget ceiling | $10 |
| expected size | 4-6 tasks, 1-2 implementation phases |
| stack | Python >=3.11, standard library only; pytest for tests only |
| package location | `csvledger/` at repo root (flat layout, no `src/`) |
| entry point | `python -m csvledger <command> ...` run from repo root |

## Contestant brief

Build `csvledger`, a small Python command-line tool that reads one or more bank-export CSV files of transactions, assigns each transaction a category using a rules file, and prints a monthly report. It must run as `python -m csvledger` from the repository root using only the Python 3.11+ standard library. Provide two commands: `report` (per-month, per-category totals) and `categorize` (each transaction with its assigned category). Both commands print either an aligned text table or JSON. Money must be exact (no floating point) and output must be byte-for-byte deterministic on Windows, macOS and Linux. Bad input must fail cleanly with a clear message on stderr and a specific exit code, never a traceback. Identical transactions repeated across overlapping exports must be counted once. The full interface contract is in `spec.md`; include pytest tests for your implementation.

## Scope

- Parsing and validating transaction CSV files and one rules CSV file.
- Rule-based categorization with priority and tie-breaking.
- Duplicate removal, month filtering, `report` and `categorize` output in `table` and `json`.

## Out of scope

- Persistent storage or ledger state between runs; reading stdin; currencies, FX, thousands separators.
- Configurable date/amount formats, locales, colours, paging, packaging metadata beyond what `python -m` needs.

## Functional requirements

- **R1** `python -m csvledger` exposes subcommands `report` and `categorize`; `--help` exits 0.
- **R2** Transaction files are parsed per the CSV contract; any invalid file or row aborts the run with exit 3 and no stdout.
- **R3** The rules file is parsed per the rules contract; any invalid rule aborts with exit 4 and no stdout.
- **R4** Each transaction gets exactly one category: the highest-priority matching rule; ties go to the rule earliest in the file; no match gives `Uncategorized`.
- **R5** Duplicate transactions (same date, stripped description, and numeric amount value) across all inputs are kept once (first occurrence) and a warning is written to stderr.
- **R6** `report` aggregates by month and category: count, income, expenses, net.
- **R7** `categorize` lists every transaction, sorted by date ascending, ties in input order.
- **R8** `--month YYYY-MM` restricts both commands to transactions in that month.
- **R9** `--format table|json` selects output; default `table`.
- **R10** Money uses `decimal.Decimal`; sums are exact; displayed values are rounded once to 2 dp, ROUND_HALF_UP, never shown as `-0.00`.
- **R11** Output is deterministic: UTF-8, `\n` line endings, stable ordering, no locale use.

## Interface contract

### Commands

```
python -m csvledger report     [--rules PATH] [--format table|json] [--month YYYY-MM] FILE [FILE ...]
python -m csvledger categorize [--rules PATH] [--format table|json] [--month YYYY-MM] FILE [FILE ...]
```

- `FILE`: one or more transaction CSV paths, processed in argument order. `-` is an ordinary file name; stdin is never read.
- `--rules`: optional. When omitted, every transaction is `Uncategorized`.
- `--month`: must match `^\d{4}-(0[1-9]|1[0-2])$`, else usage error.
- argparse `prog` is `csvledger`. stdout is reconfigured to `encoding="utf-8", newline="\n"`.
- Load order: rules file first, then transaction files in argument order. First error wins.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (including empty result and duplicate warnings) |
| 1 | Reserved for unexpected internal error; never intentional |
| 2 | Usage error (argparse: unknown flag, missing FILE, bad `--format`/`--month`) |
| 3 | Transaction file error |
| 4 | Rules file error |

### Transaction CSV

- Encoding UTF-8, optional BOM (`utf-8-sig`); opened with `newline=""`; parsed with `csv.reader` defaults (comma, `"` quoting).
- Line 1 is the header. Header names are stripped and lowercased; `date`, `description`, `amount` are required, in any order; extra columns are ignored; duplicate names are an error.
- Rows with zero fields (blank lines) are skipped. Every other row must have exactly as many fields as the header.
- `date`: stripped value must match `^\d{4}-\d{2}-\d{2}$` and be a valid calendar date (regex first; do not rely on `date.fromisoformat` alone).
- `amount`: stripped value must match `^-?\d+(\.\d+)?$`. Negative = expense (outflow), positive = income, zero counts but adds to neither.
- `description`: stripped; may be empty.
- A header-only file is valid (zero transactions). A file with no header line (0 bytes) is an error.

### Rules CSV

- Same encoding/header/blank-row/field-count rules. Required columns: `category`, `type`, `pattern`, `priority`.
- `category`: stripped, non-empty. `type`: stripped, exactly `contains` or `regex`. `pattern`: stripped, non-empty. `priority`: stripped, matches `^-?\d+$`.
- `contains`: `pattern.casefold() in description.casefold()`.
- `regex`: `re.search(pattern, description, re.IGNORECASE)`; compiled at load time.
- Zero rules is valid.

### Money formatting

`q = value.quantize(Decimal("0.01"), ROUND_HALF_UP)`; if `q == 0` print `0.00`; otherwise `format(q, "f")`. Aggregates (income, expenses, net, month totals) are summed unrounded, then formatted. `net = income_raw + expenses_raw`.

### `report` table

Columns, in order: `MONTH` (left), `CATEGORY` (left), `COUNT` (right), `INCOME` (right), `EXPENSES` (right), `NET` (right). Width of each column = max(len(header), longest value) using `len()` on code points. Cells joined by two spaces; each line right-stripped. Line 1: headers. Line 2: dashes of each column width. Then one row per (month, category), sorted by month ascending then category by code-point ascending. No total rows. Zero transactions: header and dash line only.

### `categorize` table

Columns: `DATE` (left), `AMOUNT` (right, per-transaction amount formatted as money), `CATEGORY` (left), `DESCRIPTION` (left). Same width, separator, dash-line and right-strip rules.

### JSON

`json.dumps(obj, indent=2, ensure_ascii=False)` followed by `\n`. Money values are strings; counts are integers. Key order is exactly as shown.

- `report`: `{"months": [{"month", "count", "income", "expenses", "net", "categories": [{"category", "count", "income", "expenses", "net"}]}]}`. Months and categories sorted as in the table.
- `categorize`: `{"transactions": [{"date", "description", "amount", "category"}]}`.
- Empty: `{"months": []}` / `{"transactions": []}`.

## Error handling

Errors go to stderr as one line, prefix `csvledger: error: `, then exit with the code shown; stdout stays empty. `<path>` is as given on the command line; `<line>` is `csv.reader.line_num` after reading the record. Row checks run in this order: field count, date, amount (transactions) or field count, category, type, pattern, priority, regex (rules).

| Condition | Exit | stderr (after prefix) |
|---|---|---|
| File missing/unreadable | 3 / 4 | `<path>: cannot read file` |
| Not valid UTF-8 | 3 / 4 | `<path>: not valid UTF-8` |
| No header line | 3 / 4 | `<path>: missing header` |
| Required column absent (first in listed order) | 3 / 4 | `<path>: missing column '<name>'` |
| Duplicate header name | 3 / 4 | `<path>: duplicate column '<name>'` |
| Field count mismatch | 3 / 4 | `<path>:<line>: expected <N> fields, got <M>` |
| Bad date | 3 | `<path>:<line>: invalid date '<value>'` |
| Bad amount | 3 | `<path>:<line>: invalid amount '<value>'` |
| Empty category / pattern | 4 | `<path>:<line>: empty category` / `empty pattern` |
| Bad type | 4 | `<path>:<line>: invalid type '<value>'` |
| Bad priority | 4 | `<path>:<line>: invalid priority '<value>'` |
| Regex fails to compile | 4 | `<path>:<line>: invalid regex '<pattern>'` |
| argparse usage errors | 2 | argparse default; last stderr line starts `csvledger: error:` |

Warning (exit unaffected): `csvledger: warning: skipped <N> duplicate row(s)` when N > 0, written after stdout output. `<value>` is the stripped field value.

## Acceptance criteria

- **AC1 (R1)** `python -m csvledger --help` → exit 0, stdout mentions `report` and `categorize`.
- **AC2 (R2, R3, R4, R6, R9, R10)** Oracle case O1 → stdout equals the O1 table exactly, exit 0.
- **AC3 (R6, R9)** `report --format json` on O1 input → valid JSON with key order per contract; January Groceries `expenses` is `"-57.11"`.
- **AC4 (R7)** `categorize` on O1 input → rows in date order; `Blue Bottle Cafe` categorized `Coffee`.
- **AC5 (R8)** `report --month 2026-02` on O1 input → only `2026-02` rows.
- **AC6 (R5)** O4 → each duplicated row counted once; stderr warning; exit 0.
- **AC7 (R2)** O3 → exit 3, exact stderr line, empty stdout.
- **AC8 (R3)** Invalid regex rule → exit 4, `invalid regex` message.
- **AC9 (R10)** O5 → `0.13`, `-0.13`, `0.00`, `0.01` as shown.
- **AC10 (R11)** Running any case twice yields identical bytes; output contains no `\r`.

## Hidden oracle outline

Categories: CLI/usage (exit 2), CSV parsing and validation, rules parsing and precedence, aggregation and rounding, ordering, table layout, JSON shape, dedupe, month filter, determinism. Tests invoke `subprocess.run([sys.executable, "-m", "csvledger", ...], cwd=repo_root)` and compare stdout bytes decoded as UTF-8.

**O1 — baseline report.** `rules.csv`:
```
category,type,pattern,priority
Groceries,contains,market,10
Coffee,regex,^(starbucks|blue bottle),10
Dining,contains,cafe,5
Salary,contains,payroll,0
```
`tx.csv`:
```
date,description,amount
2026-01-03,Corner Market,-45.10
2026-01-05,STARBUCKS #12,-4.50
2026-01-15,ACME PAYROLL,2500.00
2026-01-20,Corner Market,-12.005
2026-02-02,Blue Bottle Cafe,-6.25
2026-02-10,Unknown Shop,-10
```
`report --rules rules.csv tx.csv` →
```
MONTH    CATEGORY       COUNT   INCOME  EXPENSES      NET
-------  -------------  -----  -------  --------  -------
2026-01  Coffee             1     0.00     -4.50    -4.50
2026-01  Groceries          2     0.00    -57.11   -57.11
2026-01  Salary             1  2500.00      0.00  2500.00
2026-02  Coffee             1     0.00     -6.25    -6.25
2026-02  Uncategorized      1     0.00    -10.00   -10.00
```

**O2 — empty file.** `tx.csv` contains only the header → `report` prints:
```
MONTH  CATEGORY  COUNT  INCOME  EXPENSES  NET
-----  --------  -----  ------  --------  ---
```
`--format json` prints `{"months": []}` (indent rules apply), exit 0.

**O3 — bad date.** Line 3 is `2026-02-30,X,-1` → exit 3, stderr `csvledger: error: tx.csv:3: invalid date '2026-02-30'`. Same for `2026-2-01` and `20260201`.

**O4 — duplicates.** `a.csv` and `b.csv` both contain `2026-01-05,STARBUCKS #12,-4.50`; `b.csv` has it as `-4.5` with surrounding spaces in the description → one Coffee row, count 1; stderr `csvledger: warning: skipped 1 duplicate row(s)`.

**O5 — rounding and sign.** Rules `Misc,contains,misc,0` and `Tiny,contains,tiny,0`; rows in 2026-03: `misc` `0.125`, `misc` `-0.125`, `tiny` `0.005`, `tiny` `0.005`, `tiny` `-0.004` →
```
MONTH    CATEGORY  COUNT  INCOME  EXPENSES   NET
-------  --------  -----  ------  --------  ----
2026-03  Misc          2    0.13     -0.13  0.00
2026-03  Tiny          3    0.01      0.00  0.01
```

**O6 — precedence tie.** Rules `A,contains,shop,5` then `B,regex,sho+p,5`; description `Shop Ltd` → `A`. Swap file order → `B`. Raise B to 6 → `B` regardless of order.

**O7 — categorize.** O1 input, `categorize --month 2026-01 --rules rules.csv tx.csv` → first rows:
```
DATE         AMOUNT  CATEGORY   DESCRIPTION
----------  -------  ---------  -------------
2026-01-03   -45.10  Groceries  Corner Market
```

**O8 — rules errors.** `Coffee,regex,(,1` → exit 4 `invalid regex '('`; `X,glob,a,1` → `invalid type 'glob'`; `X,contains,a,1.5` → `invalid priority '1.5'`.

**O9 — amount grammar.** `+5`, `1,000` (quoted), `.5`, `5.`, `$5`, `1e3` each → exit 3 `invalid amount`.

**O10 — multi-file, multi-month ordering.** Files given out of date order spanning 2025-12 to 2026-02 → months ascending; `categorize` ties on equal dates keep argument/file order.

## Suggested decomposition

Reference only; contestants plan their own.

- **Phase 1 — core**
  - T1 Package skeleton, `__main__.py`, argparse, error type mapped to exit codes, UTF-8/LF stdout.
  - T2 Transaction loader: header, row validation, Decimal parsing, dedupe.
  - T3 Rules loader and matcher with precedence.
- **Phase 2 — output**
  - T4 `report` aggregation, month filter, table and JSON renderers.
  - T5 `categorize` command reusing the renderer.
  - T6 pytest suite covering O1-O10.

## Quality signals

- **Minimal code:** roughly 200-300 LOC of source in 3-5 modules (`cli`, `loader`, `rules`, `render`); one shared CSV header/row validator for both file types; one table renderer used by both commands; no classes beyond a small dataclass and one exception type; no third-party imports.
- **No defects:** every oracle case passes; no float anywhere in money paths; no traceback reaches the user; no `-0.00`; no trailing whitespace or `\r`; JSON key order exact; error precedence (rules before transactions, first file first) honoured.
- **Tests:** about 150-250 LOC of pytest using `tmp_path` fixtures and subprocess calls; no network; no reliance on dict order beyond insertion order.
