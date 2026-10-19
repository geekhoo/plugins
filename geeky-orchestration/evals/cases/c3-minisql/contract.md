# minisql: Contract

## Constraints

- Stack: Python >=3.11, standard library only; pytest for tests only.
- Package location: `minisql/` at repo root (flat layout, no `src/`), with `__init__.py` and `__main__.py`.
- Entry points: `python -m minisql [--data DIR] [--format csv|table] [SQL]` from repo root; `import minisql; minisql.connect(DIR).execute(SQL)`.
- Do not use `sqlite3` or any existing SQL engine or parser.

## Functional requirements

- **R1** Importable as `minisql`, runnable as `python -m minisql`; standard-library imports only, never `sqlite3` or any SQL engine/parser.
- **R2** Tables load from the data directory per the data contract.
- **R3** Column types are inferred per the inference rules; empty fields are NULL.
- **R4** The tokenizer implements the lexical rules.
- **R5** The parser implements the grammar and precedence table.
- **R6** Keywords and all names resolve case-insensitively.
- **R7** Expressions are statically typed; violations are SemanticErrors raised before any row is evaluated.
- **R8** Arithmetic follows the numeric rules, including division by zero.
- **R9** Predicates follow three-valued logic.
- **R10** Projection supports `*`, `t.*`, expressions, aliases and the output naming rule.
- **R11** INNER and LEFT joins follow nested-loop semantics and order.
- **R12** Grouping, `HAVING` and aggregates follow the aggregate rules, including empty input.
- **R13** `DISTINCT` keeps first occurrences.
- **R14** `ORDER BY` supports aliases, ordinals, expressions, multiple keys, `ASC`/`DESC`; NULLs smallest; stable ties.
- **R15** `LIMIT`/`OFFSET` take non-negative integer literals.
- **R16** Clauses evaluate in the defined order; `AND`/`OR` short-circuit.
- **R17** The library API matches the contract.
- **R18** CSV and table formats match byte-for-byte.
- **R19** The one-shot CLI follows the output and exit-code rules.
- **R20** The REPL follows the prompt, buffering, command and exit rules.
- **R21** Errors use the specified classes, format, templates and positions.

## Language reference

### Lexical rules

- Whitespace: space, tab, `\r`, `\n`. Comments: `--` to end of line.
- Lines split on `\n` only; line and column are 1-based; column counts code points; tab and `\r` count as one column.
- Keywords (reserved, case-insensitive): `SELECT DISTINCT FROM WHERE GROUP BY HAVING ORDER ASC DESC LIMIT OFFSET AS JOIN INNER LEFT OUTER ON AND OR NOT IS NULL LIKE ESCAPE IN`.
- Unquoted identifier: `[A-Za-z_][A-Za-z0-9_]*`, not a keyword. Quoted identifier: `"..."` with `""` for a literal `"`; may contain any character and may equal a keyword. Function names (`COUNT SUM AVG MIN MAX`) are ordinary identifiers.
- String literal: `'...'` with `''` for a literal `'`; may span lines; no backslash escapes (`\` is literal).
- INTEGER literal: `[0-9]+`. REAL literal: `[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?`, `\.[0-9]+([eE][+-]?[0-9]+)?`, or `[0-9]+[eE][+-]?[0-9]+`. A numeric literal immediately followed by a letter, digit, `_` or `.` is a LexError (`invalid number literal`). Signs are unary operators.
- Operators: `+ - * / % = <> != < <= > >= ( ) , . * ;`.

### Grammar (EBNF)

```
query     = "SELECT" ["DISTINCT"] item {"," item}
            ["FROM" tableref {join}] ["WHERE" expr]
            ["GROUP" "BY" expr {"," expr}] ["HAVING" expr]
            ["ORDER" "BY" order {"," order}]
            ["LIMIT" INT] ["OFFSET" INT] [";"] EOF ;
item      = "*" | name "." "*" | expr [["AS"] name] ;
tableref  = name [["AS"] name] ;
join      = (["INNER"] "JOIN" | "LEFT" ["OUTER"] "JOIN") tableref "ON" expr ;
order     = expr ["ASC" | "DESC"] ;
expr      = and {"OR" and} ;
and       = not {"AND" not} ;
not       = "NOT" not | cmp ;
cmp       = add [ cmpop add | "IS" ["NOT"] "NULL"
                | ["NOT"] "LIKE" add ["ESCAPE" STRING]
                | ["NOT"] "IN" "(" expr {"," expr} ")" ] ;
cmpop     = "=" | "<>" | "!=" | "<" | "<=" | ">" | ">=" ;
add       = mul {("+" | "-") mul} ;
mul       = unary {("*" | "/" | "%") unary} ;
unary     = ("-" | "+") unary | primary ;
primary   = INT | REAL | STRING | "NULL" | call | colref | "(" expr ")" ;
call      = name "(" ("*" | expr) ")" ;
colref    = name ["." name] ;
name      = IDENT | QUOTED_IDENT ;
```

`FROM` is optional; without it the query runs over exactly one empty row. A table alias makes the table name unusable as a qualifier in that query.

### Precedence (highest first)

| Level | Operators | Associativity |
|---|---|---|
| 1 | unary `-`, `+` | right |
| 2 | `*` `/` `%` | left |
| 3 | binary `+` `-` | left |
| 4 | `= <> != < <= > >=`, `IS [NOT] NULL`, `[NOT] LIKE`, `[NOT] IN` | none (`a = b = c` is a ParseError at the second operator) |
| 5 | `NOT` | right |
| 6 | `AND` | left |
| 7 | `OR` | left |

### Types and values

- Static types: `INTEGER` (`int`), `REAL` (`float`), `TEXT` (`str`), `NULL` (bare `NULL` literal only). Any value may be `None`; never `bool`. Comparison, logical, `IS`, `LIKE`, `IN` yield INTEGER `1`, `0` or NULL.
- Arithmetic operands must be INTEGER, REAL or NULL type. Result type: REAL if either operand is REAL; else NULL if both are NULL; else INTEGER. Unary minus/plus keeps its operand type.
- Comparisons (`=`, `<>`, `IN` items, `MIN`/`MAX`, ordering) require both sides numeric (INTEGER/REAL mixed freely, compared numerically) or both TEXT, or either side NULL type. TEXT compares by Python `str` ordering (code points, case-sensitive).
- `LIKE` operands and `ESCAPE` must be TEXT or NULL. `AND`/`OR`/`NOT` operands and `WHERE`/`ON`/`HAVING` conditions must be INTEGER, REAL or NULL type; nonzero is true, zero is false, NULL is unknown.
- Integer `/` truncates toward zero (`-7 / 2` = `-3`); integer `%` takes the sign of the dividend (`-7 % 2` = `-1`, `7 % -2` = `1`). REAL `/` is float division; REAL `%` is `math.fmod`.
- If either arithmetic operand is NULL the result is NULL (checked first). Otherwise a zero divisor for `/` or `%` (INTEGER or REAL) raises RuntimeError `division by zero` at the operator.

### NULL and predicates

- Any comparison with a NULL operand is NULL. `NOT NULL` is NULL. `AND`: false if either side false, else NULL if either NULL, else true. `OR`: true if either true, else NULL if either NULL, else false.
- `x IS NULL` / `x IS NOT NULL` return 1/0, never NULL.
- `x [NOT] IN (list)`: NULL if `x` is NULL; 1 if some item equals `x`; else NULL if any item is NULL; else 0. `NOT IN` negates with 3VL.
- `LIKE`: whole-string, case-sensitive; `%` matches any sequence (including empty), `_` exactly one character. With `ESCAPE 'c'`, `c` followed by `%`, `_` or `c` matches that character literally; `c` followed by anything else or at pattern end raises RuntimeError `invalid LIKE pattern` at the `LIKE` token. `ESCAPE` must be a one-character string literal. Any NULL operand gives NULL.
- Equality for `GROUP BY`, `DISTINCT` treats NULL as equal to NULL; join conditions follow normal 3VL, so NULL never matches.

### Type inference

For each column, over its non-empty raw fields (no trimming): if every field fully matches `[+-]?[0-9]+` the column is INTEGER (`int(field)`); else if every field fully matches `[+-]?([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)([eE][+-]?[0-9]+)?` it is REAL (`float(field)`); else TEXT (fields kept verbatim, including numeric-looking ones). A column with no non-empty fields is TEXT. Empty fields (quoted or not) are NULL in every type. Consequently `" 1"` makes a column TEXT, `007` is INTEGER `7`, and `1`, `2.5` makes a REAL column.

## Interface contract

### Data directory

- `--data DIR` (default `.`); library `connect(DIR)`. A missing or non-directory `DIR` is an IOError: `connect(DIR)` raises `DataIOError` immediately, and the one-shot CLI reports it and exits 3 before lexing the SQL.
- A table is any regular file directly in `DIR` whose name ends in `.csv` (case-insensitive). Table name = file stem; lookup is case-insensitive. Two files whose stems are equal case-insensitively make every reference to that name an IOError `ambiguous table file '<name>'`.
- Files are read on each `execute` with `encoding='utf-8-sig'`, `newline=''` and `csv.reader(f, strict=True)` (default dialect). Only the tables referenced in `FROM`/`JOIN` are read; any other file in `DIR`, however malformed, never affects a query. `tables()` lists stems without reading file contents.
- Row 1 is the header; names are used verbatim. Empty header name, or duplicate names (case-insensitive), is an IOError. Lines yielding zero fields are skipped. A record with a different field count than the header is IOError `<file>: line N: expected K fields, got M`, where N is the reader's `line_num` after that record.

### Name resolution and output names

- Column reference `c` searches all tables in `FROM`; `q.c` searches the table whose range name (alias, else table name) is `q`. Zero matches: unknown column; more than one: ambiguous column. Duplicate range names are a SemanticError. An `ON` condition sees only tables introduced before or in its own join; later tables are unknown there. Joins associate left.
- `*` expands to all columns of all tables in `FROM` order; `t.*` to that table's columns. Duplicate output names are allowed.
- Output name: the alias as written (quotes removed); else for an unparenthesized column reference, the column's header name as in the CSV; else the verbatim source text of the item from its first to last character (e.g. `COUNT(*)`, `a + 1`, `(a)`).

### Aggregates and grouping

- A query is an aggregate query if it has `GROUP BY`, `HAVING`, or an aggregate call in the select list or `ORDER BY`.
- `COUNT(*)` counts rows; `COUNT(e)` counts non-NULL values (INTEGER). `SUM` of INTEGER is INTEGER, of REAL is REAL. `AVG` is REAL. `MIN`/`MAX` keep the argument type. All ignore NULLs. Over zero non-NULL values `COUNT` is `0`, others NULL. `SUM`/`AVG` need numeric arguments; only `COUNT` accepts `*`.
- Without `GROUP BY` the whole filtered input (after `WHERE`) forms a single group, even when empty; without `HAVING` the query yields exactly one row, and `HAVING` filters that group, yielding 0 or 1 row (1 row over empty input when `HAVING` is true, e.g. `HAVING COUNT(*) = 0`). With `GROUP BY`, empty input yields zero rows; groups appear in first-seen order unless ordered.
- In an aggregate query, every select, `HAVING` and `ORDER BY` expression must be built from aggregate calls, literals, and subexpressions structurally identical to a `GROUP BY` expression (same resolved columns, operators and literals). `*` is not allowed. Aggregates are not allowed in `WHERE`, `ON`, `GROUP BY`, or inside another aggregate.

### ORDER BY, DISTINCT, LIMIT

- An `ORDER BY` item that is a bare INTEGER literal is a 1-based output ordinal, counted after `*` expansion. A bare identifier equal to exactly one select-item alias (written with or without `AS`) refers to that output column (two such aliases: ambiguous column). Otherwise it is an expression over input rows (or groups).
- With `DISTINCT`, each `ORDER BY` item must be an ordinal, an alias, or structurally identical to a select expression.
- Sorting is stable; ties keep pre-sort order for both `ASC` and `DESC`. NULL sorts before every value (first in `ASC`, last in `DESC`).
- `LIMIT 0` yields no rows; `OFFSET` past the end yields no rows.

### Evaluation order

1. `FROM`/joins: nested loop; for each left row in order, right rows in file order; `ON` evaluated for every pair; `LEFT JOIN` emits one NULL-filled row for an unmatched left row.
2. `WHERE` per row. 3. Group keys and aggregate arguments per surviving row. 4. `HAVING` per group. 5. Select expressions per surviving row/group. 6. `ORDER BY` keys. 7. `DISTINCT` (first occurrence kept). 8. Sort. 9. `OFFSET`, then `LIMIT`.

`AND` skips its right side when the left is false; `OR` when the left is true. Rows are processed in order within each step; the first failure is reported and no output is produced.

### Library API

```python
minisql.connect(data_dir: str | os.PathLike) -> Connection
Connection.execute(sql: str) -> Result
Connection.tables() -> list[str]                    # stems, sorted by (lower(), name)
Connection.schema(table: str) -> list[tuple[str, str]]  # (column, type) in header order
@dataclass(frozen=True)
class Result: columns: list[str]; types: list[str]; rows: list[tuple]
minisql.format_csv(result: Result) -> str
minisql.format_table(result: Result) -> str
```

`types` holds `"INTEGER"`, `"REAL"`, `"TEXT"` or `"NULL"`. Row values are `int`, `float`, `str` or `None`.

### Output formats

Value text: INTEGER `str(v)`; REAL `repr(v)` (`100.0`, `2.5`, `1e+20`); TEXT verbatim.

**CSV** (`--format csv`, default for one-shot): header line, then one line per row, fields joined by `,`, every line terminated by `\n` (also on Windows). NULL is an empty unquoted field. A field is wrapped in `"` (inner `"` doubled) iff it is the empty string, contains `,`, `"`, `\n` or `\r`, or starts or ends with a space. Header names follow the same quoting.

**Table** (`--format table`, default for REPL): cell text is the value text with newline and carriage-return characters replaced by the two-character escapes `\n` and `\r`; NULL is `NULL`. Width of a column = max code-point length of header and cells. Header cells left-aligned; INTEGER/REAL values right-aligned; TEXT and `NULL` left-aligned. Cells joined by ` | `; separator line is `-` × width per column joined by `-+-`; trailing spaces stripped from every line; then `(N rows)` or `(1 row)`. Every line ends with `\n`.

### CLI

`python -m minisql [--data DIR] [--format csv|table] [SQL]`. With `SQL`: one-shot, print the formatted result to stdout. Without `SQL`: REPL on stdin. stdout and stderr are UTF-8 with `\n`.

### REPL

- Prompt `minisql> ` when the buffer is empty, `   ...> ` otherwise; written to stdout without newline, flushed, whether or not stdin is a TTY. Input is not echoed.
- With an empty buffer, a line whose stripped text starts with `.` is a command; a blank line is ignored. Otherwise the line is appended (joined with `\n`); when the buffer, right-stripped, ends with `;`, it is executed and cleared.
- Commands: `.help` (free text), `.tables` (one name per line, `tables()` order), `.schema NAME` (`name TYPE` per line), `.format csv|table`, `.quit` and `.exit`. Unknown command: stderr `unknown command: <text>`.
- Results print in the current format (CSV has no row-count footer). Errors print one line to stderr and the session continues; positions are relative to the buffer.
- At EOF a non-empty buffer is executed; then exit 0 with nothing further printed. `.quit` exits 0.

### Exit codes (one-shot)

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | LexError, ParseError, SemanticError, RuntimeError |
| 2 | usage error (argparse) |
| 3 | IOError |

On error stdout is empty and stderr holds exactly the error line plus `\n`. No tracebacks.

## Error handling

Classes exported from `minisql`, subclassing `MiniSQLError(Exception)`: `LexError`, `ParseError`, `SemanticError`, `QueryRuntimeError`, `DataIOError`, with attributes `kind` (`Lex`/`Parse`/`Semantic`/`Runtime`/`IO`), `line`, `column` (`None` for IO), `message`; `str(err)` is the formatted line.

Format: `<Kind>Error at line L, column C: <message>`; IO errors: `IOError: <message>`.

| Kind | Message templates | Position |
|---|---|---|
| Lex | `unexpected character 'X'`, `unterminated string literal`, `unterminated quoted identifier`, `invalid number literal` | offending character / opening quote / literal start |
| Parse | `unexpected token 'T'` (T = token source text), `unexpected end of input` | token start / one past last input character |
| Semantic | `unknown table 'N'`, `duplicate table name 'N'`, `unknown column 'R'`, `ambiguous column 'R'`, `unknown function 'F'`, `'*' argument only allowed for COUNT`, `type mismatch: cannot apply 'OP' to T1 and T2`, `type mismatch: cannot apply 'OP' to T`, `condition must be numeric, got TEXT`, `aggregate function not allowed here`, `column 'R' must appear in GROUP BY or be used in an aggregate`, `'*' not allowed in aggregate query`, `ORDER BY position N is out of range`, `ORDER BY expression must appear in select list when DISTINCT is used`, `ESCAPE must be a single character` | table/name token; column ref start; operator token (function name for aggregates); condition/expression start; `*`; ordinal; ESCAPE string |
| Runtime | `division by zero`, `invalid LIKE pattern` | `/` or `%` token; `LIKE` token |
| IO | `data directory not found: DIR` (DIR as given), `ambiguous table file 'N'`, `<file>: empty file`, `<file>: empty column name`, `<file>: duplicate column 'C'`, `<file>: line N: expected K fields, got M`, `<file>: line N: malformed CSV`, `<file>: invalid UTF-8` | none |

`N`, `R`, `F` are names as written in the query without quotes (`R` qualified as `q.c`). `OP` is the operator as written for symbols, upper-case for keywords and aggregates (`LIKE`, `IN`, `AND`, `SUM`). `<file>` is the base file name. For `duplicate table name 'N'`, the position is the range-name token of the second `tableref` with that range name (its alias if present, else its table name) and `N` is that range name as written. For `'*' argument only allowed for COUNT`, the position is the `*` token inside the call. For `duplicate column 'C'`, `C` is the second occurrence's header name exactly as written in the CSV. For `malformed CSV`, `N` is the reader's `line_num` at the moment `csv.Error` is raised. Phases run lex → parse → semantic (including IO for referenced tables, in `FROM` order) → execute. The oracle only uses queries containing a single error.

## Acceptance criteria

Fixture `emp.csv`: `id,name,dept,salary` / `1,Ann,eng,100` / `2,Bob,eng,` / `3,Cid,ops,80` / `4,Dee,,80` / `5,Eve,ops,120`. Fixture `dept.csv`: `code,title` / `eng,Engineering` / `ops,Operations` / `ops,Ops Dup` / `hr,Human Resources`.

- **AC1** (R1, R19) `python -m minisql --data D "SELECT 1 AS one"` prints `one\n1\n`, exit 0; no non-stdlib or `sqlite3` import in `minisql/`.
- **AC2** (R2, R21) `SELECT * FROM EMP` returns 5 rows; `--data missing` exits 3 with `IOError: data directory not found: missing`.
- **AC3** (R3) `schema("emp")` is `[("id","INTEGER"),("name","TEXT"),("dept","TEXT"),("salary","INTEGER")]`.
- **AC4** (R4, R21) `SELECT 1 # 2` → `LexError at line 1, column 10: unexpected character '#'`.
- **AC5** (R5) `SELECT 1 + 2 * 3, -2 * 3, NOT 1 = 2` → `1 + 2 * 3,-2 * 3,NOT 1 = 2` / `7,-6,1`.
- **AC6** (R6) `select NAME from Emp e where E.Id = 1` → `name` / `Ann` (header from the CSV, not the query).
- **AC7** (R7) `SELECT name + 1 FROM emp` → `SemanticError at line 1, column 13: type mismatch: cannot apply '+' to TEXT and INTEGER`.
- **AC8** (R8) `SELECT 7 / 2, -7 / 2, 7 % -2, 7.0 / 2, NULL / 0` → `3,-3,1,3.5,`.
- **AC9** (R9) `SELECT name FROM emp WHERE dept NOT IN ('eng', NULL)` → header only.
- **AC10** (R10) `SELECT salary * 2, name AS n FROM emp WHERE id = 1` → header `salary * 2,n`, row `200,Ann`.
- **AC11** (R17) `connect(D).execute("SELECT AVG(salary) FROM emp")` has `types == ["REAL"]`, `rows == [(95.0,)]`.
- **AC12** (R2-R21) Behaviour specified in the Language reference, Interface contract and Error handling sections is reproduced exactly (byte-for-byte output, exit codes and error lines) by hidden tests.
