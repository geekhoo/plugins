import pytest

from conftest import T0, expect_error, expect_link, iso


def expect_redirect(resp, url):
    assert resp.status == 302, resp
    assert resp.header("Location") == url
    assert resp.header("Content-Length") == "0"
    assert resp.body == b""


def test_redirect_and_click_stats(server):
    """AC6, R7, E7: 302 exact Location, empty body; E5 then shows clicks 1 and last_clicked_at = now."""
    tok = server.new_token()
    url = "https://example.com/path?q=1&r=a%20b#frag"
    expect_link(server.create(tok, url=url, slug="click1"), 201)
    server.set_clock(T0 + 5)
    expect_redirect(server.request("GET", "/click1"), url)
    link = expect_link(server.request("GET", "/v1/links/click1", token=tok))
    assert link["clicks"] == 1
    assert link["last_clicked_at"] == iso(T0 + 5)
    assert link["created_at"] == iso(T0)


def test_redirect_ignores_query_string(server):
    """E7, Conventions: query string ignored on the redirect route; still counts the click."""
    tok = server.new_token()
    expect_link(server.create(tok, url="http://a.com/", slug="qs123"), 201)
    expect_redirect(server.request("GET", "/qs123?utm=x"), "http://a.com/")
    assert expect_link(server.request("GET", "/v1/links/qs123", token=tok))["clicks"] == 1


def test_redirect_unknown_slug_404(server):
    """R8, E7: unknown slug returns 404 not_found."""
    expect_error(server.request("GET", "/unknown1"), 404, "not_found")


@pytest.mark.parametrize("path", ["/ab", "/a.b", "/" + "a" * 33, "/"])
def test_redirect_bad_slug_is_route_404(server, path):
    """E7, Routing: a path failing the slug pattern returns 404 not_found."""
    expect_error(server.request("GET", path), 404, "not_found")


def test_expiry_boundary(server):
    """AC7, R8, R12, oracle example 3: 302 at T+59, 410 gone at T+60; clicks unchanged; E5 still 200."""
    tok = server.new_token()
    expect_link(server.create(tok, url="http://a.com/e", slug="exp001", expires_in=60), 201)
    server.set_clock(T0 + 59)
    expect_redirect(server.request("GET", "/exp001"), "http://a.com/e")
    server.set_clock(T0 + 60)
    expect_error(server.request("GET", "/exp001"), 410, "gone")
    server.set_clock(T0 + 3600)
    expect_error(server.request("GET", "/exp001"), 410, "gone")
    link = expect_link(server.request("GET", "/v1/links/exp001", token=tok))
    assert link["clicks"] == 1
    assert link["last_clicked_at"] == iso(T0 + 59)
    assert link["expires_at"] == iso(T0 + 60)


def test_redirect_needs_no_auth_and_counts_each_click(server):
    """R7, E7: redirects need no auth; each one increments clicks."""
    tok = server.new_token()
    expect_link(server.create(tok, url="http://a.com/", slug="many01"), 201)
    for _ in range(5):
        expect_redirect(server.request("GET", "/many01"), "http://a.com/")
    assert expect_link(server.request("GET", "/v1/links/many01", token=tok))["clicks"] == 5
