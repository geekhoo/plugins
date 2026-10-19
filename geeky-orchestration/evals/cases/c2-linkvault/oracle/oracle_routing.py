import pytest

from conftest import expect_error


@pytest.mark.parametrize("method,path", [
    ("PUT", "/v1/links"),
    ("GET", "/v1/links/"),
    ("PATCH", "/v1/links/abc"),
    ("POST", "/healthz"),
    ("GET", "/v1/tokens"),
    ("DELETE", "/v1/links"),
    ("POST", "/abcdef"),
    ("GET", "/healthz/"),
])
def test_unlisted_routes_404(server, method, path):
    """Oracle example 11, Conventions: unlisted (method, path) pairs return 404 not_found, no slash normalisation."""
    tok = server.new_token()
    expect_error(server.request(method, path, token=tok), 404, "not_found")


def test_head_returns_404(server):
    """Oracle example 11, Conventions: HEAD /x returns 404."""
    assert server.request("HEAD", "/x").status == 404
