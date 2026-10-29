# Minimal Claude/MXC Messages API tool checks

27 October 2026. **Four models passed the real Claude Code → MXC → LiteLLM
Messages tool roundtrip. Two routes returned upstream resource/routing 404s
before a tool call. Both C0 evaluations remain stopped.**

| Requested model | Correct-route Messages attempts | HTTP | Native MCP roundtrip | MXC/Claude exit |
|---|---:|---|---|---:|
| `vercel/gpt-6-luna` | 2 | 200, 200 | PASS | 0 |
| `vercel/minimax-m3` | 1 | 404 | Not reached | 1 |
| `vercel/glm-5.3-flash` | 2 | 200, 200 | PASS | 0 |
| `vercel/deepseek-v4.1-flash-1017` | 1 | 404 | Not reached | 1 |
| `vercel/claude-haiku-5.5` | 2 | 200, 200 | PASS | 0 |
| `vercel/mimo-v2.6-pro` | 2 | 200, 200 | PASS | 0 |

Each passing lane generated an actual `tool_use`, executed the stdlib MCP echo
server inside MXC exactly once with the required input, sent its correlated
`tool_result` to LiteLLM, and returned the exact tool-only result marker. The
marker was absent from the first request. IDs match across the first response,
second request and native MCP evidence. Stop reasons were `tool_use` then
`end_turn`. This is actual Claude harness/tool behavior, not direct HTTP-only
or scripted-model proof. No C0 prompt, oracle, score, judge or workflow ran.

## Exact scope and configuration

- Fresh workspaces, homes, config, temp and MXC state per model under dedicated
  `C:\repos\mxc-claude-messages-*` roots.
- Installed Claude Code **2.1.311**, with its current binary SHA recorded. This
  differs from the earlier evaluation's CLI version and is not assumed equivalent.
- Vetted MXC SDK **1.0.1** Windows ProcessContainer build, native EXE/DLL pins and
  complete 18-file build manifest verified. Direct MXC host execution used the
  same source-backed Claude workload path, bypassing the full evaluation runner.
- Bare print mode, replaced minimal system prompt, built-ins disabled, one explicit
  MCP server, max two agent turns, no session persistence/hooks/plugin discovery.
  Every model alias was pinned to the requested model.
- Captured real requests: `POST /v1/messages?beta=true`, forwarded unchanged to
  LiteLLM's `/v1/messages?beta=true`; streaming, `max_tokens=256`,
  `output_config.effort=low`, no `thinking` field, only `mcp__probe__echo` exposed.
- A diagnostic relay injected the actual LiteLLM key only upstream. The workload
  received a temporary local credential. Real provider credentials never entered
  its argv/config. Headers were not logged. The relay buffered bounded responses
  for redaction; this is not a streaming-latency benchmark.

The four passing lanes reported **2,379 input and 252 output tokens**, with zero
thinking tokens reported by the CLI. These fields do not independently establish
billing or effective provider thinking settings. Counts are local forwarded HTTP
attempts, not necessarily internal provider attempts.

## Failures and operator correction

MiniMax returned `not_found_error`, wrapping `litellm.NotFoundError` /
`MinimaxException` and resource-not-found evidence. DeepSeek returned the same
outer class with `DeepseekException` and upstream 404 evidence. Neither had a
fallback model group. This establishes failure to reach a usable provider resource
on this Messages route, not tool-schema incompatibility or a proven nonexistent
model. Both had previously answered through Responses; the API paths must be
qualified independently. No reliable internal-attempt counters were exposed.

After each provider error, two further client attempts were blocked locally
because there was no correlated tool result. They were not forwarded. CLI retry
controls and turn limits alone are therefore not treated as a hard API-call limit.

The operator's first relay incorrectly derived `/messages` from the proxy's
supported `/responses` alias. Those six HTTP 404 attempts are preserved separately
and excluded from model compatibility results. The endpoint OpenAPI schema
confirmed `/v1/messages` (service version 1.106.0), then the relay path was corrected
and fresh isolated checks performed. Total external posts in this task: **16**
(six misrouted plus ten correct-route attempts), plus one read-only schema GET.
There were also two local fake-service requests for the real-harness preflight;
those contacted no provider and are not live-model results.

## Evidence and limitations

Ignored `outputs/mxc-claude-messages-20261027/` retains initial attempts and the
mapping correction, route-discovery.json, source scripts and local preflight.
`corrected-route/` contains fresh authorizations, per-model launch/controller,
Claude stream/stderr, request/response captures, HTTP summaries, MCP reports and
cleanup records. verification.json binds all evidence and confirms containment
and historical preservation. Independent offline audit confirmed the four ID-
correlated roundtrips and the two provider-resource failures.

These are minimal Messages tool checks, not full orchestration, native Codex V2,
encryption or C0 qualification. No commits/pushes, judge or explicit telemetry
operations occurred. All diagnostic listeners and native processes were checked
after closeout. Root/plugin READMEs and readiness link this record; historical
results remain unchanged. See [kanban](kanban.md), [handoff](handoff.md),
[references](references.md).
