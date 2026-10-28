"""Loopback-only Responses HTTP bridge, with a fixed authenticated upstream.

No retries, redirect following, body logs, credential files, or provider discovery.
Run one process per trusted run. Termination discards the plaintext provenance.
"""

from __future__ import annotations

import hmac
import http.client
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from .mapper import BridgeState, MappingError, ToolCallAsText, map_response_json, map_sse_frame, translate_request


MAX_BODY = 16 * 1024 * 1024
TIMEOUT = 120


def upstream_target(base_url):
    parsed = urlsplit(base_url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("Invalid fixed upstream URL")
    path = parsed.path.rstrip("/")
    if not path.endswith("/responses"):
        path += "/responses"
    return parsed, path


def make_server(base_url, api_key, *, port=0, state=None, timeout=TIMEOUT, max_body=MAX_BODY):
    """Create an unstarted loopback server; caller owns serve/shutdown/close."""
    parsed, upstream_path = upstream_target(base_url)
    if not isinstance(api_key, str) or not api_key.strip() or "\r" in api_key or "\n" in api_key:
        raise ValueError("A fixed upstream API key is required")
    state = state if state is not None else BridgeState()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def log_message(self, *_args):
            pass

        def _error(self, status, code):
            body = json.dumps({"error": {"type": "bridge_error", "code": code,
                                         "message": code.replace("_", " ")}}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self.connection.settimeout(timeout)
            if self.path not in {"/v1/responses", "/responses"}:
                self._error(404, "unsupported_path")
                return
            auth = self.headers.get_all("Authorization", [])
            if len(auth) != 1 or not hmac.compare_digest(auth[0].encode(), ("Bearer " + api_key).encode()):
                self._error(401, "unauthorized")
                return
            lengths = self.headers.get_all("Content-Length", [])
            if self.headers.get("Transfer-Encoding") or len(lengths) != 1:
                self._error(400, "content_length_required")
                return
            try:
                length = int(lengths[0])
            except ValueError:
                self._error(400, "invalid_content_length")
                return
            if length < 0 or length > max_body:
                self._error(413, "request_too_large")
                return
            connection = None
            started = False
            try:
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise MappingError("Truncated request")
                request, context = translate_request(json.loads(raw), state)
                payload = json.dumps(request, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                connection_type = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
                connection = connection_type(parsed.hostname, parsed.port, timeout=timeout)
                # Deliberately construct headers rather than copying credentials,
                # hop-by-hop fields or a client-controlled routing header.
                forward_headers = {
                    "Authorization": "Bearer " + api_key,
                    "Content-Type": "application/json", "Accept-Encoding": "identity",
                    "Accept": "text/event-stream" if request.get("stream") else "application/json"}
                user_agent = self.headers.get_all("User-Agent", [])
                if len(user_agent) == 1 and len(user_agent[0]) <= 512 and all(32 <= ord(char) < 127 for char in user_agent[0]):
                    forward_headers["User-Agent"] = user_agent[0]
                connection.request("POST", upstream_path, body=payload, headers=forward_headers)
                response = connection.getresponse()
                if response.status != 200:
                    self._error(response.status if 400 <= response.status <= 599 else 502, "upstream_http_error")
                    return
                content_type = response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
                if request.get("stream"):
                    if content_type != "text/event-stream":
                        self._error(502, "unexpected_upstream_content_type")
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    started = True
                    frame = bytearray()
                    while True:
                        line = response.readline(max_body + 1)
                        if len(frame) + len(line) > max_body:
                            raise MappingError("Upstream SSE frame too large")
                        if not line:
                            if frame:
                                self.wfile.write(map_sse_frame(bytes(frame), context))
                            break
                        frame.extend(line)
                        if line in {b"\n", b"\r\n"}:
                            self.wfile.write(map_sse_frame(bytes(frame), context))
                            self.wfile.flush()
                            frame.clear()
                else:
                    if content_type != "application/json":
                        self._error(502, "unexpected_upstream_content_type")
                        return
                    raw_response = response.read(max_body + 1)
                    if len(raw_response) > max_body:
                        raise MappingError("Upstream response too large")
                    result = map_response_json(json.loads(raw_response), context)
                    data = json.dumps(result, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Connection", "close")
                    self.end_headers()
                    started = True
                    self.wfile.write(data)
            except ToolCallAsText:
                if started:
                    self.wfile.write(b'event: error\ndata: {"type":"error","code":"bridge_tool_call_as_text","message":"Tool-call markup in assistant output text"}\n\n')
                else:
                    self._error(502, "bridge_tool_call_as_text")
            except (MappingError, ValueError, UnicodeError, TypeError):
                if started:
                    self.wfile.write(b'event: error\ndata: {"type":"error","code":"bridge_mapping_error","message":"Bridge mapping failed"}\n\n')
                else:
                    self._error(400 if connection is None else 502, "bridge_mapping_error")
            except (OSError, http.client.HTTPException):
                if started:
                    try:
                        self.wfile.write(b'event: error\ndata: {"type":"error","code":"upstream_transport_error","message":"Upstream transport failed"}\n\n')
                    except OSError:
                        pass
                else:
                    self._error(502, "upstream_transport_error")
            finally:
                if connection is not None:
                    connection.close()

        def do_GET(self):
            self._error(405, "post_required")

        def do_PUT(self):
            self._error(405, "post_required")

    class Server(ThreadingHTTPServer):
        daemon_threads = True
        allow_reuse_address = False

        def handle_error(self, request, client_address):
            # The standard implementation prints tracebacks containing request
            # details. Clients get sanitized errors above; never dump bodies.
            pass

        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(timeout)
            return connection, address

    return Server(("127.0.0.1", port), Handler)
