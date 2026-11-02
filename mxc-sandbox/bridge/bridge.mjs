#!/usr/bin/env node
// Messages -> Responses bridge. See DESIGN.md. Node 22+, standard library only.
import http from 'node:http';
import https from 'node:https';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pipeline } from 'node:stream/promises';
import { fileURLToPath } from 'node:url';

export const DEFAULT_MODELS_REGEX = '^(gpt-|o\\d|azure-gpt-)';
export const DEFAULT_REASONING_REGEX = '^(azure-)?(o\\d|gpt-([5-9]|\\d{2,}))';
const BILLING_PREFIX = 'x-anthropic-billing-header:';
// xhigh passes through: the gateway accepts it for gpt-6.1-sol (2026-11-02 sweep); max has no Responses equivalent
export const DEFAULT_EFFORT_MAP = 'low:low,medium:medium,high:high,xhigh:xhigh,max:xhigh';

export function parseEffortMap(s = DEFAULT_EFFORT_MAP) {
  const m = {};
  for (const pair of String(s).split(',')) {
    const [k, v] = pair.split(':').map((x) => x && x.trim());
    if (k && v) m[k] = v;
  }
  return m;
}

// ---------------------------------------------------------------- request mapping

const DROPPED_PARAMS = ['temperature', 'top_p', 'top_k', 'stop_sequences', 'context_management'];

function textOf(content) {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';
  return content.filter((b) => b && b.type === 'text').map((b) => b.text ?? '').join('\n\n');
}

function collectToolRefs(messages, set = new Set()) {
  const walk = (v) => {
    if (Array.isArray(v)) v.forEach(walk);
    else if (v && typeof v === 'object') {
      if (v.type === 'tool_reference' && v.tool_name) set.add(v.tool_name);
      for (const k of Object.keys(v)) if (typeof v[k] === 'object') walk(v[k]);
    }
  };
  walk(messages);
  return set;
}

function decodeSignature(sig) {
  if (typeof sig !== 'string' || !sig.startsWith('rb1:')) return null;
  try {
    const o = JSON.parse(Buffer.from(sig.slice(4), 'base64url').toString('utf8'));
    if (o && o.enc) return o;
  } catch { /* fallthrough */ }
  return null;
}

function imageUrl(src) {
  if (!src) return null;
  if (src.type === 'base64') return `data:${src.media_type};base64,${src.data}`;
  if (src.type === 'url') return src.url;
  return null;
}

export function mapRequest(body, opts = {}) {
  const effortMap = opts.effortMap || parseEffortMap(process.env.BRIDGE_EFFORT_MAP);
  const summary = opts.summary ?? process.env.BRIDGE_SUMMARY ?? 'detailed';
  const dropped = [];
  const out = { model: body.model };

  if (body.system != null) {
    let sysBlocks = typeof body.system === 'string' ? body.system : Array.isArray(body.system) ? body.system : [];
    if (typeof sysBlocks === 'string') {
      const lines = sysBlocks.split('\n');
      const kept = lines.filter((l) => !l.startsWith(BILLING_PREFIX));
      if (kept.length !== lines.length) { dropped.push('system:billing-header'); sysBlocks = kept.join('\n').replace(/^\n+/, ''); }
    } else {
      const kept = sysBlocks.filter((b) => !(b && b.type === 'text' && typeof b.text === 'string' && b.text.startsWith(BILLING_PREFIX)));
      if (kept.length !== sysBlocks.length) dropped.push('system:billing-header');
      sysBlocks = kept;
    }
    const sys = textOf(sysBlocks);
    if (sys) out.instructions = sys;
  }
  if (body.max_tokens != null) out.max_output_tokens = Math.max(16, body.max_tokens);
  if (body.stream != null) out.stream = body.stream;

  out.store = false;
  const reasoningRe = opts.reasoningModels instanceof RegExp ? opts.reasoningModels
    : new RegExp(opts.reasoningModels || process.env.BRIDGE_REASONING_MODELS || DEFAULT_REASONING_REGEX);
  if (reasoningRe.test(body.model || '')) {
    const reasoning = { effort: effortMap[body.output_config?.effort] || (body.output_config?.effort ? body.output_config.effort : 'medium') };
    if (body.thinking && body.thinking.type !== 'disabled' && summary !== 'none') reasoning.summary = summary;
    out.reasoning = reasoning;
    out.include = ['reasoning.encrypted_content'];
  }

  try {
    const uid = typeof body.metadata?.user_id === 'string' ? JSON.parse(body.metadata.user_id) : body.metadata?.user_id;
    if (uid?.session_id) out.prompt_cache_key = 'cc-' + uid.session_id;
  } catch { /* user_id not JSON */ }

  for (const p of DROPPED_PARAMS) if (body[p] != null) dropped.push(`param:${p}`);

  // tools
  const refs = collectToolRefs(body.messages || []);
  const tools = [];
  for (const t of body.tools || []) {
    if (t.type && t.type !== 'custom') { dropped.push(`tool:${t.name || t.type} (server tool ${t.type})`); continue; }
    if (t.defer_loading && !refs.has(t.name)) { dropped.push(`tool:${t.name} (deferred)`); continue; }
    tools.push({ type: 'function', name: t.name, description: t.description ?? '', parameters: t.input_schema ?? { type: 'object', properties: {} }, strict: false });
  }
  if (tools.length) out.tools = tools;
  const tc = body.tool_choice;
  if (tools.length) out.parallel_tool_calls = !tc?.disable_parallel_tool_use;
  if (tc && tools.length) {
    if (tc.type === 'auto') out.tool_choice = 'auto';
    else if (tc.type === 'any') out.tool_choice = 'required';
    else if (tc.type === 'none') out.tool_choice = 'none';
    else if (tc.type === 'tool') out.tool_choice = { type: 'function', name: tc.name };
  }

  // messages
  const input = [];
  for (const msg of body.messages || []) {
    const blocks = typeof msg.content === 'string' ? [{ type: 'text', text: msg.content }] : Array.isArray(msg.content) ? msg.content : [];
    if (msg.role === 'system') {
      const text = textOf(blocks);
      if (text) input.push({ role: 'developer', content: [{ type: 'input_text', text }] });
    } else if (msg.role === 'user') {
      let pending = [];
      const toolImgs = [];
      const flush = () => { if (pending.length) { input.push({ role: 'user', content: pending }); pending = []; } };
      for (const b of blocks) {
        if (b.type === 'text') pending.push({ type: 'input_text', text: b.text ?? '' });
        else if (b.type === 'image') {
          const url = imageUrl(b.source);
          if (url) pending.push({ type: 'input_image', image_url: url }); else dropped.push('block:image (unsupported source)');
        } else if (b.type === 'tool_result') {
          flush();
          const parts = [];
          const imgs = [];
          if (typeof b.content === 'string') parts.push(b.content);
          else for (const c of b.content || []) {
            if (c.type === 'text') parts.push(c.text ?? '');
            else if (c.type === 'tool_reference') parts.push(`Tool ${c.tool_name} is now available.`);
            else if (c.type === 'image') { const u = imageUrl(c.source); if (u) imgs.push({ type: 'input_image', image_url: u }); }
          }
          let output = parts.join('\n');
          if (!output && imgs.length) output = '[image attached below]';
          if (b.is_error) output = '[tool error] ' + output;
          input.push({ type: 'function_call_output', call_id: b.tool_use_id, output });
          toolImgs.push(...imgs);
        } else dropped.push(`block:${b.type}`);
      }
      if (toolImgs.length) input.push({ role: 'user', content: toolImgs });
      flush();
    } else if (msg.role === 'assistant') {
      const startLen = input.length;
      let pending = [];
      const flush = () => { if (pending.length) { input.push({ role: 'assistant', content: pending }); pending = []; } };
      for (const b of blocks) {
        if (b.type === 'text') { if (b.text) pending.push({ type: 'output_text', text: b.text }); }
        else if (b.type === 'tool_use') {
          flush();
          input.push({ type: 'function_call', call_id: b.id, name: b.name, arguments: JSON.stringify(b.input ?? {}) });
        } else if (b.type === 'thinking') {
          const sig = decodeSignature(b.signature);
          if (sig) {
            flush();
            input.push({ type: 'reasoning', id: sig.id, summary: [{ type: 'summary_text', text: b.thinking ?? '' }], encrypted_content: sig.enc });
          } else dropped.push('block:thinking (foreign)');
        } else if (b.type === 'redacted_thinking') dropped.push('block:redacted_thinking');
        else dropped.push(`block:${b.type}`);
      }
      flush();
      // a replayed reasoning item must be followed by its message / function_call
      while (input.length > startLen && input[input.length - 1].type === 'reasoning') { input.pop(); dropped.push('block:thinking (orphan reasoning)'); }
    }
  }
  out.input = input;
  return { responsesBody: out, dropped };
}

export function countTokens(body) {
  let chars = 0;
  if (body.system != null) chars += typeof body.system === 'string' ? body.system.length : JSON.stringify(body.system).length;
  if (body.messages) chars += JSON.stringify(body.messages).length;
  for (const t of body.tools || []) chars += JSON.stringify({ name: t.name, description: t.description, input_schema: t.input_schema }).length;
  return { input_tokens: Math.ceil(chars / 4) };
}

// ---------------------------------------------------------------- response mapping

export function encodeSignature(id, enc) {
  return 'rb1:' + Buffer.from(JSON.stringify({ id, enc })).toString('base64url');
}

export function mapUsage(u = {}) {
  const input = u.input_tokens ?? 0;
  const cached = u.input_tokens_details?.cached_tokens ?? 0;
  const write = u.input_tokens_details?.cache_write_tokens ?? 0;
  return {
    // Anthropic: input_tokens excludes cache reads AND cache writes (total = input + read + creation);
    // OpenAI input_tokens includes both, so subtract both or Claude Code counts the writes twice
    input_tokens: Math.max(0, input - cached - write),
    cache_read_input_tokens: cached,
    cache_creation_input_tokens: write,
    output_tokens: u.output_tokens ?? 0,
  };
}

function stopReason(resp, hadToolCall) {
  if (resp?.status === 'incomplete') {
    const reason = resp?.incomplete_details?.reason;
    if (reason === 'max_output_tokens') return 'max_tokens';
    if (reason === 'content_filter') return 'refusal';
  }
  if (hadToolCall) return 'tool_use';
  return 'end_turn';
}

export function frame(event, obj) {
  return `event: ${event}\ndata: ${JSON.stringify(obj)}\n\n`;
}

export function errorFrame(message, type = 'api_error') {
  return frame('error', { type: 'error', error: { type, message } });
}

export class SseTranslator {
  constructor(model) {
    this.model = model;
    this.started = false;
    this.finished = false;
    this.next = 0;
    this.blocks = new Map(); // key -> {index, open}
    this.summaryIdx = new Map();
    this.argsSeen = new Set();
    this.hadToolCall = false;
    this.usage = null;
    this.stop = null;
    this.error = null;
  }

  _start(out) {
    if (this.started) return;
    this.started = true;
    out.push(frame('message_start', { type: 'message_start', message: { id: 'msg_' + (this.respId || crypto.randomUUID()), type: 'message', role: 'assistant', model: this.model, content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 0, output_tokens: 0 } } }));
  }

  _open(key, contentBlock, out) {
    let b = this.blocks.get(key);
    if (b) return b;
    this._start(out);
    b = { index: this.next++, open: true };
    this.blocks.set(key, b);
    out.push(frame('content_block_start', { type: 'content_block_start', index: b.index, content_block: contentBlock }));
    return b;
  }

  _delta(b, delta, out) {
    out.push(frame('content_block_delta', { type: 'content_block_delta', index: b.index, delta }));
  }

  _close(key, out) {
    const b = this.blocks.get(key);
    if (b && b.open) { b.open = false; out.push(frame('content_block_stop', { type: 'content_block_stop', index: b.index })); }
  }

  _closeAll(out) {
    for (const k of this.blocks.keys()) this._close(k, out);
  }

  /** Consume one parsed Responses event; returns array of Anthropic SSE frame strings. */
  push(ev) {
    const out = [];
    if (this.finished || !ev || typeof ev !== 'object') return out;
    const oi = ev.output_index;
    switch (ev.type) {
      case 'response.created':
        this.respId = ev.response?.id;
        this._start(out);
        break;
      case 'response.output_item.added': {
        this._start(out);
        const it = ev.item || {};
        if (it.type === 'reasoning') this._open(`r:${oi}`, { type: 'thinking', thinking: '', signature: '' }, out);
        else if (it.type === 'function_call') {
          this.hadToolCall = true;
          this._open(`f:${oi}`, { type: 'tool_use', id: it.call_id, name: it.name, input: {} }, out);
        }
        break;
      }
      case 'response.reasoning_summary_part.added': {
        const b = this._open(`r:${oi}`, { type: 'thinking', thinking: '', signature: '' }, out);
        const si = ev.summary_index ?? 0;
        if (si > 0 && this.summaryIdx.get(oi) !== si) this._delta(b, { type: 'thinking_delta', thinking: '\n\n' }, out);
        this.summaryIdx.set(oi, si);
        break;
      }
      case 'response.reasoning_summary_text.delta': {
        const b = this._open(`r:${oi}`, { type: 'thinking', thinking: '', signature: '' }, out);
        if (ev.delta) this._delta(b, { type: 'thinking_delta', thinking: ev.delta }, out);
        break;
      }
      case 'response.content_part.added':
        if (ev.part?.type === 'output_text' || ev.part?.type === 'refusal') this._open(`m:${oi}:${ev.content_index ?? 0}`, { type: 'text', text: '' }, out);
        break;
      case 'response.output_text.delta':
      case 'response.refusal.delta': {
        const b = this._open(`m:${oi}:${ev.content_index ?? 0}`, { type: 'text', text: '' }, out);
        if (ev.delta) this._delta(b, { type: 'text_delta', text: ev.delta }, out);
        break;
      }
      case 'response.content_part.done':
        this._close(`m:${oi}:${ev.content_index ?? 0}`, out);
        break;
      case 'response.function_call_arguments.delta': {
        this.hadToolCall = true;
        const b = this.blocks.get(`f:${oi}`) || this._open(`f:${oi}`, { type: 'tool_use', id: ev.item_id, name: '', input: {} }, out);
        if (ev.delta) { this.argsSeen.add(oi); this._delta(b, { type: 'input_json_delta', partial_json: ev.delta }, out); }
        break;
      }
      case 'response.output_item.done': {
        const it = ev.item || {};
        if (it.type === 'reasoning') {
          const b = this._open(`r:${oi}`, { type: 'thinking', thinking: '', signature: '' }, out);
          this._delta(b, { type: 'signature_delta', signature: encodeSignature(it.id, it.encrypted_content) }, out);
          this._close(`r:${oi}`, out);
        } else if (it.type === 'function_call') {
          this.hadToolCall = true;
          const b = this._open(`f:${oi}`, { type: 'tool_use', id: it.call_id, name: it.name, input: {} }, out);
          if (!this.argsSeen.has(oi) && it.arguments) this._delta(b, { type: 'input_json_delta', partial_json: it.arguments }, out);
          this._close(`f:${oi}`, out);
        } else if (it.type === 'message') {
          for (const k of this.blocks.keys()) if (k.startsWith(`m:${oi}:`)) this._close(k, out);
        }
        break;
      }
      case 'response.completed':
      case 'response.incomplete': {
        this._start(out);
        this._closeAll(out);
        const r = ev.response || {};
        this.usage = mapUsage(r.usage);
        this.rawUsage = r.usage;
        this.stop = stopReason(ev.type === 'response.incomplete' && !r.status ? { ...r, status: 'incomplete' } : r, this.hadToolCall);
        out.push(frame('message_delta', { type: 'message_delta', delta: { stop_reason: this.stop, stop_sequence: null }, usage: this.usage }));
        out.push(frame('message_stop', { type: 'message_stop' }));
        this.finished = true;
        break;
      }
      case 'response.failed':
        this.fail(ev.response?.error?.message || ev.response?.status_details?.error?.message || 'upstream response failed', out);
        break;
      case 'error':
        this.fail(ev.message || ev.error?.message || 'upstream error', out);
        break;
      default:
        break;
    }
    return out;
  }

  fail(message, out = []) {
    if (this.finished) return out;
    this.finished = true;
    this.error = message;
    if (this.started) this._closeAll(out);
    out.push(errorFrame(message));
    return out;
  }

  /** Call when upstream ends; emits an error frame if the stream never completed. */
  end() {
    const out = [];
    if (!this.finished) this.fail('upstream stream ended before response.completed', out);
    return out;
  }
}

/** Incremental SSE parser: feed text chunks, get parsed JSON events ([DONE] skipped). */
export class SseParser {
  constructor() { this.buf = ''; }
  feed(chunk) {
    this.buf += chunk;
    const events = [];
    let m;
    while ((m = /\r?\n\r?\n/.exec(this.buf))) {
      const raw = this.buf.slice(0, m.index);
      this.buf = this.buf.slice(m.index + m[0].length);
      const ev = SseParser.parseBlock(raw);
      if (ev) events.push(ev);
    }
    return events;
  }
  flush() {
    const raw = this.buf; this.buf = '';
    const ev = raw.trim() ? SseParser.parseBlock(raw) : null;
    return ev ? [ev] : [];
  }
  static parseBlock(raw) {
    const data = [];
    let name = null;
    for (const line of raw.split(/\r?\n/)) {
      if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''));
      else if (line.startsWith('event:')) name = line.slice(6).trim();
    }
    const s = data.join('\n');
    if (!s || s.trim() === '[DONE]') return null;
    try {
      const j = JSON.parse(s);
      if (name && !j.type) j.type = name;
      return j;
    } catch { return null; }
  }
}

export function mapNonStream(resp, model) {
  const content = [];
  let tool = false;
  for (const it of resp.output || []) {
    if (it.type === 'reasoning') {
      const text = (it.summary || []).map((s) => s.text || '').join('\n\n');
      content.push({ type: 'thinking', thinking: text, signature: encodeSignature(it.id, it.encrypted_content) });
    } else if (it.type === 'message') {
      for (const p of it.content || []) {
        if (p.type === 'output_text') content.push({ type: 'text', text: p.text ?? '' });
        else if (p.type === 'refusal') content.push({ type: 'text', text: p.refusal ?? '' });
      }
    } else if (it.type === 'function_call') {
      tool = true;
      let input = {};
      try { input = it.arguments ? JSON.parse(it.arguments) : {}; }
      catch {
        // truncated arguments: never hand a guessed input to the client
        if (resp.status === 'incomplete') continue;
        input = {};
      }
      content.push({ type: 'tool_use', id: it.call_id, name: it.name, input });
    }
  }
  return { id: 'msg_' + resp.id, type: 'message', role: 'assistant', model, content, stop_reason: stopReason(resp, tool), stop_sequence: null, usage: mapUsage(resp.usage) };
}

// ---------------------------------------------------------------- errors

const ERR_TYPES = { 400: 'invalid_request_error', 401: 'authentication_error', 403: 'permission_error', 404: 'not_found_error', 413: 'request_too_large', 429: 'rate_limit_error', 529: 'overloaded_error' };

export function mapErrorBody(status, text) {
  let message = text;
  try {
    const j = JSON.parse(text);
    const e = j.error;
    message = (typeof e === 'string' ? e : e?.message) || j.message || j.detail || text;
    if (typeof message !== 'string') message = JSON.stringify(message);
  } catch { /* raw text */ }
  return { type: 'error', error: { type: ERR_TYPES[status] || 'api_error', message: message || `upstream returned ${status}` } };
}

// ---------------------------------------------------------------- server

const HOP = new Set(['host', 'connection', 'content-length', 'transfer-encoding', 'keep-alive', 'proxy-connection', 'upgrade']);
const FWD_ERR_HEADERS = /^(retry-after|x-ratelimit-.*|anthropic-ratelimit-.*)$/i;
// header timeout; the idle timeout defaults to 600 s because a high-effort reasoning model can think silently
// for minutes between response.created and its first summary event
const DEFAULT_TIMEOUT_MS = 300000;
const DEFAULT_IDLE_TIMEOUT_MS = 600000;
const DEFAULT_MAX_BODY = 64 * 1024 * 1024;

function httpError(status, code, message) { return Object.assign(new Error(message), { status, code }); }

function readBody(req, maxBytes = DEFAULT_MAX_BODY) {
  return new Promise((resolve, reject) => {
    const declared = Number(req.headers['content-length']);
    if (Number.isFinite(declared) && declared > maxBytes) { req.resume(); return reject(httpError(413, 'TOO_LARGE', 'request body too large')); }
    const chunks = [];
    let size = 0;
    let settled = false;
    const done = (fn, v) => { if (!settled) { settled = true; fn(v); } };
    req.on('data', (c) => {
      if (settled) return;
      size += c.length;
      if (size > maxBytes) { chunks.length = 0; done(reject, httpError(413, 'TOO_LARGE', 'request body too large')); return; }
      chunks.push(c);
    });
    req.on('end', () => done(resolve, Buffer.concat(chunks)));
    req.on('error', (e) => done(reject, e));
    req.on('aborted', () => done(reject, httpError(499, 'CLIENT_ABORT', 'client aborted request')));
    req.on('close', () => done(reject, httpError(499, 'CLIENT_ABORT', 'client aborted request')));
  });
}

export function normalizeUpstream(u) {
  const t = String(u).trim().replace(/\/+$/, '');
  return !t || /^[a-z][a-z0-9+.-]*:\/\//i.test(t) ? t : `http://${t}`;
}

function upstreamRequest(upstream, pathAndQuery, method, headers, body, { signal, timeoutMs } = {}) {
  const base = new URL(upstream);
  const lib = base.protocol === 'https:' ? https : http;
  return new Promise((resolve, reject) => {
    let timer = null;
    const req = lib.request({
      hostname: base.hostname, port: base.port || undefined, method, signal,
      path: base.pathname.replace(/\/$/, '') + pathAndQuery,
      headers: { ...headers, ...(body ? { 'content-length': Buffer.byteLength(body) } : {}) },
    }, (r) => { if (timer) clearTimeout(timer); resolve(r); });
    if (timeoutMs > 0) timer = setTimeout(() => req.destroy(httpError(504, 'UPSTREAM_TIMEOUT', `upstream did not respond within ${timeoutMs}ms`)), timeoutMs);
    req.on('error', (e) => { if (timer) clearTimeout(timer); reject(e); });
    if (body) req.write(body);
    req.end();
  });
}

function sendJson(res, status, obj, extra = {}) {
  if (res.headersSent || res.destroyed) { try { res.end(); } catch { /* ignore */ } return; }
  const b = JSON.stringify(obj);
  res.writeHead(status, { ...extra, 'content-type': 'application/json', 'content-length': Buffer.byteLength(b) });
  res.end(b);
}

function isLoopback(h) { return ['127.0.0.1', '::1', 'localhost'].includes(h); }

function drained(stream) {
  return new Promise((r) => {
    const fin = () => { stream.off('drain', fin); stream.off('close', fin); stream.off('error', fin); r(); };
    stream.once('drain', fin); stream.once('close', fin); stream.once('error', fin);
  });
}

export function startServer(opts = {}) {
  // ANTHROPIC_BASE_URL may have no scheme (curl assumes http://); new URL() needs one
  const upstream = normalizeUpstream(opts.upstream || process.env.BRIDGE_UPSTREAM || '');
  if (!upstream) throw new Error('BRIDGE_UPSTREAM / upstream is required');
  const host = opts.host || process.env.BRIDGE_HOST || '127.0.0.1';
  if (!isLoopback(host)) throw new Error(`refusing to bind non-loopback address ${host}`);
  const port = opts.port ?? Number(process.env.BRIDGE_PORT || 8788);
  const modelsSrc = opts.modelsRegex || process.env.BRIDGE_RESPONSES_MODELS || DEFAULT_MODELS_REGEX;
  const modelsRe = new RegExp(modelsSrc);
  const effortMap = opts.effortMap || parseEffortMap(process.env.BRIDGE_EFFORT_MAP);
  const summary = opts.summary ?? process.env.BRIDGE_SUMMARY ?? 'detailed';
  const logFile = opts.logFile ?? process.env.BRIDGE_LOG;
  const captureDir = opts.captureDir ?? process.env.BRIDGE_CAPTURE_DIR;
  const pingMs = opts.pingMs ?? 15000;
  const headerTimeoutMs = opts.upstreamTimeoutMs ?? Number(process.env.BRIDGE_UPSTREAM_TIMEOUT_MS || DEFAULT_TIMEOUT_MS);
  const idleTimeoutMs = opts.idleTimeoutMs ?? Number(process.env.BRIDGE_IDLE_TIMEOUT_MS || DEFAULT_IDLE_TIMEOUT_MS);
  const maxBody = opts.maxBodyBytes ?? Number(process.env.BRIDGE_MAX_BODY_BYTES || DEFAULT_MAX_BODY);
  const reasoningModels = opts.reasoningModels;
  if (captureDir) fs.mkdirSync(captureDir, { recursive: true });
  const caps = new Set();

  const log = (rec) => { if (logFile) { try { fs.appendFileSync(logFile, JSON.stringify(rec) + '\n'); } catch { /* ignore */ } } };

  const onIdle = (up) => up.setTimeout(idleTimeoutMs > 0 ? idleTimeoutMs : 0, () => up.destroy(httpError(504, 'UPSTREAM_TIMEOUT', `upstream idle for ${idleTimeoutMs}ms`)));

  const passthrough = async (req, res, body, rec, ac) => {
    rec.route = 'passthrough';
    const headers = {};
    for (const [k, v] of Object.entries(req.headers)) if (!HOP.has(k)) headers[k] = v;
    const t0 = Date.now();
    let up;
    try { up = await upstreamRequest(upstream, req.url, req.method, headers, body.length ? body : null, { signal: ac.signal, timeoutMs: headerTimeoutMs }); }
    catch (e) {
      if (ac.signal.aborted) { rec.status = 499; return; }
      rec.status = e.status === 504 ? 504 : 502;
      return sendJson(res, rec.status, { type: 'error', error: { type: 'api_error', message: `upstream unreachable: ${e.message}` } });
    }
    rec.status = up.statusCode;
    onIdle(up);
    const h = { ...up.headers }; delete h['transfer-encoding']; delete h.connection;
    res.writeHead(up.statusCode, h);
    up.once('data', () => { rec.ms_first_byte = Date.now() - t0; });
    try { await pipeline(up, res); }
    catch (e) { rec.error = e.message; if (!res.destroyed) res.destroy(); if (!up.destroyed) up.destroy(); }
  };

  const translate = async (req, res, body, json, rec, ac) => {
    rec.route = 'responses';
    const { responsesBody, dropped } = mapRequest(json, { effortMap, summary, reasoningModels });
    rec.effort = responsesBody.reasoning?.effort;
    rec.items_in = responsesBody.input.length;
    rec.tools_in = (responsesBody.tools || []).length;
    rec.tools_dropped = dropped.filter((d) => d.startsWith('tool:')).length;
    const wantStream = !!json.stream;
    const upBody = JSON.stringify(responsesBody);
    if (captureDir) { try { fs.writeFileSync(path.join(captureDir, `${rec.req_id}.request.json`), upBody); } catch { /* capture is best effort */ } }
    const key = (req.headers['x-api-key'] || '').toString() || (req.headers.authorization || '').toString().replace(/^Bearer\s+/i, '');
    const headers = { 'content-type': 'application/json', accept: wantStream ? 'text/event-stream' : 'application/json', 'accept-encoding': 'identity' };
    if (key) headers.authorization = `Bearer ${key}`;
    const t0 = Date.now();
    let up;
    try { up = await upstreamRequest(upstream, '/v1/responses', 'POST', headers, upBody, { signal: ac.signal, timeoutMs: headerTimeoutMs }); }
    catch (e) {
      if (ac.signal.aborted) { rec.status = 499; return; }
      rec.status = e.status === 504 ? 504 : 502;
      return sendJson(res, rec.status, { type: 'error', error: { type: 'api_error', message: `upstream unreachable: ${e.message}` } });
    }
    onIdle(up);

    if (up.statusCode >= 400) {
      const text = Buffer.concat(await up.toArray()).toString('utf8');
      rec.status = up.statusCode;
      const extra = {};
      for (const [k, v] of Object.entries(up.headers)) if (FWD_ERR_HEADERS.test(k)) extra[k] = v;
      return sendJson(res, up.statusCode, mapErrorBody(up.statusCode, text), extra);
    }

    if (!wantStream) {
      const text = Buffer.concat(await up.toArray()).toString('utf8');
      rec.ms_first_byte = Date.now() - t0;
      if (captureDir) { try { fs.writeFileSync(path.join(captureDir, `${rec.req_id}.upstream.json`), text); } catch { /* best effort */ } }
      let j;
      try { j = JSON.parse(text); } catch { rec.status = 502; return sendJson(res, 502, mapErrorBody(502, 'invalid JSON from upstream')); }
      if (j.status === 'failed' || j.error) { rec.status = 502; return sendJson(res, 502, mapErrorBody(502, JSON.stringify({ message: j.error?.message || 'upstream response failed' }))); }
      rec.status = 200;
      const m = mapNonStream(j, json.model);
      rec.usage = usageRec(j.usage);
      return sendJson(res, 200, m);
    }

    rec.status = 200;
    res.writeHead(200, { 'content-type': 'text/event-stream', 'cache-control': 'no-cache', connection: 'keep-alive' });
    const tr = new SseTranslator(json.model);
    const parser = new SseParser();
    let cap = null;
    if (captureDir) {
      try {
        cap = fs.createWriteStream(path.join(captureDir, `${rec.req_id}.upstream.sse`));
        const c = cap;
        caps.add(c);
        c.on('error', () => { if (cap === c) cap = null; caps.delete(c); });
        c.on('close', () => caps.delete(c));
      } catch { cap = null; }
    }
    let lastWrite = Date.now();
    const write = async (frames) => {
      for (const f of frames) {
        if (res.destroyed) return;
        lastWrite = Date.now();
        if (!res.write(f)) await drained(res);
      }
    };
    const ping = setInterval(() => {
      if (!tr.finished && !res.destroyed && Date.now() - lastWrite >= pingMs) { lastWrite = Date.now(); res.write(frame('ping', { type: 'ping' })); }
    }, Math.max(10, Math.min(pingMs, 1000)));
    res.on('close', () => { clearInterval(ping); if (!up.destroyed) up.destroy(); });
    up.setEncoding('utf8');
    let first = true;
    try {
      for await (const chunk of up) {
        if (first) { rec.ms_first_byte = Date.now() - t0; first = false; }
        if (cap) { const c = cap; if (!c.write(chunk)) await drained(c); }
        for (const ev of parser.feed(chunk)) await write(tr.push(ev));
        if (tr.finished) break;
      }
      if (!tr.finished) {
        for (const ev of parser.flush()) await write(tr.push(ev));
        await write(tr.end());
      }
    } catch (e) {
      if (!res.destroyed) await write(tr.fail(`upstream stream error: ${e.message}`));
    } finally {
      clearInterval(ping);
      if (cap) cap.end();
      if (!up.destroyed) up.destroy();
    }
    if (tr.error) rec.error = tr.error;
    rec.usage = usageRec(tr.rawUsage);
    res.end();
  };

  const usageRec = (u) => u ? { input: u.input_tokens, cached: u.input_tokens_details?.cached_tokens ?? 0, cache_write: u.input_tokens_details?.cache_write_tokens ?? 0, output: u.output_tokens, reasoning: u.output_tokens_details?.reasoning_tokens ?? 0 } : undefined;

  const server = http.createServer(async (req, res) => {
    const t0 = Date.now();
    const rec = { ts: new Date().toISOString(), req_id: crypto.randomBytes(6).toString('hex'), route: 'passthrough', model: null };
    const pathname = (req.url || '').split('?')[0];
    const ac = new AbortController();
    res.on('close', () => { if (!res.writableEnded) ac.abort(); });
    try {
      if (req.method === 'GET' && pathname === '/health') {
        return sendJson(res, 200, { ok: true, upstream, models_regex: modelsSrc });
      }
      const hasBody = Number(req.headers['content-length']) > 0 || req.headers['transfer-encoding'] != null;
      const body = hasBody ? await readBody(req, maxBody) : Buffer.alloc(0);
      const isMsgs = req.method === 'POST' && pathname === '/v1/messages';
      const isCount = req.method === 'POST' && pathname === '/v1/messages/count_tokens';
      let json = null;
      if (isMsgs || isCount) { try { json = JSON.parse(body.toString('utf8')); } catch { json = null; } }
      if (json && typeof json.model === 'string') rec.model = json.model;
      if (json && modelsRe.test(json.model || '')) {
        if (isCount) { rec.route = 'responses'; rec.status = 200; return sendJson(res, 200, countTokens(json)); }
        if (isMsgs) return await translate(req, res, body, json, rec, ac);
      }
      await passthrough(req, res, body, rec, ac);
    } catch (e) {
      if (e.code === 'CLIENT_ABORT') { rec.status = 499; return; }
      rec.status = e.status || rec.status || 500;
      rec.error = e.message;
      if (e.code === 'TOO_LARGE') {
        sendJson(res, 413, mapErrorBody(413, e.message), { connection: 'close' });
        res.once('finish', () => req.destroy());
      } else if (!res.headersSent) sendJson(res, e.code === 'UPSTREAM_TIMEOUT' ? 504 : 500, { type: 'error', error: { type: 'api_error', message: e.message } });
      else res.end();
    } finally {
      rec.ms_total = Date.now() - t0;
      if (rec.route !== 'passthrough' || rec.model) log(rec);
    }
  });

  const endCaps = () => { for (const c of caps) { try { c.end(); } catch { /* ignore */ } } };

  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, host, () => {
      const addr = server.address();
      resolve({
        server, host, port: addr.port, url: `http://${host}:${addr.port}`,
        close: () => new Promise((r) => { server.close(() => r()); server.closeAllConnections?.(); endCaps(); }),
        /** Graceful: stop accepting, let in-flight finish; force after graceMs. */
        shutdown: (graceMs = 2000) => new Promise((r) => {
          const t = setTimeout(() => { server.closeAllConnections?.(); endCaps(); r(); }, graceMs);
          server.close(() => { clearTimeout(t); endCaps(); r(); });
          server.closeIdleConnections?.();
        }),
      });
    });
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.on('uncaughtException', (e) => console.error('bridge uncaughtException:', e && e.message));
  process.on('unhandledRejection', (e) => console.error('bridge unhandledRejection:', e && e.message));
  startServer({}).then((s) => {
    console.error(`bridge listening on ${s.url} -> ${process.env.BRIDGE_UPSTREAM}`);
    let closing = false;
    const stop = () => { if (closing) return; closing = true; s.shutdown(2000).then(() => process.exit(0)); };
    process.on('SIGINT', stop);
    process.on('SIGTERM', stop);
  }).catch((e) => { console.error(e.message); process.exit(1); });
}
