"""Data loading, joins, grouping, ordering, DISTINCT and LIMIT (R2, R3, R11-R15)."""
import pytest


def ok(res, out):
    assert res == (0, out, "")


def fails(res, line, code=1):
    assert res == (code, "", line + "\n")


# ---------------------------------------------------------------- loading (R2)


@pytest.mark.parametrize(
    "files, line",
    [
        ({"empty.csv": b""}, "IOError: empty.csv: empty file"),
        ({"empty.csv": b"a,,c\n1,2,3\n"}, "IOError: empty.csv: empty column name"),
        ({"empty.csv": b"a,b,a\n1,2,3\n"}, "IOError: empty.csv: duplicate column 'a'"),
        ({"empty.csv": b"id,x,ID\n1,2,3\n"}, "IOError: empty.csv: duplicate column 'ID'"),
        ({"empty.csv": b"a,b\n1,2\n3\n"}, "IOError: empty.csv: line 3: expected 2 fields, got 1"),
        ({"empty.csv": b'a,b\n"x\ny",1\n2\n'}, "IOError: empty.csv: line 4: expected 2 fields, got 1"),
        ({"empty.csv": b'a\n"x"y\n'}, "IOError: empty.csv: line 2: malformed CSV"),
        ({"empty.csv": b"a\n\xff\n"}, "IOError: empty.csv: invalid UTF-8"),
    ],
)
def test_load_errors(cli, make_data, files, line):
    """R2, R19, R21: data-file IO errors exit 3 with the file's base name."""
    d = make_data(files)
    fails(cli("--data", d, "SELECT * FROM empty"), line, 3)


def test_data_dir_is_file(cli, data):
    """R2, R21: a non-directory DIR is an IOError naming DIR as given."""
    path = str(data / "emp.csv")
    fails(cli("--data", path, "SELECT * FROM emp"), f"IOError: data directory not found: {path}", 3)


def test_unreferenced_bad_file_ignored(cli, make_data):
    """R2: only tables referenced in FROM/JOIN are read."""
    d = make_data({"good.csv": b"x\n1\n", "bad.csv": b"", "worse.csv": b"a\n\xff\n"})
    ok(cli("--data", d, "SELECT x FROM good"), "x\n1\n")


def test_tables_does_not_read_contents(lib, make_data):
    """R2, R17: tables() lists stems without reading (malformed) file contents."""
    d = make_data({"bad.csv": b"", "worse.csv": b"a,a\n\xff\n", "good.csv": b"x\n1\n"})
    assert lib("print(repr(minisql.connect(DATA).tables()))", d) == repr(["bad", "good", "worse"])


def test_missing_data_dir_before_lexing(cli):
    """R2, R19: the one-shot CLI reports a missing DIR (exit 3) before lexing the SQL."""
    fails(cli("--data", "missing", "SELECT 'abc"), "IOError: data directory not found: missing", 3)


def test_ambiguous_table_file(cli, tmp_path):
    """R2, R21: two stems equal case-insensitively make the name ambiguous (case-sensitive FS only)."""
    probe = tmp_path / "probe"
    probe.mkdir()
    (probe / "a.csv").write_bytes(b"x\n1\n")
    (probe / "A.csv").write_bytes(b"x\n2\n")
    if sorted(p.name for p in probe.iterdir()) != ["A.csv", "a.csv"]:
        pytest.skip("filesystem is case-insensitive; cannot create a.csv and A.csv together")
    fails(cli("--data", probe, "SELECT x FROM a"), "IOError: ambiguous table file 'a'", 3)


@pytest.mark.parametrize(
    "q, out",
    [
        ("SELECT COUNT(*) AS n FROM emp HAVING COUNT(*) > 10", "n\n"),
        ("SELECT COUNT(*) AS n FROM emp HAVING COUNT(*) > 1", "n\n5\n"),
        ("SELECT COUNT(*) AS n FROM emp WHERE id > 99 HAVING COUNT(*) = 0", "n\n0\n"),
        ("SELECT MAX(salary) AS m FROM emp WHERE id > 99 HAVING COUNT(*) > 0", "m\n"),
    ],
)
def test_having_without_group_by(sql, q, out):
    """R12: without GROUP BY the filtered input is one group that HAVING may filter out."""
    ok(sql(q), out)


def test_bom_crlf_blank_lines(cli, make_data):
    """R2: utf-8-sig BOM stripped, CRLF records, blank lines skipped, quoted fields."""
    d = make_data({"t.csv": b'\xef\xbb\xbfa,b\r\n1,"x,y"\r\n\r\n2,z\r\n'})
    ok(cli("--data", d, "SELECT a, b FROM t"), 'a,b\n1,"x,y"\n2,z\n')


def test_table_extension_and_lookup_case_insensitive(cli, make_data):
    """R2, R6: .CSV extension accepted; table lookup case-insensitive."""
    d = make_data({"Data.CSV": b"v\n1\n"})
    ok(cli("--data", d, "SELECT v FROM data"), "v\n1\n")


def test_tables_listing(lib, make_data):
    """R2, R17: tables() lists regular *.csv stems sorted by (lower(), name)."""
    d = make_data({"b.csv": b"x\n", "A.csv": b"x\n", "c.txt": b"x\n", "C2.csv": b"x\n"})
    (d / "dir.csv").mkdir()
    assert lib("print(repr(minisql.connect(DATA).tables()))", d) == repr(["A", "b", "C2"])


# ---------------------------------------------------------------- inference (R3)


def test_inference_edge_cases(lib, make_data):
    """R3: [0-9] only (no Unicode digits, underscores, inf/nan); signs; empty column is TEXT."""
    d = make_data({
        "t.csv": "p,q,r,s,u,v,w\n+5,1_000,١,inf,1.,,1E5\n-3,2,2,nan,.5,,2\n".encode("utf-8")
    })
    body = "c = minisql.connect(DATA)\nprint(repr(c.schema('t')))\nprint(repr(run('SELECT * FROM t')))\n"
    out = lib(body, d).splitlines()
    assert out[0] == repr([("p", "INTEGER"), ("q", "TEXT"), ("r", "TEXT"), ("s", "TEXT"),
                           ("u", "REAL"), ("v", "TEXT"), ("w", "REAL")])
    assert out[1] == repr(("ok", ["p", "q", "r", "s", "u", "v", "w"],
                           ["INTEGER", "TEXT", "TEXT", "TEXT", "REAL", "TEXT", "REAL"],
                           [(5, "1_000", "١", "inf", 1.0, None, 100000.0),
                            (-3, "2", "2", "nan", 0.5, None, 2.0)]))


def test_quoted_empty_is_null(cli, make_data):
    """R3: quoted empty fields are NULL too."""
    d = make_data({"q.csv": b'"a","b"\n"",1\n'})
    ok(cli("--data", d, "SELECT a IS NULL, b FROM q"), "a IS NULL,b\n1,1\n")


# ---------------------------------------------------------------- joins (R11)


def test_inner_join_keyword_and_as(sql):
    """R11, R5: INNER JOIN with AS aliases; ON sees both tables."""
    ok(
        sql("SELECT e.name, d.title FROM emp AS e INNER JOIN dept AS d ON d.code = e.dept WHERE e.id = 1"),
        "name,title\nAnn,Engineering\n",
    )


def test_join_nested_loop_order(sql):
    """R11: output order is left rows in order, right rows in file order."""
    ok(
        sql("SELECT d.code, e.name FROM dept d JOIN emp e ON e.dept = d.code"),
        "code,name\neng,Ann\neng,Bob\nops,Cid\nops,Eve\nops,Cid\nops,Eve\n",
    )


def test_left_outer_join_count(sql):
    """R11, R12: LEFT OUTER JOIN keeps unmatched left rows once."""
    ok(sql("SELECT COUNT(*) AS n FROM emp e LEFT OUTER JOIN dept d ON e.dept = d.code"), "n\n7\n")


def test_left_join_false_condition(sql):
    """R11: LEFT JOIN with a never-true ON NULL-fills every left row."""
    ok(sql("SELECT e.name, d.code FROM emp e LEFT JOIN dept d ON 0 WHERE e.id = 1"), "name,code\nAnn,\n")


def test_star_expansion_with_join(sql):
    """R10, R11: * expands all tables in FROM order; t.* expands one table."""
    ok(
        sql("SELECT * FROM emp e JOIN dept d ON e.dept = d.code WHERE e.id = 1"),
        "id,name,dept,salary,code,title\n1,Ann,eng,100,eng,Engineering\n",
    )
    ok(
        sql("SELECT d.*, e.id FROM emp e JOIN dept d ON e.dept = d.code WHERE e.id = 1"),
        "code,title,id\neng,Engineering,1\n",
    )


# ---------------------------------------------------------------- aggregates (R12)


def test_min_max_text_and_real(sql):
    """R12: MIN/MAX keep argument type; SUM of REAL is REAL; COUNT(e) skips NULL."""
    ok(sql("SELECT MIN(name), MAX(dept) FROM emp"), "MIN(name),MAX(dept)\nAnn,ops\n")
    ok(sql("SELECT SUM(b), MAX(b), COUNT(a) FROM mixed"), "SUM(b),MAX(b),COUNT(a)\n303.5,300.0,2\n")


def test_group_first_seen_order(sql):
    """R12: groups appear in first-seen order without ORDER BY; NULL is one group."""
    ok(sql("SELECT dept, COUNT(*) FROM emp GROUP BY dept"), "dept,COUNT(*)\neng,2\nops,2\n,1\n")


def test_group_by_expression(sql):
    """R12, R14: grouping on an expression reused structurally in select and ORDER BY."""
    ok(
        sql("SELECT salary + 1, COUNT(*) FROM emp GROUP BY salary + 1 ORDER BY salary + 1"),
        "salary + 1,COUNT(*)\n,1\n81,2\n101,1\n121,1\n",
    )


def test_order_by_aggregate_not_selected(sql):
    """R12, R14: ORDER BY an aggregate not in the select list; stable tie-break key."""
    ok(sql("SELECT dept FROM emp GROUP BY dept ORDER BY COUNT(*) DESC, dept"), "dept\neng\nops\n\n")


def test_aggregate_query_via_order_by(sql):
    """R12: an aggregate in ORDER BY makes an aggregate query (one row without GROUP BY)."""
    ok(sql("SELECT 1 AS one FROM emp ORDER BY COUNT(*)"), "one\n1\n")


def test_aggregate_with_literal(sql):
    """R12: literals are allowed in aggregate queries."""
    ok(sql("SELECT 'x' AS k, COUNT(*) AS n FROM emp"), "k,n\nx,5\n")


def test_all_null_group(sql):
    """R12: MAX over only NULLs is NULL."""
    ok(sql("SELECT dept, MAX(salary) FROM emp WHERE id = 2 GROUP BY dept"), "dept,MAX(salary)\neng,\n")


# ---------------------------------------------------------------- ORDER BY (R14)


def test_order_by_ordinals(sql):
    """R14: ordinals, DESC then ASC tie-break."""
    ok(sql("SELECT name, salary FROM emp ORDER BY 2 DESC, 1"), "name,salary\nEve,120\nAnn,100\nCid,80\nDee,80\nBob,\n")


def test_order_by_ordinal_after_star(sql):
    """R14: ordinal counted after * expansion."""
    ok(
        sql("SELECT * FROM dept ORDER BY 2"),
        "code,title\neng,Engineering\nhr,Human Resources\nops,Operations\nops,Ops Dup\n",
    )


def test_order_by_alias(sql):
    """R14: bare identifier equal to an AS alias refers to the output column."""
    ok(
        sql("SELECT salary * -1 AS neg, name FROM emp ORDER BY neg"),
        "neg,name\n,Bob\n-120,Eve\n-100,Ann\n-80,Cid\n-80,Dee\n",
    )


def test_order_by_alias_without_as(sql):
    """R14: an alias written without AS also resolves in ORDER BY."""
    ok(
        sql("SELECT salary * -1 neg, name FROM emp ORDER BY neg"),
        "neg,name\n,Bob\n-120,Eve\n-100,Ann\n-80,Cid\n-80,Dee\n",
    )


def test_order_by_unselected_column(sql):
    """R14: ORDER BY an input column not in the select list."""
    ok(sql("SELECT name FROM emp ORDER BY id DESC"), "name\nEve\nDee\nCid\nBob\nAnn\n")


def test_order_desc_stable_ties(sql):
    """R14: DESC keeps pre-sort order among ties; NULL last."""
    ok(sql("SELECT name FROM emp ORDER BY dept DESC"), "name\nCid\nEve\nAnn\nBob\nDee\n")


# ---------------------------------------------------------------- DISTINCT / LIMIT (R13, R15)


def test_distinct_null_equal(sql):
    """R13: DISTINCT keeps first occurrences; NULLs are equal."""
    ok(sql("SELECT DISTINCT dept FROM emp"), "dept\neng\nops\n\n")


def test_distinct_order_by_alias(sql):
    """R13, R14: DISTINCT with ORDER BY alias."""
    ok(sql("SELECT DISTINCT dept AS d FROM emp ORDER BY d DESC"), "d\nops\neng\n\n")


def test_distinct_multi_column(sql):
    """R13: DISTINCT over whole output rows."""
    ok(sql("SELECT DISTINCT dept, salary FROM emp WHERE salary IS NOT NULL ORDER BY 2"),
       "dept,salary\nops,80\n,80\neng,100\nops,120\n")


@pytest.mark.parametrize(
    "tail, out",
    [
        ("LIMIT 0", "id\n"),
        ("LIMIT 2", "id\n1\n2\n"),
        ("OFFSET 3", "id\n4\n5\n"),
        ("LIMIT 10 OFFSET 4", "id\n5\n"),
        ("LIMIT 1 OFFSET 9", "id\n"),
    ],
)
def test_limit_offset(sql, tail, out):
    """R15: LIMIT/OFFSET; OFFSET applied before LIMIT; past end yields no rows."""
    ok(sql("SELECT id FROM emp " + tail), out)
