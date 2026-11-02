import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { mapRequest, countTokens, encodeSignature, parseEffortMap } from '../bridge.mjs';

const fx = JSON.parse(fs.readFileSync(new URL('./fixtures/claude-code-request.json', import.meta.url), 'utf8'));
const opts = { effortMap: parseEffortMap(), summary: 'detailed' };

test('fixture request maps top-level fields', () => {
  const { responsesBody: r, dropped } = mapRequest(fx.body, opts);
  assert.equal(r.model, 'gpt-6.1-sol');
  assert.equal(r.max_output_tokens, 32000);
  assert.equal(r.stream, true);
  assert.deepEqual(r.reasoning, { effort: 'high', summary: 'detailed' });
  assert.equal(r.store, false);
  assert.deepEqual(r.include, ['reasoning.encrypted_content']);
  assert.equal(r.parallel_tool_calls, true);
  assert.equal(r.prompt_cache_key, 'cc-00000000-0000-4000-8000-000000000001');
  assert.ok(!r.instructions.includes('x-anthropic-billing-header'));
  assert.ok(!JSON.stringify(r).includes('cache_control'));
  assert.ok(dropped.includes('param:context_management'));
});

test('fixture: system message becomes developer, deferred placeholder dropped', () => {
  const { responsesBody: r, dropped } = mapRequest(fx.body, opts);
  assert.equal(r.input[0].role, 'user');
  assert.ok(r.input[0].content.every((c) => c.type === 'input_text'));
  assert.equal(r.input[1].role, 'developer');
  assert.equal(r.input[1].content[0].type, 'input_text');
  assert.ok(!r.tools.some((t) => t.name === 'DeferredToolPlaceholder'));
  assert.equal(r.tools.length, fx.body.tools.length - 1);
  assert.ok(r.tools.every((t) => t.type === 'function' && t.strict === false && t.parameters));
  assert.ok(dropped.some((d) => d.startsWith('tool:DeferredToolPlaceholder')));
});

test('effort map and defaults', () => {
  const b = { model: 'gpt-5', messages: [], output_config: { effort: 'max' } };
  assert.equal(mapRequest(b, opts).responsesBody.reasoning.effort, 'xhigh'); // max -> xhigh (gateway accepts xhigh)
  assert.equal(mapRequest({ model: 'gpt-5', messages: [] }, opts).responsesBody.reasoning.effort, 'medium');
  assert.equal(mapRequest({ model: 'gpt-5', messages: [], thinking: { type: 'enabled' } }, { ...opts, summary: 'none' }).responsesBody.reasoning.summary, undefined);
  assert.equal(mapRequest({ model: 'gpt-5', messages: [] }, opts).responsesBody.reasoning.summary, undefined);
});

test('string system, sampling params dropped, server tools dropped, tool_choice', () => {
  const body = {
    model: 'gpt-x', system: 'be brief', temperature: 0.2, top_p: 0.9, top_k: 5, stop_sequences: ['x'],
    messages: [{ role: 'user', content: 'hi' }],
    tools: [{ type: 'web_search_20250305', name: 'web_search' }, { name: 'a', description: 'd', input_schema: { type: 'object' } }],
    tool_choice: { type: 'any' },
  };
  const { responsesBody: r, dropped } = mapRequest(body, opts);
  assert.equal(r.instructions, 'be brief');
  for (const k of ['temperature', 'top_p', 'top_k', 'stop_sequences']) { assert.equal(r[k], undefined); assert.ok(dropped.includes('param:' + k)); }
  assert.equal(r.tools.length, 1);
  assert.equal(r.tool_choice, 'required');
  assert.deepEqual(r.input, [{ role: 'user', content: [{ type: 'input_text', text: 'hi' }] }]);
  for (const [tc, want] of [[{ type: 'auto' }, 'auto'], [{ type: 'none' }, 'none'], [{ type: 'tool', name: 'a' }, { type: 'function', name: 'a' }]]) {
    assert.deepEqual(mapRequest({ ...body, tool_choice: tc }, opts).responsesBody.tool_choice, want);
  }
});

test('round trip: tool_use, tool_result, rb1 thinking, images, foreign thinking', () => {
  const sig = encodeSignature('rs_1', 'ENC');
  const body = {
    model: 'gpt-x',
    messages: [
      { role: 'user', content: [{ type: 'text', text: 'go' }, { type: 'image', source: { type: 'base64', media_type: 'image/png', data: 'AAA' } }] },
      { role: 'assistant', content: [
        { type: 'thinking', thinking: 'foreign', signature: 'abc' },
        { type: 'redacted_thinking', data: 'x' },
        { type: 'thinking', thinking: 'mine', signature: sig },
        { type: 'text', text: 'calling' },
        { type: 'tool_use', id: 'call_1', name: 'Bash', input: { cmd: 'ls' } },
      ] },
      { role: 'user', content: [
        { type: 'tool_result', tool_use_id: 'call_1', content: [{ type: 'text', text: 'a' }, { type: 'text', text: 'b' }, { type: 'image', source: { type: 'base64', media_type: 'image/png', data: 'BBB' } }], is_error: true },
        { type: 'text', text: 'after' },
      ] },
    ],
  };
  const { responsesBody: r, dropped } = mapRequest(body, opts);
  assert.deepEqual(r.input, [
    { role: 'user', content: [{ type: 'input_text', text: 'go' }, { type: 'input_image', image_url: 'data:image/png;base64,AAA' }] },
    { type: 'reasoning', id: 'rs_1', summary: [{ type: 'summary_text', text: 'mine' }], encrypted_content: 'ENC' },
    { role: 'assistant', content: [{ type: 'output_text', text: 'calling' }] },
    { type: 'function_call', call_id: 'call_1', name: 'Bash', arguments: '{"cmd":"ls"}' },
    { type: 'function_call_output', call_id: 'call_1', output: '[tool error] a\nb' },
    { role: 'user', content: [{ type: 'input_image', image_url: 'data:image/png;base64,BBB' }] },
    { role: 'user', content: [{ type: 'input_text', text: 'after' }] },
  ]);
  assert.equal(dropped.filter((d) => d.startsWith('block:')).length, 2);
});

test('deferred tool included after tool_reference', () => {
  const tools = [{ name: 'Deferred', defer_loading: true, description: 'd', input_schema: { type: 'object' } }, { name: 'ToolSearch', description: 's', input_schema: { type: 'object' } }];
  const base = { model: 'gpt-x', tools, messages: [{ role: 'user', content: 'x' }] };
  assert.deepEqual(mapRequest(base, opts).responsesBody.tools.map((t) => t.name), ['ToolSearch']);
  const withRef = { ...base, messages: [...base.messages,
    { role: 'assistant', content: [{ type: 'tool_use', id: 'c1', name: 'ToolSearch', input: {} }] },
    { role: 'user', content: [{ type: 'tool_result', tool_use_id: 'c1', content: [{ type: 'tool_reference', tool_name: 'Deferred' }] }] }] };
  const r = mapRequest(withRef, opts).responsesBody;
  assert.deepEqual(r.tools.map((t) => t.name), ['Deferred', 'ToolSearch']);
  assert.equal(r.input.at(-1).output, 'Tool Deferred is now available.');
});

test('countTokens estimates chars/4', () => {
  const b = { system: 'x'.repeat(40), messages: [], tools: [] };
  const n = countTokens(b).input_tokens;
  assert.ok(n >= 10 && n <= 11, String(n));
  assert.ok(countTokens(fx.body).input_tokens > 1000);
});

test('billing header stripped: prefix is stable across requests', () => {
  const clone = (suffix, cch) => {
    const b = JSON.parse(JSON.stringify(fx.body));
    b.system[0].text = `x-anthropic-billing-header: cc_version=2.1.316.${suffix}; cc_entrypoint=cli; cch=${cch};`;
    return b;
  };
  const a = mapRequest(clone('aaa', '11111'), opts).responsesBody;
  const b = mapRequest(clone('bbb', '22222'), opts).responsesBody;
  assert.equal(a.instructions, b.instructions);
  assert.ok(!a.instructions.includes('x-anthropic-billing-header'));
  // string system with the header on its own line
  const s = mapRequest({ model: 'gpt-5', system: 'x-anthropic-billing-header: cc=1\nbe brief', messages: [] }, opts).responsesBody;
  assert.equal(s.instructions, 'be brief');
});

test('thinking disabled gives no summary; adaptive does', () => {
  const m = (thinking) => mapRequest({ model: 'gpt-5', messages: [], thinking }, opts).responsesBody.reasoning;
  assert.ok(!('summary' in m({ type: 'disabled' })));
  assert.equal(m({ type: 'adaptive' }).summary, 'detailed');
});

test('orphan reasoning item is not replayed', () => {
  const sig = encodeSignature('rs_1', 'ENC');
  const mk = (assistant) => mapRequest({ model: 'gpt-5', messages: [
    { role: 'user', content: 'a' }, { role: 'assistant', content: assistant }, { role: 'user', content: 'b' }] }, opts).responsesBody.input;
  assert.ok(!mk([{ type: 'thinking', thinking: 't', signature: sig }]).some((i) => i.type === 'reasoning'));
  assert.ok(!mk([{ type: 'thinking', thinking: 't', signature: sig }, { type: 'text', text: '' }]).some((i) => i.type === 'reasoning'));
  assert.ok(mk([{ type: 'thinking', thinking: 't', signature: sig }, { type: 'text', text: 'ok' }]).some((i) => i.type === 'reasoning'));
});

test('parallel tool results stay contiguous; images follow; image-only placeholder', () => {
  const img = (d) => ({ type: 'image', source: { type: 'base64', media_type: 'image/png', data: d } });
  const { responsesBody: r } = mapRequest({ model: 'gpt-5', messages: [
    { role: 'assistant', content: [{ type: 'tool_use', id: 'a', name: 'X', input: {} }, { type: 'tool_use', id: 'b', name: 'X', input: {} }] },
    { role: 'user', content: [
      { type: 'tool_result', tool_use_id: 'a', content: [img('AAA')] },
      { type: 'tool_result', tool_use_id: 'b', content: 'two' }] }] }, opts);
  const kinds = r.input.map((i) => i.type || i.role);
  assert.deepEqual(kinds, ['function_call', 'function_call', 'function_call_output', 'function_call_output', 'user']);
  assert.equal(r.input[2].output, '[image attached below]');
  assert.equal(r.input[3].output, 'two');
});

test('reasoning params only for reasoning models', () => {
  const g4 = mapRequest({ model: 'gpt-4.1', messages: [] }, opts).responsesBody;
  assert.ok(!('reasoning' in g4) && !('include' in g4));
  assert.equal(g4.store, false);
  const g5 = mapRequest({ model: 'gpt-5', messages: [] }, opts).responsesBody;
  assert.ok(g5.reasoning && g5.include);
  assert.ok(!('reasoning' in mapRequest({ model: 'gpt-4o', messages: [] }, opts).responsesBody));
  assert.ok(mapRequest({ model: 'o3', messages: [] }, opts).responsesBody.reasoning);
});

test('max_output_tokens floor of 16', () => {
  assert.equal(mapRequest({ model: 'gpt-5', max_tokens: 1, messages: [] }, opts).responsesBody.max_output_tokens, 16);
  assert.equal(mapRequest({ model: 'gpt-5', max_tokens: 500, messages: [] }, opts).responsesBody.max_output_tokens, 500);
});

test('parallel_tool_calls follows disable_parallel_tool_use and needs tools', () => {
  const tools = [{ name: 'a', input_schema: { type: 'object' } }];
  const m = (b) => mapRequest({ model: 'gpt-5', messages: [], ...b }, opts).responsesBody;
  assert.equal(m({ tools, tool_choice: { type: 'auto', disable_parallel_tool_use: true } }).parallel_tool_calls, false);
  assert.equal(m({ tools }).parallel_tool_calls, true);
  assert.ok(!('parallel_tool_calls' in m({})));
});

test('effort map passes xhigh through and maps max to xhigh', async () => {
  const { mapRequest, parseEffortMap } = await import('../bridge.mjs');
  const body = { model: 'gpt-6.1-sol', max_tokens: 100, messages: [{ role: 'user', content: 'hi' }], thinking: { type: 'adaptive' } };
  for (const [e, want] of [['xhigh', 'xhigh'], ['max', 'xhigh'], ['high', 'high']]) {
    const { responsesBody } = mapRequest({ ...body, output_config: { effort: e } }, { effortMap: parseEffortMap() });
    assert.equal(responsesBody.reasoning.effort, want, e);
  }
});

test('upstream without a scheme gets http://', async () => {
  const { normalizeUpstream } = await import('../bridge.mjs');
  assert.equal(normalizeUpstream('litellm.corp.example.<proxy>.localhost:7891/'), 'http://litellm.corp.example.<proxy>.localhost:7891');
  assert.equal(normalizeUpstream('https://gw.example.com'), 'https://gw.example.com');
});
