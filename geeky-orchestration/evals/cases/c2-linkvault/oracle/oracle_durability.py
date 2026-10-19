import http.client
import threading
import time

from conftest import HTTP_TIMEOUT, T0, expect_link, iso


def test_restart_persistence(start_server):
    """AC10, R13, oracle example 6: after SIGINT and restart, token works; clicks, created_at, last_clicked_at kept."""
    srv = start_server()
    tok = srv.new_token()
    created = expect_link(srv.create(tok, url="http://a.com/p", slug="keep01", expires_in=600), 201)
    srv.set_clock(T0 + 7)
    assert srv.request("GET", "/keep01").status == 302
    assert srv.request("GET", "/keep01").status == 302
    before = expect_link(srv.request("GET", "/v1/links/keep01", token=tok))
    assert srv.stop()[0] == 0, srv.stderr_text()

    srv2 = start_server(db=srv.db)
    after = expect_link(srv2.request("GET", "/v1/links/keep01", token=tok))
    assert after["clicks"] == 2
    assert after["created_at"] == created["created_at"] == iso(T0)
    assert after["last_clicked_at"] == iso(T0 + 7)
    assert after["expires_at"] == created["expires_at"]
    assert after["url"] == before["url"]
    assert after["short_url"] == f"http://127.0.0.1:{srv2.port}/keep01"
    assert srv2.request("GET", "/keep01").status == 302


def test_concurrent_clicks(server):
    """AC11, R14, oracle example 5: 50 threads each send one redirect; clicks ends at exactly 50."""
    tok = server.new_token()
    expect_link(server.create(tok, url="http://a.com/c", slug="conc50"), 201)
    n = 50
    barrier = threading.Barrier(n)
    statuses, errors = [], []
    lock = threading.Lock()

    def worker():
        conn = None
        try:
            barrier.wait(HTTP_TIMEOUT)
            for attempt in range(20):
                conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=HTTP_TIMEOUT)
                try:
                    conn.connect()  # a refused connect never reached the server, so retry is safe
                    break
                except ConnectionRefusedError:
                    conn.close()
                    time.sleep(0.05 * (attempt + 1))
            conn.request("GET", "/conc50")
            resp = conn.getresponse()
            resp.read()
            with lock:
                statuses.append(resp.status)
        except Exception as exc:  # recorded and asserted below
            with lock:
                errors.append(repr(exc))
        finally:
            if conn is not None:
                conn.close()

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(HTTP_TIMEOUT * 3)
    assert not any(t.is_alive() for t in threads), "redirect threads hung"
    assert errors == []
    assert statuses == [302] * n
    assert expect_link(server.request("GET", "/v1/links/conc50", token=tok))["clicks"] == n
