import time

import pytest

from conftest import FAKE_ISO, T0, expect_error, expect_json, iso, parse_iso


def test_admin_clock_sets_now(server):
    """E8, R12: 200 {"now":...}; later timestamps use the new instant; any valid timestamp (even earlier) accepted."""
    resp = server.request("POST", "/v1/admin/clock", body={"now": "2031-06-15T12:34:56Z"},
                          admin=server.admin_key)
    assert expect_json(resp, 200) == {"now": "2031-06-15T12:34:56Z"}
    obj = expect_json(server.request("POST", "/v1/tokens", admin=server.admin_key), 201)
    assert obj["created_at"] == "2031-06-15T12:34:56Z"
    server.set_clock(T0 - 86400)
    obj = expect_json(server.request("POST", "/v1/tokens", admin=server.admin_key), 201)
    assert obj["created_at"] == iso(T0 - 86400)


def test_fake_clock_is_frozen(server):
    """R12: with --fake-clock, now does not advance with real time."""
    time.sleep(1.2)
    obj = expect_json(server.request("POST", "/v1/tokens", admin=server.admin_key), 201)
    assert obj["created_at"] == FAKE_ISO


@pytest.mark.parametrize("key", ["wrong-key", None])
def test_admin_clock_bad_key(server, key):
    """E8: wrong or missing admin key returns 401 unauthorized."""
    resp = server.request("POST", "/v1/admin/clock", body={"now": FAKE_ISO}, admin=key)
    expect_error(resp, 401, "unauthorized")


@pytest.mark.parametrize("body", [
    {"now": "2030-01-01 00:00:00"}, {"now": "yesterday"}, {"now": "2030-13-45T00:00:00Z"},
    {"now": 1893456000}, {"now": None}, {"now": ["2030-01-01T00:00:00Z"]}, {},
    {"now": FAKE_ISO, "extra": 1}, {"time": FAKE_ISO},
])
def test_admin_clock_bad_now(server, body):
    """E8 body rules: missing key, extra key, wrong type or unparseable timestamp returns 400 invalid_request."""
    resp = server.request("POST", "/v1/admin/clock", body=body, admin=server.admin_key)
    expect_error(resp, 400, "invalid_request")


def test_admin_clock_invalid_json(server):
    """E8, Error handling: non-JSON body returns 400 invalid_json."""
    resp = server.request("POST", "/v1/admin/clock", body=b"{bad", admin=server.admin_key)
    expect_error(resp, 400, "invalid_json")


def test_admin_clock_absent_without_fake_clock(start_server):
    """E8, oracle example 11: without --fake-clock the route returns 404, even with the right key."""
    srv = start_server(fake_clock=None)
    resp = srv.request("POST", "/v1/admin/clock", body={"now": FAKE_ISO}, admin=srv.admin_key)
    expect_error(resp, 404, "not_found")


def test_real_clock_without_fake_clock(start_server):
    """R12: without --fake-clock, now is real time in whole seconds."""
    srv = start_server(fake_clock=None)
    before = int(time.time())
    obj = expect_json(srv.request("POST", "/v1/tokens", admin=srv.admin_key), 201)
    after = int(time.time())
    assert before - 1 <= parse_iso(obj["created_at"]) <= after + 1


def test_fake_clock_not_persisted(start_server):
    """R12: the clock set via E8 is not persisted; a restart starts from --fake-clock again."""
    srv = start_server()
    srv.set_clock(T0 + 5000)
    assert srv.stop()[0] == 0
    srv2 = start_server(db=srv.db)
    obj = expect_json(srv2.request("POST", "/v1/tokens", admin=srv2.admin_key), 201)
    assert obj["created_at"] == FAKE_ISO
