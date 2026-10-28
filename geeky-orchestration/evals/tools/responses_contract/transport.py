"""One-shot, bounded Responses HTTP transport; no proxy, redirects or retries."""
from __future__ import annotations

import hashlib
import json
import math
import re
import select
import socket
import ssl
import threading
import time
from urllib.parse import parse_qsl, urlsplit, urlunsplit

_LIMIT = 2 * 1024 * 1024


def _error(code, path, message):
    return {"code": code, "path": path, "message": message}


def normalize_endpoint(endpoint):
    """Preserve explicit paths; append /responses to root or version base URLs."""
    try:
        p = urlsplit(endpoint)
        if (p.scheme not in ("http", "https") or not p.hostname or p.username is not None
                or p.password is not None or p.fragment or p.port is not None and not 1 <= p.port <= 65535
                or any(ord(c) < 33 or ord(c) == 127 for c in endpoint)):
            raise ValueError
        # Query values are preserved for routing, but credentials belong in headers.
        # Names are decoded and normalized before matching, including percent encoding.
        if "#" in endpoint:
            raise ValueError
        credential_names = {"key", "apikey", "token", "accesstoken", "refreshtoken",
                            "secret", "clientsecret", "signature", "sig", "authorization",
                            "auth", "password", "passwd", "credential", "credentials", "subscriptionkey"}
        for key, _value in parse_qsl(p.query, keep_blank_values=True):
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            if (not normalized or normalized in credential_names
                    or any(part in normalized for part in ("token", "secret", "password", "signature", "credential", "apikey"))
                    or re.search(r"(?:^|[^a-z0-9])key$", key.lower())):
                raise ValueError
        path = p.path
        base = path.rstrip("/")
        if not base or re.search(r"/v[0-9]+$", base, re.IGNORECASE):
            path = base + "/responses"
        return urlunsplit((p.scheme, p.netloc, path, p.query, ""))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid endpoint") from None


def _json_object(value):
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError
            result[key] = item
        return result
    def invalid_constant(_value):
        raise ValueError
    def finite_float(raw):
        number = float(raw)
        if not math.isfinite(number):
            raise ValueError
        return number
    result = json.loads(value, object_pairs_hook=pairs, parse_constant=invalid_constant, parse_float=finite_float)
    if not isinstance(result, dict):
        raise ValueError
    return result


def decode_json(body):
    """Decode a UTF-8 JSON response object with the same rules as live exchange."""
    try:
        return _json_object(body.decode("utf-8")), []
    except (ValueError, UnicodeError, AttributeError):
        return None, [_error("invalid_json", "$.body", "Response is not a UTF-8 JSON object")]


def parse_sse(body):
    errors, events = [], []
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], [_error("invalid_utf8", "$", "Stream is not valid UTF-8")]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    data, name, done, completed = [], None, False, False
    def dispatch():
        nonlocal data, name, done, completed
        if data:
            value = "\n".join(data)
            if value == "[DONE]":
                if done:
                    errors.append(_error("duplicate_done", "$.events", "Stream has more than one end marker"))
                elif not completed:
                    errors.append(_error("premature_done", "$.events", "End marker precedes response completion"))
                done = True
            elif done:
                errors.append(_error("event_after_done", "$.events", "Event follows the end marker"))
            else:
                try:
                    event = _json_object(value)
                    if name and "type" not in event:
                        event["type"] = name
                    elif name and name != event.get("type"):
                        errors.append(_error("event_type_mismatch", "$.events", "SSE event name and type disagree"))
                    events.append(event)
                    if event.get("type") == "response.completed" and isinstance(event.get("response"), dict):
                        completed = True
                except (ValueError, json.JSONDecodeError):
                    errors.append(_error("invalid_sse_json", "$.events", "SSE data is not a JSON object"))
        data, name = [], None
    lines = text.split("\n")
    for index, line in enumerate(lines):
        # The final split sentinel is not a blank SSE line.
        if index == len(lines) - 1 and line == "":
            break
        if not line:
            dispatch()
        elif not line.startswith(":"):
            field, _, value = line.partition(":")
            if value.startswith(" "):
                value = value[1:]
            if field == "data":
                data.append(value)
            elif field == "event":
                name = value
    # EOF does not dispatch an incomplete SSE frame.
    if data:
        errors.append(_error("truncated_sse_frame", "$.events", "Stream ended in an incomplete frame"))
    return events, errors


def _matching_index(event, expected):
    if "output_index" not in event:
        return True
    index = event["output_index"]
    return isinstance(index, int) and not isinstance(index, bool) and index >= 0 and index == expected


def reconstruct_response(events):
    """Return the completed response and flag inconsistencies in streamed items."""
    errors, completed, terminal = [], None, False
    items, ids, deltas, text_deltas, argument_done, text_done, call_ids = {}, {}, {}, {}, {}, {}, set()
    def err(code, message):
        errors.append(_error(code, "$.events", message))
    for event in events:
        if not isinstance(event, dict):
            err("invalid_event", "Event must be an object")
            continue
        kind = event.get("type")
        if terminal:
            err("event_after_terminal", "Event follows a terminal event")
            continue
        if kind in ("error", "response.failed", "response.incomplete"):
            err("stream_failed", "Stream reported a failure or incomplete response")
            terminal = True
        elif kind == "response.completed":
            terminal = True
            completed = event.get("response")
            if not isinstance(completed, dict):
                err("invalid_completed", "Completion has no response object")
                completed = None
        elif kind in ("response.output_item.added", "response.output_item.done"):
            index, item = event.get("output_index"), event.get("item")
            if not isinstance(index, int) or isinstance(index, bool) or index < 0 or not isinstance(item, dict):
                err("invalid_item", "Output item has invalid index or shape")
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                err("invalid_item_id", "Output item is missing its id")
                continue
            old = items.get(index)
            if kind.endswith(".added"):
                if old is not None or item_id in ids:
                    err("duplicate_item", "Output item or id appears more than once")
                else:
                    items[index] = {"added": item, "done": None}
                    ids[item_id] = index
            elif old is None or old["done"] is not None or old["added"].get("id") != item_id:
                err("item_order", "Output item completion lacks a matching addition")
            else:
                old["done"] = item
                if item.get("type") != old["added"].get("type"):
                    err("item_mismatch", "Output item type changed")
                if item.get("type") == "function_call":
                    if any(field in old["added"] and old["added"][field] != item.get(field)
                           for field in ("name", "namespace")):
                        err("item_mismatch", "Function call name or namespace changed")
                    call_id = item.get("call_id")
                    if old["added"].get("call_id") != call_id or not isinstance(call_id, str) or not call_id or call_id in call_ids:
                        err("call_id_mismatch", "Function call id changed, is missing, or is duplicated")
                    elif call_id:
                        call_ids.add(call_id)
                    if (item_id in deltas and item.get("arguments") != deltas[item_id] or
                            item_id in argument_done and item.get("arguments") != argument_done[item_id]):
                        err("arguments_mismatch", "Function arguments disagree with completed item")
        elif kind == "response.function_call_arguments.delta":
            item_id, delta = event.get("item_id"), event.get("delta")
            if (not isinstance(item_id, str) or item_id not in ids or not isinstance(delta, str) or items[ids[item_id]]["done"] is not None
                    or items[ids[item_id]]["added"].get("type") != "function_call"
                    or not _matching_index(event, ids[item_id]) or item_id in argument_done):
                err("delta_order", "Function argument delta lacks an active matching item")
            else:
                deltas[item_id] = deltas.get(item_id, "") + delta
        elif kind == "response.function_call_arguments.done":
            item_id = event.get("item_id")
            if (not isinstance(item_id, str) or item_id not in ids or items[ids[item_id]]["done"] is not None
                    or items[ids[item_id]]["added"].get("type") != "function_call"
                    or not _matching_index(event, ids[item_id])
                    or item_id in argument_done or not isinstance(event.get("arguments"), str)):
                err("delta_order", "Function argument completion lacks an active matching item")
            else:
                argument_done[item_id] = event["arguments"]
                if item_id in deltas and event["arguments"] != deltas[item_id]:
                    err("arguments_mismatch", "Function argument deltas disagree with argument completion")
        elif kind == "response.output_text.delta":
            item_id, ci, delta = event.get("item_id"), event.get("content_index"), event.get("delta")
            if (not isinstance(item_id, str) or item_id not in ids or not isinstance(ci, int) or isinstance(ci, bool) or ci < 0
                    or not isinstance(delta, str) or items[ids[item_id]]["done"] is not None
                    or items[ids[item_id]]["added"].get("type") != "message"
                    or not _matching_index(event, ids[item_id])
                    or (item_id, ci) in text_done):
                err("delta_order", "Text delta lacks an active item")
            else:
                key = (item_id, ci)
                text_deltas[key] = text_deltas.get(key, "") + delta
        elif kind == "response.output_text.done":
            item_id, ci, value = event.get("item_id"), event.get("content_index"), event.get("text")
            if (not isinstance(item_id, str) or item_id not in ids or not isinstance(ci, int) or isinstance(ci, bool) or ci < 0
                    or not isinstance(value, str) or items[ids[item_id]]["done"] is not None
                    or items[ids[item_id]]["added"].get("type") != "message"
                    or not _matching_index(event, ids[item_id])
                    or (item_id, ci) in text_done):
                err("delta_order", "Text completion lacks an active matching item")
            else:
                key = (item_id, ci)
                text_done[key] = value
                if key in text_deltas and text_deltas[key] != value:
                    err("text_mismatch", "Text deltas disagree with text completion")
    if completed is None and not any(e["code"] == "stream_failed" for e in errors):
        err("missing_completion", "Stream has no response.completed event")
    if items and sorted(items) != list(range(len(items))):
        err("output_index_gap", "Output indices are not contiguous")
    if completed is not None:
        if completed.get("status") in ("failed", "incomplete", "cancelled"):
            err("stream_failed", "Completed response reports a non-complete status")
        output = completed.get("output")
        if not isinstance(output, list):
            err("invalid_output", "Completed response has no output array")
        else:
            for index, record in items.items():
                item = record["done"]
                if item is None:
                    err("missing_item_done", "Output item was not completed")
                elif index >= len(output) or output[index] != item:
                    err("item_mismatch", "Completed response differs from completed output item")
                else:
                    for (item_id, ci), delta in {**text_deltas, **text_done}.items():
                        if item.get("id") == item_id:
                            content = item.get("content")
                            if not isinstance(content, list) or ci >= len(content) or not isinstance(content[ci], dict) or content[ci].get("text") != delta:
                                err("text_mismatch", "Text deltas disagree with completed output item")
            if len(output) != len(items):
                err("output_mismatch", "Completed output count differs from streamed items")
    return completed, errors


class _ProtocolError(Exception):
    pass


class _UnsupportedContentEncoding(Exception):
    pass


def _connect(host, port, deadline):
    result = []
    done = threading.Event()
    def resolve():
        try:
            result.append(socket.getaddrinfo(host, port, type=socket.SOCK_STREAM))
        except OSError:
            result.append(None)
        finally:
            done.set()
    threading.Thread(target=resolve, daemon=True).start()
    if not done.wait(max(0, deadline - time.monotonic())):
        raise TimeoutError
    if not result or not result[0]:
        raise OSError
    # One address attempt only: no hidden retries or address fallback.
    family, kind, proto, _, address = result[0][0]
    sock = socket.socket(family, kind, proto)
    sock.setblocking(False)
    try:
        code = sock.connect_ex(address)
        if code:
            _ready(sock, deadline, write=True)
            if sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR):
                raise OSError
        return sock
    except BaseException:
        sock.close()
        raise


def _ready(sock, deadline, write=False):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError
    readable, writable, _ = select.select([] if write else [sock], [sock] if write else [], [], remaining)
    if not (readable or writable):
        raise TimeoutError


def _io(sock, deadline, action, data=None):
    while True:
        if time.monotonic() >= deadline:
            raise TimeoutError
        try:
            return sock.send(data) if action == "send" else sock.recv(65536)
        except BlockingIOError:
            _ready(sock, deadline, write=action == "send")
        except ssl.SSLWantReadError:
            _ready(sock, deadline)
        except ssl.SSLWantWriteError:
            _ready(sock, deadline, write=True)


def exchange(endpoint, request, headers, timeout=30, max_bytes=_LIMIT):
    start = time.monotonic()
    result = {"http_status": None, "content_type": "", "body": b"", "response": None,
              "events": [], "errors": [], "elapsed_s": 0.0, "request_count": 1, "body_complete": False,
              "wire_sha256": hashlib.sha256(b"").hexdigest()}
    body = bytearray()
    sock = None
    try:
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout < float("inf") or not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
            raise ValueError
        p = urlsplit(normalize_endpoint(endpoint))
        if not isinstance(request, dict) or not isinstance(headers, dict):
            raise ValueError
        payload = json.dumps(request, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        safe_headers = []
        reserved = {"host", "content-length", "transfer-encoding", "connection", "proxy-authorization", "accept-encoding"}
        for key, value in headers.items():
            if not isinstance(key, str) or not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", key) or key.lower() in reserved or not isinstance(value, str) or any(ord(c) < 32 or ord(c) > 126 for c in value):
                raise ValueError
            safe_headers.append((key, value))
        port = p.port or (443 if p.scheme == "https" else 80)
        deadline = start + timeout
        sock = _connect(p.hostname, port, deadline)
        if p.scheme == "https":
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=p.hostname, do_handshake_on_connect=False)
            while True:
                try:
                    sock.do_handshake()
                    break
                except ssl.SSLWantReadError:
                    _ready(sock, deadline)
                except ssl.SSLWantWriteError:
                    _ready(sock, deadline, write=True)
        host = f"[{p.hostname}]" if ":" in p.hostname else p.hostname
        if p.port is not None:
            host += ":" + str(p.port)
        target = (p.path or "/") + ("?" + p.query if p.query else "")
        if any(ord(c) > 127 for c in target):
            raise ValueError
        header = f"POST {target} HTTP/1.1\r\nHost: {host}\r\nContent-Length: {len(payload)}\r\nConnection: close\r\nAccept-Encoding: identity\r\n"
        if not any(k.lower() == "content-type" for k, _ in safe_headers):
            header += "Content-Type: application/json\r\n"
        header += "".join(f"{k}: {v}\r\n" for k, v in safe_headers) + "\r\n"
        wire = header.encode("ascii") + payload
        while wire:
            sent = _io(sock, deadline, "send", wire)
            if not sent:
                raise OSError
            wire = wire[sent:]
        pending = bytearray()
        while b"\r\n\r\n" not in pending:
            chunk = _io(sock, deadline, "recv")
            if not chunk:
                raise _ProtocolError
            pending.extend(chunk)
            if len(pending) > 65536 and b"\r\n\r\n" not in pending:
                raise _ProtocolError
        head, pending_bytes = bytes(pending).split(b"\r\n\r\n", 1)
        if len(head) > 65536:
            raise _ProtocolError
        lines = head.split(b"\r\n")
        match = re.fullmatch(rb"HTTP/1\.[01] ([0-9]{3})(?: .*)?", lines[0])
        if not match:
            raise _ProtocolError
        result["http_status"] = int(match.group(1))
        fields = {}
        for line in lines[1:]:
            key, sep, value = line.partition(b":")
            if not sep or not re.fullmatch(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]+", key):
                raise _ProtocolError
            fields.setdefault(key.lower(), []).append(value.strip())
        content = fields.get(b"content-type", [b""])[0].split(b";", 1)[0].strip().lower()
        if re.fullmatch(rb"[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+", content):
            result["content_type"] = content.decode("ascii")
        encoding = fields.get(b"content-encoding", [])
        if len(encoding) > 1 or encoding and encoding[0].lower() != b"identity":
            raise _UnsupportedContentEncoding
        lengths = fields.get(b"content-length", [])
        transfer = fields.get(b"transfer-encoding", [])
        if len(lengths) > 1 or len(transfer) > 1 or lengths and transfer:
            raise _ProtocolError
        if lengths and not re.fullmatch(rb"[0-9]+", lengths[0]):
            raise _ProtocolError
        if transfer and transfer[0].lower() != b"chunked":
            raise _ProtocolError
        remaining = int(lengths[0]) if lengths else None
        pending = bytearray(pending_bytes)
        def receive():
            chunk = _io(sock, deadline, "recv")
            if not chunk:
                raise EOFError
            pending.extend(chunk)
        def take(count):
            while len(pending) < count:
                receive()
            value = bytes(pending[:count])
            del pending[:count]
            return value
        def append(data):
            room = max_bytes - len(body)
            body.extend(data[:room])
            if len(data) > room:
                raise OverflowError
        if transfer:
            while True:
                while b"\r\n" not in pending:
                    if len(pending) > 8192:
                        raise _ProtocolError
                    receive()
                line, rest = bytes(pending).split(b"\r\n", 1)
                pending = bytearray(rest)
                size = line.split(b";", 1)[0]
                if not re.fullmatch(rb"[0-9a-fA-F]+", size) or len(size) > 16:
                    raise _ProtocolError
                count = int(size, 16)
                if not count:
                    # Consume bounded trailers; require terminating CRLF.
                    while True:
                        while b"\r\n" not in pending:
                            if len(pending) > 65536:
                                raise _ProtocolError
                            receive()
                        line, rest = bytes(pending).split(b"\r\n", 1)
                        pending = bytearray(rest)
                        if not line:
                            break
                    break
                while count:
                    if not pending:
                        receive()
                    n = min(count, len(pending), max_bytes - len(body) + 1)
                    append(take(n))
                    count -= n
                if take(2) != b"\r\n":
                    raise _ProtocolError
        elif remaining is not None:
            while remaining:
                if not pending:
                    receive()
                n = min(remaining, len(pending), max_bytes - len(body) + 1)
                append(take(n))
                remaining -= n
        else:
            while True:
                if pending:
                    append(take(min(len(pending), max_bytes - len(body) + 1)))
                try:
                    receive()
                except EOFError:
                    break
        result["body_complete"] = True
        if not 200 <= result["http_status"] < 300:
            result["errors"].append(_error("http_status", "$.http_status", "Endpoint returned a non-success HTTP status"))
        elif result["content_type"] == "text/event-stream":
            result["events"], errors = parse_sse(bytes(body))
            result["errors"].extend(errors)
            result["response"], errors = reconstruct_response(result["events"])
            result["errors"].extend(errors)
        elif result["content_type"] == "application/json":
            result["response"], errors = decode_json(bytes(body))
            result["errors"].extend(errors)
        else:
            result["errors"].append(_error("content_type", "$.content_type", "Unexpected response content type"))
    except TimeoutError:
        result["errors"].append(_error("timeout", "$", "Request exceeded its total deadline"))
    except OverflowError:
        result["errors"].append(_error("body_too_large", "$.body", "Response exceeds the byte limit"))
    except EOFError:
        result["errors"].append(_error("truncated_body", "$.body", "Response body ended early"))
    except _ProtocolError:
        result["errors"].append(_error("invalid_http", "$", "Invalid HTTP response"))
    except _UnsupportedContentEncoding:
        result["errors"].append(_error("unsupported_content_encoding", "$.body", "Unsupported response content encoding"))
    except (ValueError, TypeError, UnicodeError, OverflowError):
        result["errors"].append(_error("invalid_request", "$", "Invalid endpoint, request, headers, or limits"))
    except (OSError, ssl.SSLError):
        result["errors"].append(_error("transport_error", "$", "HTTP transport failed"))
    finally:
        if sock is not None:
            sock.close()
        result["body"] = bytes(body)
        result["wire_sha256"] = hashlib.sha256(result["body"]).hexdigest()
        result["elapsed_s"] = time.monotonic() - start
    return result
