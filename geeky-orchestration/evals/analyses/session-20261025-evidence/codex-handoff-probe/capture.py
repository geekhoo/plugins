import json, os, subprocess, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
codex, model, extra = sys.argv[1], sys.argv[2], sys.argv[3:]
seen = []
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        b = b'{"models": []}'; self.send_response(200); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers['Content-Length']))); seen.append(d)
        ev = [{'type': 'response.created', 'response': {'id': 'r1'}},
              {'type': 'response.output_item.done', 'item': {'type': 'message', 'role': 'assistant', 'id': 'm', 'content': [{'type': 'output_text', 'text': 'done'}]}},
              {'type': 'response.completed', 'response': {'id': 'r1', 'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}}]
        b = ''.join('event: %s\ndata: %s\n\n' % (e['type'], json.dumps(e)) for e in ev).encode()
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
s = ThreadingHTTPServer(('127.0.0.1', 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
home = tempfile.mkdtemp(); ws = tempfile.mkdtemp(); subprocess.run(['git', 'init', '-q', ws])
prov = '{name="probe",base_url="http://127.0.0.1:%d/v1",wire_api="responses",requires_openai_auth=false,supports_websockets=false,request_max_retries=0,stream_max_retries=0}' % s.server_port
cmd = [codex, '--no-daemon', 'exec', '--json', '--sandbox', 'danger-full-access', '--skip-git-repo-check', '--cd', ws,
       '-c', 'model="%s"' % model, '-c', 'model_provider="probe"', '-c', 'model_providers.probe=' + prov,
       '-c', 'features.multi_agent=true'] + sum((['-c', x] for x in extra), []) + ['hello']
try:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=40, env={**os.environ, 'CODEX_HOME': home, 'RUST_LOG': 'warn'})
except subprocess.TimeoutExpired as e:
    print('TIMEOUT requests=', len(seen)); print((e.stderr or b'')[-1500:].decode('utf-8','replace') if isinstance(e.stderr, bytes) else str(e.stderr)[-1500:]); print((e.stdout or b'')[-800:]); sys.exit(1)
s.shutdown()
if not seen: print('NO REQUEST', r.returncode, r.stderr[-800:]); sys.exit(1)
tools = seen[0].get('tools', [])
json.dump(seen[0], open('req-%s.json' % model.replace('/', '_'), 'w'), indent=1)
print('keys', sorted(seen[0]))
def walk(ts, ns=''):
    for t in ts:
        if t.get('type') == 'namespace' or 'tools' in t:
            walk(t.get('tools', []), t.get('name', ''))
        else:
            n = t.get('name')
            if n and any(k in n for k in ('agent', 'message', 'followup', 'wait', 'spawn', 'close')):
                props = (t.get('parameters') or {}).get('properties', {})
                print(f"  {ns + '.' if ns else ''}{n}: params={list(props)} msg={json.dumps(props.get('message'))[:160]}")
print(model, extra, 'tools:', len(tools), 'include:', seen[0].get('include'))
walk(tools)
