"""Offline proof: the pinned tracer against a loopback collector. No provider call and no Langfuse write."""
import gzip
import http.server
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse

import pytest

HERE = Path(__file__).resolve().parent
TOOLS = Path(os.environ.get('GEEKY_EVAL_TOOLS', r'C:\repos\.eval-tools'))
PINS = json.loads((HERE / 'pins.json').read_text())
ORIGINAL = TOOLS / f"langfuse/codex-tracing/{PINS['codex_plugin']['version']}/dist/index.mjs"
SESSION = 'codex-mxc-win-c2-run'
THREAD, TURN = '019a0000-0000-7000-8000-000000000001', 'turn-1'

spec = importlib.util.spec_from_file_location('codex_flush', HERE / 'codex-flush.py')
flush = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flush)


def write_ledger(rollout, *entries):
    Path(f'{rollout}.langfuse-attempts').write_text(''.join(json.dumps(e) + '\n' for e in entries), encoding='utf-8')


def attempt(turns=(TURN,), spans=('a', 'b')):
    return {'event': 'attempt', 'turn_ids': list(turns), 'span_ids': list(spans)}


def sidecar(rollout):
    path = Path(f'{rollout}.langfuse')
    return path.read_text(encoding='utf-8').split() if path.exists() else []


def test_turn_is_marked_only_when_every_attempted_span_is_readable(tmp_path):
    rollout = tmp_path / 'rollout.jsonl'
    write_ledger(rollout, attempt(), {'event': 'flush', 'ok': False, 'elapsed_ms': 30001, 'error': 'Timeout'})
    assert flush.mark_delivered_turns(rollout, lambda: {'a', 'b', 'unrelated'}) == [TURN]
    assert sidecar(rollout) == [TURN]


def test_partial_delivery_stays_unmarked_for_replay_after_the_settle_window(tmp_path):
    rollout = tmp_path / 'rollout.jsonl'
    write_ledger(rollout, attempt())
    now = [0.0]
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    assert flush.mark_delivered_turns(rollout, lambda: {'a'}, settle_seconds=30, poll_seconds=10,
                                      sleep=sleep, clock=lambda: now[0]) == []
    assert sidecar(rollout) == [] and sleeps == [10, 10, 10]


def test_late_ingestion_is_confirmed_by_a_later_poll(tmp_path):
    rollout = tmp_path / 'rollout.jsonl'
    write_ledger(rollout, attempt())
    reads = iter([set(), {'a'}, {'a', 'b'}])
    assert flush.mark_delivered_turns(rollout, lambda: next(reads), sleep=lambda _: None) == [TURN]


@pytest.mark.parametrize('error', [OSError('down'), ValueError('bad json')])
def test_unreadable_langfuse_fails_open_to_replay(tmp_path, error):
    rollout = tmp_path / 'rollout.jsonl'
    write_ledger(rollout, attempt())

    def read():
        raise error

    assert flush.mark_delivered_turns(rollout, read, settle_seconds=0) == []
    assert sidecar(rollout) == []


def test_no_ledger_or_marked_turn_or_no_credentials_needs_no_read(tmp_path):
    def forbidden():
        raise AssertionError('Langfuse must not be read')

    rollout = tmp_path / 'rollout.jsonl'
    assert flush.mark_delivered_turns(rollout, forbidden) == []     # the hook never reached a flush
    write_ledger(rollout, attempt(turns=[None, '']), {'event': 'attempt', 'turn_ids': [TURN], 'span_ids': []})
    assert flush.mark_delivered_turns(rollout, forbidden) == []     # nothing that could be proved
    write_ledger(rollout, attempt())
    assert flush.mark_delivered_turns(rollout, None) == []          # no way to check
    Path(f'{rollout}.langfuse').write_text(f'{TURN}\n', encoding='utf-8')
    assert flush.mark_delivered_turns(rollout, forbidden) == []     # already marked
    assert sidecar(rollout) == [TURN]


def test_reader_needs_session_and_all_keys():
    full = {'GEEKY_SESSION_ID': 's', 'LANGFUSE_CODEX_PUBLIC_KEY': 'p', 'LANGFUSE_SECRET_KEY': 'k', 'LANGFUSE_BASE_URL': 'http://x'}
    assert callable(flush.reader_from_environment(full))
    for missing in full:
        assert flush.reader_from_environment({k: v for k, v in full.items() if k != missing}) is None


def test_runner_sets_the_span_processor_timeout_to_match_the_exporter():
    source = (HERE / 'telemetry.ps1').read_text(encoding='utf-8')
    assert "'LANGFUSE_TIMEOUT=300'" in source and "'OTEL_BSP_EXPORT_TIMEOUT=300000'" in source


class Collector:
    """OTLP sink plus the v2 read path, serving only what it stored."""

    def __init__(self, delay=0.0, drop=0):
        self.delay, self.drop = delay, drop
        self.posts, self.ids, self.reads = [], [], 0
        collector = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def read_body(self):
                if self.headers.get('Content-Length'):
                    return self.rfile.read(int(self.headers['Content-Length']))
                body = b''
                while size := int(self.rfile.readline().strip(), 16):
                    body += self.rfile.read(size)
                    self.rfile.readline()
                self.rfile.readline()
                return body

            def do_POST(self):
                body = self.read_body()
                if self.headers.get('Content-Encoding') == 'gzip':
                    body = gzip.decompress(body)
                spans = [span['spanId'] for resource in json.loads(body)['resourceSpans']
                         for scope in resource['scopeSpans'] for span in scope['spans']]
                collector.posts.append(spans)
                time.sleep(collector.delay)
                collector.ids.extend(spans[collector.drop:])
                collector.drop = 0
                self.respond(b'{}')

            def do_GET(self):
                query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                assert query['sessionId'] == [SESSION]
                collector.reads += 1
                self.respond(json.dumps({'data': [{'id': i} for i in collector.ids], 'meta': {}}).encode())

            def respond(self, body):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def stack(tmp_path):
    node = shutil.which('node')
    if not node or not ORIGINAL.exists():
        pytest.skip('Needs Node and the pinned tracer from install-telemetry-tools.ps1')
    tracer = tmp_path / 'index.geeky.mjs'
    subprocess.run([node, str(HERE / 'patch-codex-tracer.mjs'), str(ORIGINAL), str(tracer)], check=True)
    rollout = tmp_path / 'rollout.jsonl'
    stamp = '2026-11-04T06:00:0{}.000Z'
    rows = [('session_meta', {'id': THREAD, 'timestamp': stamp.format(0), 'cwd': str(tmp_path), 'originator': 'test', 'cli_version': '0'}),
            ('event_msg', {'type': 'task_started', 'turn_id': TURN}),
            ('event_msg', {'type': 'user_message', 'message': 'hello'}),
            ('response_item', {'type': 'function_call', 'name': 'shell', 'call_id': 'c1', 'arguments': '{}'}),
            ('response_item', {'type': 'function_call_output', 'call_id': 'c1', 'output': 'ok'}),
            ('event_msg', {'type': 'agent_message', 'message': 'done'}),
            ('event_msg', {'type': 'task_complete', 'turn_id': TURN})]
    rollout.write_text(''.join(json.dumps({'timestamp': stamp.format(i), 'type': kind, 'payload': item}) + '\n'
                               for i, (kind, item) in enumerate(rows)), encoding='utf-8')
    payload = tmp_path / 'payload.json'
    payload.write_text(json.dumps({'session_id': THREAD, 'transcript_path': str(rollout), 'hook_event_name': 'Stop'}))

    def env(collector, **extra):
        return {**os.environ, 'TRACE_TO_LANGFUSE': 'true', 'LANGFUSE_PUBLIC_KEY': 'pk-offline', 'LANGFUSE_SECRET_KEY': 'sk-offline',
                'LANGFUSE_BASE_URL': collector.url, 'GEEKY_SESSION_ID': SESSION, 'GEEKY_AGENT_FAMILY': 'codex-mxc-win',
                'LANGFUSE_TIMEOUT': '300', 'OTEL_EXPORTER_OTLP_PROTOCOL': 'http/json', **extra}

    def hook(collector, **extra):
        stop = {'session_id': THREAD, 'transcript_path': str(rollout), 'hook_event_name': 'Stop', 'turn_id': TURN}
        subprocess.run([node, str(tracer)], input=json.dumps(stop).encode(), env=env(collector, **extra), timeout=60, check=True)

    def replay(collector):
        code = ('import importlib.util,sys;s=importlib.util.spec_from_file_location("f",sys.argv[1]);m=importlib.util.module_from_spec(s);'
                's.loader.exec_module(m);sys.exit(m.main(sys.argv[1:],settle_seconds=0))')
        return subprocess.run([sys.executable, '-c', code, str(HERE / 'codex-flush.py'), node, str(tracer), str(payload)],
                              env=env(collector), timeout=60, capture_output=True, text=True)

    return rollout, hook, replay


def ledger_entries(rollout):
    return [json.loads(line) for line in Path(f'{rollout}.langfuse-attempts').read_text(encoding='utf-8').splitlines()]


def test_slow_flush_leaves_no_sidecar_and_replay_does_not_deliver_twice(stack):
    rollout, hook, replay = stack
    collector = Collector(delay=1.0)
    try:
        hook(collector, OTEL_BSP_EXPORT_TIMEOUT='100')       # the 4 November path: batch outlives the processor timeout
        assert sidecar(rollout) == [] and collector.ids
        attempted, outcome = ledger_entries(rollout)
        assert attempted['turn_ids'] == [TURN] and sorted(attempted['span_ids']) == sorted(collector.ids)
        assert outcome['ok'] is False and outcome['error'] == 'Timeout'
        posts = len(collector.posts)
        result = replay(collector)
        assert result.returncode == 0, result.stderr
        assert collector.reads >= 1 and len(collector.posts) == posts
        assert sidecar(rollout) == [TURN]
        assert 'already delivered' in result.stdout and 'ok=False' in result.stdout
        assert 'pk-offline' not in result.stdout + result.stderr and 'sk-offline' not in result.stdout + result.stderr
    finally:
        collector.close()


def test_span_lost_by_a_timed_out_flush_is_replayed_with_the_same_ids(stack):
    rollout, hook, replay = stack
    collector = Collector(delay=1.0, drop=1)
    try:
        hook(collector, OTEL_BSP_EXPORT_TIMEOUT='100')
        assert sidecar(rollout) == []
        first = collector.posts[0]
        result = replay(collector)
        assert result.returncode == 0, result.stderr
        assert len(collector.posts) == 2 and sorted(collector.posts[1]) == sorted(first)
        assert sidecar(rollout) == [TURN]
    finally:
        collector.close()


def test_runner_timeout_value_lets_the_same_slow_flush_write_its_sidecar(stack):
    rollout, hook, replay = stack
    collector = Collector(delay=1.0)
    try:
        hook(collector, OTEL_BSP_EXPORT_TIMEOUT='300000')
        assert sidecar(rollout) == [TURN]
        attempted, outcome = ledger_entries(rollout)
        assert outcome['ok'] is True and 'error' not in outcome
        assert len(attempted['span_ids']) == len(collector.ids)
        posts = len(collector.posts)
        assert replay(collector).returncode == 0
        assert collector.reads == 0 and len(collector.posts) == posts
    finally:
        collector.close()
