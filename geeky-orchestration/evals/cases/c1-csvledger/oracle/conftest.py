"""Shared fixtures for the c1-csvledger hidden oracle.

The implementation under test is located by the ORACLE_TARGET environment
variable (the contestant repo root). Every test runs the CLI as a subprocess:
``python -m csvledger ...`` with cwd=ORACLE_TARGET.
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

TIMEOUT = 30

O1_RULES = (
    "category,type,pattern,priority\n"
    "Groceries,contains,market,10\n"
    "Coffee,regex,^(starbucks|blue bottle),10\n"
    "Dining,contains,cafe,5\n"
    "Salary,contains,payroll,0\n"
)

O1_TX = (
    "date,description,amount\n"
    "2026-01-03,Corner Market,-45.10\n"
    "2026-01-05,STARBUCKS #12,-4.50\n"
    "2026-01-15,ACME PAYROLL,2500.00\n"
    "2026-01-20,Corner Market,-12.005\n"
    "2026-02-02,Blue Bottle Cafe,-6.25\n"
    "2026-02-10,Unknown Shop,-10\n"
)

O1_REPORT = (
    "MONTH    CATEGORY       COUNT   INCOME  EXPENSES      NET\n"
    "-------  -------------  -----  -------  --------  -------\n"
    "2026-01  Coffee             1     0.00     -4.50    -4.50\n"
    "2026-01  Groceries          2     0.00    -57.11   -57.11\n"
    "2026-01  Salary             1  2500.00      0.00  2500.00\n"
    "2026-02  Coffee             1     0.00     -6.25    -6.25\n"
    "2026-02  Uncategorized      1     0.00    -10.00   -10.00\n"
)

TX_HEADER = "date,description,amount\n"
RULES_HEADER = "category,type,pattern,priority\n"


@dataclass
class Result:
    code: int
    raw_out: bytes
    raw_err: bytes

    @property
    def out(self) -> str:
        return self.raw_out.decode("utf-8")

    @property
    def err(self) -> str:
        return self.raw_err.decode("utf-8", errors="replace")

    @property
    def err_lines(self) -> list:
        return self.err.splitlines()


@pytest.fixture(scope="session")
def target() -> Path:
    raw = os.environ.get("ORACLE_TARGET")
    if not raw:
        pytest.fail("ORACLE_TARGET is not set; point it at the contestant repo root")
    root = Path(raw)
    if not root.is_dir():
        pytest.fail(f"ORACLE_TARGET={raw!r} does not exist or is not a directory")
    if not (root / "csvledger").is_dir():
        pytest.fail(f"ORACLE_TARGET={raw!r} has no csvledger/ package at its root")
    return root


@pytest.fixture
def run(target):
    """Run ``python -m csvledger *args`` in the target repo; return a Result.

    ``cwd=`` runs from another directory with PYTHONPATH=target instead
    (only used by the relative-path test).
    """

    base_env = dict(os.environ)
    base_env["PYTHONDONTWRITEBYTECODE"] = "1"

    def _run(*args, stdin_bytes=None, cwd=None) -> Result:
        env = dict(base_env)
        if cwd is not None:
            env["PYTHONPATH"] = os.pathsep.join(p for p in (str(target), base_env.get("PYTHONPATH")) if p)
        kwargs = {}
        if stdin_bytes is None:
            kwargs["stdin"] = subprocess.DEVNULL
        else:
            kwargs["input"] = stdin_bytes
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "csvledger", *[str(a) for a in args]],
                cwd=target if cwd is None else cwd,
                capture_output=True,
                timeout=TIMEOUT,
                env=env,
                **kwargs,
            )
        except subprocess.TimeoutExpired:
            pytest.fail(f"csvledger {' '.join(map(str, args))} timed out after {TIMEOUT}s")
        return Result(proc.returncode, proc.stdout, proc.stderr)

    return _run


@pytest.fixture
def write(tmp_path):
    """Write exact content (str encoded UTF-8 without newline translation, or bytes)."""

    def _write(name: str, content) -> Path:
        path = tmp_path / name
        if isinstance(content, str):
            content = content.encode("utf-8")
        path.write_bytes(content)
        return path

    return _write


@pytest.fixture
def o1(write):
    """(rules_path, tx_path) for oracle case O1."""
    return write("rules.csv", O1_RULES), write("tx.csv", O1_TX)


def assert_error(res: Result, code: int, message: str) -> None:
    """Exact single-line error contract: exit code, empty stdout, one stderr line."""
    assert "Traceback" not in res.err, res.err
    assert res.code == code, (res.code, res.err)
    assert res.raw_out == b"", res.raw_out
    assert res.err_lines == [f"csvledger: error: {message}"], res.err_lines


def assert_usage(res: Result) -> None:
    """Usage error contract: exit 2, empty stdout, last stderr line matches the contract regex."""
    assert "Traceback" not in res.err, res.err
    assert res.code == 2, (res.code, res.err)
    assert res.raw_out == b"", res.raw_out
    assert res.err_lines, "expected an argparse usage message on stderr"
    assert re.match(r"^csvledger( report| categorize)?: error: ", res.err_lines[-1]), res.err_lines


def assert_ok(res: Result) -> None:
    assert "Traceback" not in res.err, res.err
    assert res.code == 0, (res.code, res.err)
