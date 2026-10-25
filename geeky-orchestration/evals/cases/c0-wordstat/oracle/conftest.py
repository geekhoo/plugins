"""Shared fixtures for the c0-wordstat hidden oracle.

The implementation under test is located by the ORACLE_TARGET environment
variable (the contestant repo root). Every test runs the CLI as a subprocess:
``python -m wordstat ...`` with cwd=ORACLE_TARGET.
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

TIMEOUT = 30

SAMPLE = "The cat sat.\nThe cat ran!\nA dog.\n"
SAMPLE_TEXT = "lines: 3\nwords: 8\nchars: 33\ntop: cat=2 the=2 a=1\n"
SAMPLE_JSON_TOP2 = ('{"lines": 3, "words": 8, "chars": 33, "top": [{"word": "cat", "count": 2}, '
                    '{"word": "the", "count": 2}]}\n')


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
    if not (root / "wordstat").is_dir():
        pytest.fail(f"ORACLE_TARGET={raw!r} has no wordstat/ package at its root")
    return root


@pytest.fixture
def run(target):
    """Run ``python -m wordstat *args`` in the target repo; return a Result."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    def _run(*args) -> Result:
        try:
            proc = subprocess.run([sys.executable, "-m", "wordstat", *[str(a) for a in args]], cwd=target,
                                  capture_output=True, timeout=TIMEOUT, env=env, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            pytest.fail(f"wordstat {' '.join(map(str, args))} timed out after {TIMEOUT}s")
        return Result(proc.returncode, proc.stdout, proc.stderr)

    return _run


@pytest.fixture
def write(tmp_path):
    """Write exact content (str encoded UTF-8 without newline translation, or bytes)."""

    def _write(name: str, content) -> Path:
        path = tmp_path / name
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        return path

    return _write


def assert_ok(res: Result) -> None:
    assert "Traceback" not in res.err, res.err
    assert res.code == 0, (res.code, res.err)


def assert_error(res: Result, message: str) -> None:
    """Exact single-line error contract: exit 3, empty stdout, one stderr line."""
    assert "Traceback" not in res.err, res.err
    assert res.code == 3, (res.code, res.err)
    assert res.raw_out == b"", res.raw_out
    assert res.err_lines == [f"wordstat: error: {message}"], res.err_lines


def assert_usage(res: Result) -> None:
    assert "Traceback" not in res.err, res.err
    assert res.code == 2, (res.code, res.err)
    assert res.raw_out == b"", res.raw_out
    assert res.err_lines and re.match(r"^wordstat: error: ", res.err_lines[-1]), res.err_lines
