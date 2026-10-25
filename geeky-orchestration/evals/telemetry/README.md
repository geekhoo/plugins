# Langfuse telemetry for MXC eval runs

Both runners can send every eval session to Langfuse in full. The Claude Code runner is `run-baseline.ps1` and the Codex runner is `run-codex-baseline.ps1`. "In full" means every turn, model generation, subagent or child thread, tool call with its input and output, and thinking or reasoning summary, with nothing truncated. Use the traces to inspect, evaluate and score runs alongside `score-run.py`.

Each harness uses Langfuse's own transcript hook, pinned in `pins.json` and verified by SHA-256:

| Harness | Hook | Runs | Full-content settings |
|---|---|---|---|
| Claude Code | [`langfuse/claude-observability-plugin`](https://github.com/langfuse/claude-observability-plugin) `hooks/langfuse_hook.py` (Python, `langfuse` SDK) | `Stop` and `SessionEnd`, from the run's `--settings` | `CC_LANGFUSE_MAX_CHARS=2147483647`, skill content captured, `showThinkingSummaries: true` |
| Codex | [`@langfuse/codex-observability-plugin`](https://github.com/langfuse/codex-observability-plugin) `dist/index.mjs` (Node 22+, self-contained bundle) | `Stop`, registered through the profile's `-c hooks=...` overrides and trusted by its exact command. That command is `agent-py python <run home>/langfuse-tracer.py`, which runs node with the bundle, so no shell has to quote a path like `C:\Program Files\nodejs\node.exe` | Never truncates; `model_reasoning_summary = "detailed"` |

Each hook reads the transcript the harness already writes and uploads it over OTLP. That is the Claude session JSONL and `subagents/` folder, or the Codex rollout and its child-thread rollouts. The hooks fail open, so an upload problem never stops a run.

Thinking: in `claude -p` runs, Claude Code asks for `display: "omitted"` thinking by default, which leaves only signatures in the transcript. All 124 thinking blocks in C1 run 6 were empty. `showThinkingSummaries` makes it request API-side summaries instead. Codex runs used `summary: none`, so their reasoning was encrypted only. Summaries are the only plaintext reasoning either vendor returns; raw reasoning stays provider-encrypted.

## Setup (once per host)

```powershell
pwsh -File geeky-orchestration/evals/telemetry/install-telemetry-tools.ps1   # needs uv; Node 22+ for Codex
```

This installs, under `<ToolsDir>`, which defaults to `C:\repos\.eval-tools` on Windows and `~/repos/.eval-tools` elsewhere:
- `langfuse/claude-hook/<commit>/langfuse_hook.py`
- `langfuse/codex-tracing/<version>/dist/index.mjs`
- `langfuse-py`, a venv with the pinned `langfuse` SDK

## Environment

Telemetry is on when the host has `TRACE_TO_LANGFUSE=true`. Pass `-NoTelemetry` to a runner to turn it off.

| Variable | Used by |
|---|---|
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` | Claude; Codex fallback |
| `LANGFUSE_CODEX_PUBLIC_KEY`, `LANGFUSE_CODEX_SECRET_KEY`, `LANGFUSE_CODEX_BASE_URL` | Codex (take precedence) |
| `LANGFUSE_TRACING_ENVIRONMENT` | both (default `eval`) |
| `CC_LANGFUSE_TRACE_TAGS` / `LANGFUSE_CODEX_TAGS` | appended to the run tags |
| `LANGFUSE_USER_ID` / `LANGFUSE_CODEX_USER_ID` | user on traces (default `geeky-eval-agent`) |

Keys reach the sandbox only as bare `--env NAME`. The MXC host copies the value and never prints it. Codex always gets an explicit `LANGFUSE_CODEX_USER_ID`, so its hook never reads `CODEX_HOME/auth.json`. When the host trusts a private CA through `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE` or `NODE_EXTRA_CA_CERTS`, those variables pass through with a read-only grant on the bundle's folder.

## Finding a run in Langfuse

Every trace carries these tags: `geeky-eval`, `harness:<claude-code|codex>`, `case:<case>`, `run:<stamp>`, `plugin:<sha7>`, plus `mock` for mock runs. The Langfuse session id is the run's `session_id` in `run.json`, which is the Claude session id or the Codex main thread id.

After each run the runner reads the session back with `langfuse-run.py` and writes `langfuse.json` (counts by type, usage totals, truncated observations). It records `telemetry.delivered` and `telemetry.observations` in `run.json`. Claude runs also keep the hook log as `langfuse-hook.log`. To pull a session in full, including all inputs and outputs:

```powershell
python geeky-orchestration/evals/telemetry/langfuse-run.py --session-id <id> --output summary.json --full observations.json
```

`langfuse-run.py` reads `/api/public/v2/observations`, the only read API on Langfuse v4 events-only deployments.

## Harness coverage

`langfuse-coverage.py` checks which harness points a session reached, using its Langfuse observations: all five skills, subagents, the coder and reviewer roles, planning gates, pytest, commits, file edits, reasoning summaries and token usage. It also reports nested subagents (the agent may run `geeky-implement` itself or delegate it to `geeky-implement-orchestrator`), MCP gate tools and encrypted Codex handoffs as information only. The runners call it after each run and write `langfuse-coverage.json`, plus `telemetry.coverage_complete` and `telemetry.coverage_missed` in `run.json`. Run it on demand too:

```powershell
python geeky-orchestration/evals/telemetry/langfuse-coverage.py --session-id <id>
```

It was calibrated on two real sessions, Claude C1 run 6 and Codex C1 run 3 (replayed through the pinned tracers under `environment=smoke`). Both hit every point except reasoning summaries, which those runs predate. `cases/c0-wordstat` is the minimal case built to hit every point; see its `spec.md`.

## Known limits

- **Codex inter-agent payloads are encrypted by the provider.** `spawn_agent`, `send_message` and `followup_task` arguments, and the `agent_message` a child thread receives, carry `encrypted_content` (`encrypted_function_args`), so no plaintext exists on disk or in Langfuse. Each thread's own messages, tool calls and outputs are plaintext. Coverage counts these handoffs as `encrypted_handoffs`.
- **A stage counts when its SKILL.md is read.** Codex reads skills by opening the file, and an agent may read every skill up front: Codex C0 attempt 5 hit `stage:impl-review` without reaching it. Check the commits and the review files when a stage matters.
- **Raw reasoning stays encrypted**; only the summaries are plaintext.
- **Export timeout.** Both SDKs cap one OTLP export at `LANGFUSE_TIMEOUT` seconds, 5 by default. A full session needs longer, so the runners pass `LANGFUSE_TIMEOUT=300`. Without it, the C1 Codex run 3 replay delivered nothing while the hook still exited 0.
- **Proxies.** The Codex tracer's exporter uses Node's `http` module, which ignores `HTTPS_PROXY`. It needs direct egress to Langfuse, which the MXC sandbox provides.

## Mock runs

The mocks exercise the real hooks with no model calls. `mock_claude.py` runs the `--settings` `Stop` hooks on its transcript and fails on any hook error. `mock_codex.py` runs the configured `Stop` hook on a turn-shaped rollout and requires the tracer's `.langfuse` delivery sidecar to record the turn. `run-mock-matrix.ps1` runs both harnesses on every case and fails a run whose session never reached Langfuse.

## Parity note

Telemetry changes the contestant setup: one extra `Stop` (and `SessionEnd`) hook, plus summarized thinking and reasoning. A run with telemetry is a different configuration from the earlier stored baselines (D101).
