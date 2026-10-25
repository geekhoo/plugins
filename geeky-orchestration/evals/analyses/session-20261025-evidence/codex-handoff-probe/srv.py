import json, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): sys.stderr.write('HTTP ' + (a[0] % a[1:]) + '\n')
    def do_GET(self):
        b = b'{"models": []}'; self.send_response(200); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        n = len([f for f in __import__('os').listdir('.') if f.startswith('req')])
        json.dump(d, open(f'req{n}.json', 'w'), indent=1)
        ev = [{'type': 'response.created', 'response': {'id': 'r1'}},
              {'type': 'response.output_item.done', 'item': {'type': 'message', 'role': 'assistant', 'id': 'm', 'content': [{'type': 'output_text', 'text': 'done'}]}},
              {'type': 'response.completed', 'response': {'id': 'r1', 'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}}]
        b = ''.join('event: %s\ndata: %s\n\n' % (e['type'], json.dumps(e)) for e in ev).encode()
        self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.send_header('Content-Length', str(len(b))); self.send_header('Connection', 'close'); self.end_headers(); self.wfile.write(b)
ThreadingHTTPServer(('127.0.0.1', 18765), H).serve_forever()
