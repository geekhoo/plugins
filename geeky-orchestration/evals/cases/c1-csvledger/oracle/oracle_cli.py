"""CLI surface and usage errors (exit 2)."""

import pytest

from conftest import O1_TX, TX_HEADER, assert_error, assert_ok, assert_usage


def test_help_lists_subcommands(run):
    """AC1, R1: --help exits 0 and mentions both subcommands."""
    res = run("--help")
    assert_ok(res)
    assert "report" in res.out
    assert "categorize" in res.out


@pytest.mark.parametrize("month", ["2026-13", "2026-00", "2026-1", "26-01", "2026/01", "2026-01-01"])
def test_bad_month_is_usage_error(run, write, month):
    """R8, Interface (--month regex), Exit codes 2: malformed --month is a usage error."""
    tx = write("tx.csv", O1_TX)
    assert_usage(run("report", "--month", month, tx))


def test_bad_format_is_usage_error(run, write):
    """R9, Exit codes 2: --format outside table|json is a usage error."""
    tx = write("tx.csv", O1_TX)
    assert_usage(run("report", "--format", "xml", tx))


@pytest.mark.parametrize("command", ["report", "categorize"])
def test_missing_file_argument_is_usage_error(run, command):
    """R1, Exit codes 2: FILE is required for both commands."""
    assert_usage(run(command))


def test_unknown_flag_is_usage_error(run, write):
    """Exit codes 2: unknown flag is an argparse usage error."""
    tx = write("tx.csv", O1_TX)
    assert_usage(run("report", "--bogus", tx))


def test_dash_is_a_file_name_not_stdin(run):
    """Interface (FILE): '-' is an ordinary file name; stdin is never read."""
    res = run("report", "-", stdin_bytes=(TX_HEADER + "2026-01-01,x,-1\n").encode())
    assert_error(res, 3, "-: cannot read file")


def test_no_rules_means_uncategorized(run, write):
    """Interface (--rules optional), R4: without --rules everything is Uncategorized."""
    tx = write("tx.csv", O1_TX)
    res = run("report", tx)
    assert_ok(res)
    assert res.out == (
        "MONTH    CATEGORY       COUNT   INCOME  EXPENSES      NET\n"
        "-------  -------------  -----  -------  --------  -------\n"
        "2026-01  Uncategorized      4  2500.00    -61.61  2438.40\n"
        "2026-02  Uncategorized      2     0.00    -16.25   -16.25\n"
    )
