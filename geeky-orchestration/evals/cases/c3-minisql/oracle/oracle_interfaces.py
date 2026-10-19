"""Library API, output formats, one-shot CLI and REPL (R17-R21)."""


def ok(res, out):
    assert res == (0, out, "")


def fails(res, line, code=1):
    assert res == (code, "", line + "\n")


# ---------------------------------------------------------------- library API (R17, R21)


def test_api_result_is_frozen_dataclass(lib, data):
    """R17: Result is a frozen dataclass with list columns/types and tuple rows."""
    body = (
        "import dataclasses, pathlib\n"
        "r = minisql.connect(pathlib.Path(DATA)).execute('SELECT id, name FROM emp WHERE id < 3')\n"
        "print(dataclasses.is_dataclass(r))\n"
        "try:\n"
        "    r.rows = []\n"
        "    print('mutable')\n"
        "except dataclasses.FrozenInstanceError:\n"
        "    print('frozen')\n"
        "print(repr((r.columns, r.types, r.rows)))\n"
    )
    assert lib(body, data).splitlines() == [
        "True",
        "frozen",
        repr((["id", "name"], ["INTEGER", "TEXT"], [(1, "Ann"), (2, "Bob")])),
    ]


def test_api_error_hierarchy(lib):
    """R21: error classes exported and subclass MiniSQLError(Exception)."""
    body = (
        "names = ['LexError', 'ParseError', 'SemanticError', 'QueryRuntimeError', 'DataIOError']\n"
        "print(issubclass(minisql.MiniSQLError, Exception))\n"
        "print(all(issubclass(getattr(minisql, n), minisql.MiniSQLError) for n in names))\n"
    )
    assert lib(body).splitlines() == ["True", "True"]


def test_api_lex_error_attributes(query):
    """R17, R21: LexError attributes and str()."""
    assert query("SELECT 1 # 2") == repr(
        ("err", "LexError", "Lex", 1, 10, "unexpected character '#'",
         "LexError at line 1, column 10: unexpected character '#'")
    )


def test_api_parse_error_attributes(query):
    """R17, R21: ParseError attributes and str()."""
    assert query("SELECT name FROM") == repr(
        ("err", "ParseError", "Parse", 1, 17, "unexpected end of input",
         "ParseError at line 1, column 17: unexpected end of input")
    )


def test_api_semantic_error_attributes(query):
    """R17, R21: SemanticError attributes and str()."""
    assert query("SELECT name + 1 FROM emp") == repr(
        ("err", "SemanticError", "Semantic", 1, 13, "type mismatch: cannot apply '+' to TEXT and INTEGER",
         "SemanticError at line 1, column 13: type mismatch: cannot apply '+' to TEXT and INTEGER")
    )


def test_api_runtime_error_attributes(query):
    """R17, R21: QueryRuntimeError kind Runtime, formatted as RuntimeError."""
    assert query("SELECT 1 / 0") == repr(
        ("err", "QueryRuntimeError", "Runtime", 1, 10, "division by zero",
         "RuntimeError at line 1, column 10: division by zero")
    )


def test_api_io_error_attributes(lib, data):
    """R2, R17, R21: connect() raises DataIOError immediately; kind IO, no position."""
    missing = str(data) + "_missing"
    body = (
        "try:\n"
        "    minisql.connect(DATA)\n"
        "    print('no error')\n"
        "except minisql.MiniSQLError as e:\n"
        "    print(repr((type(e).__name__, e.kind, e.line, e.column, e.message, str(e))))\n"
    )
    assert lib(body, missing) == repr(
        ("DataIOError", "IO", None, None, f"data directory not found: {missing}",
         f"IOError: data directory not found: {missing}")
    )


def test_api_schema_case_insensitive(lib, data):
    """R3, R6, R17: schema lookup is case-insensitive; REAL/TEXT inference."""
    assert lib("print(repr(minisql.connect(DATA).schema('MIXED')))", data) == repr(
        [("a", "INTEGER"), ("b", "REAL"), ("c", "INTEGER"), ("d", "TEXT"), ("e", "TEXT")]
    )


# ---------------------------------------------------------------- formats (R18)


def test_format_functions(lib, data):
    """R17, R18: format_csv/format_table quoting, escapes, alignment, footer."""
    body = (
        "r = minisql.connect(DATA).execute(\"SELECT 'a\\rb' AS p, 'x ' AS q, 'a\\nb' AS r, 1.5 AS s\")\n"
        "print(repr(minisql.format_csv(r)))\n"
        "print(repr(minisql.format_table(r)))\n"
    )
    assert lib(body, data).splitlines() == [
        repr('p,q,r,s\n"a\rb","x ","a\nb",1.5\n'),
        repr("p    | q  | r    | s\n-----+----+------+----\na\\rb | x  | a\\nb | 1.5\n(1 row)\n"),
    ]


def test_table_format_mixed_types(sql):
    """R18: TEXT/NULL left-aligned, REAL right-aligned, newline escaped, trailing spaces stripped."""
    ok(
        sql("SELECT 'x' AS t, 2.5 AS r, NULL AS n, 'a\nb' AS m", "--format", "table"),
        "t | r   | n    | m\n--+-----+------+-----\nx | 2.5 | NULL | a\\nb\n(1 row)\n",
    )


def test_table_format_zero_rows(sql):
    """R18: zero rows footer is (0 rows)."""
    ok(sql("SELECT id FROM emp WHERE id > 99", "--format", "table"), "id\n--\n(0 rows)\n")


def test_table_format_right_align_and_nulls(sql):
    """R18: numeric cells right-aligned to the widest cell; NULL left-aligned."""
    ok(
        sql("SELECT salary * -10 AS s, dept FROM emp WHERE id > 2", "--format", "table"),
        "s     | dept\n------+-----\n -800 | ops\n -800 | NULL\n-1200 | ops\n(3 rows)\n",
    )


def test_utf8_output(sql):
    """R18, R19: stdout is UTF-8; table width counts code points."""
    ok(sql("SELECT 'héllo ☃' AS s"), "s\nhéllo ☃\n")
    ok(sql("SELECT 'héllo ☃' AS s", "--format", "table"), "s\n-------\nhéllo ☃\n(1 row)\n")


def test_csv_quoting_more(sql):
    """R18: trailing space, embedded newline and comma header are quoted."""
    ok(sql("SELECT 'x ' AS \"a,b\", 'l1\nl2' AS c"), '"a,b",c\n"x ","l1\nl2"\n')


# ---------------------------------------------------------------- CLI (R19)


def test_cli_usage_error(cli, data):
    """R19: argparse usage error exits 2 with empty stdout."""
    code, out, _ = cli("--data", data, "--format", "xml", "SELECT 1")
    assert (code, out) == (2, "")


def test_cli_default_data_dir(cli):
    """R19: --data defaults to '.'; query without FROM needs no tables."""
    ok(cli("SELECT 1 AS x"), "x\n1\n")


def test_cli_io_error_exit_code(cli, make_data):
    """R19, R21: IO errors during a query exit 3."""
    d = make_data({"t.csv": b"a,a\n1,2\n"})
    fails(cli("--data", d, "SELECT * FROM t"), "IOError: t.csv: duplicate column 'a'", 3)


# ---------------------------------------------------------------- REPL (R20)


def test_repl_tables_and_schema(cli, data):
    """R20: .tables and .schema output; EOF with empty buffer exits 0."""
    ok(
        cli("--data", data, stdin=".tables\n.schema emp\n"),
        "minisql> dept\nemp\nfiles\nmixed\nminisql> id INTEGER\nname TEXT\ndept TEXT\nsalary INTEGER\nminisql> ",
    )


def test_repl_error_continues(cli, data):
    """R20, R21: errors go to stderr and the session continues in table format."""
    res = cli("--data", data, stdin="SELECT nope;\nSELECT 1 AS a;\n")
    assert res == (
        0,
        "minisql> minisql> a\n-\n1\n(1 row)\nminisql> ",
        "SemanticError at line 1, column 8: unknown column 'nope'\n",
    )


def test_repl_positions_relative_to_buffer(cli, data):
    """R20, R21: error positions are relative to the multi-line buffer."""
    res = cli("--data", data, stdin="SELECT 1,\n  #;\n")
    assert res == (0, "minisql>    ...> minisql> ", "LexError at line 2, column 3: unexpected character '#'\n")


def test_repl_eof_executes_buffer(cli, data):
    """R20: at EOF a non-empty buffer is executed, then exit 0."""
    ok(cli("--data", data, stdin="SELECT 1 AS a\n"), "minisql>    ...> a\n-\n1\n(1 row)\n")


def test_repl_unknown_command(cli, data):
    """R20: unknown command message on stderr."""
    assert cli("--data", data, stdin=".foo\n") == (0, "minisql> minisql> ", "unknown command: .foo\n")


def test_repl_blank_lines_and_exit(cli, data):
    """R20: blank lines ignored; .exit stops before later input."""
    ok(
        cli("--data", data, stdin="\n\nSELECT 1 AS a;\n.exit\nSELECT 2;\n"),
        "minisql> minisql> minisql> a\n-\n1\n(1 row)\nminisql> ",
    )


def test_repl_dot_line_inside_buffer_is_sql(cli, data):
    """R20: a dot line is only a command when the buffer is empty."""
    res = cli("--data", data, stdin="SELECT 1 AS a\n.quit\n;\n")
    assert res == (
        0,
        "minisql>    ...>    ...> minisql> ",
        "ParseError at line 2, column 1: unexpected token '.'\n",
    )
