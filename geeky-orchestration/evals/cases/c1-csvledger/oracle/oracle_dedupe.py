"""Duplicate removal across and within inputs (R5)."""

import json

from conftest import O1_RULES, TX_HEADER, assert_ok

WARN_1 = "csvledger: warning: skipped 1 duplicate row(s)"


def test_o4_duplicate_across_files(run, write):
    """AC6, O4, R5: -4.50 vs -4.5 with padded description counted once; warning; exit 0."""
    rules = write("rules.csv", O1_RULES)
    a = write("a.csv", TX_HEADER + "2026-01-05,STARBUCKS #12,-4.50\n")
    b = write("b.csv", TX_HEADER + "2026-01-05,  STARBUCKS #12  ,-4.5\n")
    res = run("report", "--rules", rules, a, b)
    assert_ok(res)
    assert res.out == (
        "MONTH    CATEGORY  COUNT  INCOME  EXPENSES    NET\n"
        "-------  --------  -----  ------  --------  -----\n"
        "2026-01  Coffee        1    0.00     -4.50  -4.50\n"
    )
    assert res.err_lines == [WARN_1]


def test_duplicates_within_one_file_counted(run, write):
    """R5, Warning text: duplicates in the same file are dropped and counted (N=2)."""
    tx = write(
        "tx.csv",
        TX_HEADER + "2026-01-05,Shop,-1.00\n2026-01-05,Shop,-1\n2026-01-05, Shop ,-1.000\n2026-01-06,Shop,-1\n",
    )
    res = run("categorize", "--format", "json", tx)
    assert_ok(res)
    assert [t["date"] for t in json.loads(res.out)["transactions"]] == ["2026-01-05", "2026-01-06"]
    assert res.err_lines == ["csvledger: warning: skipped 2 duplicate row(s)"]


def test_near_duplicates_are_kept(run, write):
    """R5: rows differing in date, amount value, or (case of) stripped description are not duplicates."""
    tx = write(
        "tx.csv",
        TX_HEADER + "2026-01-05,Shop,-1\n2026-01-06,Shop,-1\n2026-01-05,Shop,-1.01\n2026-01-05,shop,-1\n",
    )
    res = run("report", "--format", "json", tx)
    assert_ok(res)
    assert json.loads(res.out)["months"][0]["count"] == 4
    assert res.raw_err == b""


def test_first_occurrence_is_kept(run, write):
    """R5 (first occurrence kept), R7 (ties in input order): the kept row keeps its first position."""
    a = write("a.csv", TX_HEADER + "2026-01-05,X,-1\n2026-01-05,Y,-2\n")
    b = write("b.csv", TX_HEADER + "2026-01-05,X,-1.0\n")
    res = run("categorize", "--format", "json", a, b)
    assert_ok(res)
    assert [t["description"] for t in json.loads(res.out)["transactions"]] == ["X", "Y"]
    assert res.err_lines == [WARN_1]


def test_dedupe_runs_before_month_filter(run, write):
    """R5 (dedupe before --month; N covers all inputs), R8: duplicates outside the month still count."""
    a = write("a.csv", TX_HEADER + "2026-01-05,Jan,-1\n2026-02-01,Feb,-2\n2026-01-09,Jan2,-3\n")
    b = write("b.csv", TX_HEADER + "2026-01-05,Jan,-1.0\n2026-01-09, Jan2 ,-3\n2026-02-01,Feb,-2.00\n")
    res = run("categorize", "--month", "2026-02", "--format", "json", a, b)
    assert_ok(res)
    assert [t["description"] for t in json.loads(res.out)["transactions"]] == ["Feb"]
    assert res.err_lines == ["csvledger: warning: skipped 3 duplicate row(s)"]


def test_dedupe_counted_when_month_has_no_rows(run, write):
    """R5 (N regardless of --month), R8: empty filtered report still warns about out-of-month duplicates."""
    a = write("a.csv", TX_HEADER + "2026-01-05,Jan,-1\n")
    b = write("b.csv", TX_HEADER + "2026-01-05,Jan,-1\n")
    res = run("report", "--month", "2026-03", a, b)
    assert_ok(res)
    assert res.out == (
        "MONTH  CATEGORY  COUNT  INCOME  EXPENSES  NET\n"
        "-----  --------  -----  ------  --------  ---\n"
    )
    assert res.err_lines == [WARN_1]
