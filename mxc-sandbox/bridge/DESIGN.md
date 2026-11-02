# Messages-to-Responses bridge: design

Claude Code speaks the Anthropic Messages API. Through LiteLLM's `/v1/messages` route, GPT models lose three
things: prompt-cache reporting (no cache fields, full price), reasoning text (thinking blocks always empty), and
any way to check effort. The same gateway's `/v1/responses` route has all three (probed 2026-11-02 with
`gpt-6.1-sol`: `cached_tokens` 1889 of 1934 on a second turn, streamed reasoning summaries, `encrypted_content`,
`reasoning_tokens`). The bridge sits between Claude Code and the gateway and translates Messages to Responses
for selected models. Everything else passes through unchanged.

It runs on the host. The MXC workload reaches it with `--host-loopback` (verified: claude inside MXC reached
`127.0.0.1:8790`). Node 22+, standard library only (Santa allows node by TeamID; no npm install on the host).

## Process and configuration

`node mxc-sandbox/bridge/bridge.mjs` with environment:

| Variable | Default | Meaning |
|---|---|---|
| `BRIDGE_UPSTREAM` | required | Gateway base URL, e.g. the value of `ANTHROPIC_BASE_URL`; a value without a scheme gets `http://` |
| `BRIDGE_HOST`, `BRIDGE_PORT` | `127.0.0.1`, `8788` | Listen address. Never bind a non-loopback address. |
| `BRIDGE_RESPONSES_MODELS` | `^(gpt-|o\d|azure-gpt-)` | Regex on the request `model`; matches go to `/v1/responses`, the rest pass through |
| `BRIDGE_EFFORT_MAP` | `low:low,medium:medium,high:high,xhigh:xhigh,max:xhigh` (the gateway accepts `xhigh`) | `output_config.effort` → `reasoning.effort` |
| `BRIDGE_SUMMARY` | `detailed` | `reasoning.summary` (`detailed`, `auto`, `none` to omit) |
| `BRIDGE_LOG` | unset | JSONL file: one line per request (time, route, model, status, durations, mapped counts, usage) |
| `BRIDGE_UPSTREAM_TIMEOUT_MS`, `BRIDGE_IDLE_TIMEOUT_MS` | `300000`, `600000` | Header wait; longest silence in a stream (reasoning can be silent for minutes) |
| `BRIDGE_CAPTURE_DIR` | unset | If set, write each translated request and the raw upstream SSE per request id (for replay and debugging) |

Auth: no key is stored. The client's `x-api-key` or `Authorization: Bearer` value is forwarded to the upstream as
`Authorization: Bearer <value>`. Never log header values.

## Routes

- `POST /v1/messages` (query string such as `?beta=true` preserved for pass-through): translate if the model
  matches `BRIDGE_RESPONSES_MODELS`, else proxy byte-for-byte (request and streamed response piped).
- `POST /v1/messages/count_tokens`: matched models get a local estimate `{input_tokens: ceil(chars/4)}` over
  system, messages and tool schemas; others pass through.
- `GET /health`: `{ok: true, upstream, models_regex}`. Everything else passes through.

## Request mapping (Messages → Responses)

| Messages | Responses |
|---|---|
| `model` | `model` (unchanged) |
| `system` (string, or array of text blocks; drop `cache_control` and Claude Code's per-request `x-anthropic-billing-header:` block) | `instructions` (texts joined with `\n\n`) |
| `max_tokens` | `max_output_tokens` |
| `stream` | `stream` |
| `output_config.effort` | `reasoning.effort` via `BRIDGE_EFFORT_MAP`; default `medium` if absent |
| `thinking` (any) | `reasoning.summary = BRIDGE_SUMMARY` |
| always | `store: false`, `include: ["reasoning.encrypted_content"]`, `parallel_tool_calls: true` |
| `metadata.user_id` (JSON string with `session_id`) | `prompt_cache_key = "cc-" + session_id` (stable per session, so the prefix caches) |
| `tools[]` custom tools (`name`, `description`, `input_schema`) | `{type: "function", name, description, parameters: input_schema, strict: false}` |
| tools with `defer_loading: true` | included only if a `tool_reference` with that name appears in the messages; the placeholder tool is dropped |
| server tools (with a `type` such as `web_search_*`) | dropped (logged) |
| `tool_choice` `auto`/`any`/`{type:tool,name}`/`none` | `auto`/`required`/`{type:"function",name}`/`none` |
| `temperature`, `top_p`, `top_k`, `stop_sequences`, `context_management`, `anthropic-beta` | dropped (reasoning models reject sampling params; Responses has no stop sequences) |

`messages[]` become `input[]` items, in order:

| Message content | Responses input item |
|---|---|
| `role: user`, `text` blocks (string content = one text block) | `{role: "user", content: [{type: "input_text", text}]}` (consecutive text blocks in one message) |
| `role: user`, `image` block (base64) | `{type: "input_image", image_url: "data:<media_type>;base64,<data>"}` in that user message |
| `role: user`, `tool_result` block | `{type: "function_call_output", call_id: tool_use_id, output: <text>}`; text = joined text parts; `is_error` prefixes `"[tool error] "`; `tool_reference` parts become `"Tool <name> is now available."`; images inside a result become a following user message with `input_image` |
| `role: system` message inside `messages` | `{role: "developer", content: [{type: "input_text", text}]}` |
| `role: assistant`, `text` block | `{role: "assistant", content: [{type: "output_text", text}]}` |
| `role: assistant`, `tool_use` block | `{type: "function_call", call_id: id, name, arguments: JSON.stringify(input)}` |
| `role: assistant`, `thinking` block whose `signature` starts with `rb1:` | `{type: "reasoning", id, summary: [{type: "summary_text", text: thinking}], encrypted_content}` decoded from the signature |
| `thinking` without an `rb1:` signature, `redacted_thinking` | dropped (it came from another model) |

Item order inside an assistant message is kept (reasoning, text, function calls as they appear). A
`function_call_output` must follow its `function_call`; the Messages order already guarantees that.

## Response mapping (Responses SSE → Messages SSE)

The gateway sends `data:` lines only (no `event:` lines) and ends with `data: [DONE]`. Parse both forms.

Emit Anthropic events with `event: <type>` and `data: <json>` lines:

1. On `response.created`: `message_start` with `{id: "msg_" + response.id, type: "message", role: "assistant",
   model: <request model>, content: [], stop_reason: null, stop_sequence: null, usage: {input_tokens: 0,
   output_tokens: 0}}`.
2. Each Responses output item gets the next Anthropic content block index:
   - `reasoning` item: `content_block_start {type: "thinking", thinking: "", signature: ""}`;
     `response.reasoning_summary_text.delta` → `content_block_delta {type: "thinking_delta", thinking}`, with
     `"\n\n"` between summary parts; on `response.output_item.done` → `signature_delta` with
     `"rb1:" + base64url(JSON.stringify({id, enc: encrypted_content}))`, then `content_block_stop`.
   - `message` item: each `output_text` part → `content_block_start {type: "text", text: ""}`,
     `response.output_text.delta` → `text_delta`, part done → `content_block_stop`. A `refusal` part is text.
   - `function_call` item: `content_block_start {type: "tool_use", id: call_id, name, input: {}}`,
     `response.function_call_arguments.delta` → `input_json_delta {partial_json}`, item done →
     `content_block_stop`.
3. On `response.completed` (or `response.incomplete`): `message_delta {delta: {stop_reason, stop_sequence:
   null}, usage: {input_tokens: input - cached - cache_write, cache_read_input_tokens: cached,
   cache_creation_input_tokens: cache_write, output_tokens}}` (Anthropic input_tokens excludes both cache reads and
   writes; OpenAI input_tokens includes both)` then `message_stop`. `stop_reason`: `tool_use` if any function call,
   `max_tokens` if incomplete for `max_output_tokens`, else `end_turn`.
4. `response.failed`, `error` events, or a broken upstream stream: emit `event: error` with
   `{type: "error", error: {type: "api_error", message}}` and end. An upstream HTTP error before streaming
   returns the same status with an Anthropic error body `{type: "error", error: {type, message}}`.
5. While waiting for upstream, send `event: ping` (`{type: "ping"}`) every 15 s.

Non-streaming requests: same mapping, returned as one Messages JSON object.

## Logging and evidence

`BRIDGE_LOG` lines carry: `ts, req_id, route (responses|passthrough), model, effort, status, ms_first_byte,
ms_total, items_in, tools_in, tools_dropped, usage {input, cached, cache_write, output, reasoning}`. A run's
log shows whether caching and reasoning worked without reading the transcript.

## Tests (node --test, no network)

- Request mapping against `test/fixtures/claude-code-request.json` (shortened capture of a real Claude Code
  2.1.316 request: system array with cache_control, a `role: system` message, adaptive thinking,
  `output_config.effort`, deferred placeholder tool).
- Round trip: tool_use + tool_result, thinking with an `rb1:` signature → reasoning item, deferred tool included
  after a `tool_reference`.
- SSE translation of the two recorded gateway streams (`responses-function-call.sse`,
  `responses-reasoning-text.sse`): event order, block indices, deltas reassemble to the final text and
  arguments, usage mapping (cached 1889 → `cache_read_input_tokens`), stop reasons.
- Server: a mock upstream on a random port; pass-through of a Claude model is byte-identical; errors map.
