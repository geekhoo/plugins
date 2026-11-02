import test from 'node:test';
import assert from 'node:assert/strict';
import { load, parseFrames } from './helpers.mjs';
import { SseTranslator, SseParser, mapNonStream, mapUsage } from '../bridge.mjs';

function translate(name, chunk = 1 << 30) {
  const sse = load(name);
  const tr = new SseTranslator('gpt-6.1-sol');
  const p = new SseParser();
  let out = '';
  for (let i = 0; i < sse.length; i += chunk) for (const ev of p.feed(sse.slice(i, i + chunk))) out += tr.push(ev).join('');
  for (const ev of p.flush()) out += tr.push(ev).join('');
  out += tr.end().join('');
  return { frames: parseFrames(out), tr };
}

test('function call stream', () => {
  const { frames, tr } = translate('responses-function-call.sse');
  const types = frames.map((f) => f.type);
  assert.deepEqual(types.slice(0, 2), ['message_start', 'content_block_start']);
  assert.deepEqual(types.slice(-3), ['content_block_stop', 'message_delta', 'message_stop']);
  assert.equal(frames[0].message.model, 'gpt-6.1-sol');
  assert.match(frames[0].message.id, /^msg_resp_/);
  const start = frames[1];
  assert.equal(start.index, 0);
  assert.equal(start.content_block.type, 'tool_use');
  assert.equal(start.content_block.name, 'get_weather');
  assert.equal(start.content_block.id, 'call_5BBuaLLxraLgXcpd1aVPTKrl');
  const json = frames.filter((f) => f.delta?.type === 'input_json_delta').map((f) => f.delta.partial_json).join('');
  assert.deepEqual(JSON.parse(json), { city: 'Paris' });
  const md = frames.at(-2);
  assert.equal(md.delta.stop_reason, 'tool_use');
  assert.deepEqual(md.usage, { input_tokens: 69, cache_read_input_tokens: 0, cache_creation_input_tokens: 0, output_tokens: 18 });
  assert.equal(tr.error, null);
});

test('reasoning + text stream, usage, signature', () => {
  for (const chunk of [1 << 30, 97]) {
    const { frames } = translate('responses-reasoning-text.sse', chunk);
    const types = frames.map((f) => f.type);
    assert.equal(types[0], 'message_start');
    assert.equal(types.at(-1), 'message_stop');
    assert.equal(types.at(-2), 'message_delta');
    const starts = frames.filter((f) => f.type === 'content_block_start');
    assert.deepEqual(starts.map((s) => [s.index, s.content_block.type]), [[0, 'thinking'], [1, 'text']]);
    // each block: start, deltas, stop, in order and non-overlapping
    let open = null;
    for (const f of frames) {
      if (f.type === 'content_block_start') { assert.equal(open, null); open = f.index; }
      else if (f.type === 'content_block_delta') assert.equal(f.index, open);
      else if (f.type === 'content_block_stop') { assert.equal(f.index, open); open = null; }
    }
    assert.equal(open, null);
    const thinking = frames.filter((f) => f.delta?.type === 'thinking_delta').map((f) => f.delta.thinking).join('');
    const sig = frames.find((f) => f.delta?.type === 'signature_delta').delta.signature;
    const text = frames.filter((f) => f.delta?.type === 'text_delta').map((f) => f.delta.text).join('');
    assert.ok(thinking.length > 0);
    assert.ok(sig.startsWith('rb1:'));
    const dec = JSON.parse(Buffer.from(sig.slice(4), 'base64url').toString());
    assert.match(dec.id, /^rs_/);
    assert.ok(dec.enc.startsWith('gAAAA'));
    // reassembles to the final text/summary recorded in the stream's done events
    const evs = load('responses-reasoning-text.sse').split('\n\n').map((b) => b.replace(/^data: /, '')).filter((s) => s.startsWith('{')).map((s) => JSON.parse(s));
    assert.equal(text, evs.find((e) => e.type === 'response.output_text.done').text);
    assert.equal(thinking, evs.find((e) => e.type === 'response.reasoning_summary_text.done').text);
    const md = frames.at(-2);
    assert.equal(md.delta.stop_reason, 'end_turn');
    assert.deepEqual(md.usage, { input_tokens: 3, cache_read_input_tokens: 1889, cache_creation_input_tokens: 42, output_tokens: 144 });
  }
});

test('synthetic: multiple summary parts, incomplete -> max_tokens, failed, truncated', () => {
  const tr = new SseTranslator('m');
  const evs = [
    { type: 'response.created', response: { id: 'r1' } },
    { type: 'response.output_item.added', output_index: 0, item: { type: 'reasoning', id: 'rs' } },
    { type: 'response.reasoning_summary_part.added', output_index: 0, summary_index: 0 },
    { type: 'response.reasoning_summary_text.delta', output_index: 0, summary_index: 0, delta: 'a' },
    { type: 'response.reasoning_summary_part.added', output_index: 0, summary_index: 1 },
    { type: 'response.reasoning_summary_text.delta', output_index: 0, summary_index: 1, delta: 'b' },
    { type: 'response.output_item.done', output_index: 0, item: { type: 'reasoning', id: 'rs', encrypted_content: 'E' } },
    { type: 'response.incomplete', response: { id: 'r1', status: 'incomplete', incomplete_details: { reason: 'max_output_tokens' }, usage: { input_tokens: 5, output_tokens: 7 } } },
  ];
  const frames = parseFrames(evs.flatMap((e) => tr.push(e)).join(''));
  assert.equal(frames.filter((f) => f.delta?.type === 'thinking_delta').map((f) => f.delta.thinking).join(''), 'a\n\nb');
  assert.equal(frames.at(-2).delta.stop_reason, 'max_tokens');

  const t2 = new SseTranslator('m');
  t2.push({ type: 'response.created', response: { id: 'r' } });
  const f2 = parseFrames(t2.push({ type: 'response.failed', response: { error: { message: 'boom' } } }).join(''));
  assert.equal(f2[0].type, 'error');
  assert.deepEqual(f2[0].error, { type: 'api_error', message: 'boom' });
  assert.deepEqual(t2.push({ type: 'response.output_text.delta', output_index: 0, delta: 'x' }), []);

  const t3 = new SseTranslator('m');
  t3.push({ type: 'response.created', response: { id: 'r' } });
  const f3 = parseFrames(t3.end().join(''));
  assert.equal(f3[0].type, 'error');
});

test('parser handles event: lines, CRLF, [DONE]', () => {
  const p = new SseParser();
  const evs = p.feed('event: response.created\r\ndata: {"response":{"id":"x"}}\r\n\r\ndata: [DONE]\r\n\r\n');
  assert.equal(evs.length, 1);
  assert.equal(evs[0].type, 'response.created');
});

test('mapNonStream', () => {
  const m = mapNonStream({ id: 'resp_1', status: 'completed', output: [
    { type: 'reasoning', id: 'rs1', summary: [{ text: 'x' }, { text: 'y' }], encrypted_content: 'E' },
    { type: 'message', content: [{ type: 'output_text', text: 'hello' }, { type: 'refusal', refusal: 'no' }] },
    { type: 'function_call', call_id: 'c', name: 'N', arguments: '{"a":1}' },
  ], usage: { input_tokens: 100, input_tokens_details: { cached_tokens: 60, cache_write_tokens: 10 }, output_tokens: 5 } }, 'gpt-x');
  assert.equal(m.id, 'msg_resp_1');
  assert.equal(m.stop_reason, 'tool_use');
  assert.equal(m.content[0].thinking, 'x\n\ny');
  assert.ok(m.content[0].signature.startsWith('rb1:'));
  assert.deepEqual(m.content.slice(1), [{ type: 'text', text: 'hello' }, { type: 'text', text: 'no' }, { type: 'tool_use', id: 'c', name: 'N', input: { a: 1 } }]);
  assert.deepEqual(m.usage, mapUsage({ input_tokens: 100, input_tokens_details: { cached_tokens: 60, cache_write_tokens: 10 }, output_tokens: 5 }));
  assert.equal(m.usage.input_tokens, 30); // 100 total - 60 cached - 10 written
});

test('truncated function call: incomplete max_output_tokens -> max_tokens (stream)', () => {
  const tr = new SseTranslator('m');
  const evs = [
    { type: 'response.created', response: { id: 'r1' } },
    { type: 'response.output_item.added', output_index: 0, item: { type: 'function_call', call_id: 'c1', name: 'Bash' } },
    { type: 'response.function_call_arguments.delta', output_index: 0, delta: '{"cmd":"l' },
    { type: 'response.incomplete', response: { id: 'r1', status: 'incomplete', incomplete_details: { reason: 'max_output_tokens' }, usage: {} } },
  ];
  const frames = parseFrames(evs.flatMap((e) => tr.push(e)).join(''));
  assert.equal(frames.at(-2).delta.stop_reason, 'max_tokens');
  assert.equal(frames.filter((f) => f.type === 'content_block_start').length, frames.filter((f) => f.type === 'content_block_stop').length);
});

test('truncated function call: mapNonStream -> max_tokens, tool_use dropped; content_filter -> refusal', () => {
  const m = mapNonStream({ id: 'r', status: 'incomplete', incomplete_details: { reason: 'max_output_tokens' }, output: [
    { type: 'function_call', call_id: 'c', name: 'N', arguments: '{"cmd":"l' }] }, 'gpt-x');
  assert.equal(m.stop_reason, 'max_tokens');
  assert.equal(m.content.length, 0);
  assert.equal(mapNonStream({ id: 'r', status: 'incomplete', incomplete_details: { reason: 'content_filter' }, output: [] }, 'x').stop_reason, 'refusal');
});
