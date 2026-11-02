# Messages-to-Responses bridge

A local proxy that lets Claude Code drive OpenAI reasoning models (for example `gpt-6.1-sol`) through a
LiteLLM gateway's `/v1/responses` route instead of its `/v1/messages` route. Claude models pass through
unchanged. Node 22+, standard library only.

Why: through LiteLLM's `/v1/messages`, GPT models report no prompt-cache use (charged at full price), return
empty thinking blocks, and give no way to check reasoning effort. The gateway's `/v1/responses` route has all
three. The bridge translates between the two contracts; see [DESIGN.md](DESIGN.md) for the mapping.

## Run

On the host, next to the gateway:

```bash
BRIDGE_UPSTREAM="$ANTHROPIC_BASE_URL" BRIDGE_LOG=bridge.log.jsonl node mxc-sandbox/bridge/bridge.mjs
# bridge listening on http://127.0.0.1:8788 -> <gateway>
```

Point Claude Code at it with `ANTHROPIC_BASE_URL=http://127.0.0.1:8788` and keep the gateway key in
`ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN`; the bridge forwards it and never stores or logs it. Inside MXC,
pass `--host-loopback` so the workload can reach `127.0.0.1` on the host:

```bash
mxc.ps1 run --workspace <ws> --host-loopback --env ANTHROPIC_BASE_URL=http://127.0.0.1:8788 --env ANTHROPIC_API_KEY \
  -- -p "..." --model gpt-6.1-sol --effort high --thinking-display summarized
```

| Variable | Default | Meaning |
|---|---|---|
| `BRIDGE_UPSTREAM` | required | Gateway base URL; a value without a scheme gets `http://` |
| `BRIDGE_HOST`, `BRIDGE_PORT` | `127.0.0.1`, `8788` | Listen address; a non-loopback host is refused |
| `BRIDGE_RESPONSES_MODELS` | `^(gpt-\|o\d\|azure-gpt-)` | Models sent to `/v1/responses`; the rest pass through |
| `BRIDGE_REASONING_MODELS` | GPT-5+ and o-series | Models that get `reasoning` and encrypted reasoning |
| `BRIDGE_EFFORT_MAP` | `low:low,medium:medium,high:high,xhigh:xhigh,max:xhigh` | Claude Code effort to `reasoning.effort` |
| `BRIDGE_SUMMARY` | `detailed` | `reasoning.summary`; `none` to omit |
| `BRIDGE_UPSTREAM_TIMEOUT_MS` | `300000` | Wait for upstream response headers |
| `BRIDGE_IDLE_TIMEOUT_MS` | `600000` | Longest silence inside a stream (reasoning can be silent for minutes) |
| `BRIDGE_MAX_BODY_BYTES` | 64 MiB | Largest accepted request body |
| `BRIDGE_LOG` | unset | JSONL per request: route, model, status, timings, usage (input, cached, cache write, output, reasoning) |
| `BRIDGE_CAPTURE_DIR` | unset | Saves each translated request and raw upstream stream, for replay |

## What it maps

- Request: `system` to `instructions` (Claude Code's per-request billing header is dropped so the prefix
  caches), messages to input items, `tool_use`/`tool_result` to `function_call`/`function_call_output`,
  in-conversation system messages to `developer` messages, `output_config.effort` to `reasoning.effort`,
  the session id to `prompt_cache_key`, deferred tools only once a `tool_reference` names them.
- Response: Responses SSE to Anthropic SSE (thinking, text and tool_use blocks), reasoning summaries to
  `thinking_delta`, usage to `input_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens`.
- Reasoning across turns: the encrypted reasoning is carried in the thinking block's `signature`
  (`rb1:` prefix). Claude Code sends signed thinking blocks back, and the bridge turns them into reasoning
  input items again.

## Gateway measurements (2026-11-02, `gpt-6.1-sol`, 3 repeats per effort)

Effort is applied on both routes; only the Responses route shows it. Mean tokens for one arithmetic prompt:

| effort | `/v1/messages` output tokens | `/v1/responses` reasoning tokens |
|---|---:|---:|
| low | 27 | 17 |
| medium | 30 | 19 |
| high | 42 | 42 |
| xhigh | 64 | 41 |

Cache: a repeated ~1.9k-token prefix read 1889 cached tokens on `/v1/responses`; `/v1/messages` reports no
cache fields for GPT and charges the uncached price.

## Verified (2026-11-02, Claude Code 2.1.316, gateway LiteLLM 1.91.5, inside MXC on macOS)

- Three-turn tool task with `gpt-6.1-sol`: correct answer; cache share 0%, 72%, 99.5% by turn; a thinking
  block with 430 characters of summary; reasoning tokens reported. Claude Code recorded the cache reads.
- Two parallel foreground subagents: 6 requests, all 200, correct answer.
- `claude-sonnet-5-5` through the bridge: passed through unchanged, its own cache intact.
- Full C2 run (`gpt-6.1-sol` high, 20261102T053248Z, 75 min): 391 requests, all 200; 91% of 18.7M input tokens
  cached; 91k reasoning tokens; 68 of 252 thinking blocks with summary text; the first GPT run to reach all five
  workflow stages.
- Direct `/v1/messages` for comparison: 0% cache in every GPT C2 run.

Tests: `cd mxc-sandbox/bridge && node --test test/*.test.mjs` (42 tests, no network).

Limits: images inside tool results become a separate user message; `stop_sequences` and sampling parameters
are dropped; `count_tokens` for bridged models is an estimate (characters / 4).
