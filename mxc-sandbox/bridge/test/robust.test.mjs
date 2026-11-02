import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { startServer } from '../bridge.mjs';
import { parseFrames } from './helpers.mjs';

const req0 = JSON.parse(fs.readFileSync(new URL('./fixtures/claude-code-request.json', import.meta.url), 'utf8')).body;
const ev = (o) => `data: ${JSON.stringify(o)}\n\n`;
const created = ev({ type: 'response.created', response: { id: 'r' } });
const completed = ev({ type: 'response.completed', response: { id: 'r', usage: {} } });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const until = async (fn, ms = 2000) => { const t = Date.now(); while (!fn()) { if (Date.now() - t > ms) throw new Error('timeout waiting for condition'); await sleep(10); } };

function mock(handler) {
  const state = { seen: [], closed: 0, sockets: new Set() };
  const server = http.createServer(async (rq, rs) => {
    const chunks = []; for await (const c of rq) chunks.push(c);
    const entry = { method: rq.method, url: rq.url, headers: rq.headers, body: Buffer.concat(chunks), reqClosed: false, resClosed: false };
    rs.on('close', () => { entry.resClosed = true; state.closed++; });
    state.seen.push(entry);
    handler(rq, rs, entry);
  });
  server.on('connection', (s) => { state.sockets.add(s); s.on('close', () => state.sockets.delete(s)); });
  return new Promise((r) => server.listen(0, '127.0.0.1', () => r({ ...state, state, server, url: `http://127.0.0.1:${server.address().port}`, close: () => { server.closeAllConnections(); return new Promise((x) => server.close(x)); } })));
}

function open(base, method, p, body, headers = {}) {
  const u = new URL(base + p);
  const r = http.request({ hostname: u.hostname, port: u.port, path: u.pathname + u.search, method, headers: { ...headers, ...(body ? { 'content-length': Buffer.byteLength(body) } : {}) } });
  if (body) r.write(body);
  r.end();
  return r;
}
function call(base, method, p, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const r = open(base, method, p, body, headers);
    r.on('response', async (res) => { const c = []; for await (const x of res) c.push(x); resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(c) }); });
    r.on('error', reject);
  });
}
const msgBody = (extra = {}) => JSON.stringify({ ...req0, ...extra });

test('pass-through: upstream dying mid-stream terminates the client response', async () => {
  const up = await mock((rq, rs) => { rs.writeHead(200, { 'content-type': 'text/event-stream' }); rs.write('data: partial\n\n'); setTimeout(() => rs.socket.destroy(), 50); });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const r = open(b.url, 'POST', '/v1/messages', msgBody({ model: 'claude-x' }), { 'content-type': 'application/json' });
    const outcome = await Promise.race([
      new Promise((res) => r.on('response', (resp) => { resp.on('aborted', () => res('aborted')); resp.on('error', () => res('error')); resp.on('close', () => res('close')); resp.on('end', () => res('end')); resp.resume(); })),
      new Promise((res) => r.on('error', () => res('error'))),
      sleep(1500).then(() => 'hang'),
    ]);
    assert.notEqual(outcome, 'hang');
  } finally { await b.close(); await up.close(); }
});

test('client disconnect propagates upstream (header wait, pass-through and translate, and mid-stream)', async () => {
  for (const [model, delay] of [['claude-x', 1500], ['gpt-5', 1500], ['gpt-5', 0]]) {
    const up = await mock((rq, rs) => {
      const go = () => { if (rs.destroyed) return; rs.writeHead(200, { 'content-type': 'text/event-stream' }); rs.write(created); const iv = setInterval(() => rs.write(': keep\n\n'), 20); rs.on('close', () => clearInterval(iv)); };
      if (delay) setTimeout(go, delay); else go();
    });
    const b = await startServer({ upstream: up.url, port: 0 });
    try {
      const r = open(b.url, 'POST', '/v1/messages', msgBody({ model, stream: true }), { 'content-type': 'application/json' });
      r.on('error', () => {});
      r.on('response', (resp) => resp.resume());
      await until(() => up.state.seen.length === 1);
      await sleep(300);
      r.destroy();
      await until(() => up.state.seen[0].resClosed, 800);
    } finally { await b.close(); await up.close(); }
  }
});

test('upstream never responds -> 504; stalls after headers -> SSE error frame', async () => {
  const up = await mock(() => {});
  const b = await startServer({ upstream: up.url, port: 0, upstreamTimeoutMs: 200 });
  try {
    const t = Date.now();
    const r = await call(b.url, 'POST', '/v1/messages', msgBody({ stream: true }), { 'content-type': 'application/json' });
    assert.equal(r.status, 504);
    assert.ok(Date.now() - t < 1500);
    const p = await call(b.url, 'POST', '/v1/messages', msgBody({ model: 'claude-x' }), { 'content-type': 'application/json' });
    assert.equal(p.status, 504);
  } finally { await b.close(); await up.close(); }
  const up2 = await mock((rq, rs) => { rs.writeHead(200, { 'content-type': 'text/event-stream' }); rs.flushHeaders(); });
  const b2 = await startServer({ upstream: up2.url, port: 0, upstreamTimeoutMs: 200, idleTimeoutMs: 200 });
  try {
    const t = Date.now();
    const r = await call(b2.url, 'POST', '/v1/messages', msgBody({ stream: true }), { 'content-type': 'application/json' });
    assert.ok(Date.now() - t < 1500);
    assert.equal(parseFrames(r.body.toString()).at(-1).type, 'error');
  } finally { await b2.close(); await up2.close(); }
});

test('streaming honours backpressure from a paused client', async () => {
  const chunk = ev({ type: 'response.output_text.delta', output_index: 0, content_index: 0, delta: 'x'.repeat(8192) });
  const total = 6000; // ~48MB
  let sent = 0;
  const up = await mock((rq, rs) => {
    rs.writeHead(200, { 'content-type': 'text/event-stream' });
    rs.write(created);
    const pump = () => {
      while (sent < total) { sent++; if (!rs.write(chunk)) { rs.once('drain', pump); return; } }
      rs.end(completed);
    };
    pump();
  });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const r = open(b.url, 'POST', '/v1/messages', msgBody({ stream: true }), { 'content-type': 'application/json' });
    const resp = await new Promise((res, rej) => { r.on('response', res); r.on('error', rej); });
    resp.pause();
    await sleep(1000);
    assert.ok(sent < total * 0.8, `upstream drained too eagerly: ${sent}/${total}`);
    let bytes = 0, tail = '';
    resp.on('data', (c) => { bytes += c.length; tail = (tail + c.toString('latin1')).slice(-200); });
    resp.resume();
    await new Promise((res) => resp.on('end', res));
    assert.ok(tail.includes('message_stop'));
    assert.equal(sent, total);
  } finally { await b.close(); await up.close(); }
});

test('capture failure does not break the request', async () => {
  const up = await mock((rq, rs) => { rs.writeHead(200, { 'content-type': 'text/event-stream' }); rs.end(created + completed); });
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bridge-cap-'));
  const capDir = path.join(dir, 'cap');
  const b = await startServer({ upstream: up.url, port: 0, captureDir: capDir });
  try {
    fs.rmSync(capDir, { recursive: true, force: true });
    for (let i = 0; i < 2; i++) {
      const r = await call(b.url, 'POST', '/v1/messages', msgBody({ stream: true }), { 'content-type': 'application/json' });
      assert.equal(r.status, 200);
      assert.equal(parseFrames(r.body.toString()).at(-1).type, 'message_stop');
    }
    assert.equal((await call(b.url, 'GET', '/health')).status, 200);
  } finally { await b.close(); await up.close(); }
});

test('no ping after message_stop and the response ends promptly', async () => {
  const up = await mock((rq, rs) => { rs.writeHead(200, { 'content-type': 'text/event-stream' }); rs.write(created + completed); /* keep socket open */ });
  const b = await startServer({ upstream: up.url, port: 0, pingMs: 30 });
  try {
    const t = Date.now();
    const r = await call(b.url, 'POST', '/v1/messages', msgBody({ stream: true }), { 'content-type': 'application/json' });
    assert.ok(Date.now() - t < 1000);
    const types = parseFrames(r.body.toString()).map((f) => f.type);
    assert.equal(types.at(-1), 'message_stop');
    await until(() => up.state.seen[0].resClosed, 500);
  } finally { await b.close(); await up.close(); }
});

test('error frame closes open blocks first', async () => {
  const up = await mock((rq, rs) => {
    rs.writeHead(200, { 'content-type': 'text/event-stream' });
    rs.end(created + ev({ type: 'response.output_text.delta', output_index: 0, content_index: 0, delta: 'hi' }) + ev({ type: 'response.failed', response: { error: { message: 'boom' } } }));
  });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const f = parseFrames((await call(b.url, 'POST', '/v1/messages', msgBody({ stream: true }), { 'content-type': 'application/json' })).body.toString()).map((x) => x.type);
    assert.deepEqual(f.slice(-2), ['content_block_stop', 'error']);
  } finally { await b.close(); await up.close(); }
});

test('body cap -> 413; aborted upload settles; PATCH body forwarded byte-identical', async () => {
  const up = await mock((rq, rs) => { rs.writeHead(200, { 'content-type': 'application/json' }); rs.end('{}'); });
  const b = await startServer({ upstream: up.url, port: 0, maxBodyBytes: 1000 });
  try {
    const big = JSON.stringify({ pad: 'x'.repeat(5000) });
    const r = await call(b.url, 'POST', '/v1/messages', big, { 'content-type': 'application/json' }).catch((e) => ({ status: 'err:' + e.code }));
    assert.ok(r.status === 413 || String(r.status).startsWith('err:'), String(r.status));
    assert.equal(up.state.seen.length, 0);
    // chunked body over cap (no content-length)
    const chunked = await new Promise((resolve) => {
      const rq = http.request(b.url + '/v1/messages', { method: 'POST', headers: { 'content-type': 'application/json' } }, (res) => { res.resume(); resolve(res.statusCode); });
      rq.on('error', (e) => resolve('err:' + e.code));
      rq.write('{"pad":"' + 'x'.repeat(5000)); rq.end('"}');
    });
    assert.ok(chunked === 413 || String(chunked).startsWith('err:'), String(chunked));
    // aborted half-sent upload does not wedge the server
    await new Promise((resolve) => {
      const rq = http.request(b.url + '/v1/messages', { method: 'POST', headers: { 'content-length': '500' } });
      rq.on('error', () => {}); rq.write('{"a":'); setTimeout(() => { rq.destroy(); resolve(); }, 50);
    });
    assert.equal((await call(b.url, 'GET', '/health')).status, 200);
    const raw = Buffer.from('{"patch":true}');
    const p = await call(b.url, 'PATCH', '/v1/things', raw, { 'content-type': 'application/json' });
    assert.equal(p.status, 200);
    assert.ok(up.state.seen.at(-1).body.equals(raw));
  } finally { await b.close(); await up.close(); }
});

test('upstream 429 keeps retry-after and maps error body', async () => {
  const up = await mock((rq, rs) => { rs.writeHead(429, { 'retry-after': '7', 'x-ratelimit-remaining-requests': '0' }); rs.end('slow'); });
  const b = await startServer({ upstream: up.url, port: 0 });
  try {
    const r = await call(b.url, 'POST', '/v1/messages', msgBody({ stream: true }), { 'content-type': 'application/json' });
    assert.equal(r.status, 429);
    assert.equal(r.headers['retry-after'], '7');
    assert.equal(r.headers['x-ratelimit-remaining-requests'], '0');
    assert.equal(JSON.parse(r.body).error.type, 'rate_limit_error');
  } finally { await b.close(); await up.close(); }
});

const bridgePath = new URL('../bridge.mjs', import.meta.url).pathname;
function spawnBridge(upUrl) {
  const child = spawn(process.execPath, [bridgePath], { env: { ...process.env, BRIDGE_UPSTREAM: upUrl, BRIDGE_PORT: '0' }, stdio: ['ignore', 'ignore', 'pipe'] });
  return new Promise((resolve, reject) => {
    let err = '';
    child.stderr.on('data', (d) => { err += d; const m = /listening on (http:\/\/\S+)/.exec(err); if (m) resolve({ child, url: m[1] }); });
    child.on('exit', (c) => reject(new Error('exited early ' + c + err)));
  });
}
const exited = (child) => new Promise((res) => child.on('exit', (code, sig) => res({ code, sig })));

test('SIGTERM: idle server exits 0 immediately; in-flight stream exits 0 within grace', async () => {
  const up = await mock(() => {});
  try {
    const idle = await spawnBridge(up.url);
    let t = Date.now();
    idle.child.kill('SIGTERM');
    let x = await exited(idle.child);
    assert.equal(x.code, 0);
    assert.ok(Date.now() - t < 1500);

    const busy = await spawnBridge(up.url);
    const r = open(busy.url, 'POST', '/v1/messages', msgBody({ stream: true }), { 'content-type': 'application/json' });
    r.on('error', () => {}); r.on('response', (rs) => { rs.on('error', () => {}); rs.resume(); });
    await until(() => up.state.seen.length === 1);
    t = Date.now();
    busy.child.kill('SIGTERM');
    x = await exited(busy.child);
    assert.equal(x.code, 0);
    assert.ok(Date.now() - t < 3000);
  } finally { await up.close(); }
});
