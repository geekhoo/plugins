"""Hidden oracle harness for c2-linkvault.

Set ORACLE_TARGET to the contestant repo root, then run `python -m pytest` from
this directory. Std lib + pytest only. Every wait is bounded; nothing is skipped.
"""
import calendar
import http.client
import json
import os
import queue
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ADMIN_KEY = "oracle-admin-key"
FAKE_ISO = "2030-01-01T00:00:00Z"
T0 = 1893456000  # FAKE_ISO as Unix seconds; a 60-second window start
READY_TIMEOUT = 10
HTTP_TIMEOUT = 10
CLI_TIMEOUT = 30
LINK_KEYS = ["slug", "url", "short_url", "created_at", "expires_at", "clicks", "last_clicked_at"]
IS_WINDOWS = os.name == "nt"


def iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def parse_iso(text):
    return calendar.timegm(time.strptime(text, "%Y-%m-%dT%H:%M:%SZ"))


def compact(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)


def clean_env(**extra):
    env = dict(os.environ)
    for key in ("LINKVAULT_SERVER", "LINKVAULT_TOKEN", "PYTHONSAFEPATH"):
        env.pop(key, None)
    env.update(extra)
    return env


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Resp:
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = headers
        self.body = body

    def header(self, name):
        return self.headers.get(name)

    def json(self):
        try:
            return json.loads(self.body.decode("utf-8"))
        except ValueError:
            pytest.fail(f"response body is not JSON (status {self.status}): {self.body[:300]!r}")

    def __repr__(self):
        return f"<Resp {self.status} {self.body[:200]!r}>"


def expect_json(resp, status):
    """Status, Content-Type, Content-Length and exact compact encoding; returns the parsed body."""
    assert resp.status == status, resp
    assert resp.header("Content-Type") == "application/json", resp.header("Content-Type")
    assert resp.header("Content-Length") == str(len(resp.body))
    obj = resp.json()
    assert resp.body == compact(obj).encode("ascii"), "body is not compact json.dumps output"
    return obj


def expect_error(resp, status, code):
    obj = expect_json(resp, status)
    assert list(obj) == ["error"], obj
    assert list(obj["error"]) == ["code", "message"], obj
    assert obj["error"]["code"] == code, obj
    assert isinstance(obj["error"]["message"], str)
    return obj


def expect_link(resp, status=200):
    obj = expect_json(resp, status)
    assert list(obj) == LINK_KEYS, list(obj)
    return obj


class Server:
    _count = 0

    def __init__(self, target, workdir, db=None, port=0, admin_key=ADMIN_KEY,
                 rate_limit=10000, fake_clock=FAKE_ISO):
        Server._count += 1
        self.db = Path(db) if db else Path(workdir) / "lv.db"
        self.admin_key = admin_key
        args = [sys.executable, "-m", "linkvault", "serve", "--port", str(port),
                "--db", str(self.db), "--admin-key", admin_key]
        if rate_limit is not None:
            args += ["--rate-limit", str(rate_limit)]
        if fake_clock is not None:
            args += ["--fake-clock", fake_clock]
        self.stderr_path = Path(workdir) / f"server-{Server._count}.stderr"
        self._stderr = open(self.stderr_path, "wb")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0
        self.proc = subprocess.Popen(args, cwd=target, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=self._stderr,
                                     env=clean_env(), creationflags=flags)
        self._lines = queue.Queue()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()
        try:
            first = self._lines.get(timeout=READY_TIMEOUT)
        except queue.Empty:
            self._kill()
            pytest.fail(f"no ready line within {READY_TIMEOUT}s; stderr:\n{self.stderr_text()}")
        if first is None:
            self._kill()
            pytest.fail(f"server exited (code {self.proc.returncode}) before the ready line; "
                        f"stderr:\n{self.stderr_text()}")
        self.ready_line = first
        m = re.fullmatch(rb"LISTENING http://127\.0\.0\.1:(\d+)\r?\n", first)
        if not m:
            self._kill()
            pytest.fail(f"bad ready line {first!r}")
        self.port = int(m.group(1))
        self.base = f"http://127.0.0.1:{self.port}"
        self.extra_stdout = b""

    def _read_stdout(self):
        for line in iter(self.proc.stdout.readline, b""):
            self._lines.put(line)
        self._lines.put(None)

    def _kill(self):
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(10)
        self._stderr.close()

    def stderr_text(self):
        if not self._stderr.closed:
            self._stderr.flush()
        return self.stderr_path.read_bytes().decode("utf-8", "replace")[-3000:]

    def stop(self):
        """Signal a clean shutdown; returns (exit code, seconds taken). Kills as a last resort."""
        start = time.monotonic()
        if self.proc.poll() is None:
            self.proc.send_signal(signal.CTRL_BREAK_EVENT if IS_WINDOWS else signal.SIGINT)
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(10)
        elapsed = time.monotonic() - start
        self._stderr.close()
        self._reader.join(5)
        rest = []
        while True:
            try:
                item = self._lines.get_nowait()
            except queue.Empty:
                break
            if item is not None:
                rest.append(item)
        self.extra_stdout = b"".join(rest)
        return self.proc.returncode, elapsed

    # HTTP -----------------------------------------------------------------
    def request(self, method, path, body=None, token=None, admin=None, headers=None):
        hdrs = dict(headers or {})
        if token is not None:
            hdrs["Authorization"] = f"Bearer {token}"
        if admin is not None:
            hdrs["X-Admin-Key"] = admin
        if body is not None and not isinstance(body, bytes):
            body = json.dumps(body).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=HTTP_TIMEOUT)
        try:
            conn.request(method, path, body=body, headers=hdrs)
            resp = conn.getresponse()
            data = resp.read()
            return Resp(resp.status, resp.headers, data)
        finally:
            conn.close()

    def new_token(self):
        obj = expect_json(self.request("POST", "/v1/tokens", admin=self.admin_key), 201)
        return obj["token"]

    def create(self, token, url="https://example.com/x", slug=None, expires_in=None):
        body = {"url": url}
        if slug is not None:
            body["slug"] = slug
        if expires_in is not None:
            body["expires_in"] = expires_in
        return self.request("POST", "/v1/links", body=body, token=token)

    def set_clock(self, ts):
        obj = expect_json(self.request("POST", "/v1/admin/clock", body={"now": iso(ts)},
                                       admin=self.admin_key), 200)
        assert obj == {"now": iso(ts)}


@pytest.fixture(scope="session")
def target():
    raw = os.environ.get("ORACLE_TARGET")
    if not raw:
        pytest.fail("ORACLE_TARGET is not set; point it at the contestant repo root")
    path = Path(raw).resolve()
    if not path.is_dir():
        pytest.fail(f"ORACLE_TARGET {path} is not a directory")
    if not (path / "linkvault" / "__main__.py").is_file():
        pytest.fail(f"ORACLE_TARGET {path} has no linkvault/__main__.py")
    return path


@pytest.fixture
def start_server(target, tmp_path):
    started = []

    def start(**kwargs):
        srv = Server(target, tmp_path, **kwargs)
        started.append(srv)
        return srv

    yield start
    for srv in started:
        if srv.proc.poll() is None:
            srv.stop()


@pytest.fixture
def server(start_server):
    return start_server()


@pytest.fixture
def cli(target):
    def run(*args, **env):
        try:
            return subprocess.run([sys.executable, "-m", "linkvault", *args], cwd=target,
                                  stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                  env=clean_env(**env), timeout=CLI_TIMEOUT)
        except subprocess.TimeoutExpired:
            pytest.fail(f"CLI {args!r} did not exit within {CLI_TIMEOUT}s")

    return run
