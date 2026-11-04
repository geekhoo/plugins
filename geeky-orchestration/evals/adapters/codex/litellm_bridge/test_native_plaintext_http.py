"""Loopback fake upstream checks for native plaintext wire mode; no models."""
from contextlib import contextmanager
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

import pytest

from litellm_bridge.native_plaintext import NativePlaintextState
from litellm_bridge.server import make_server
from litellm_bridge.test_native_plaintext import request, response_call

KEY = 'native-offline-fixture-key'


@contextmanager
def servers(*, stream=False, response_mode='normal', max_body=100000):
    captured = []

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            captured.append((self.path, dict(self.headers), body))
            if response_mode == 'redirect':
                self.send_response(307)
                self.send_header('Location', 'http://127.0.0.1:1/not-followed')
                self.end_headers()
                return
            call = response_call()
            if response_mode == 'opaque':
                call['encrypted_content'] = 'unverified-opaque-envelope'
            if stream:
                events = [
                    {'type': 'response.output_item.added', 'output_index': 0,
                     'item': {**call, 'arguments': '', 'status': 'in_progress'}},
                    {'type': 'response.function_call_arguments.delta', 'item_id': 'fc_fixture',
                     'output_index': 0, 'delta': call['arguments']},
                    {'type': 'response.output_item.done', 'output_index': 0, 'item': call},
                    {'type': 'response.completed', 'response': {'id': 'resp_fixture', 'output': [call]}},
                ]
                raw = ''.join('event: ' + e['type'] + '\nid: fixture-id\ndata: ' + json.dumps(e) + '\n\n'
                              for e in events).encode() + b'data: [DONE]\n\n'
                content_type = 'text/event-stream'
            else:
                raw = (b'{"private-invalid-upstream-payload":' if response_mode == 'invalid-json'
                       else json.dumps({'id': 'resp_fixture', 'output': [call]}).encode())
                content_type = 'application/json'
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
    state = NativePlaintextState()
    proxy = make_server(f'http://127.0.0.1:{upstream.server_port}/v1', KEY,
                        wire_mode='native-plaintext', state=state, timeout=3, max_body=max_body)
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (upstream, proxy)]
    for thread in threads:
        thread.start()
    try:
        yield proxy, state, captured
    finally:
        for server in (proxy, upstream):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(3)


def post(server, body, *, key=KEY):
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    try:
        connection.request('POST', '/v1/responses', json.dumps(body), {
            'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
            'User-Agent': 'Codex-native-offline-fixture', 'X-Untrusted-Routing': 'must-not-forward'})
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


@pytest.mark.parametrize('stream', [False, True])
def test_native_http_preserves_namespaces_affinity_ids_and_plaintext_contract(stream):
    body = request()
    body.update(stream=stream, client_metadata={'session_id': 'fixture-session-affinity'})
    with servers(stream=stream) as (proxy, state, captured):
        status, raw = post(proxy, body)
        assert status == 200
        assert captured[0][0] == '/v1/responses'
        headers, forwarded = captured[0][1:]
        assert headers['Authorization'] == 'Bearer ' + KEY
        assert headers['User-Agent'] == 'Codex-native-offline-fixture'
        assert 'X-Untrusted-Routing' not in headers
        assert forwarded['client_metadata'] == body['client_metadata']
        assert forwarded['input'] == body['input']
        assert forwarded['tools'][0]['name'] == 'collaboration'
        assert forwarded['tools'][0]['tools'][0]['name'] == 'spawn_agent'
        assert 'encrypted' not in forwarded['tools'][0]['tools'][0]['parameters']['properties']['message']
        if stream:
            events = [json.loads(line[6:]) for line in raw.decode().splitlines()
                      if line.startswith('data: ') and line != 'data: [DONE]']
            assert events[0]['item']['encrypted_function_args'] == []
            assert events[1]['delta'] == response_call()['arguments']
            assert events[2]['item']['encrypted_function_args'] == []
            assert events[2]['item']['namespace'] == 'collaboration'
            assert b'id: fixture-id' in raw and raw.endswith(b'data: [DONE]\n\n')
        else:
            assert json.loads(raw)['output'][0] == {**response_call(), 'encrypted_function_args': []}
        assert state.recover('Literal task value') == 'Literal task value'
        assert KEY.encode() not in raw


@pytest.mark.parametrize('stream', [False, True])
def test_native_http_rejects_opaque_response_without_learning_or_content_leak(stream):
    body = request()
    body['stream'] = stream
    with servers(stream=stream, response_mode='opaque') as (proxy, state, captured):
        status, raw = post(proxy, body)
        assert status == (200 if stream else 502)
        assert b'bridge_mapping_error' in raw
        assert b'unverified-opaque-envelope' not in raw
        assert b'response.completed' not in raw
        assert not state._known and len(captured) == 1


@pytest.mark.parametrize('failure,status', [('auth', 401), ('unknown-content', 400), ('body-limit', 413)])
def test_native_http_rejects_invalid_requests_before_upstream(failure, status):
    body = request()
    if failure == 'unknown-content':
        body['input'].append({'type': 'function_call_output', 'call_id': 'call_unknown', 'output': [
            {'type': 'encrypted_content', 'encrypted_content': 'unknown-opaque-content'}]})
    with servers(max_body=100 if failure == 'body-limit' else 100000) as (proxy, state, captured):
        actual, raw = post(proxy, body, key='wrong-key' if failure == 'auth' else KEY)
        assert actual == status and not captured and not state._known
        assert b'unknown-opaque-content' not in raw and KEY.encode() not in raw


def test_native_http_does_not_follow_upstream_redirects():
    with servers(response_mode='redirect') as (proxy, _, captured):
        status, raw = post(proxy, request())
        assert status == 502 and len(captured) == 1
        assert b'upstream_http_error' in raw


@pytest.mark.parametrize('case,phase,status,started,error_kind', [
    ('request', 'request_map', 400, False, 'MappingError'),
    ('response', 'upstream_response_map', 502, False, 'MappingError'),
    ('stream', 'upstream_stream_map', 200, True, 'MappingError'),
    ('invalid-json', 'upstream_response_decode', 502, False, 'JSONDecodeError'),
])
def test_mapping_diagnostics_identify_phase_without_logging_content(case, phase, status, started, error_kind, capsys):
    body = request()
    body['stream'] = case == 'stream'
    if case == 'request':
        body['input'].append({'type': 'function_call_output', 'call_id': 'call_unknown', 'output': [
            {'type': 'encrypted_content', 'encrypted_content': 'unknown-opaque-content'}]})
    response_mode = 'invalid-json' if case == 'invalid-json' else 'opaque'
    with servers(stream=case == 'stream', response_mode=response_mode) as (proxy, _, captured):
        actual, raw = post(proxy, body)
        assert actual == status
        assert b'bridge_mapping_error' in raw
        assert len(captured) == (0 if case == 'request' else 1)
    err = capsys.readouterr().err
    events = [event for event in map(json.loads, err.splitlines()) if event['event'] == 'bridge_mapping_error']
    assert len(events) == 1
    event = events[0]
    assert set(event) == {'event', 'phase', 'error', 'diagnostic_id', 'stream_started', 'ts'}
    assert event['event'] == 'bridge_mapping_error'
    assert event['phase'] == phase
    assert event['error'] == error_kind
    assert event['stream_started'] is started
    assert len(event['diagnostic_id']) == 32
    assert int(event['diagnostic_id'], 16) >= 0
    assert KEY not in err
    assert 'unknown-opaque-content' not in err
    assert 'unverified-opaque-envelope' not in err
    assert 'private-invalid-upstream-payload' not in err


@pytest.mark.parametrize('payload,error_kind', [
    (b'{"private-request-sentinel":', 'JSONDecodeError'),
    (b'\xffprivate-request-sentinel', 'UnicodeError'),
])
def test_invalid_request_encoding_has_safe_diagnostics(payload, error_kind, capsys):
    with servers() as (proxy, _, captured):
        connection = http.client.HTTPConnection('127.0.0.1', proxy.server_port, timeout=5)
        try:
            connection.request('POST', '/v1/responses', payload, {
                'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
            response = connection.getresponse()
            assert response.status == 400 and b'bridge_mapping_error' in response.read()
        finally:
            connection.close()
        assert not captured
    err = capsys.readouterr().err
    event = next(event for event in map(json.loads, err.splitlines()) if event['event'] == 'bridge_mapping_error')
    assert event['phase'] == 'request_decode'
    assert event['error'] == error_kind and event['stream_started'] is False
    assert 'private-request-sentinel' not in err and KEY not in err
