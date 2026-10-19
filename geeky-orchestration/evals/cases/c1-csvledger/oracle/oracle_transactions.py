"""Transaction CSV parsing and validation (exit 3)."""

import json

import pytest

from conftest import O1_REPORT, O1_RULES, O1_TX, TX_HEADER, assert_error, assert_ok


@pytest.mark.parametrize("bad", ["2026-02-30", "2026-2-01", "20260201"])
def test_o3_bad_date(run, write, bad):
    """AC7, O3, R2: invalid date on line 3 -> exit 3, exact stderr line, empty stdout."""
    tx = write("tx.csv", TX_HEADER + "2026-02-01,Y,-1\n" + f"{bad},X,-1\n")
    assert_error(run("report", tx), 3, f"{tx}:3: invalid date '{bad}'")


@pytest.mark.parametrize("bad", ["2026-13-01", "2026-04-31", "2025-02-29", "2026-01-01T00", "x"])
def test_more_bad_dates(run, write, bad):
    """Transaction CSV (date regex + calendar validity), R2: exit 3."""
    tx = write("tx.csv", TX_HEADER + f"{bad},X,-1\n")
    assert_error(run("categorize", tx), 3, f"{tx}:2: invalid date '{bad}'")


def test_leap_day_and_padded_date_valid(run, write):
    """Transaction CSV (date stripped, valid calendar date): 2024-02-29 with padding is accepted."""
    tx = write("tx.csv", TX_HEADER + "  2024-02-29  ,leap,-1\n")
    res = run("categorize", "--format", "json", tx)
    assert_ok(res)
    assert json.loads(res.out)["transactions"][0]["date"] == "2024-02-29"


@pytest.mark.parametrize("raw, shown", [("+5", "+5"), ('"1,000"', "1,000"), (".5", ".5"), ("5.", "5."), ("$5", "$5"), ("1e3", "1e3"), ("", ""), ("-", "-"), ("1.2.3", "1.2.3")])
def test_o9_bad_amount(run, write, raw, shown):
    """O9, R2, Error handling (bad amount): amount grammar ^-?\\d+(\\.\\d+)?$ -> exit 3."""
    tx = write("tx.csv", TX_HEADER + f"2026-01-01,X,{raw}\n")
    assert_error(run("report", tx), 3, f"{tx}:2: invalid amount '{shown}'")


def test_amount_value_is_stripped(run, write):
    """Transaction CSV (amount stripped), Error handling (<value> is stripped)."""
    ok = write("ok.csv", TX_HEADER + "2026-01-01,X,  -4.50  \n")
    res = run("categorize", "--format", "json", ok)
    assert_ok(res)
    assert json.loads(res.out)["transactions"][0]["amount"] == "-4.50"
    bad = write("bad.csv", TX_HEADER + "2026-01-01,X,  1e3  \n")
    assert_error(run("report", bad), 3, f"{bad}:2: invalid amount '1e3'")


def test_date_checked_before_amount(run, write):
    """Error handling (row check order: field count, date, amount)."""
    tx = write("tx.csv", TX_HEADER + "2026-02-30,X,abc\n")
    assert_error(run("report", tx), 3, f"{tx}:2: invalid date '2026-02-30'")


@pytest.mark.parametrize("row, got", [("2026-01-01,X", 2), ("2026-01-01,X,-1,extra", 4), ("2026-99-99", 1)])
def test_field_count_mismatch(run, write, row, got):
    """Error handling (field count mismatch, checked first), R2: exit 3."""
    tx = write("tx.csv", TX_HEADER + row + "\n")
    assert_error(run("report", tx), 3, f"{tx}:2: expected 3 fields, got {got}")


def test_blank_lines_skipped_but_counted_in_line_num(run, write):
    """Transaction CSV (zero-field rows skipped), Error handling (<line> = csv line_num)."""
    tx = write("tx.csv", TX_HEADER + "\n2026-01-01,A,-1\n\n\n2026-01-02,B,zz\n")
    assert_error(run("report", tx), 3, f"{tx}:6: invalid amount 'zz'")


def test_line_num_after_multiline_record(run, write):
    """Error handling (<line> is csv.reader.line_num after reading the record)."""
    tx = write("tx.csv", TX_HEADER + '2026-01-01,"two\nlines",bad\n')
    assert_error(run("report", tx), 3, f"{tx}:3: invalid amount 'bad'")


def test_header_case_order_and_extra_columns(run, write):
    """Transaction CSV (header stripped+lowercased, any order, extras ignored)."""
    tx = write(
        "tx.csv",
        " Amount ,Memo, DATE ,Description\n-45.10,m,2026-01-03,Corner Market\n2500,n,2026-01-15,ACME PAYROLL\n",
    )
    rules = write("rules.csv", O1_RULES)
    res = run("categorize", "--rules", rules, "--format", "json", tx)
    assert_ok(res)
    got = [(t["date"], t["description"], t["amount"], t["category"]) for t in json.loads(res.out)["transactions"]]
    assert got == [
        ("2026-01-03", "Corner Market", "-45.10", "Groceries"),
        ("2026-01-15", "ACME PAYROLL", "2500.00", "Salary"),
    ]


def test_bom_and_crlf_input(run, write):
    """Transaction CSV (utf-8-sig BOM, newline=''), R11: BOM+CRLF input gives the O1 bytes."""
    rules = write("rules.csv", b"\xef\xbb\xbf" + O1_RULES.replace("\n", "\r\n").encode())
    tx = write("tx.csv", b"\xef\xbb\xbf" + O1_TX.replace("\n", "\r\n").encode())
    res = run("report", "--rules", rules, tx)
    assert_ok(res)
    assert res.out == O1_REPORT


@pytest.mark.parametrize(
    "header, name",
    [("description,amount", "date"), ("date,amount", "description"), ("date,description", "amount"), ("amount,foo", "date")],
)
def test_missing_column(run, write, header, name):
    """Error handling (required column absent, first in listed order), R2: exit 3."""
    tx = write("tx.csv", header + "\n")
    assert_error(run("report", tx), 3, f"{tx}: missing column '{name}'")


def test_duplicate_column(run, write):
    """Transaction CSV (duplicate header names are an error), R2: exit 3."""
    tx = write("tx.csv", "date,description,amount,amount\n")
    assert_error(run("report", tx), 3, f"{tx}: duplicate column 'amount'")


def test_missing_header_zero_bytes(run, write):
    """Transaction CSV (0-byte file has no header), R2: exit 3."""
    tx = write("tx.csv", b"")
    assert_error(run("report", tx), 3, f"{tx}: missing header")


def test_not_utf8(run, write):
    """Transaction CSV (UTF-8), Error handling (not valid UTF-8): exit 3."""
    tx = write("tx.csv", TX_HEADER.encode() + b"2026-01-01,caf\xe9,-1\n")
    assert_error(run("report", tx), 3, f"{tx}: not valid UTF-8")


def test_missing_file(run, tmp_path):
    """Error handling (file missing), R2: exit 3, path as given."""
    missing = tmp_path / "absent.csv"
    assert_error(run("report", missing), 3, f"{missing}: cannot read file")


def test_first_file_error_wins(run, write):
    """Interface (transaction files in argument order; first error wins)."""
    good = write("good.csv", TX_HEADER + "2026-01-01,A,-1\n")
    bad1 = write("bad1.csv", TX_HEADER + "2026-01-01,A,nope\n")
    bad2 = write("bad2.csv", "date,amount\n")
    assert_error(run("report", good, bad1, bad2), 3, f"{bad1}:2: invalid amount 'nope'")
    assert_error(run("report", good, bad2, bad1), 3, f"{bad2}: missing column 'description'")


@pytest.mark.parametrize(
    "header, message",
    [
        ("date,date", "duplicate column 'date'"),
        ("Amount,x, AMOUNT ,x", "duplicate column 'amount'"),
        ("note,memo,MEMO,note,date,description,amount", "duplicate column 'memo'"),
        ("x,X,amount", "duplicate column 'x'"),
        ("amount", "missing column 'date'"),
        ("description,memo", "missing column 'date'"),
    ],
)
def test_header_check_order(run, write, header, message):
    """Error handling (header check order: duplicate before missing; first duplicate in header order)."""
    tx = write("tx.csv", header + "\n")
    assert_error(run("report", tx), 3, f"{tx}: {message}")


def test_relative_path_reported_as_given(run, tmp_path):
    """Error handling (<path> is exactly the argv string; relative stays relative), R2, R3."""
    data = tmp_path / "data"
    data.mkdir()
    (data / "tx.csv").write_bytes((TX_HEADER + "2026-02-01,Y,-1\n2026-02-30,X,-1\n").encode())
    (data / "rules.csv").write_bytes(b"category,type,pattern,priority\nX,glob,a,1\n")
    assert_error(run("report", "data/tx.csv", cwd=tmp_path), 3, "data/tx.csv:3: invalid date '2026-02-30'")
    assert_error(
        run("report", "--rules", "data/rules.csv", "data/tx.csv", cwd=tmp_path),
        4,
        "data/rules.csv:2: invalid type 'glob'",
    )
    assert_error(run("categorize", "data/none.csv", cwd=tmp_path), 3, "data/none.csv: cannot read file")
