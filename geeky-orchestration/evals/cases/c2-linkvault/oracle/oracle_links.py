import re

import pytest

from conftest import FAKE_ISO, T0, expect_error, expect_json, expect_link, iso


def test_create_generated_slug(server):
    """AC4, R4, R5, E3: generated slug ^[a-z0-9]{7}$ and full link object in key order."""
    tok = server.new_token()
    link = expect_link(server.create(tok, url="https://example.com/a"), 201)
    assert re.fullmatch(r"[a-z0-9]{7}", link["slug"])
    assert link == {
        "slug": link["slug"], "url": "https://example.com/a",
        "short_url": f"http://127.0.0.1:{server.port}/{link['slug']}",
        "created_at": FAKE_ISO, "expires_at": None, "clicks": 0, "last_clicked_at": None,
    }


def test_create_custom_slug_echoed(server):
    """AC4, R4: custom slug echoed back; short_url uses the bound port."""
    tok = server.new_token()
    link = expect_link(server.create(tok, slug="My_Slug-1"), 201)
    assert link["slug"] == "My_Slug-1"
    assert link["short_url"] == f"http://127.0.0.1:{server.port}/My_Slug-1"


def test_repeated_slug_409(server):
    """AC4, R5: creating an existing slug returns 409 slug_taken."""
    tok = server.new_token()
    expect_link(server.create(tok, slug="dupe"), 201)
    expect_error(server.create(tok, slug="dupe"), 409, "slug_taken")


def test_reserved_and_short_slug(server):
    """AC4, R5: healthz returns 409 slug_taken; ab returns 400 invalid_request."""
    tok = server.new_token()
    expect_error(server.create(tok, slug="healthz"), 409, "slug_taken")
    expect_error(server.create(tok, slug="ab"), 400, "invalid_request")


@pytest.mark.parametrize("slug", ["a" * 33, "a.b", "has space", "ab/c", "", 123])
def test_invalid_custom_slug(server, slug):
    """R5, E3: a slug failing ^[A-Za-z0-9_-]{3,32}$ or not a string returns 400 invalid_request."""
    tok = server.new_token()
    resp = server.request("POST", "/v1/links", body={"url": "http://a.com", "slug": slug}, token=tok)
    expect_error(resp, 400, "invalid_request")


def test_slug_length_bounds_and_case_sensitivity(server):
    """R5: 3- and 32-char slugs are valid; slugs are case-sensitive."""
    tok = server.new_token()
    expect_link(server.create(tok, slug="abc"), 201)
    expect_link(server.create(tok, slug="B" * 32), 201)
    expect_link(server.create(tok, slug="promo"), 201)
    expect_link(server.create(tok, slug="Promo"), 201)


def test_slug_collision_across_tokens(server):
    """Oracle example 1, R5: second token gets 409 on promo; first token's link unchanged."""
    a, b = server.new_token(), server.new_token()
    first = expect_link(server.create(a, url="https://a.example/1", slug="promo"), 201)
    expect_error(server.create(b, url="https://b.example/2", slug="promo"), 409, "slug_taken")
    assert expect_link(server.request("GET", "/v1/links/promo", token=a)) == first


def test_expires_in_sets_expires_at(server):
    """E3, R4: expires_at = created_at + expires_in; max 31536000 accepted."""
    tok = server.new_token()
    link = expect_link(server.create(tok, slug="exp60", expires_in=60), 201)
    assert link["expires_at"] == iso(T0 + 60)
    link = expect_link(server.create(tok, slug="expmax", expires_in=31536000), 201)
    assert link["expires_at"] == iso(T0 + 31536000)


@pytest.mark.parametrize("value", [True, 0, 1.5, "60", 31536001, -1])
def test_invalid_expires_in(server, value):
    """Oracle example 10, E3: bool, 0, float, string, too large, negative return 400 invalid_request."""
    tok = server.new_token()
    resp = server.request("POST", "/v1/links", body={"url": "http://a.com", "expires_in": value},
                          token=tok)
    expect_error(resp, 400, "invalid_request")


@pytest.mark.parametrize("url", [
    "ftp://x", "javascript:alert(1)", "http://", "http://a.com/with space",
    "http://a.com/" + "a" * (2049 - len("http://a.com/")),
])
def test_ac5_invalid_urls(server, url):
    """AC5, R6: bad scheme, no host, whitespace, 2049 chars return 400 invalid_request."""
    tok = server.new_token()
    expect_error(server.create(tok, url=url), 400, "invalid_request")


@pytest.mark.parametrize("url", [
    "FTP://h", "mailto:a@b", "javascript:x", "file:///etc/passwd",
    "http://a.com/\tx", "http://a.com/\x7f", "http://a.com/\x01", "http://a.com/\nx",
])
def test_invalid_schemes_and_control_chars(server, url):
    """Oracle example 2, R6: other schemes and control/whitespace characters return 400."""
    tok = server.new_token()
    expect_error(server.create(tok, url=url), 400, "invalid_request")


def test_uppercase_scheme_stored_verbatim(server):
    """Oracle example 2, R6: HTTPS://Example.com returns 201 and is stored verbatim."""
    tok = server.new_token()
    link = expect_link(server.create(tok, url="HTTPS://Example.com", slug="upper"), 201)
    assert link["url"] == "HTTPS://Example.com"
    resp = server.request("GET", "/upper")
    assert resp.status == 302
    assert resp.header("Location") == "HTTPS://Example.com"


def test_url_of_2048_chars_accepted(server):
    """R6: a 2048-character URL is accepted."""
    tok = server.new_token()
    url = "http://a.com/" + "a" * (2048 - len("http://a.com/"))
    assert expect_link(server.create(tok, url=url), 201)["url"] == url


@pytest.mark.parametrize("body", [{}, {"url": 123}, {"url": None}, {"slug": "abc"}])
def test_missing_or_wrong_type_url(server, body):
    """E3: url is required and must be a string; otherwise 400 invalid_request."""
    tok = server.new_token()
    expect_error(server.request("POST", "/v1/links", body=body, token=tok), 400, "invalid_request")


@pytest.mark.parametrize("raw,code", [
    (b"{bad", "invalid_json"),
    (b"[]", "invalid_json"),
    (b'"x"', "invalid_json"),
    (b"", "invalid_json"),
    (b'{"url":"http://a.com/\xff"}', "invalid_json"),
    (b'{"url":"http://a","extra":1}', "invalid_request"),
])
def test_malformed_json(server, raw, code):
    """Oracle example 8, Error handling: non-JSON/non-object/bad UTF-8 is invalid_json; extra key is invalid_request."""
    tok = server.new_token()
    expect_error(server.request("POST", "/v1/links", body=raw, token=tok), 400, code)


def test_oversized_body_413(server):
    """Oracle example 9, Error handling: Content-Length 8193 returns 413 with Connection: close, body unread."""
    tok = server.new_token()
    resp = server.request("POST", "/v1/links", token=tok, headers={"Content-Length": "8193"})
    expect_error(resp, 413, "payload_too_large")
    assert resp.header("Connection").lower() == "close"


def test_body_of_exactly_8192_bytes_passes(server):
    """Oracle example 9, Conventions: an 8192-byte body passes the size step."""
    tok = server.new_token()
    raw = b'{"url":"http://a.com/big","slug":"big8192"}'
    raw = raw + b" " * (8192 - len(raw))
    assert len(raw) == 8192
    assert expect_link(server.request("POST", "/v1/links", body=raw, token=tok), 201)["slug"] == "big8192"


def test_size_check_after_auth(server):
    """Precedence: auth 401 precedes size 413."""
    resp = server.request("POST", "/v1/links", headers={"Content-Length": "8193"})
    expect_error(resp, 401, "unauthorized")


def test_list_order_and_ownership(server):
    """AC8, R9, E4: only own links, ordered by created_at then slug, expired included."""
    a, b = server.new_token(), server.new_token()
    expect_link(server.create(a, slug="zeta", expires_in=1), 201)
    expect_link(server.create(a, slug="alpha"), 201)
    expect_link(server.create(b, slug="bravo"), 201)
    server.set_clock(T0 + 30)
    expect_link(server.create(a, slug="aaa"), 201)
    obj = expect_json(server.request("GET", "/v1/links", token=a), 200)
    assert list(obj) == ["links"]
    assert [link["slug"] for link in obj["links"]] == ["alpha", "zeta", "aaa"]
    assert all(list(link) == ["slug", "url", "short_url", "created_at", "expires_at", "clicks",
                              "last_clicked_at"] for link in obj["links"])
    other = expect_json(server.request("GET", "/v1/links", token=b), 200)
    assert [link["slug"] for link in other["links"]] == ["bravo"]


def test_list_empty(server):
    """E4: a token with no links gets {"links":[]}."""
    tok = server.new_token()
    assert expect_json(server.request("GET", "/v1/links", token=tok), 200) == {"links": []}


def test_cross_token_access_is_404(server):
    """AC8, R9, oracle example 7: token B gets 404 on E5 and E6 for A's slug; A's link survives."""
    a, b = server.new_token(), server.new_token()
    link = expect_link(server.create(a, slug="mine01"), 201)
    expect_error(server.request("GET", "/v1/links/mine01", token=b), 404, "not_found")
    expect_error(server.request("DELETE", "/v1/links/mine01", token=b), 404, "not_found")
    assert expect_link(server.request("GET", "/v1/links/mine01", token=a)) == link


def test_delete_then_reuse(server):
    """AC8, R10, E6: 204 empty body; slug then 404 on redirect and inspect; can be created again."""
    tok = server.new_token()
    expect_link(server.create(tok, slug="gone01"), 201)
    resp = server.request("DELETE", "/v1/links/gone01", token=tok)
    assert resp.status == 204
    assert resp.body == b""
    assert resp.header("Content-Length") == "0"
    expect_error(server.request("GET", "/gone01"), 404, "not_found")
    expect_error(server.request("GET", "/v1/links/gone01", token=tok), 404, "not_found")
    expect_error(server.request("DELETE", "/v1/links/gone01", token=tok), 404, "not_found")
    expect_link(server.create(tok, slug="gone01"), 201)


def test_delete_204_sends_content_length_zero(server):
    """E6, Conventions (R-b): a 204 has an empty body and sends Content-Length: 0."""
    tok = server.new_token()
    expect_link(server.create(tok, slug="cl0del"), 201)
    resp = server.request("DELETE", "/v1/links/cl0del", token=tok)
    assert resp.status == 204
    assert resp.header("Content-Length") == "0"
    assert resp.body == b""


@pytest.mark.parametrize("field", ["slug", "expires_in"])
def test_explicit_null_optional_field(server, field):
    """E3 body rules (R-d): an explicit null for slug or expires_in returns 400 invalid_request."""
    tok = server.new_token()
    resp = server.request("POST", "/v1/links", body={"url": "http://a.com", field: None}, token=tok)
    expect_error(resp, 400, "invalid_request")


def test_inspect_unknown_slug(server):
    """R9, E5: unknown slug returns 404 not_found."""
    tok = server.new_token()
    expect_error(server.request("GET", "/v1/links/nosuch", token=tok), 404, "not_found")
