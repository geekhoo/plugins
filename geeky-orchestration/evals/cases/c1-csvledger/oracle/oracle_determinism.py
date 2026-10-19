"""Determinism: identical bytes across runs, LF only (R11)."""

import pytest

from conftest import O1_RULES, TX_HEADER, assert_ok


@pytest.mark.parametrize(
    "args",
    [
        ("report",),
        ("report", "--format", "json"),
        ("categorize",),
        ("categorize", "--format", "json"),
    ],
    ids=["report-table", "report-json", "categorize-table", "categorize-json"],
)
def test_twice_identical_and_no_cr(run, write, args):
    """AC10, R11: two runs give identical stdout/stderr bytes; stdout has no \\r; ends with \\n."""
    rules = write("rules.csv", O1_RULES)
    a = write("a.csv", TX_HEADER + "2026-01-05,STARBUCKS #12,-4.50\n2026-01-03,Corner Market,-45.10\n")
    b = write("b.csv", TX_HEADER + "2026-01-05,STARBUCKS #12,-4.5\n2026-02-02,Café Ünïcode,-6.25\n")
    first = run(*args, "--rules", rules, a, b)
    second = run(*args, "--rules", rules, a, b)
    assert_ok(first)
    assert first.raw_out == second.raw_out
    assert first.raw_err == second.raw_err
    assert b"\r" not in first.raw_out
    assert first.raw_out.endswith(b"\n")
    assert "Café Ünïcode".encode("utf-8") in first.raw_out or args[0] == "report"
