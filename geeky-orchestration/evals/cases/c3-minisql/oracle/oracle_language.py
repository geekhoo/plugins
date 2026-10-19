"""Lexer, parser, semantic analysis and expression semantics (R4-R10, R16, R21)."""
import pytest


def ok(res, out):
    assert res == (0, out, "")


def fails(res, line, code=1):
    assert res == (code, "", line + "\n")


# ---------------------------------------------------------------- lexer (R4)


@pytest.mark.parametrize(
    "q, line",
    [
        ("SELECT 1abc", "LexError at line 1, column 8: invalid number literal"),
        ("SELECT 1.2.3", "LexError at line 1, column 8: invalid number literal"),
        ('SELECT "abc FROM emp', "LexError at line 1, column 8: unterminated quoted identifier"),
        ("SELECT 'it''s", "LexError at line 1, column 8: unterminated string literal"),
    ],
)
def test_lex_errors(sql, q, line):
    """R4, R21: lexical error templates and positions."""
    fails(sql(q), line)


def test_lex_comment_and_escaped_quote(sql):
    """R4: -- comments to end of line; '' inside a string is a literal quote."""
    ok(sql("SELECT 'it''s' AS s -- trailing comment"), "s\nit's\n")


def test_lex_real_literal_forms(sql):
    """R4, R18: REAL literal forms and repr output."""
    ok(sql("SELECT .5 AS a, 1e3 AS b, 2. AS c, 1.5E-1 AS d, 1e20 AS e"), "a,b,c,d,e\n0.5,1000.0,2.0,0.15,1e+20\n")


def test_lex_positions_tab_line2(query):
    """R4, R21: lines split on \\n, tab counts one column."""
    assert query("SELECT\n\t1 $") == repr(
        ("err", "LexError", "Lex", 2, 4, "unexpected character '$'",
         "LexError at line 2, column 4: unexpected character '$'")
    )


def test_lex_positions_cr_and_codepoints(query):
    """R4, R21: \\r is whitespace and one column; columns count code points."""
    assert query("SELECT 1,\n\r'é', @") == repr(
        ("err", "LexError", "Lex", 2, 7, "unexpected character '@'",
         "LexError at line 2, column 7: unexpected character '@'")
    )


def test_lex_case_insensitive_keywords(sql):
    """R6: keywords are case-insensitive."""
    ok(sql("sElEcT 1 aS x"), "x\n1\n")


def test_quoted_identifiers_may_be_keywords(cli, make_data):
    """R4, R6, R10: quoted identifiers may equal keywords; resolution case-insensitive; header name verbatim."""
    d = make_data({"kw.csv": b"select,Order\n1,a\n"})
    ok(cli("--data", d, 'SELECT "select", "ORDER" FROM kw'), "select,Order\n1,a\n")


def test_quoted_identifier_doubled_quote(sql):
    """R4, R18: "" in a quoted identifier is a literal quote; header quoting."""
    ok(sql('SELECT 1 AS "a""b"'), '"a""b"\n1\n')


# ---------------------------------------------------------------- parser (R5)


@pytest.mark.parametrize(
    "q, line",
    [
        ("SELECT 1 = 2 = 3", "ParseError at line 1, column 14: unexpected token '='"),
        ("SELECT", "ParseError at line 1, column 7: unexpected end of input"),
        ("SELECT 1; 2", "ParseError at line 1, column 11: unexpected token '2'"),
        ("SELECT 1 FROM emp LIMIT -1", "ParseError at line 1, column 25: unexpected token '-'"),
        ("SELECT 1 FROM emp LIMIT 1.5", "ParseError at line 1, column 25: unexpected token '1.5'"),
        ("SELECT id FROM emp WHERE", "ParseError at line 1, column 25: unexpected end of input"),
        ("SELECT name FROM emp ORDER", "ParseError at line 1, column 27: unexpected end of input"),
    ],
)
def test_parse_errors(sql, q, line):
    """R5, R15, R21: non-associative comparisons, LIMIT literal, end of input."""
    fails(sql(q), line)


def test_precedence_and_associativity(sql):
    """R5: left-assoc arithmetic, unary chains, NOT above AND above OR."""
    ok(
        sql("SELECT 2 - 3 - 4 AS a, 10 % 4 * 3 AS b, - -1 AS c, 1 OR 0 AND 0 AS d, NOT 0 AND 0 AS e"),
        "a,b,c,d,e\n-5,6,1,1,0\n",
    )


def test_optional_as_and_semicolon(sql):
    """R5, R6: implicit item and table aliases; trailing semicolon."""
    ok(sql("SELECT name n FROM emp x WHERE x.id = 2;"), "n\nBob\n")


def test_from_less_query(sql):
    """R5, R12: without FROM there is exactly one empty row."""
    ok(sql("SELECT COUNT(*) AS c"), "c\n1\n")
    ok(sql("SELECT 1 AS a WHERE 0"), "a\n")


# ---------------------------------------------------------------- naming (R10)


def test_output_name_verbatim_source(sql):
    """R10: verbatim item text, including inner whitespace and parentheses."""
    ok(sql("SELECT id  +  1, (id), count( * ) FROM emp WHERE id = 1 GROUP BY id"), "id  +  1,(id),count( * )\n2,1,1\n")


def test_output_name_quoted_column_uses_header(sql):
    """R6, R10: a quoted column reference is named by the CSV header."""
    ok(sql('SELECT "NAME" FROM emp WHERE id = 1'), "name\nAnn\n")


def test_duplicate_output_names(sql):
    """R10: duplicate output names are allowed."""
    ok(sql("SELECT id, id FROM emp WHERE id = 1"), "id,id\n1,1\n")


# ---------------------------------------------------------------- semantic errors (R7, R21)


@pytest.mark.parametrize(
    "q, msg",
    [
        ("SELECT emp.name FROM emp e", "column 8: unknown column 'emp.name'"),
        ("SELECT 1 FROM emp JOIN emp ON 1 = 1", "column 24: duplicate table name 'emp'"),
        ("SELECT nope FROM emp", "column 8: unknown column 'nope'"),
        ("SELECT e.nope FROM emp e", "column 8: unknown column 'e.nope'"),
        ("SELECT code FROM dept a JOIN dept b ON a.code = b.code", "column 8: ambiguous column 'code'"),
        ("SELECT 1 FROM emp e JOIN dept d ON e.dept = f.code JOIN dept f ON 1 = 1", "column 45: unknown column 'f.code'"),
        ("SELECT foo(id) FROM emp", "column 8: unknown function 'foo'"),
        ("SELECT -name FROM emp", "column 8: type mismatch: cannot apply '-' to TEXT"),
        ("SELECT 1 FROM emp WHERE id LIKE 'a'", "column 28: type mismatch: cannot apply 'LIKE' to INTEGER and TEXT"),
        ("SELECT 1 FROM emp WHERE id IN (1, 'a')", "column 28: type mismatch: cannot apply 'IN' to INTEGER and TEXT"),
        ("SELECT SUM(name) FROM emp", "column 8: type mismatch: cannot apply 'SUM' to TEXT"),
        ("SELECT 1 FROM emp WHERE name", "column 25: condition must be numeric, got TEXT"),
        ("SELECT 1 FROM emp WHERE COUNT(*) > 1", "column 25: aggregate function not allowed here"),
        ("SELECT SUM(COUNT(*)) FROM emp", "column 12: aggregate function not allowed here"),
        ("SELECT name, COUNT(*) FROM emp GROUP BY dept", "column 8: column 'name' must appear in GROUP BY or be used in an aggregate"),
        ("SELECT *, COUNT(*) FROM emp", "column 8: '*' not allowed in aggregate query"),
        ("SELECT id FROM emp ORDER BY 2", "column 29: ORDER BY position 2 is out of range"),
        ("SELECT id FROM emp ORDER BY 0", "column 29: ORDER BY position 0 is out of range"),
        ("SELECT fname FROM files WHERE fname LIKE 'a' ESCAPE '!!'", "column 53: ESCAPE must be a single character"),
        ("SELECT id AS k, salary AS k FROM emp ORDER BY k", "column 47: ambiguous column 'k'"),
        ("SELECT id AS k FROM emp WHERE k = 1", "column 31: unknown column 'k'"),
    ],
)
def test_semantic_errors(sql, q, msg):
    """R6, R7, R10-R14, R21: semantic error templates and positions."""
    fails(sql(q), "SemanticError at line 1, " + msg)


def test_star_argument_only_for_count(sql):
    """R12, R21: '*' argument is only for COUNT; positioned at the '*' token."""
    fails(sql("SELECT SUM(*) FROM emp"), "SemanticError at line 1, column 12: '*' argument only allowed for COUNT")


@pytest.mark.parametrize(
    "q, msg",
    [
        ("SELECT 1 FROM emp e JOIN dept e ON 1 = 1", "column 31: duplicate table name 'e'"),
        ("SELECT 1 FROM emp E JOIN dept e ON 1 = 1", "column 31: duplicate table name 'e'"),
        ("SELECT 1 FROM emp JOIN dept AS emp ON 1 = 1", "column 32: duplicate table name 'emp'"),
    ],
)
def test_duplicate_range_name_with_aliases(sql, q, msg):
    """R6, R21: duplicate range name at the second tableref's range-name token, as written."""
    fails(sql(q), "SemanticError at line 1, " + msg)


def test_semantic_error_before_rows(sql):
    """R7: type errors are raised even when no row would be evaluated."""
    fails(
        sql("SELECT name + 1 FROM emp WHERE id > 99"),
        "SemanticError at line 1, column 13: type mismatch: cannot apply '+' to TEXT and INTEGER",
    )


# ---------------------------------------------------------------- arithmetic (R8)


def test_arithmetic_mixed(sql):
    """R8: integer %, REAL % (fmod), mixed promotion."""
    ok(
        sql("SELECT -7 % 2, 7.5 % 2, -7.5 % 2, 1 + 2.5, 2 * 0.5, 0.1 + 0.2"),
        "-7 % 2,7.5 % 2,-7.5 % 2,1 + 2.5,2 * 0.5,0.1 + 0.2\n-1,1.5,-1.5,3.5,1.0,0.30000000000000004\n",
    )


def test_arithmetic_big_integer(sql):
    """R8: INTEGER is an unbounded Python int."""
    ok(sql("SELECT 99999999999999999999 * 10 AS big"), "big\n999999999999999999990\n")


@pytest.mark.parametrize(
    "q, col",
    [("SELECT 1 / 0", 10), ("SELECT 1.0 / 0", 12), ("SELECT 5 % 0", 10), ("SELECT NULL AND 1 / 0", 19)],
)
def test_division_by_zero(sql, q, col):
    """R8, R16, R21: zero divisor at the operator; AND evaluates right when left is NULL."""
    fails(sql(q), f"RuntimeError at line 1, column {col}: division by zero")


def test_division_by_zero_first_row(sql):
    """R8, R16: the first failing row (Ann, id 1) is reported, no output."""
    fails(
        sql("SELECT name FROM emp WHERE salary / (id - 1) > 0"),
        "RuntimeError at line 1, column 35: division by zero",
    )


def test_no_runtime_error_without_rows(sql):
    """R16: expressions are only evaluated for surviving rows."""
    ok(sql("SELECT 1 / 0 FROM emp WHERE id > 99"), "1 / 0\n")


def test_short_circuit(sql):
    """R16: AND skips right on false, OR skips right on true."""
    ok(sql("SELECT 0 AND 1 / 0 AS a, 1 OR 1 / 0 AS b"), "a,b\n0,1\n")


def test_static_result_types(query):
    """R7, R8, R17: NULL type only for NULL literal / NULL op NULL; arithmetic promotion."""
    assert query("SELECT NULL AS a, NULL + 1 AS b, NULL + NULL AS c, 1 + 1.0 AS d, -NULL AS e, 1 = 1 AS f") == repr(
        ("ok", ["a", "b", "c", "d", "e", "f"], ["NULL", "INTEGER", "NULL", "REAL", "NULL", "INTEGER"],
         [(None, None, None, 2.0, None, 1)])
    )


# ---------------------------------------------------------------- predicates (R9)


def test_comparisons(sql):
    """R9: numeric mixed comparison, code-point TEXT ordering, NULL comparisons."""
    ok(
        sql("SELECT 1 = 1.0 AS a, 2 > 1.5 AS b, 'a' < 'b' AS c, 'B' < 'a' AS d, NULL = NULL AS e, 1 <> 2 AS f, 1 != 1 AS g"),
        "a,b,c,d,e,f,g\n1,1,1,1,,1,0\n",
    )


def test_is_null(sql):
    """R9: IS [NOT] NULL never yields NULL."""
    ok(sql("SELECT NULL IS NULL AS a, 1 IS NULL AS b, NULL IS NOT NULL AS c, 1 IS NOT NULL AS d"), "a,b,c,d\n1,0,0,1\n")


def test_and_or_not_truth_table(sql):
    """R9: three-valued AND/OR/NOT; nonzero REAL is true."""
    ok(
        sql("SELECT NULL AND 0 AS a, NULL AND 1 AS b, NULL OR 1 AS c, NULL OR 0 AS d, NOT NULL AS e, 0.5 AND 2 AS f"),
        "a,b,c,d,e,f\n0,,1,,,1\n",
    )


def test_in_semantics(sql):
    """R9: IN / NOT IN with NULLs and mixed numerics."""
    ok(
        sql("SELECT 2 IN (1, 2) AS a, 3 IN (1, 2) AS b, 3 IN (1, NULL) AS c, NULL IN (1) AS d, "
            "2 NOT IN (1, NULL) AS e, 2 NOT IN (1, 3) AS f, 1 IN (1.0) AS g"),
        "a,b,c,d,e,f,g\n1,0,,,,1,1\n",
    )


def test_like_semantics(sql):
    """R9: whole-string, case-sensitive LIKE; regex metacharacters are literal; NULL operand."""
    ok(
        sql("SELECT 'abc' LIKE 'a%' AS a, 'abc' LIKE 'A%' AS b, 'abc' LIKE '_b_' AS c, 'abc' LIKE 'ab' AS d, "
            "'' LIKE '%' AS e, NULL LIKE 'a' AS f, 'a' NOT LIKE 'b' AS g, 'abc' LIKE 'a.c' AS h, "
            "'a.c' LIKE 'a.c' AS i, 'a!b' LIKE 'a!!b' ESCAPE '!' AS j, 'a(b' LIKE 'a(%' AS k"),
        "a,b,c,d,e,f,g,h,i,j,k\n1,0,1,0,1,,1,0,1,1,1\n",
    )


def test_like_underscore_matches_newline(query):
    """R9: '_' matches exactly one character, including a newline."""
    assert query("SELECT 'a\nb' LIKE 'a_b' AS m, 'a\nb' LIKE 'a%' AS n") == repr(
        ("ok", ["m", "n"], ["INTEGER", "INTEGER"], [(1, 1)])
    )
