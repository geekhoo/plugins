from conftest import T0, expect_error, expect_json, expect_link


def limited(resp, retry_after):
    expect_error(resp, 429, "rate_limited")
    assert resp.header("Retry-After") == str(retry_after)


def test_ac9_rate_limit_window(start_server):
    """AC9, R11: limit 3 at window+10: requests 1-3 ok, 4th 429 Retry-After 50; next window ok; redirects never limited."""
    srv = start_server(rate_limit=3)
    tok = srv.new_token()
    srv.set_clock(T0 + 10)
    expect_link(srv.create(tok, url="http://a.com/", slug="rl0001"), 201)
    expect_json(srv.request("GET", "/v1/links", token=tok), 200)
    expect_link(srv.request("GET", "/v1/links/rl0001", token=tok), 200)
    limited(srv.request("GET", "/v1/links", token=tok), 50)
    limited(srv.request("POST", "/v1/links", body={"url": "http://b.com"}, token=tok), 50)
    for _ in range(5):
        assert srv.request("GET", "/rl0001").status == 302
    srv.set_clock(T0 + 60)
    expect_json(srv.request("GET", "/v1/links", token=tok), 200)


def test_example4_counting_boundary(start_server):
    """Oracle example 4, R11: a 400 counts, 401s do not; at window+59 the 429 carries Retry-After: 1."""
    srv = start_server(rate_limit=2)
    tok = srv.new_token()
    srv.set_clock(T0 + 59)
    for _ in range(3):
        expect_error(srv.request("GET", "/v1/links", token="lv_" + "0" * 32), 401, "unauthorized")
    expect_error(srv.request("POST", "/v1/links", body={"url": "ftp://x"}, token=tok), 400,
                 "invalid_request")
    expect_json(srv.request("GET", "/v1/links", token=tok), 200)
    limited(srv.request("GET", "/v1/links", token=tok), 1)
    limited(srv.request("GET", "/v1/links", token=tok), 1)
    srv.set_clock(T0 + 60)
    expect_json(srv.request("GET", "/v1/links", token=tok), 200)


def test_resource_404_counts_route_404_does_not(start_server):
    """R11, precedence: route 404s are not counted; a resource 404 is counted."""
    srv = start_server(rate_limit=2)
    tok = srv.new_token()
    for _ in range(3):
        expect_error(srv.request("PUT", "/v1/links", token=tok), 404, "not_found")
        expect_error(srv.request("GET", "/v1/links/ab", token=tok), 404, "not_found")
    expect_error(srv.request("GET", "/v1/links/nosuch", token=tok), 404, "not_found")
    expect_json(srv.request("GET", "/v1/links", token=tok), 200)
    limited(srv.request("GET", "/v1/links", token=tok), 60)


def test_rate_limit_precedes_validation(start_server):
    """Precedence: 429 wins over size 413 and JSON 400 once the limit is reached."""
    srv = start_server(rate_limit=1)
    tok = srv.new_token()
    expect_json(srv.request("GET", "/v1/links", token=tok), 200)
    limited(srv.request("POST", "/v1/links", body=b"{bad", token=tok), 60)
    limited(srv.request("POST", "/v1/links", token=tok, headers={"Content-Length": "8193"}), 60)


def test_default_limit_is_60(start_server):
    """R11, Server CLI: default --rate-limit is 60 per window."""
    srv = start_server(rate_limit=None)
    tok = srv.new_token()
    for _ in range(60):
        expect_json(srv.request("GET", "/v1/links", token=tok), 200)
    limited(srv.request("GET", "/v1/links", token=tok), 60)


def test_limit_is_per_token(start_server):
    """R11: counters are per token; another token is unaffected."""
    srv = start_server(rate_limit=1)
    a, b = srv.new_token(), srv.new_token()
    expect_json(srv.request("GET", "/v1/links", token=a), 200)
    limited(srv.request("GET", "/v1/links", token=a), 60)
    expect_json(srv.request("GET", "/v1/links", token=b), 200)


def test_admin_and_healthz_not_limited(start_server):
    """R11: /healthz and admin routes (E2, E8) are not rate-limited."""
    srv = start_server(rate_limit=1)
    for _ in range(5):
        srv.new_token()
        expect_json(srv.request("GET", "/healthz"), 200)
        srv.set_clock(T0 + 1)


def test_counters_reset_on_restart(start_server):
    """R11, R13: counters are in memory and reset on restart (fake clock back in the same window)."""
    srv = start_server(rate_limit=1)
    tok = srv.new_token()
    expect_json(srv.request("GET", "/v1/links", token=tok), 200)
    limited(srv.request("GET", "/v1/links", token=tok), 60)
    assert srv.stop()[0] == 0
    srv2 = start_server(rate_limit=1, db=srv.db)
    expect_json(srv2.request("GET", "/v1/links", token=tok), 200)
