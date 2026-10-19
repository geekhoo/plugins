import json
import re

from conftest import ADMIN_KEY, T0, compact, expect_error, expect_link, free_port, iso


def stderr_error_code(result):
    for line in reversed(result.stderr.strip().splitlines()):
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("error"), dict):
            return obj["error"].get("code")
    raise AssertionError(f"no error JSON on stderr: {result.stderr!r}")


def test_shorten_prints_link_json(server, cli):
    """AC12, R16: shorten prints the compact link JSON plus newline and exits 0."""
    tok = server.new_token()
    r = cli("shorten", "http://a.com/cli", "--slug", "cli001", "--expires-in", "120",
            "--server", server.base, "--token", tok)
    assert r.returncode == 0, r.stderr
    assert r.stdout.endswith("\n") and r.stdout.count("\n") == 1
    obj = json.loads(r.stdout)
    assert r.stdout == compact(obj) + "\n"
    assert list(obj) == ["slug", "url", "short_url", "created_at", "expires_at", "clicks",
                         "last_clicked_at"]
    assert obj["slug"] == "cli001"
    assert obj["expires_at"] == iso(T0 + 120)
    assert obj == expect_link(server.request("GET", "/v1/links/cli001", token=tok))


def test_shorten_conflict_exits_1(server, cli):
    """AC12, R16: a 409 makes shorten exit 1 with empty stdout and error JSON on stderr."""
    tok = server.new_token()
    expect_link(server.create(tok, slug="taken1"), 201)
    r = cli("shorten", "http://a.com/x", "--slug", "taken1", "--server", server.base, "--token", tok)
    assert r.returncode == 1
    assert r.stdout == ""
    assert stderr_error_code(r) == "slug_taken"


def test_unreachable_server_exits_3(cli):
    """AC12, Client exit codes: connection failure exits 3 with a stderr message."""
    r = cli("shorten", "http://a.com/x", "--server", f"http://127.0.0.1:{free_port()}",
            "--token", "lv_" + "0" * 32)
    assert r.returncode == 3
    assert r.stdout == ""
    assert r.stderr.strip() != ""


def test_missing_token_exits_2(server, cli):
    """AC12, Client CLI: no --token and no LINKVAULT_TOKEN exits 2."""
    r = cli("shorten", "http://a.com/x", "--server", server.base)
    assert r.returncode == 2
    assert r.stdout == ""
    assert r.stderr.strip() != ""


def test_missing_server_exits_2(cli):
    """Client exit codes: no --server and no LINKVAULT_SERVER exits 2."""
    r = cli("list", "--token", "lv_" + "0" * 32)
    assert r.returncode == 2
    assert r.stdout == ""


def test_unknown_command_exits_2(cli):
    """Client exit codes: a usage error exits 2."""
    assert cli("frobnicate").returncode == 2


def test_token_create(server, cli):
    """R16, Client CLI: token create prints the E2 JSON and exits 0; the token then works."""
    r = cli("token", "create", "--admin-key", ADMIN_KEY, "--server", server.base)
    assert r.returncode == 0, r.stderr
    obj = json.loads(r.stdout)
    assert r.stdout == compact(obj) + "\n"
    assert list(obj) == ["token", "created_at"]
    assert re.fullmatch(r"lv_[0-9a-f]{32}", obj["token"])
    assert server.request("GET", "/v1/links", token=obj["token"]).status == 200


def test_token_create_bad_key_exits_1(server, cli):
    """R16, Client exit codes: a 401 from E2 exits 1 with error JSON on stderr."""
    r = cli("token", "create", "--admin-key", "wrong", "--server", server.base)
    assert r.returncode == 1
    assert r.stdout == ""
    assert stderr_error_code(r) == "unauthorized"


def test_list_uses_environment(server, cli):
    """Client CLI: LINKVAULT_SERVER and LINKVAULT_TOKEN are used when options are absent."""
    tok = server.new_token()
    expect_link(server.create(tok, slug="envl01"), 201)
    r = cli("list", LINKVAULT_SERVER=server.base, LINKVAULT_TOKEN=tok)
    assert r.returncode == 0, r.stderr
    obj = json.loads(r.stdout)
    assert r.stdout == compact(obj) + "\n"
    assert [link["slug"] for link in obj["links"]] == ["envl01"]


def test_stats_prints_link(server, cli):
    """R16, Client CLI: stats prints the E5 link JSON."""
    tok = server.new_token()
    link = expect_link(server.create(tok, slug="stat01"), 201)
    r = cli("stats", "stat01", "--server", server.base, "--token", tok)
    assert r.returncode == 0, r.stderr
    assert r.stdout == compact(link) + "\n"


def test_delete_and_stats_missing(server, cli):
    """Oracle example 12, R16: delete exits 0 with empty stdout; stats missing exits 1 with not_found on stderr."""
    tok = server.new_token()
    expect_link(server.create(tok, slug="del001"), 201)
    r = cli("delete", "del001", "--server", server.base, "--token", tok)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
    expect_error(server.request("GET", "/v1/links/del001", token=tok), 404, "not_found")
    r = cli("stats", "missing", "--server", server.base, "--token", tok)
    assert r.returncode == 1
    assert r.stdout == ""
    assert stderr_error_code(r) == "not_found"
