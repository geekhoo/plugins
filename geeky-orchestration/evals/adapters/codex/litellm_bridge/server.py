"""Loopback-only Responses HTTP bridge, with a fixed authenticated upstream.

No retries, redirect following, request logs, credential files, or provider discovery.
Each upstream error writes one JSON line to stderr: status, trace headers and a
short redacted excerpt of the error body. Requests and headers are never logged.
Run one process per trusted run. Termination discards the plaintext provenance.

Each forwarded request writes one JSON line to stderr: sizes, status, response.model and
usage.cost, the evidence a provider invoice cannot give per request. These lines hold no request or
response content, header or exception text. The line is written before the client can see
completion, because a run can kill the bridge once its client finishes. If the outcome changes
afterwards, a later line with the same request_id supersedes it.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hmac
import http.client
import itertools
import json
import re
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from .mapper import BridgeState, MappingError, ToolCallAsText, map_response_json, map_sse_frame, translate_request
from .native_plaintext import NativePlaintextState, map_native_response_json, map_native_sse_frame, translate_native_request


MAX_BODY = 16 * 1024 * 1024
TIMEOUT = 120
ERROR_READ = 4096
ERROR_EXCERPT = 600
TRACE_HEADERS = ("x-litellm-call-id", "x-request-id", "cf-ray")
SECRET_PATTERNS = (re.compile(r"Bearer\s+\S+", re.IGNORECASE),
                   re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_\-]{6,}"))


def redact(text, api_key):
    if api_key:
        text = text.replace(api_key, "[REDACTED]")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def log_event(record):
    """One diagnostic line on stderr; a broken stderr never fails the request."""
    record = dict(record, ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    try:
        sys.stderr.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        sys.stderr.flush()
    except (OSError, ValueError):
        pass
MAX_LOGGED_MODEL = 200
SSE_RESPONSE_EVENTS = (b"response.created", b"response.in_progress", b"response.completed",
                       b"response.incomplete", b"response.failed")
SSE_TERMINAL_TYPES = {"response.completed", "response.incomplete", "response.failed"}
_log_lock = threading.Lock()


def stderr_log(entry):
    """Evidence must never fail a request, so a closed stream is ignored."""
    try:
        with _log_lock:
            sys.stderr.write(json.dumps(entry, separators=(",", ":")) + "\n")
            sys.stderr.flush()
    except (OSError, ValueError):
        pass


def note_response(record, response):
    """Copy only the model name and the numeric cost from an upstream response object."""
    if not isinstance(response, dict):
        return
    model = response.get("model")
    if isinstance(model, str) and model:
        record["response_model"] = model[:MAX_LOGGED_MODEL]
    usage = response.get("usage")
    cost = usage.get("cost") if isinstance(usage, dict) else None
    if isinstance(cost, (int, float)) and not isinstance(cost, bool):
        record["usage_cost"] = cost


def note_sse_frame(record, frame):
    """Copy evidence from a response event; True when the event ends the response."""
    if not any(name in frame for name in SSE_RESPONSE_EVENTS):
        return False
    data = b"\n".join(line[5:].strip() for line in frame.splitlines() if line.startswith(b"data:"))
    try:
        event = json.loads(data)
    except ValueError:
        return False
    if not isinstance(event, dict):
        return False
    note_response(record, event.get("response"))
    return event.get("type") in SSE_TERMINAL_TYPES


def upstream_target(base_url):
    parsed = urlsplit(base_url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("Invalid fixed upstream URL")
    path = parsed.path.rstrip("/")
    if not path.endswith("/responses"):
        path += "/responses"
    return parsed, path


def make_server(base_url, api_key, *, port=0, state=None, timeout=TIMEOUT, max_body=MAX_BODY, wire_mode='bridge', log=stderr_log):
    """Create an unstarted loopback server; caller owns serve/shutdown/close."""
    parsed, upstream_path = upstream_target(base_url)
    if not isinstance(api_key, str) or not api_key.strip() or "\r" in api_key or "\n" in api_key:
        raise ValueError("A fixed upstream API key is required")
    if wire_mode not in {'bridge', 'native-plaintext'}:
        raise ValueError('Unsupported Responses wire mode')
    native = wire_mode == 'native-plaintext'
    state_type = NativePlaintextState if native else BridgeState
    state = state if state is not None else state_type()
    if not isinstance(state, state_type):
        raise ValueError('Responses state does not match wire mode')
    response_mapper = map_native_response_json if native else map_response_json
    frame_mapper = map_native_sse_frame if native else map_sse_frame
    request_ids = itertools.count(1)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"
        record = None
        logged = None

        def log_message(self, *_args):
            pass

        def _flush_record(self):
            if self.record is not None and self.record != self.logged:
                self.logged = dict(self.record)
                log(dict(self.record))

        def _error(self, status, code, **fields):
            body = json.dumps({"error": {"type": "bridge_error", "code": code,
                                         "message": code.replace("_", " "), **fields}}).encode()
            if self.record is not None:
                self.record.update(status=status, outcome=code)
                self._flush_record()
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
            phase = "client_read"
            self.record = record = {"event": "bridge_request", "request_id": next(request_ids),
                                    "ts": datetime.now(timezone.utc).isoformat(), "request_bytes": length, "upstream_request_bytes": None, "stream": None,
                                    "status": None, "outcome": None, "response_model": None, "usage_cost": None}
            try:
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise MappingError("Truncated request")
                body = json.loads(raw)
                request, context = (translate_native_request(body, state, origin=uuid.uuid4().hex)
                                    if native else translate_request(body, state))
                payload = json.dumps(request, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                record.update(upstream_request_bytes=len(payload), stream=bool(request.get("stream")))
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
                phase = "connect"
                connection.connect()
                phase = "send"
                connection.request("POST", upstream_path, body=payload, headers=forward_headers)
                phase = "response_headers"
                response = connection.getresponse()
                phase = "response_body"
                if response.status != 200:
                    try:
                        error_body = response.read(ERROR_READ)
                    except (OSError, http.client.HTTPException):
                        error_body = b""
                    headers = {name.lower(): value for name, value in response.getheaders()}
                    log_event({"event": "upstream_http_error", "status": response.status,
                               "content_type": headers.get("content-type", ""),
                               "trace": {name: headers[name] for name in TRACE_HEADERS if name in headers},
                               "excerpt": redact(error_body.decode("utf-8", "replace"), api_key)[:ERROR_EXCERPT]})
                    self._error(response.status if 400 <= response.status <= 599 else 502, "upstream_http_error")
                    return
                content_type = response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
                if request.get("stream"):
                    if content_type != "text/event-stream":
                        self._error(502, "unexpected_upstream_content_type")
                        return
                    phase = "client_write"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    started = True
                    record.update(status=200, outcome="ok")
                    frame = bytearray()
                    while True:
                        phase = "response_body"
                        line = response.readline(max_body + 1)
                        if len(frame) + len(line) > max_body:
                            raise MappingError("Upstream SSE frame too large")
                        if not line:
                            if frame:
                                terminal = note_sse_frame(record, bytes(frame))
                                mapped_frame = frame_mapper(bytes(frame), context)
                                phase = "client_write"
                                if terminal:
                                    self._flush_record()
                                self.wfile.write(mapped_frame)
                            break
                        frame.extend(line)
                        if line in {b"\n", b"\r\n"}:
                            terminal = note_sse_frame(record, bytes(frame))
                            mapped_frame = frame_mapper(bytes(frame), context)
                            phase = "client_write"
                            if terminal:
                                self._flush_record()
                            self.wfile.write(mapped_frame)
                            self.wfile.flush()
                            frame.clear()
                else:
                    if content_type != "application/json":
                        self._error(502, "unexpected_upstream_content_type")
                        return
                    raw_response = response.read(max_body + 1)
                    if len(raw_response) > max_body:
                        raise MappingError("Upstream response too large")
                    upstream_result = json.loads(raw_response)
                    if isinstance(upstream_result, dict):
                        note_response(record, upstream_result)
                    result = response_mapper(upstream_result, context)
                    data = json.dumps(result, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                    phase = "client_write"
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Connection", "close")
                    self.end_headers()
                    started = True
                    record.update(status=200, outcome="ok")
                    self._flush_record()
                    self.wfile.write(data)
            except ToolCallAsText:
                if started:
                    record["outcome"] = "bridge_tool_call_as_text"
                    self._flush_record()
                    self.wfile.write(b'event: error\ndata: {"type":"error","code":"bridge_tool_call_as_text","message":"Tool-call markup in assistant output text"}\n\n')
                else:
                    self._error(502, "bridge_tool_call_as_text")
            except (MappingError, ValueError, UnicodeError, TypeError):
                if started:
                    record["outcome"] = "bridge_mapping_error"
                    self._flush_record()
                    self.wfile.write(b'event: error\ndata: {"type":"error","code":"bridge_mapping_error","message":"Bridge mapping failed"}\n\n')
                else:
                    self._error(400 if connection is None else 502, "bridge_mapping_error")
            except (OSError, http.client.HTTPException) as error:
                log_event({"event": "upstream_transport_error", "error": type(error).__name__,
                           "stream_started": started, "phase": phase})
                # client_read and client_write are the Codex side of the bridge, not the provider.
                record.update(phase=phase, error_type=type(error).__name__)
                if started:
                    record["outcome"] = "upstream_transport_error"
                    self._flush_record()
                    try:
                        self.wfile.write(b'event: error\ndata: {"type":"error","code":"upstream_transport_error","phase":"'
                                         + phase.encode() + b'","message":"Upstream transport failed"}\n\n')
                    except OSError:
                        pass
                else:
                    self._error(502, "upstream_transport_error", phase=phase)
            finally:
                if connection is not None:
                    connection.close()
                self._flush_record()

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
