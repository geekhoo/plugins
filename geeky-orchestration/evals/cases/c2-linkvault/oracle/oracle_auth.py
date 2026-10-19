import hashlib
import re
import sqlite3

import pytest

from conftest import FAKE_ISO, expect_error, expect_json


def test_token_issuance(server):
    """AC2, R2, E2: 201, lv_ + 32 lowercase hex, keys [token, created_at], created_at = fake now."""
    obj = expect_json(server.request("POST", "/v1/tokens", admin=server.admin_key), 201)
    assert list(obj) == ["token", "created_at"]
    assert re.fullmatch(r"lv_[0-9a-f]{32}", obj["token"])
    assert obj["created_at"] == FAKE_ISO


def test_tokens_are_unique(server):
    """R2: each issuance returns a new token."""
    assert server.new_token() != server.new_token()


@pytest.mark.parametrize("key", ["wrong-key", None])
def test_token_bad_admin_key(server, key):
    """AC2, E2: wrong or missing X-Admin-Key returns 401 unauthorized."""
    expect_error(server.request("POST", "/v1/tokens", admin=key), 401, "unauthorized")


def test_db_stores_only_token_hash_and_exact_schema(start_server):
    """AC2, R2, DB schema: tokens table holds SHA-256 hex digests only; user_version 1; exact columns."""
    srv = start_server()
    tok = srv.new_token()
    expect_json(srv.create(tok, slug="hashed"), 201)
    assert srv.stop()[0] == 0
    assert tok.encode() not in srv.db.read_bytes()
    con = sqlite3.connect(srv.db)
    try:
        hashes = [r[0] for r in con.execute("SELECT token_hash FROM tokens")]
        assert hashes == [hashlib.sha256(tok.encode()).hexdigest()]
        assert con.execute("SELECT token_hash FROM links").fetchall() == [(hashes[0],)]
        assert con.execute("PRAGMA user_version").fetchone()[0] == 1
        assert [r[1] for r in con.execute("PRAGMA table_info(tokens)")] == ["token_hash", "created_at"]
        assert [r[1] for r in con.execute("PRAGMA table_info(links)")] == [
            "slug", "url", "token_hash", "created_at", "expires_at", "clicks", "last_clicked_at"]
    finally:
        con.close()


@pytest.mark.parametrize("method,path,body", [
    ("POST", "/v1/links", {"url": "http://a.com"}),
    ("GET", "/v1/links", None),
    ("GET", "/v1/links/abc", None),
    ("DELETE", "/v1/links/abc", None),
])
def test_links_routes_require_bearer(server, method, path, body):
    """AC3, R3: E3, E4, E5 (and E6) without a token return 401 unauthorized."""
    expect_error(server.request(method, path, body=body), 401, "unauthorized")


@pytest.mark.parametrize("auth", [
    "Basic dXNlcjpwYXNz",
    "Bearer",
    "Bearer ",
    "lv_0123456789abcdef0123456789abcdef",
    "Bearer lv_0123456789abcdef0123456789abcdef",
])
def test_malformed_or_unknown_bearer(server, auth):
    """AC3, R3: malformed or unknown bearer tokens return 401 unauthorized."""
    server.new_token()
    resp = server.request("GET", "/v1/links", headers={"Authorization": auth})
    expect_error(resp, 401, "unauthorized")


def test_route_404_precedes_auth(server):
    """E5/E6/E7 slug rule, precedence: a slug failing the pattern is 404 before auth."""
    expect_error(server.request("GET", "/v1/links/ab"), 404, "not_found")
    expect_error(server.request("DELETE", "/v1/links/a.b"), 404, "not_found")


def test_auth_precedes_validation(server):
    """Precedence: auth 401 wins over JSON 400."""
    expect_error(server.request("POST", "/v1/links", body=b"{bad"), 401, "unauthorized")
