"""Hidden oracle harness for the c3-minisql eval.

Set ORACLE_TARGET to the contestant repo root (the directory containing
``minisql/``). The contestant package is only ever run in subprocesses.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

TIMEOUT = 30

EMP = b"id,name,dept,salary\n1,Ann,eng,100\n2,Bob,eng,\n3,Cid,ops,80\n4,Dee,,80\n5,Eve,ops,120\n"
DEPT = b"code,title\neng,Engineering\nops,Operations\nops,Ops Dup\nhr,Human Resources\n"
FILES = b"fname\nreport_1.txt\nreport1.txt\n100%.txt\na\\b\n"
MIXED = b"a,b,c,d,e\n1,1.5,007,x, 1\n2,2,,1,2\n,3e2,-4,2,3\n"

STD_FILES = {"emp.csv": EMP, "dept.csv": DEPT, "files.csv": FILES, "mixed.csv": MIXED}


@pytest.fixture(scope="session")
def target():
    raw = os.environ.get("ORACLE_TARGET")
    if not raw:
        pytest.fail("ORACLE_TARGET is not set; point it at the contestant repo root", pytrace=False)
    root = Path(raw)
    if not root.is_dir():
        pytest.fail(f"ORACLE_TARGET does not exist or is not a directory: {raw}", pytrace=False)
    if not (root / "minisql" / "__init__.py").is_file():
        pytest.fail(f"ORACLE_TARGET has no minisql/__init__.py: {raw}", pytrace=False)
    return root.resolve()


def _write(directory, files):
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (directory / name).write_bytes(content)
    return directory


@pytest.fixture
def data(tmp_path):
    """Standard fixture directory: emp, dept, files, mixed."""
    return _write(tmp_path / "data", STD_FILES)


@pytest.fixture
def make_data(tmp_path):
    """Factory: make_data({"name.csv": b"..."}) -> directory path."""
    counter = iter(range(1000))

    def make(files):
        return _write(tmp_path / f"d{next(counter)}", files)

    return make


def _env(utf8):
    env = dict(os.environ)
    for key in ("PYTHONIOENCODING", "PYTHONUTF8", "PYTHONPATH", "PYTHONSTARTUP"):
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if utf8:
        env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_cli(target, args, stdin=None):
    proc = subprocess.run(
        [sys.executable, "-m", "minisql", *[str(a) for a in args]],
        cwd=target,
        input=None if stdin is None else stdin.encode("utf-8"),
        stdin=subprocess.DEVNULL if stdin is None else None,
        capture_output=True,
        timeout=TIMEOUT,
        env=_env(utf8=False),
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


@pytest.fixture
def cli(target):
    """cli(*args, stdin=None) -> (exit_code, stdout, stderr), exact UTF-8 text."""

    def call(*args, stdin=None):
        return run_cli(target, args, stdin)

    return call


@pytest.fixture
def sql(cli, data):
    """One-shot query against the standard fixture directory."""

    def call(query, *extra):
        return cli("--data", data, *extra, query)

    return call


LIB_PRELUDE = (
    "import sys\n"
    "sys.path.insert(0, {target!r})\n"
    "import minisql\n"
    "DATA = {data!r}\n"
)

LIB_EXEC = (
    "def run(q):\n"
    "    try:\n"
    "        r = minisql.connect(DATA).execute(q)\n"
    "        return ('ok', r.columns, r.types, r.rows)\n"
    "    except minisql.MiniSQLError as e:\n"
    "        return ('err', type(e).__name__, e.kind, e.line, e.column, e.message, str(e))\n"
)


@pytest.fixture
def lib(target):
    """lib(body, data_dir) runs Python in a subprocess with minisql importable
    and DATA bound; returns stripped stdout. ``run(q)`` is predefined."""

    def call(body, data_dir="."):
        code = LIB_PRELUDE.format(target=str(target), data=str(data_dir)) + LIB_EXEC + body
        proc = subprocess.run(
            [sys.executable, "-"],
            cwd=target,
            input=code.encode("utf-8"),
            capture_output=True,
            timeout=TIMEOUT,
            env=_env(utf8=True),
        )
        err = proc.stderr.decode("utf-8", "replace")
        assert proc.returncode == 0, f"library subprocess failed:\n{err}"
        return proc.stdout.decode("utf-8").strip()

    return call


@pytest.fixture
def query(lib, data):
    """query(q) -> repr of run(q) tuple via the library API on standard data."""

    def call(q, data_dir=None):
        return lib(f"print(repr(run({q!r})))", data if data_dir is None else data_dir)

    return call
