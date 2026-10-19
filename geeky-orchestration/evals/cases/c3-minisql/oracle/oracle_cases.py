"""The 15 reference oracle cases (AC12)."""


def ok(res, out):
    assert res == (0, out, "")


def fails(res, line, code=1):
    assert res == (code, "", line + "\n")


def test_case01_join_duplicates(sql):
    """Case 1, AC12, R11: inner join emits one row per matching pair in nested-loop order."""
    ok(
        sql("SELECT e.name, d.title FROM emp e JOIN dept d ON e.dept = d.code ORDER BY e.id"),
        "name,title\nAnn,Engineering\nBob,Engineering\nCid,Operations\nCid,Ops Dup\nEve,Operations\nEve,Ops Dup\n",
    )


def test_case02_left_join_null_fill(sql):
    """Case 2, AC12, R11: LEFT JOIN NULL-fills unmatched left rows."""
    ok(
        sql("SELECT e.name, d.title FROM emp e LEFT JOIN dept d ON e.dept = d.code WHERE e.id >= 3"),
        "name,title\nCid,Operations\nCid,Ops Dup\nDee,\nEve,Operations\nEve,Ops Dup\n",
    )


def test_case02_left_join_anti(sql):
    """Case 2, AC12, R11, R9: anti-join via IS NULL on the right side."""
    ok(sql("SELECT d.code FROM dept d LEFT JOIN emp e ON e.dept = d.code WHERE e.id IS NULL"), "code\nhr\n")


def test_case03_null_group(sql):
    """Case 3, AC12, R12, R14: NULL forms its own group and sorts first."""
    ok(
        sql(
            "SELECT dept, COUNT(*) AS n, COUNT(salary) AS ns, SUM(salary) AS s, AVG(salary) AS a "
            "FROM emp GROUP BY dept ORDER BY dept"
        ),
        "dept,n,ns,s,a\n,1,1,80,80.0\neng,2,1,100,100.0\nops,2,2,200,100.0\n",
    )


def test_case04_having(sql):
    """Case 4, AC12, R12, R14: HAVING with aggregates; ORDER BY alias DESC."""
    ok(
        sql(
            "SELECT dept, MAX(salary) AS top FROM emp GROUP BY dept "
            "HAVING COUNT(*) > 1 AND MIN(salary) >= 80 ORDER BY top DESC"
        ),
        "dept,top\nops,120\neng,100\n",
    )


def test_case05_order_desc_nulls_last(sql):
    """Case 5, AC12, R14: DESC puts NULL last; ties stable."""
    ok(
        sql("SELECT name, salary FROM emp ORDER BY salary DESC"),
        "name,salary\nEve,120\nAnn,100\nCid,80\nDee,80\nBob,\n",
    )


def test_case05_order_multi_key(sql):
    """Case 5, AC12, R14: multiple keys, mixed directions, NULL first in ASC."""
    ok(sql("SELECT name FROM emp ORDER BY salary, name DESC"), "name\nBob\nDee\nCid\nAnn\nEve\n")


def test_case06_like_escape_underscore(sql):
    """Case 6, R9: ESCAPE makes '_' literal."""
    ok(sql("SELECT fname FROM files WHERE fname LIKE 'report!_%' ESCAPE '!'"), "fname\nreport_1.txt\n")


def test_case06_like_escape_percent(sql):
    """Case 6, R9: ESCAPE makes '%' literal."""
    ok(sql("SELECT fname FROM files WHERE fname LIKE '%!%%' ESCAPE '!'"), "fname\n100%.txt\n")


def test_case06_like_backslash_literal(sql):
    """Case 6, R4, R9: backslash is literal in strings and patterns."""
    ok(sql("SELECT fname FROM files WHERE fname LIKE 'a\\b'"), "fname\na\\b\n")


def test_case06_like_case_sensitive(sql):
    """Case 6, R9: LIKE is case-sensitive."""
    ok(sql("SELECT fname FROM files WHERE fname LIKE 'REPORT%'"), "fname\n")


def test_case06_like_invalid_pattern(sql):
    """Case 6, R9, R21: escape char at pattern end is RuntimeError at LIKE."""
    fails(
        sql("SELECT fname FROM files WHERE fname LIKE 'x!' ESCAPE '!'"),
        "RuntimeError at line 1, column 37: invalid LIKE pattern",
    )


def test_case07_division_by_zero(sql):
    """Case 7, AC12, R8, R16: first failing row aborts with no output."""
    fails(
        sql("SELECT name FROM emp WHERE 10 / (salary - 80) > 0"),
        "RuntimeError at line 1, column 31: division by zero",
    )


def test_case07_and_short_circuit(sql):
    """Case 7, AC12, R16: AND skips the right side when left is false."""
    ok(sql("SELECT name FROM emp WHERE salary <> 80 AND 100 / (salary - 80) > 1"), "name\nAnn\nEve\n")


def test_case08_type_inference_output(sql):
    """Case 8, R3, R18: inference, NULLs, REAL repr, TEXT verbatim and quoting."""
    ok(
        sql("SELECT a + 1, b, c, d, e FROM mixed ORDER BY d"),
        'a + 1,b,c,d,e\n3,2.0,,1,2\n,300.0,-4,2,3\n2,1.5,7,x," 1"\n',
    )


def test_case08_type_inference_types(query):
    """Case 8, R3, R17: result types of inferred columns."""
    assert query("SELECT a + 1, b, c, d, e FROM mixed ORDER BY d") == repr(
        (
            "ok",
            ["a + 1", "b", "c", "d", "e"],
            ["INTEGER", "REAL", "INTEGER", "TEXT", "TEXT"],
            [(3, 2.0, None, "1", "2"), (None, 300.0, -4, "2", "3"), (2, 1.5, 7, "x", " 1")],
        )
    )


def test_case08_text_vs_integer(sql):
    """Case 8, R7: numeric-looking TEXT column compared to INTEGER is a SemanticError."""
    fails(
        sql("SELECT d FROM mixed WHERE d = 1"),
        "SemanticError at line 1, column 29: type mismatch: cannot apply '=' to TEXT and INTEGER",
    )


def test_case09_parse_error_multiline(sql):
    """Case 9, AC12, R5, R21: position on line 4 of a multi-line query."""
    fails(
        sql("SELECT name,\n       salary\nFROM emp\nWHERE salary >> 3"),
        "ParseError at line 4, column 15: unexpected token '>'",
    )


def test_case09_unterminated_string(sql):
    """Case 9, AC12, R4, R21: unterminated string at opening quote."""
    fails(sql("SELECT 'abc FROM emp"), "LexError at line 1, column 8: unterminated string literal")


def test_case09_double_quotes_are_identifiers(sql):
    """Case 9, AC12, R4, R21: "Ann" is a quoted identifier, so an unknown column."""
    fails(
        sql('SELECT name FROM emp WHERE name = "Ann"'),
        "SemanticError at line 1, column 35: unknown column 'Ann'",
    )


def test_case09_unexpected_end(sql):
    """Case 9, AC12, R5, R21: end of input positioned one past the last character."""
    fails(sql("SELECT name FROM"), "ParseError at line 1, column 17: unexpected end of input")


def test_case09_unknown_table(sql):
    """Case 9, AC12, R21: unknown table at its name token."""
    fails(sql("SELECT * FROM nope"), "SemanticError at line 1, column 15: unknown table 'nope'")


def test_case10_empty_aggregate(sql):
    """Case 10, AC12, R12: aggregate without GROUP BY over empty input yields one row."""
    ok(
        sql("SELECT COUNT(*), SUM(salary), AVG(salary), MIN(name), MAX(salary) FROM emp WHERE id > 99"),
        "COUNT(*),SUM(salary),AVG(salary),MIN(name),MAX(salary)\n0,,,,\n",
    )


def test_case10_empty_grouped(sql):
    """Case 10, AC12, R12: GROUP BY over empty input yields zero rows."""
    ok(sql("SELECT dept, COUNT(*) FROM emp WHERE id > 99 GROUP BY dept"), "dept,COUNT(*)\n")


def test_case11_not_null(sql):
    """Case 11, R9: NOT of NULL comparison is NULL."""
    ok(
        sql("SELECT name, NOT (salary > 90) AS low FROM emp"),
        "name,low\nAnn,0\nBob,\nCid,1\nDee,1\nEve,0\n",
    )


def test_case11_in_or_is_null(sql):
    """Case 11, R9: IN with NULL item combined with OR."""
    ok(sql("SELECT name FROM emp WHERE dept IN ('ops', NULL) OR dept IS NULL"), "name\nCid\nDee\nEve\n")


def test_case12_distinct_limit_offset(sql):
    """Case 12, AC12, R13, R15: DISTINCT, sort, OFFSET then LIMIT."""
    ok(sql("SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 2 OFFSET 1"), "salary\n100\n80\n")


def test_case12_distinct_order_by_rule(sql):
    """Case 12, AC12, R13, R21: DISTINCT ORDER BY item must be in select list."""
    fails(
        sql("SELECT DISTINCT dept FROM emp ORDER BY name"),
        "SemanticError at line 1, column 40: ORDER BY expression must appear in select list when DISTINCT is used",
    )


def test_case13_table_format(sql):
    """Case 13, AC12, R18: aligned table output."""
    ok(
        sql("SELECT id, name, salary FROM emp WHERE id <= 2", "--format", "table"),
        "id | name | salary\n---+------+-------\n 1 | Ann  |    100\n 2 | Bob  | NULL\n(2 rows)\n",
    )


def test_case14_csv_quoting(sql):
    """Case 14, AC12, R18: CSV quoting rules for comma, quote, empty, NULL, leading space."""
    ok(
        sql("SELECT 'a,b' AS x, 'say \"hi\"' AS y, '' AS z, NULL AS w, ' pad' AS v"),
        'x,y,z,w,v\n"a,b","say ""hi""","",," pad"\n',
    )


def test_case15_repl(cli, data):
    """Case 15, AC12, R20: REPL prompts, continuation, .format, .quit."""
    res = cli("--data", data, stdin="SELECT COUNT(*)\nFROM emp;\n.format csv\nSELECT 1 AS one;\n.quit\n")
    ok(res, "minisql>    ...> COUNT(*)\n--------\n       5\n(1 row)\nminisql> minisql> one\n1\nminisql> ")
