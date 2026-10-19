"""categorize command: ordering, table layout, JSON shape, month filter."""

import json

from conftest import TX_HEADER, assert_ok

O1_CATEGORIZE = (
    "DATE         AMOUNT  CATEGORY       DESCRIPTION\n"
    "----------  -------  -------------  ----------------\n"
    "2026-01-03   -45.10  Groceries      Corner Market\n"
    "2026-01-05    -4.50  Coffee         STARBUCKS #12\n"
    "2026-01-15  2500.00  Salary         ACME PAYROLL\n"
    "2026-01-20   -12.01  Groceries      Corner Market\n"
    "2026-02-02    -6.25  Coffee         Blue Bottle Cafe\n"
    "2026-02-10   -10.00  Uncategorized  Unknown Shop\n"
)


def test_o1_categorize_table(run, o1):
    """AC4, R7 R4 R10, categorize table: date order; Blue Bottle Cafe is Coffee; exact bytes."""
    rules, tx = o1
    res = run("categorize", "--rules", rules, tx)
    assert_ok(res)
    assert res.out == O1_CATEGORIZE
    blue = [line for line in res.out.splitlines() if "Blue Bottle Cafe" in line]
    assert len(blue) == 1 and "  Coffee  " in blue[0]


def test_o7_categorize_month(run, o1):
    """O7, R8, categorize table: --month 2026-01 full output (widths from filtered rows)."""
    rules, tx = o1
    res = run("categorize", "--month", "2026-01", "--rules", rules, tx)
    assert_ok(res)
    assert res.out == (
        "DATE         AMOUNT  CATEGORY   DESCRIPTION\n"
        "----------  -------  ---------  -------------\n"
        "2026-01-03   -45.10  Groceries  Corner Market\n"
        "2026-01-05    -4.50  Coffee     STARBUCKS #12\n"
        "2026-01-15  2500.00  Salary     ACME PAYROLL\n"
        "2026-01-20   -12.01  Groceries  Corner Market\n"
    )


def test_o1_categorize_json(run, o1):
    """R7 R9, JSON categorize: exact text and key order date, description, amount, category."""
    rules, tx = o1
    res = run("categorize", "--rules", rules, "--format", "json", tx)
    assert_ok(res)
    rows = [
        ("2026-01-03", "Corner Market", "-45.10", "Groceries"),
        ("2026-01-05", "STARBUCKS #12", "-4.50", "Coffee"),
        ("2026-01-15", "ACME PAYROLL", "2500.00", "Salary"),
        ("2026-01-20", "Corner Market", "-12.01", "Groceries"),
        ("2026-02-02", "Blue Bottle Cafe", "-6.25", "Coffee"),
        ("2026-02-10", "Unknown Shop", "-10.00", "Uncategorized"),
    ]
    expected = {
        "transactions": [
            {"date": d, "description": desc, "amount": amt, "category": cat} for d, desc, amt, cat in rows
        ]
    }
    assert res.out == json.dumps(expected, indent=2, ensure_ascii=False) + "\n"
    assert list(json.loads(res.out)["transactions"][0]) == ["date", "description", "amount", "category"]


def test_categorize_empty_json_and_table(run, write):
    """JSON empty, categorize table: header-only input gives {"transactions": []} / header+dashes."""
    tx = write("tx.csv", TX_HEADER)
    res = run("categorize", "--format", "json", tx)
    assert_ok(res)
    assert res.out == '{\n  "transactions": []\n}\n'
    res = run("categorize", tx)
    assert_ok(res)
    assert res.out == (
        "DATE  AMOUNT  CATEGORY  DESCRIPTION\n"
        "----  ------  --------  -----------\n"
    )


def _o10_files(write):
    a = write(
        "a.csv",
        TX_HEADER + "2026-02-01,Feb A,-1\n2026-01-10,Same A1,-2\n2025-12-31,Dec A,3\n2026-01-10,Same A2,-7\n",
    )
    b = write(
        "b.csv",
        TX_HEADER + "2026-01-10,Same B1,-4\n2025-12-15,Dec B,-5\n2026-01-10,Same B2,-6\n",
    )
    return a, b


def test_o10_categorize_order_ties_keep_input_order(run, write):
    """O10, R7: date ascending across files; equal dates keep argument then file order."""
    a, b = _o10_files(write)
    res = run("categorize", "--format", "json", a, b)
    assert_ok(res)
    descs = [t["description"] for t in json.loads(res.out)["transactions"]]
    assert descs == ["Dec B", "Dec A", "Same A1", "Same A2", "Same B1", "Same B2", "Feb A"]
    res = run("categorize", "--format", "json", b, a)
    assert_ok(res)
    descs = [t["description"] for t in json.loads(res.out)["transactions"]]
    assert descs == ["Dec B", "Dec A", "Same B1", "Same B2", "Same A1", "Same A2", "Feb A"]


def test_o10_report_months_ascending(run, write):
    """O10, R6: report months ascending regardless of file/argument order."""
    a, b = _o10_files(write)
    res = run("report", "--format", "json", b, a)
    assert_ok(res)
    months = [(m["month"], m["count"]) for m in json.loads(res.out)["months"]]
    assert months == [("2025-12", 2), ("2026-01", 4), ("2026-02", 1)]


def test_categorize_amount_never_negative_zero(run, write):
    """R10, categorize AMOUNT: per-transaction money rounds HALF_UP once; -0.001 shows 0.00."""
    tx = write("tx.csv", TX_HEADER + "2026-07-01,neg tiny,-0.001\n2026-07-02,half,-0.005\n2026-07-03,big,7\n")
    res = run("categorize", "--format", "json", tx)
    assert_ok(res)
    amounts = [t["amount"] for t in json.loads(res.out)["transactions"]]
    assert amounts == ["0.00", "-0.01", "7.00"]


def test_description_stripped_and_may_be_empty(run, write):
    """Transaction CSV (description stripped, may be empty), categorize table right-strip."""
    tx = write("tx.csv", TX_HEADER + "2026-08-01,   ,-1\n2026-08-02,  padded  ,-2\n")
    res = run("categorize", tx)
    assert_ok(res)
    assert res.out == (
        "DATE        AMOUNT  CATEGORY       DESCRIPTION\n"
        "----------  ------  -------------  -----------\n"
        "2026-08-01   -1.00  Uncategorized\n"
        "2026-08-02   -2.00  Uncategorized  padded\n"
    )
