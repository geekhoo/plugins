"""Transport regression tests use an in-process loopback server only."""
import gzip
import hashlib
import json
import socket
import threading
import time
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from .transport import decode_json, exchange, normalize_endpoint, parse_sse, reconstruct_response
except ImportError:
    from transport import decode_json, exchange, normalize_endpoint, parse_sse, reconstruct_response


def sse(events):
    return b"".join(b"data: " + json.dumps(e, ensure_ascii=False).encode("utf-8") + b"\n\n" for e in events)


@contextmanager
def server(mode, payload=b"", content_type="application/json"):
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_POST(self):
            calls.append((self.path, self.headers.get("Authorization"), self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(307 if mode == "redirect" else 200)
            self.send_header("Content-Type", content_type)
            if mode == "compressed":
                self.send_header("Content-Encoding", "gzip")
            if mode == "redirect":
                self.send_header("Location", "http://127.0.0.1:1/steal")
            if mode == "chunked":
                self.send_header("Transfer-Encoding", "chunked")
            elif mode != "close":
                self.send_header("Content-Length", str(len(payload) + (10 if mode == "truncated" else 0)))
            self.end_headers()
            try:
                if mode == "chunked":
                    for pos in range(0, len(payload), 3):
                        chunk = payload[pos:pos + 3]
                        self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                    self.wfile.write(b"0\r\n\r\n")
                elif mode in ("slow", "fragmented"):
                    for byte in payload:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.04 if mode == "slow" else 0.0001)
                elif mode == "stall":
                    time.sleep(0.5)
                else:
                    self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}/v1", calls
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(2)


def codes(result):
    return [e["code"] for e in result["errors"]]


class TransportTest(unittest.TestCase):
    def test_normalize_and_reject_secrets(self):
        self.assertEqual(normalize_endpoint("https://example.test/v1/"), "https://example.test/v1/responses")
        self.assertEqual(normalize_endpoint("https://example.test/openai/deployments/d/responses?api-version=2025-01-01"), "https://example.test/openai/deployments/d/responses?api-version=2025-01-01")
        self.assertEqual(normalize_endpoint("https://example.test/custom/generate?route=blue"), "https://example.test/custom/generate?route=blue")
        self.assertEqual(normalize_endpoint("https://example.test/openai/responses?api-version=custom"), "https://example.test/openai/responses?api-version=custom")
        self.assertEqual(normalize_endpoint("https://example.test/custom/"), "https://example.test/custom/")
        self.assertEqual(normalize_endpoint("https://example.test/"), "https://example.test/responses")
        for url in ("https://u:secret@example.test/v1", "https://example.test/v1?api_key=secret", "https://example.test/v1#secret", "https://example.test/v1#", "https://example.test/v1?%61pi%5fkey=secret", "https://example.test/v1?X-ACCESS-TOKEN=secret", "https://example.test/v1?sig=secret"):
            result = exchange(url, {}, {})
            self.assertEqual(codes(result), ["invalid_request"])
            self.assertNotIn("secret", str(result))

    def test_custom_query_forwarded(self):
        with server("json", b'{"output":[]}') as (url, calls):
            result = exchange(url + "?route=blue%20pool&monkey=ok&api-version=custom", {}, {})
        self.assertEqual(codes(result), [])
        self.assertEqual(calls[0][0], "/v1/responses?route=blue%20pool&monkey=ok&api-version=custom")
        with server("json", b'{"output":[]}') as (url, calls):
            result = exchange(url + "/gateway/custom-route?route=blue", {}, {})
        self.assertEqual(codes(result), [])
        self.assertEqual(calls[0][0], "/v1/gateway/custom-route?route=blue")

    def test_json_auth_once_and_hash(self):
        payload = b'{"id":"r","output":[]}'
        with server("json", payload) as (url, calls):
            result = exchange(url, {"model": "x"}, {"Authorization": "Bearer test-secret"})
        self.assertEqual(result["response"], {"id": "r", "output": []})
        self.assertEqual(codes(result), [])
        self.assertTrue(result["body_complete"])
        self.assertEqual(result["wire_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "/v1/responses")
        self.assertEqual(calls[0][1], "Bearer test-secret")
        self.assertNotIn("test-secret", str(result))

    def test_invalid_json_objects_are_rejected(self):
        for payload in (b'[]', b'{"id":NaN}', b'{"id":1,"id":2}', b'{"nested":{"id":1,"id":2}}', b'{"value":1e999}', b'{"nested":[-1e999]}'):
            with server("json", payload) as (url, _):
                result = exchange(url, {}, {})
            self.assertEqual(codes(result), ["invalid_json"])
            self.assertIsNone(result["response"])
            self.assertTrue(result["body_complete"])
            self.assertEqual(decode_json(payload)[1][0]["code"], "invalid_json")
        self.assertEqual(decode_json(b'{"output":[]}'), ({"output": []}, []))
        self.assertEqual(parse_sse(b'data: {"type":"x","type":"y"}\n\n')[1][0]["code"], "invalid_sse_json")

    def test_sse_fragmented_unicode_and_reconstruction(self):
        added = {"id": "fc1", "type": "function_call", "call_id": "c1", "arguments": ""}
        item = dict(added, arguments='{"city":"東京"}')
        events = [{"type": "response.output_item.added", "output_index": 0, "item": added},
                  {"type": "response.function_call_arguments.delta", "item_id": "fc1", "delta": '{"city":'},
                  {"type": "response.function_call_arguments.delta", "item_id": "fc1", "delta": '"東京"}'},
                  {"type": "response.output_item.done", "output_index": 0, "item": item},
                  {"type": "response.completed", "response": {"id": "r", "output": [item]}}]
        with server("fragmented", sse(events), "text/event-stream; charset=utf-8") as (url, _):
            result = exchange(url, {"stream": True}, {}, timeout=4)
        self.assertEqual(codes(result), [])
        self.assertEqual(result["response"]["output"], [item])

    def test_sse_multiline_comments_done_and_missing_completion(self):
        raw = b': comment\r\nevent: response.completed\r\ndata: {"type":"response.completed",\r\ndata: "response":{"output":[]}}\r\n\r\ndata: [DONE]\r\n\r\n'
        events, errors = parse_sse(raw)
        self.assertEqual(errors, [])
        self.assertEqual(reconstruct_response(events)[1], [])
        events, errors = parse_sse(b'data: [DONE]\n\n')
        self.assertEqual([error["code"] for error in errors], ["premature_done"])
        self.assertEqual(reconstruct_response(events)[1][0]["code"], "missing_completion")
        event = b'data: {"type":"response.completed","response":{"output":[]}}\n\n'
        done = b'data: [DONE]\n\n'
        self.assertEqual(parse_sse(event + done)[1], [])
        self.assertIn("event_after_done", [error["code"] for error in parse_sse(done + event)[1]])
        self.assertIn("duplicate_done", [error["code"] for error in parse_sse(event + done + done)[1]])
        self.assertEqual(parse_sse(b'data: {}')[1][0]["code"], "truncated_sse_frame")
        self.assertEqual(parse_sse(b'data: {}\n')[1][0]["code"], "truncated_sse_frame")
        self.assertEqual(parse_sse(b'data: \xff\n\n')[1][0]["code"], "invalid_utf8")

    def test_terminal_item_and_delta_errors(self):
        item = {"id": "fc", "type": "function_call", "call_id": "c", "arguments": "x"}
        events = [{"type": "response.output_item.added", "output_index": 1, "item": dict(item, arguments="")},
                  {"type": "response.function_call_arguments.delta", "item_id": "fc", "delta": "bad"},
                  {"type": "response.output_item.done", "output_index": 1, "item": item},
                  {"type": "response.completed", "response": {"output": [item]}},
                  {"type": "error"}]
        _, errors = reconstruct_response(events)
        self.assertTrue({"arguments_mismatch", "output_index_gap", "item_mismatch", "event_after_terminal"} <= {e["code"] for e in errors})
        self.assertEqual(reconstruct_response([{"type": "response.failed"}])[1][0]["code"], "stream_failed")
        _, errors = reconstruct_response([{"type": "response.completed", "response": {"output": []}}, {"type": "response.completed", "response": {"output": []}}])
        self.assertIn("event_after_terminal", [e["code"] for e in errors])

    def test_missing_streamed_output_and_call_identity(self):
        call = {"id": "fc", "type": "function_call", "name": "read", "namespace": "workspace", "call_id": "c", "arguments": "{}"}
        completed = {"type": "response.completed", "response": {"output": [call]}}
        self.assertIn("output_mismatch", [e["code"] for e in reconstruct_response([completed])[1]])
        added = dict(call, arguments="", name="different")
        events = [{"type": "response.output_item.added", "output_index": 0, "item": added},
                  {"type": "response.function_call_arguments.delta", "item_id": "fc", "delta": "{}"},
                  {"type": "response.output_item.done", "output_index": 0, "item": call}, completed]
        self.assertIn("item_mismatch", [e["code"] for e in reconstruct_response(events)[1]])
        added["name"] = call["name"]
        added["namespace"] = "other"
        self.assertIn("item_mismatch", [e["code"] for e in reconstruct_response(events)[1]])
        added["namespace"] = call["namespace"]
        self.assertEqual(reconstruct_response(events)[1], [])
        completed["response"]["output"] = [dict(call, arguments="tampered")]
        self.assertIn("item_mismatch", [e["code"] for e in reconstruct_response(events)[1]])

    def test_text_and_item_identity_consistency(self):
        added = {"id": "m", "type": "message", "role": "assistant", "content": []}
        done = dict(added, content=[{"type": "output_text", "text": "Hello"}])
        events = [{"type": "response.output_item.added", "output_index": 0, "item": added},
                  {"type": "response.output_text.delta", "output_index": 0, "item_id": "m", "content_index": 0, "delta": "Hello"},
                  {"type": "response.output_text.done", "output_index": 0, "item_id": "m", "content_index": 0, "text": "Hello"},
                  {"type": "response.output_item.done", "output_index": 0, "item": done},
                  {"type": "response.completed", "response": {"output": [done]}}]
        self.assertEqual(reconstruct_response(events)[1], [])
        events[1]["output_index"] = 1
        self.assertIn("delta_order", [e["code"] for e in reconstruct_response(events)[1]])
        events[1]["item_id"] = []
        self.assertIn("delta_order", [e["code"] for e in reconstruct_response(events)[1]])

    def test_boolean_output_index_rejected_for_delta_and_done(self):
        function = {"id": "fc", "type": "function_call", "call_id": "c", "arguments": "{}"}
        message = {"id": "m", "type": "message", "content": [{"type": "output_text", "text": "Hi"}]}
        cases = [
            (function, {"type": "response.function_call_arguments.delta", "item_id": "fc", "delta": "{}", "output_index": False}),
            (function, {"type": "response.function_call_arguments.done", "item_id": "fc", "arguments": "{}", "output_index": False}),
            (message, {"type": "response.output_text.delta", "item_id": "m", "content_index": 0, "delta": "Hi", "output_index": False}),
            (message, {"type": "response.output_text.done", "item_id": "m", "content_index": 0, "text": "Hi", "output_index": False}),
        ]
        for item, event in cases:
            events = [{"type": "response.output_item.added", "output_index": 0, "item": item}, event,
                      {"type": "response.output_item.done", "output_index": 0, "item": item},
                      {"type": "response.completed", "response": {"output": [item]}}]
            self.assertIn("delta_order", [error["code"] for error in reconstruct_response(events)[1]])

    def test_timeout_is_total_not_idle(self):
        with server("slow", b'x' * 30) as (url, _):
            start = time.monotonic()
            result = exchange(url, {}, {}, timeout=0.2)
            elapsed = time.monotonic() - start
        self.assertIn("timeout", codes(result))
        self.assertFalse(result["body_complete"])
        self.assertLess(elapsed, 0.45)
        with server("stall", b'x') as (url, _):
            result = exchange(url, {}, {}, timeout=0.1)
        self.assertIn("timeout", codes(result))

    def test_chunked_body_and_cap(self):
        with server("chunked", b'{"output":[]}') as (url, _):
            result = exchange(url, {}, {})
        self.assertEqual(result["response"], {"output": []})
        self.assertEqual(codes(result), [])
        with server("chunked", b'{"output":[]}') as (url, _):
            result = exchange(url, {}, {}, max_bytes=5)
        self.assertIn("body_too_large", codes(result))
        self.assertEqual(len(result["body"]), 5)

    def test_unsupported_compressed_body_is_not_retained(self):
        payload = gzip.compress(b'{"credential":"test-secret"}')
        with server("compressed", payload) as (url, calls):
            result = exchange(url, {}, {})
        self.assertEqual(codes(result), ["unsupported_content_encoding"])
        self.assertEqual(result["body"], b"")
        self.assertIsNone(result["response"])
        self.assertFalse(result["body_complete"])
        self.assertNotIn("test-secret", str(result))
        self.assertEqual(len(calls), 1)

    def test_cap_truncation_nonutf8_and_redirect(self):
        with server("json", b'x' * 20) as (url, _):
            result = exchange(url, {}, {}, max_bytes=8)
        self.assertIn("body_too_large", codes(result))
        self.assertFalse(result["body_complete"])
        self.assertEqual(len(result["body"]), 8)
        with server("truncated", b'{}') as (url, _):
            result = exchange(url, {}, {})
        self.assertIn("truncated_body", codes(result))
        self.assertFalse(result["body_complete"])
        with server("json", b'\xff') as (url, _):
            result = exchange(url, {}, {})
        self.assertIn("invalid_json", codes(result))
        with server("redirect", b'secret-body') as (url, calls):
            result = exchange(url, {}, {})
        self.assertEqual(result["http_status"], 307)
        self.assertEqual(codes(result), ["http_status"])
        self.assertEqual(len(calls), 1)
        self.assertNotIn("secret-body", str(result["errors"]))


if __name__ == "__main__":
    unittest.main()
