"""Offline proof of the D111 identity: the pinned tracers, through identity-smoke.py, against a loopback collector."""
import base64
import gzip
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading

import pytest

HERE = Path(__file__).resolve().parent
TOOLS = Path(os.environ.get('GEEKY_EVAL_TOOLS', r'C:\repos\.eval-tools'))
PINS = json.loads((HERE / 'pins.json').read_text())
CODEX_ORIGINAL = TOOLS / f"langfuse/codex-tracing/{PINS['codex_plugin']['version']}/dist/index.mjs"
CLAUDE_HOOK = TOOLS / f"langfuse/claude-hook/{PINS['claude_hook']['commit']}/langfuse_hook.py"
VENV = TOOLS / 'langfuse-py'
STAMP = '20261105T000000Z'

DECODE = """
import base64, json, site, sys
site.addsitedir(sys.argv[1])
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
for line in sys.stdin:
    message = ExportTraceServiceRequest()
    message.ParseFromString(base64.b64decode(line))
    print(json.dumps(MessageToDict(message)))
"""


class Collector:
    """Accepts OTLP posts on loopback and keeps the raw bodies. Nothing leaves this machine."""

    def __init__(self):
        bodies = self.bodies = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
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
                bodies.append(gzip.decompress(body) if self.headers.get('Content-Encoding') == 'gzip' else body)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'{}')

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def scalar(value):
    return next(iter(value.values())) if value else None


def spans_from(documents):
    rows = []
    for document in documents:
        for resource in document['resourceSpans']:
            for scope in resource['scopeSpans']:
                for span in scope['spans']:
                    rows.append({**span, 'attrs': {a['key']: scalar(a['value']) for a in span.get('attributes', [])}})
    return rows


def run_smoke(tmp_path, collector, harness, extra):
    metadata = {'mock': 'true', 'harness': harness}
    env = {k: v for k, v in os.environ.items() if not k.startswith('LANGFUSE_')}
    env.update(TRACE_TO_LANGFUSE='true', LANGFUSE_PUBLIC_KEY='pk-offline', LANGFUSE_SECRET_KEY='sk-offline',
               LANGFUSE_BASE_URL=collector.url, LANGFUSE_TIMEOUT='60', LANGFUSE_TRACING_ENVIRONMENT='mxc-win',
               GEEKY_SESSION_ID=f'c0-wordstat/{harness}/{STAMP}', GEEKY_RUN_METADATA=json.dumps(metadata),
               GEEKY_AGENT_FAMILY=f"{'codex' if harness == 'codex' else 'claude'}-mxc-win", GEEKY_RUN_TAGS='["geeky-eval"]')
    env.update(extra.pop('env', {}))
    command = [sys.executable, str(HERE / 'identity-smoke.py'), '--home', str(tmp_path / 'home'), '--harness', harness, *extra['args']]
    done = subprocess.run(command, env=env, capture_output=True, text=True, timeout=240)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads(done.stdout.strip().splitlines()[-1])


def assert_identity(harness, report, spans):
    """Each actor owns one trace, under the exact session, user and trace name. Native IDs sit only in metadata."""
    assert spans
    session = f'c0-wordstat/{harness}/{STAMP}'
    by_trace = {}
    for span in spans:
        by_trace.setdefault(span['traceId'], []).append(span)
    assert len(by_trace) == 3
    seen = {}
    for rows in by_trace.values():
        attrs = [row['attrs'] for row in rows]
        assert {a.get('session.id', a.get('langfuse.session.id')) for a in attrs} == {session}
        users = {a.get('user.id', a.get('langfuse.user.id')) for a in attrs}
        assert len(users) == 1
        user = users.pop()
        roots = [a for a in attrs if a.get('langfuse.observation.metadata.agent_id')]
        agent_ids = {a['langfuse.observation.metadata.agent_id'] for a in roots}
        assert len(agent_ids) == 1
        agent_id = agent_ids.pop()
        role = next(r for r, value in report['actors'].items() if value == agent_id)
        names = {a['langfuse.trace.name'] for a in attrs if a.get('langfuse.trace.name')}
        seen[role] = (user, names)
        assert agent_id not in user
    assert seen == {role: (f'{harness}/{role}', {role}) for role in ('orchestrator', 'coder', 'reviewer')}
    assert report['expected']['coder'] == {'user_id': f'{harness}/coder', 'trace_name': 'coder'}


def test_codex_tracer_emits_the_new_identity(tmp_path):
    node = shutil.which('node')
    if not node or not CODEX_ORIGINAL.exists():
        pytest.skip('Needs Node and the pinned tracer from install-telemetry-tools.ps1')
    tracer = tmp_path / 'index.geeky.mjs'
    subprocess.run([node, str(HERE / 'patch-codex-tracer.mjs'), str(CODEX_ORIGINAL), str(tracer)], check=True)
    collector = Collector()
    try:
        report = run_smoke(tmp_path, collector, 'codex', {'args': ['--node', node, '--tracer', str(tracer)],
                                                          'env': {'OTEL_EXPORTER_OTLP_PROTOCOL': 'http/json'}})
    finally:
        collector.close()
    assert_identity('codex', report, spans_from(json.loads(body) for body in collector.bodies))


def test_claude_hook_emits_the_new_identity(tmp_path):
    if not CLAUDE_HOOK.exists() or not (VENV / 'pyvenv.cfg').exists():
        pytest.skip('Needs the pinned hook and venv from install-telemetry-tools.ps1')
    home = re.search(r'^home\s*=\s*(.+)$', (VENV / 'pyvenv.cfg').read_text(), re.M).group(1).strip()
    python = str(Path(home) / 'python.exe') if os.name == 'nt' else str(VENV / 'bin/python')
    venv_python = VENV / 'Scripts/python.exe' if os.name == 'nt' else VENV / 'bin/python'
    purelib = subprocess.run([str(venv_python), '-c', 'import sysconfig; print(sysconfig.get_paths()["purelib"])'],
                             capture_output=True, text=True, check=True).stdout.strip()
    command = [python, str(HERE / 'claude-hook-boot.py'), purelib, str(CLAUDE_HOOK)]
    collector = Collector()
    try:
        report = run_smoke(tmp_path, collector, 'claude-code', {
            'args': ['--hook-command', json.dumps(command)],
            'env': {'CC_LANGFUSE_STATE_DIR': str(tmp_path / 'state'), 'LANGFUSE_USER_ID': 'claude-code/orchestrator',
                    'GEEKY_TRACE_NAME': 'orchestrator', 'CC_LANGFUSE_TRACE_TAGS': '["geeky-eval"]'}})
    finally:
        collector.close()
    decoded = subprocess.run([python, '-c', DECODE, purelib], capture_output=True, text=True, check=True,
                             input=''.join(base64.b64encode(body).decode() + '\n' for body in collector.bodies))
    assert_identity('claude-code', report, spans_from(json.loads(line) for line in decoded.stdout.splitlines()))
