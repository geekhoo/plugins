import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { startServer } from '../bridge.mjs';
import { parseFrames } from './helpers.mjs';

const fixture = (n) => fs.readFileSync(new URL('./fixtures/' + n, import.meta.url));
const req = JSON.parse(fixture('claude-code-request.json').toString()).body;

function mockUpstream(handler) {
  const seen = [];
  const server = http.createServer(async (rq, rs) => {
    const chunks = []; for await (const c of rq) chunks.push(c);
    const body = Buffer.concat(chunks);
    seen.push({ method: rq.method, url: rq.url, headers: rq.headers, body });
    handler(rq, rs, body);
  });
  return new Promise((r) => server.listen(0, '127.0.0.1', () => r({ server, seen, url: `http://127.0.0.1:${server.address().port}`, close: () => { server.closeAllConnections(); return new Promise((x) => server.close(x)); } })));
}

function call(base, method, p, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(base + p);
    const r = http.request({ hostname: u.hostname, port: u.port, path: u.pathname + u.search, method, headers: { ...headers, ...(body ? { 'content-length': Buffer.byteLength(body) } : {}) } }, async (res) => {
      const chunks = []; for await (const c of res) chunks.push(c);
      resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) });
    });
    r.on('error', reject);
    if (body) r.write(body);
    r.end();
  });
}

const sseReplay = (name) => (rq, rs) => {
  rs.writeHead(200, { 'content-type': 'text/event-stream' });
  const text = fixture(name).toString();
  // write in awkward slices to exercise buffering
  for (let i = 0; i < text.length; i += 211) rs.write(text.slice(i, i + 211));
  rs.end();
};

test('streams fixture reasoning response as valid Anthropic SSE; maps request and auth', async () => {
  const up = await mockUpstream(sseReplay('responses-reasoning-text.sse'));
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bridge-'));
  const logFile = path.join(dir, 'log.jsonl');
  const b = await startServer({ upstream: up.url, port: 0, logFile, captureDir: path.join(dir, 'cap') });
  try {
    const r = await call(b.url, 'POST', '/v1/messages?beta=true', JSON.stringify(req), { 'content-type': 'application/json', 'x-api-key': 'sk-secret', 'anthropic-beta': 'x' });
    assert.equal(r.status, 200);
    assert.match(r.headers['content-type'], /text\/event-stream/);
    const frames = parseFrames(r.body.toString());
    const types = frames.map((f) => f.type);
    assert.equal(types[0], 'message_start');
    assert.equal(types.at(-1), 'message_stop');
    assert.equal(types.at(-2), 'message_delta');
    assert.equal(types.filter((t) => t === 'content_block_start').length, 2);
    assert.equal(types.filter((t) => t === 'content_block_stop').length, 2);
    assert.ok(frames.filter((f) => f.delta?.type === 'text_delta').map((f) => f.delta.text).join('').length > 0);
    assert.ok(frames.filter((f) => f.delta?.type === 'thinking_delta').map((f) => f.delta.thinking).join('').length > 0);
    assert.ok(frames.find((f) => f.delta?.type === 'signature_delta').delta.signature.startsWith('rb1:'));
    assert.equal(frames.at(-2).usage.cache_read_input_tokens, 1889);

    assert.equal(up.seen.length, 1);
    const s = up.seen[0];
    assert.equal(s.url, '/v1/responses');
    assert.equal(s.headers.authorization, 'Bearer sk-secret');
    assert.equal(s.headers['x-api-key'], undefined);
    const sent = JSON.parse(s.body.toString());
    assert.equal(sent.store, false);
    assert.equal(sent.stream, true);
    assert.ok(Array.isArray(sent.input));

    const logLine = JSON.parse(fs.readFileSync(logFile, 'utf8').trim().split('\n').at(-1));
    assert.equal(logLine.route, 'responses');
    assert.equal(logLine.usage.cached, 1889);
    assert.equal(logLine.usage.reasoning, 44);
    assert.ok(!JSON.stringify(logLine).includes('sk-secret'));
    const caps = fs.readdirSync(path.join(dir, 'cap'));
    assert.equal(caps.length, 2);
  } finally { await b.close(); await up.close(); }
});

test('streams function call fixture: tool input parses', async () => {
  const up = await mockUpstream(sseReplay('responses-function-call.sse'));
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const r = await call(b.url, 'POST', '/v1/messages', JSON.stringify(req), { authorization: 'Bearer tok' });
    const frames = parseFrames(r.body.toString());
    assert.equal(up.seen[0].headers.authorization, 'Bearer tok');
    assert.deepEqual(JSON.parse(frames.filter((f) => f.delta?.type === 'input_json_delta').map((f) => f.delta.partial_json).join('')), { city: 'Paris' });
    assert.equal(frames.at(-2).delta.stop_reason, 'tool_use');
  } finally { await b.close(); await up.close(); }
});

test('non-streaming request returns one Messages object', async () => {
  const up = await mockUpstream((rq, rs) => {
    rs.writeHead(200, { 'content-type': 'application/json' });
    rs.end(JSON.stringify({ id: 'resp_9', status: 'completed', output: [{ type: 'message', content: [{ type: 'output_text', text: 'hi' }] }], usage: { input_tokens: 10, input_tokens_details: { cached_tokens: 4 }, output_tokens: 2 } }));
  });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const r = await call(b.url, 'POST', '/v1/messages', JSON.stringify({ model: 'gpt-x', max_tokens: 5, messages: [{ role: 'user', content: 'yo' }] }), { 'x-api-key': 'k' });
    assert.equal(r.status, 200);
    const j = JSON.parse(r.body);
    assert.equal(j.type, 'message');
    assert.equal(j.content[0].text, 'hi');
    assert.equal(j.usage.cache_read_input_tokens, 4);
    assert.equal(JSON.parse(up.seen[0].body).stream, undefined);
  } finally { await b.close(); await up.close(); }
});

test('claude model passes through byte-identical (request and response)', async () => {
  const respBytes = Buffer.from('event: message_start\ndata: {"type":"message_start"}\n\né\x00\xff weird bytes');
  const up = await mockUpstream((rq, rs) => { rs.writeHead(200, { 'content-type': 'text/event-stream', 'x-custom': 'yes' }); rs.end(respBytes); });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const raw = Buffer.from(JSON.stringify({ ...req, model: 'claude-sonnet-5-5' }, null, 3) + ' ');
    const r = await call(b.url, 'POST', '/v1/messages?beta=true', raw, { 'content-type': 'application/json', 'x-api-key': 'sk-1', 'anthropic-version': '2023-06-01' });
    assert.ok(raw.equals(up.seen[0].body));
    assert.equal(up.seen[0].url, '/v1/messages?beta=true');
    assert.equal(up.seen[0].headers['x-api-key'], 'sk-1');
    assert.equal(up.seen[0].headers['anthropic-version'], '2023-06-01');
    assert.ok(r.body.equals(respBytes));
    assert.equal(r.headers['x-custom'], 'yes');
    // other routes pass through too
    const g = await call(b.url, 'GET', '/v1/models', null, { 'x-api-key': 'k' });
    assert.equal(g.status, 200);
    assert.equal(up.seen[1].url, '/v1/models');
  } finally { await b.close(); await up.close(); }
});

test('count_tokens: local for matched models, pass-through otherwise; health', async () => {
  const up = await mockUpstream((rq, rs) => { rs.writeHead(200, { 'content-type': 'application/json' }); rs.end('{"input_tokens":123}'); });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const a = await call(b.url, 'POST', '/v1/messages/count_tokens', JSON.stringify(req));
    assert.ok(JSON.parse(a.body).input_tokens > 1000);
    assert.equal(up.seen.length, 0);
    const c = await call(b.url, 'POST', '/v1/messages/count_tokens', JSON.stringify({ ...req, model: 'claude-opus' }));
    assert.equal(JSON.parse(c.body).input_tokens, 123);
    const h = JSON.parse((await call(b.url, 'GET', '/health')).body);
    assert.equal(h.ok, true);
    assert.equal(h.upstream, up.url);
  } finally { await b.close(); await up.close(); }
});

test('upstream 400 maps to Anthropic error body with same status', async () => {
  const up = await mockUpstream((rq, rs) => { rs.writeHead(400, { 'content-type': 'application/json' }); rs.end(JSON.stringify({ error: { message: 'bad param', type: 'x' } })); });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const r = await call(b.url, 'POST', '/v1/messages', JSON.stringify(req), { 'x-api-key': 'k' });
    assert.equal(r.status, 400);
    assert.deepEqual(JSON.parse(r.body), { type: 'error', error: { type: 'invalid_request_error', message: 'bad param' } });
  } finally { await b.close(); await up.close(); }
  const up2 = await mockUpstream((rq, rs) => { rs.writeHead(429); rs.end('slow down'); });
  const b2 = await startServer({ upstream: up2.url, port: 0 });
  try {
    const r = await call(b2.url, 'POST', '/v1/messages', JSON.stringify(req));
    assert.equal(r.status, 429);
    assert.equal(JSON.parse(r.body).error.type, 'rate_limit_error');
    assert.equal(JSON.parse(r.body).error.message, 'slow down');
  } finally { await b2.close(); await up2.close(); }
});

test('response.failed mid-stream -> event: error; truncated stream -> event: error', async () => {
  const ev = (o) => `data: ${JSON.stringify(o)}\n\n`;
  const up = await mockUpstream((rq, rs) => {
    rs.writeHead(200, { 'content-type': 'text/event-stream' });
    rs.write(ev({ type: 'response.created', response: { id: 'r1' } }));
    rs.write(ev({ type: 'response.failed', response: { id: 'r1', error: { message: 'model exploded' } } }));
    rs.end('data: [DONE]\n\n');
  });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const r = await call(b.url, 'POST', '/v1/messages', JSON.stringify(req));
    const frames = parseFrames(r.body.toString());
    assert.deepEqual(frames.map((f) => f.type), ['message_start', 'error']);
    assert.deepEqual(frames[1].error, { type: 'api_error', message: 'model exploded' });
  } finally { await b.close(); await up.close(); }
  const up2 = await mockUpstream((rq, rs) => { rs.writeHead(200); rs.write(ev({ type: 'response.created', response: { id: 'r1' } })); rs.end(); });
  const b2 = await startServer({ upstream: up2.url, port: 0 });
  try {
    const frames = parseFrames((await call(b2.url, 'POST', '/v1/messages', JSON.stringify(req))).body.toString());
    assert.equal(frames.at(-1).type, 'error');
  } finally { await b2.close(); await up2.close(); }
});

test('pings are sent while upstream is quiet', async () => {
  const up = await mockUpstream((rq, rs) => {
    rs.writeHead(200, { 'content-type': 'text/event-stream' });
    rs.write(`data: ${JSON.stringify({ type: 'response.created', response: { id: 'r' } })}\n\n`);
    setTimeout(() => rs.end(`data: ${JSON.stringify({ type: 'response.completed', response: { id: 'r', usage: {} } })}\n\n`), 400);
  });
  const b = await startServer({ upstream: up.url, port: 0, pingMs: 50 });
  try {
    const frames = parseFrames((await call(b.url, 'POST', '/v1/messages', JSON.stringify(req))).body.toString());
    assert.ok(frames.some((f) => f.type === 'ping'));
    assert.equal(frames.at(-1).type, 'message_stop');
  } finally { await b.close(); await up.close(); }
});

test('refuses to bind non-loopback and requires upstream', async () => {
  assert.throws(() => startServer({ upstream: 'http://x', host: '0.0.0.0', port: 0 }), /non-loopback/);
  assert.throws(() => startServer({ upstream: '', port: 0 }), /required/);
});
