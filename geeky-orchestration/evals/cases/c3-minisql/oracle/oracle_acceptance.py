"""Acceptance criteria AC1-AC11 plus the R1 import scan."""
import ast
import sys


def ok(res, out):
    assert res == (0, out, "")


def fails(res, line, code=1):
    assert res == (code, "", line + "\n")


def test_ac1_select_literal(sql):
    """AC1, R1, R19: one-shot CSV of a literal with alias."""
    ok(sql("SELECT 1 AS one"), "one\n1\n")


def test_ac1_package_layout(target):
    """AC1, R1: flat package with __init__.py and __main__.py at repo root."""
    assert (target / "minisql" / "__init__.py").is_file()
    assert (target / "minisql" / "__main__.py").is_file()


def test_ac1_import_scan(target):
    """AC1, R1: only stdlib imports, never sqlite3; no eval()/exec() calls in minisql/."""
    allowed = set(sys.stdlib_module_names) - {"sqlite3", "_sqlite3"}
    files = sorted((target / "minisql").rglob("*.py"))
    assert files, "no .py files under minisql/"
    problems = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                mods = [node.module or ""]
            for mod in mods:
                top = mod.split(".")[0]
                if top != "minisql" and top not in allowed:
                    problems.append(f"{path.name}:{node.lineno}: import {mod}")
            # Bare builtin calls only (and builtins.eval/exec); methods named eval are fine.
            if isinstance(node, ast.Call):
                fn = node.func
                name = None
                if isinstance(fn, ast.Name):
                    name = fn.id
                elif isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "builtins":
                    name = fn.attr
                if name in ("eval", "exec"):
                    problems.append(f"{path.name}:{node.lineno}: call {name}()")
    assert not problems, "\n".join(problems)


def test_ac2_select_star_case_insensitive_table(sql):
    """AC2, R2, R6: SELECT * FROM EMP returns all 5 rows with CSV header names."""
    ok(
        sql("SELECT * FROM EMP"),
        "id,name,dept,salary\n1,Ann,eng,100\n2,Bob,eng,\n3,Cid,ops,80\n4,Dee,,80\n5,Eve,ops,120\n",
    )


def test_ac2_missing_data_dir(cli):
    """AC2, R19, R21: missing data dir is IOError with exit 3."""
    fails(cli("--data", "missing", "SELECT * FROM emp"), "IOError: data directory not found: missing", 3)


def test_ac3_schema(lib, data):
    """AC3, R3, R17: schema('emp') inferred types in header order."""
    out = lib("print(repr(minisql.connect(DATA).schema('emp')))", data)
    assert out == repr([("id", "INTEGER"), ("name", "TEXT"), ("dept", "TEXT"), ("salary", "INTEGER")])


def test_ac4_lex_error(sql):
    """AC4, R4, R21: unexpected character position."""
    fails(sql("SELECT 1 # 2"), "LexError at line 1, column 10: unexpected character '#'")


def test_ac5_precedence(sql):
    """AC5, R5, R10: precedence and verbatim output names."""
    ok(sql("SELECT 1 + 2 * 3, -2 * 3, NOT 1 = 2"), "1 + 2 * 3,-2 * 3,NOT 1 = 2\n7,-6,1\n")


def test_ac6_case_insensitive_names(sql):
    """AC6, R6, R10: keywords/names case-insensitive; header from CSV."""
    ok(sql("select NAME from Emp e where E.Id = 1"), "name\nAnn\n")


def test_ac7_type_mismatch(sql):
    """AC7, R7, R21: static type error at operator."""
    fails(
        sql("SELECT name + 1 FROM emp"),
        "SemanticError at line 1, column 13: type mismatch: cannot apply '+' to TEXT and INTEGER",
    )


def test_ac8_arithmetic(sql):
    """AC8, R8: integer truncation, sign of %, REAL division, NULL before zero check."""
    ok(
        sql("SELECT 7 / 2, -7 / 2, 7 % -2, 7.0 / 2, NULL / 0"),
        "7 / 2,-7 / 2,7 % -2,7.0 / 2,NULL / 0\n3,-3,1,3.5,\n",
    )


def test_ac9_not_in_with_null(sql):
    """AC9, R9: NOT IN with a NULL item never yields true."""
    ok(sql("SELECT name FROM emp WHERE dept NOT IN ('eng', NULL)"), "name\n")


def test_ac10_projection_naming(sql):
    """AC10, R10: expression names verbatim, alias names."""
    ok(sql("SELECT salary * 2, name AS n FROM emp WHERE id = 1"), "salary * 2,n\n200,Ann\n")


def test_ac11_library_avg(query):
    """AC11, R12, R17: AVG is REAL through the library API."""
    assert query("SELECT AVG(salary) FROM emp") == repr(("ok", ["AVG(salary)"], ["REAL"], [(95.0,)]))
