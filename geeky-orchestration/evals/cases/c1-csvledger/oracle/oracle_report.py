"""report command: aggregation, rounding, table layout, JSON shape, month filter."""

import json

from conftest import O1_REPORT, RULES_HEADER, TX_HEADER, assert_ok


def _cat(category, count, income, expenses, net):
    return {"category": category, "count": count, "income": income, "expenses": expenses, "net": net}


def test_o1_baseline_table(run, o1):
    """AC2, O1, R2 R3 R4 R6 R9 R10: baseline report table is byte-exact; stderr is empty."""
    rules, tx = o1
    res = run("report", "--rules", rules, tx)
    assert_ok(res)
    assert res.out == O1_REPORT
    assert res.raw_err == b""


def test_o1_explicit_table_format_matches_default(run, o1):
    """R9: --format table is identical to the default."""
    rules, tx = o1
    res = run("report", "--rules", rules, "--format", "table", tx)
    assert_ok(res)
    assert res.out == O1_REPORT


def test_o1_report_json(run, o1):
    """AC3, O1, R6 R9 R10, JSON: exact text, key order, month totals summed unrounded."""
    rules, tx = o1
    res = run("report", "--rules", rules, "--format", "json", tx)
    assert_ok(res)
    expected = {
        "months": [
            {
                "month": "2026-01",
                "count": 4,
                "income": "2500.00",
                "expenses": "-61.61",
                "net": "2438.40",
                "categories": [
                    _cat("Coffee", 1, "0.00", "-4.50", "-4.50"),
                    _cat("Groceries", 2, "0.00", "-57.11", "-57.11"),
                    _cat("Salary", 1, "2500.00", "0.00", "2500.00"),
                ],
            },
            {
                "month": "2026-02",
                "count": 2,
                "income": "0.00",
                "expenses": "-16.25",
                "net": "-16.25",
                "categories": [
                    _cat("Coffee", 1, "0.00", "-6.25", "-6.25"),
                    _cat("Uncategorized", 1, "0.00", "-10.00", "-10.00"),
                ],
            },
        ]
    }
    assert res.out == json.dumps(expected, indent=2, ensure_ascii=False) + "\n"
    parsed = json.loads(res.out)
    assert list(parsed["months"][0]) == ["month", "count", "income", "expenses", "net", "categories"]
    groceries = parsed["months"][0]["categories"][1]
    assert list(groceries) == ["category", "count", "income", "expenses", "net"]
    assert groceries["expenses"] == "-57.11"


def test_month_filter_report(run, o1):
    """AC5, R8: --month 2026-02 keeps only 2026-02 rows (widths recomputed)."""
    rules, tx = o1
    res = run("report", "--rules", rules, "--month", "2026-02", tx)
    assert_ok(res)
    assert res.out == (
        "MONTH    CATEGORY       COUNT  INCOME  EXPENSES     NET\n"
        "-------  -------------  -----  ------  --------  ------\n"
        "2026-02  Coffee             1    0.00     -6.25   -6.25\n"
        "2026-02  Uncategorized      1    0.00    -10.00  -10.00\n"
    )


def test_month_filter_no_match(run, o1):
    """R8, report table: a month with no transactions gives header and dash line only."""
    rules, tx = o1
    res = run("report", "--rules", rules, "--month", "2025-07", tx)
    assert_ok(res)
    assert res.out == (
        "MONTH  CATEGORY  COUNT  INCOME  EXPENSES  NET\n"
        "-----  --------  -----  ------  --------  ---\n"
    )


def test_o2_empty_file_table(run, write):
    """O2, Transaction CSV (header-only valid), report table: header and dashes only."""
    tx = write("tx.csv", TX_HEADER)
    res = run("report", tx)
    assert_ok(res)
    assert res.out == (
        "MONTH  CATEGORY  COUNT  INCOME  EXPENSES  NET\n"
        "-----  --------  -----  ------  --------  ---\n"
    )


def test_o2_empty_file_json(run, write):
    """O2, JSON empty: {"months": []} with indent rules, exit 0."""
    tx = write("tx.csv", TX_HEADER)
    res = run("report", "--format", "json", tx)
    assert_ok(res)
    assert res.out == '{\n  "months": []\n}\n'


def test_o5_rounding_and_sign(run, write):
    """AC9, O5, R10: HALF_UP once on unrounded sums; no -0.00."""
    rules = write("rules.csv", RULES_HEADER + "Misc,contains,misc,0\nTiny,contains,tiny,0\n")
    tx = write(
        "tx.csv",
        TX_HEADER
        + "2026-03-01,misc,0.125\n"
        "2026-03-02,misc,-0.125\n"
        "2026-03-03,tiny,0.005\n"
        "2026-03-04,tiny,0.005\n"
        "2026-03-05,tiny,-0.004\n",
    )
    res = run("report", "--rules", rules, tx)
    assert_ok(res)
    assert res.out == (
        "MONTH    CATEGORY  COUNT  INCOME  EXPENSES   NET\n"
        "-------  --------  -----  ------  --------  ----\n"
        "2026-03  Misc          2    0.13     -0.13  0.00\n"
        "2026-03  Tiny          3    0.01      0.00  0.01\n"
    )


def test_zero_amount_counts_but_adds_to_neither(run, write):
    """Transaction CSV (amount zero), R6: zero counts; income/expenses unaffected; -0 never shown."""
    tx = write("tx.csv", TX_HEADER + "2026-04-01,a,0\n2026-04-02,b,-0.00\n")
    res = run("report", "--format", "json", tx)
    assert_ok(res)
    month = json.loads(res.out)["months"][0]
    assert month["count"] == 2
    assert (month["income"], month["expenses"], month["net"]) == ("0.00", "0.00", "0.00")


def test_exact_decimal_sums(run, write):
    """R10: sums are exact Decimal arithmetic (a float would lose the cents)."""
    tx = write(
        "tx.csv",
        TX_HEADER + "2026-05-01,a,10000000000000000.01\n2026-05-02,b,0.01\n2026-05-03,c,-0.1\n2026-05-04,d,-0.2\n",
    )
    res = run("report", "--format", "json", tx)
    assert_ok(res)
    month = json.loads(res.out)["months"][0]
    assert month["income"] == "10000000000000000.02"
    assert month["expenses"] == "-0.30"
    assert month["net"] == "9999999999999999.72"


def test_categories_sorted_by_code_point(run, write):
    """Report table ordering: categories by code point (uppercase before lowercase)."""
    rules = write(
        "rules.csv",
        RULES_HEADER + "apple,contains,a1,0\nZeta,contains,z1,0\nBeta,contains,b1,0\n",
    )
    tx = write("tx.csv", TX_HEADER + "2026-01-01,a1,-1\n2026-01-02,z1,-1\n2026-01-03,b1,-1\n2026-01-04,q,-1\n")
    res = run("report", "--rules", rules, "--format", "json", tx)
    assert_ok(res)
    cats = [c["category"] for c in json.loads(res.out)["months"][0]["categories"]]
    assert cats == ["Beta", "Uncategorized", "Zeta", "apple"]


def test_non_ascii_width_and_utf8_json(run, write):
    """R11, report table (len() on code points), JSON ensure_ascii=False: non-ASCII output."""
    rules = write("rules.csv", RULES_HEADER + "Café,contains,straße,1\n")
    tx = write("tx.csv", TX_HEADER + "2026-06-01,STRASSE Bäckerei,-3\n")
    res = run("report", "--rules", rules, tx)
    assert_ok(res)
    assert res.out == (
        "MONTH    CATEGORY  COUNT  INCOME  EXPENSES    NET\n"
        "-------  --------  -----  ------  --------  -----\n"
        "2026-06  Café          1    0.00     -3.00  -3.00\n"
    )
    res_json = run("report", "--rules", rules, "--format", "json", tx)
    assert_ok(res_json)
    assert '"category": "Café"' in res_json.out
