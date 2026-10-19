import socket
import subprocess
import sys

import pytest

from conftest import ADMIN_KEY, CLI_TIMEOUT, IS_WINDOWS, clean_env, expect_error, expect_json


def run_serve(target, *args):
    try:
        return subprocess.run([sys.executable, "-m", "linkvault", "serve", *args], cwd=target,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              env=clean_env(), timeout=CLI_TIMEOUT)
    except subprocess.TimeoutExpired:
        pytest.fail("serve did not exit on a startup error")


def expect_ready_line(srv):
    """Ready line: first stdout bytes; exactly one trailing \\n or \\r\\n stripped."""
    line = srv.ready_line
    if line.endswith(b"\r\n"):
        line = line[:-2]
    elif line.endswith(b"\n"):
        line = line[:-1]
    else:
        raise AssertionError(f"ready line has no terminator: {srv.ready_line!r}")
    assert line == f"LISTENING http://127.0.0.1:{srv.port}".encode()


def test_ready_line_terminator_and_nothing_before(start_server):
    """R1, R-a ready-line rule: first stdout bytes are the ready line plus one \\n or \\r\\n terminator."""
    srv = start_server()
    expect_ready_line(srv)
    code, _ = srv.stop()
    assert code == 0
    assert srv.extra_stdout == b""


def test_ready_line_healthz_and_clean_shutdown(start_server):
    """AC1, R1, R15, E1: exact ready line, /healthz 200, signal exits 0 within 5 s, nothing else on stdout."""
    srv = start_server()
    assert srv.port != 0
    expect_ready_line(srv)
    assert expect_json(srv.request("GET", "/healthz"), 200) == {"status": "ok"}
    code, elapsed = srv.stop()
    assert code == 0, srv.stderr_text()
    assert elapsed < 5
    assert srv.extra_stdout == b""


def test_shutdown_with_traffic_exits_zero(start_server):
    """AC1, R15: shutdown after real API traffic still exits 0 within 5 s with no extra stdout."""
    srv = start_server()
    tok = srv.new_token()
    expect_json(srv.create(tok, slug="bye123"), 201)
    srv.request("GET", "/bye123")
    code, elapsed = srv.stop()
    assert code == 0, srv.stderr_text()
    assert elapsed < 5
    assert srv.extra_stdout == b""


def test_healthz_ignores_query_string(server):
    """E1, Conventions: query strings are ignored on every route."""
    assert expect_json(server.request("GET", "/healthz?x=1"), 200) == {"status": "ok"}


def test_missing_db_flag_is_usage_error(target):
    """Server CLI: --db is required; argparse usage error exits 2."""
    assert run_serve(target, "--admin-key", ADMIN_KEY, "--port", "0").returncode == 2


def test_rate_limit_zero_is_usage_error(target, tmp_path):
    """Server CLI: --rate-limit must be an integer >= 1; usage error exits 2."""
    r = run_serve(target, "--db", str(tmp_path / "x.db"), "--admin-key", ADMIN_KEY,
                  "--port", "0", "--rate-limit", "0")
    assert r.returncode == 2
    assert r.stdout == ""


def test_db_parent_missing_exits_3(target, tmp_path):
    """Server CLI: DB that cannot be opened (missing parent dir) exits 3 with a stderr message."""
    r = run_serve(target, "--db", str(tmp_path / "nope" / "x.db"), "--admin-key", ADMIN_KEY,
                  "--port", "0")
    assert r.returncode == 3
    assert r.stdout == ""
    assert r.stderr.strip() != ""


def test_port_in_use_exits_3(target, tmp_path):
    """Server CLI: a port that cannot be bound exits 3 with a stderr message and no ready line."""
    blocker = socket.socket()
    if IS_WINDOWS:
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    try:
        port = blocker.getsockname()[1]
        r = run_serve(target, "--db", str(tmp_path / "x.db"), "--admin-key", ADMIN_KEY,
                      "--port", str(port))
    finally:
        blocker.close()
    assert r.returncode == 3
    assert "LISTENING" not in r.stdout
    assert r.stderr.strip() != ""


def test_unhandled_route_error_shape(server):
    """Error handling: every error body is {"error":{"code","message"}} with JSON headers."""
    expect_error(server.request("GET", "/v1/nothing-here"), 404, "not_found")
