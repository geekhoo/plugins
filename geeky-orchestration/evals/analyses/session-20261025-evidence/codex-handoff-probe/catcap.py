import json, os, subprocess, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
codex = '/root/repos/.eval-tools/codex/0.164.0/bin/codex'
overrides = json.loads(sys.argv[1]); extra = sys.argv[2:]
cat = json.load(open('../codex-models.json'))
base = next(m for m in cat['models'] if m['slug'] == 'gpt-5.5')
entry = dict(base, slug='ant-claude', display_name='ant-claude (LiteLLM)', description='Eval model via LiteLLM',
             upgrade=None, availability_nux=None, additional_speed_tiers=[], service_tiers=[],
             context_window=200000, max_context_window=200000, priority=0)
entry.update(overrides)
json.dump({'models': [entry]}, open('catalog-ant.json', 'w'))
cap = []
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        cap.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
        ev = [{'type': 'response.created', 'response': {'id': 'r'}}, {'type': 'response.output_item.done', 'item': {'type': 'message', 'role': 'assistant', 'id': 'm', 'content': [{'type': 'output_text', 'text': 'ok'}]}},
              {'type': 'response.completed', 'response': {'id': 'r', 'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}}]
        b = ''.join('event: %s\ndata: %s\n\n' % (e['type'], json.dumps(e)) for e in ev).encode()
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.send_header('Content-Length', str(len(b))); self.send_header('Connection', 'close'); self.end_headers(); self.wfile.write(b)
s = ThreadingHTTPServer(('127.0.0.1', 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
prov = '{name="p",base_url="http://127.0.0.1:%d/v1",wire_api="responses",requires_openai_auth=false,supports_websockets=false,request_max_retries=0,stream_max_retries=0}' % s.server_port
ws = tempfile.mkdtemp()
cmd = [codex, '--no-daemon', 'exec', '--json', '--skip-git-repo-check', '--cd', ws, '-c', 'model="ant-claude"', '-c', 'model_provider="p"', '-c', 'model_providers.p=' + prov,
       '-c', 'features.multi_agent=true', '-c', 'model_catalog_json="%s/catalog-ant.json"' % os.getcwd()] + sum((['-c', x] for x in extra), []) + ['hi']
r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90, env={**os.environ, 'CODEX_HOME': tempfile.mkdtemp(dir=os.getcwd())})
s.shutdown()
if not cap:
    print('exit', r.returncode, r.stderr.strip().splitlines()[0][-400:]); sys.exit(1)
d = cap[0]; json.dump(d, open('req-ant.json', 'w'), indent=1)
def names(ts):
    out = []
    for t in ts:
        if t.get('type') == 'namespace': out += [t['name'] + '.' + n for n in names(t.get('tools', []))]
        else: out.append(f"{t.get('name')}({t.get('type')})")
    return out
print('tools:', names(d.get('tools', [])))
for r_ in d['input']:
    if r_.get('type') == 'additional_tools': print('additional_tools:', names(r_['tools']))
t = json.dumps(d); print('encrypted flags:', t.count('"encrypted": true'), '| reasoning:', d.get('reasoning'))
