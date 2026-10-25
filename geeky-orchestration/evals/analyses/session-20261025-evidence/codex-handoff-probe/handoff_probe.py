"""Model-free probe: does a Codex spawn_agent task reach the rollout in plaintext?

Runs the real Codex CLI against a scripted loopback Responses server. The main thread spawns one
child with a marker task, waits, and finishes; the child replies. Prints, per scenario, the
multi-agent version Codex offered and where the marker text landed in the rollouts.
"""
import json, os, subprocess, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CODEX = sys.argv[1]
MARK = 'PROBE_CHILD_TASK_7f3a'


def run(name, model, overrides=(), marker_field=False):
    state = {'main': 0, 'waits': 0, 'requests': []}
    lock = threading.Lock()

    def out_item(data):
        inputs = data.get('input', [])
        text = json.dumps([r for r in inputs if r.get('type') in ('agent_message', 'message')])
        is_child = MARK in text and not any(r.get('type') == 'function_call' and r.get('name') == 'spawn_agent' for r in inputs)
        if is_child:
            return {'type': 'message', 'role': 'assistant', 'id': 'mc', 'content': [{'type': 'output_text', 'text': 'PROBE_CHILD_DONE'}]}
        state['main'] += 1
        if state['main'] == 1:
            item = {'type': 'function_call', 'call_id': 'call_spawn', 'name': 'spawn_agent', 'namespace': 'collaboration',
                    'arguments': json.dumps({'task_name': 'probe_child', 'message': MARK + ': reply PROBE_CHILD_DONE', 'fork_turns': 'none'})}
            if marker_field:
                item['encrypted_function_args'] = []
            return item
        if 'PROBE_CHILD_DONE' in json.dumps(inputs) or state['waits'] >= 5:
            return {'type': 'message', 'role': 'assistant', 'id': 'mm', 'content': [{'type': 'output_text', 'text': 'PROBE_MAIN_DONE'}]}
        state['waits'] += 1
        return {'type': 'function_call', 'call_id': f'call_wait{state["waits"]}', 'name': 'wait_agent', 'namespace': 'collaboration',
                'arguments': json.dumps({'timeout_ms': 5000})}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            b = b'{"models": []}'
            self.send_response(200); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            with lock:
                state['requests'].append(data)
                item = out_item(data)
            ev = [{'type': 'response.created', 'response': {'id': 'r'}}, {'type': 'response.output_item.done', 'item': item},
                  {'type': 'response.completed', 'response': {'id': 'r', 'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}}]
            b = ''.join('event: %s\ndata: %s\n\n' % (e['type'], json.dumps(e)) for e in ev).encode()
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.send_header('Content-Length', str(len(b)))
            self.send_header('Connection', 'close'); self.end_headers(); self.wfile.write(b)

    server = ThreadingHTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    home = Path(tempfile.mkdtemp(dir=os.getcwd())); ws = tempfile.mkdtemp(); subprocess.run(['git', 'init', '-q', ws])
    provider = ('{name="probe",base_url="http://127.0.0.1:%d/v1",wire_api="responses",requires_openai_auth=false,'
                'supports_websockets=false,request_max_retries=0,stream_max_retries=0}' % server.server_port)
    cmd = [CODEX, '--no-daemon', 'exec', '--json', '--sandbox', 'danger-full-access', '--skip-git-repo-check', '--cd', ws,
           '-c', f'model="{model}"', '-c', 'model_provider="probe"', '-c', 'model_providers.probe=' + provider,
           '-c', 'features.multi_agent=true']
    for o in overrides:
        cmd += ['-c', o]
    cmd.append('Spawn one sub-agent.')
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180, env={**os.environ, 'CODEX_HOME': str(home)})
    server.shutdown()
    first = json.dumps(state['requests'][0]) if state['requests'] else ''
    version = 'v2' if '"collaboration"' in first and 'followup_task' in first else ('v1?' if 'spawn_agent' in first else 'none')
    found = []
    for f in sorted(home.rglob('rollout-*.jsonl')):
        meta = None
        for line in f.read_text(encoding='utf-8').splitlines():
            row = json.loads(line); p = row.get('payload') or {}
            if row.get('type') == 'session_meta':
                meta = 'child' if p.get('parent_thread_id') else 'main'
            if MARK not in line:
                continue
            if p.get('type') == 'agent_message':
                kinds = sorted({c.get('type') for c in p.get('content', []) if MARK in json.dumps(c)})
                found.append(f'{meta}:agent_message[{"+".join(kinds)}]')
            else:
                found.append(f'{meta}:{row.get("type")}/{p.get("type") or ""}')
    child_got = any(MARK in json.dumps(q.get('input', [])) and q is not state['requests'][0] and
                    not any(x.get('type') == 'function_call' and x.get('name') == 'spawn_agent' for x in q.get('input', []))
                    for q in state['requests'])
    print(f'{name:28} exit={r.returncode} offered={version:4} requests={len(state["requests"])} child_saw_task={child_got}')
    print('    rollout marker locations:', sorted(set(found)) or 'none')
    if r.returncode:
        print('    stderr:', r.stderr.strip()[-300:])


catalog = json.loads(subprocess.run([CODEX, 'debug', 'models'], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                                    env={**os.environ, 'CODEX_HOME': tempfile.mkdtemp()}).stdout)
for m in catalog['models']:
    if m['slug'] == 'gpt-6.1-sol':
        m['multi_agent_version'] = 'v1'
cat_path = Path(os.getcwd(), 'catalog-v1.json'); cat_path.write_text(json.dumps(catalog))
run('A catalog v2 (gpt-6.1-sol)', 'gpt-6.1-sol')
run('B v2 + encrypted_function_args=[]', 'gpt-6.1-sol', marker_field=True)
run('C catalog override -> v1', 'gpt-6.1-sol', [f'model_catalog_json="{cat_path}"'])
run('D unknown slug zen/gpt-6.1-sol', 'zen/gpt-6.1-sol')
run('E features.multi_agent_v2=false', 'gpt-6.1-sol', ['features.multi_agent_v2=false'])
