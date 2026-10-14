# geeky_mcp — MCP server for the quality gates

A stdio [Model Context Protocol](https://modelcontextprotocol.io) server that exposes
the geeky-orchestration deterministic gates as tools, so **any** MCP-capable agent
(Claude Code, Cursor, OpenAI Agents SDK, LangGraph, …) can run them without
per-framework hook configuration.

It is a **thin adapter**: each tool shells out to the matching validator script under
`../scripts` (or `../hooks`) with its `--json` flag and returns the parsed report. The
scripts remain the single source of truth — MCP output is identical to the CLI/hook
output, and there is no logic duplication.

## Tools (all read-only)

| Tool | Wraps | Returns |
|---|---|---|
| `geeky_validate_planning_folder` | `validate-planning-folder.py` | folder completeness report |
| `geeky_validate_task_schema` | `validate-task-schema.py` | per-task required-section report |
| `geeky_validate_kanban` | `validate-kanban.py` | lane integrity (untracked / ambiguous / WIP / dangling) |
| `geeky_check_dod` | `check-dod.py` | Definition-of-Done for one task + its validation block |
| `geeky_check_commit` | `check-commit.py` | Conventional-Commit + task-ref check |
| `geeky_check_frozen_artifact` | `guard-planning-contract.py` | whether a path is a frozen planning artifact (pre-edit guardrail) |

A non-zero exit from a validator is a **validation failure** (`ok: false`), not a
server error; the tool still returns its structured report.

## Run

```bash
# Preferred — ephemeral env, no global install:
uv run --with "mcp>=1.2.0" python server.py

# Or, with mcp installed into your environment:
pip install mcp
python server.py
```

In Claude Code the server starts automatically: `.mcp.json` at the plugin root registers
it as the `geeky` server using `uv run --with "mcp>=1.2.0"`.

From version 0.3.0, the Codex-specific manifest uses `cwd: "./mcp"` and
`python server.py`. Codex resolves the working directory against the installed
plugin root, so startup does not depend on `${PLUGIN_ROOT}` substitution or a
version-specific cache path. Claude retains its own `${CLAUDE_PLUGIN_ROOT}` config.

## Node mirror

`server.mts` is a dependency-free Node/TypeScript twin of `server.py` for machines without
`uv` or a working Python. Same six tools, same input schemas and descriptions, same result
documents; it shells out to the `.mts` twins of the validators instead of the `.py` ones.

```bash
node server.mts          # Node 22.18+ (TypeScript runs natively via type stripping)
```

To make a harness use it, change the server command, e.g. in `.mcp.json`:
`"command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.mts"]`.

- **Parity is tested, not asserted.** `wire-baseline.mts` is a port of `wire_baseline.py`;
  `../tests/mcp-server.test.mts` drives the Node server with it and requires the normalised
  transcript to equal the committed `wire_baseline.json`. (The committed capture was taken on
  Windows, so the test collapses the doubled `//` that normalising a JSON-escaped `\\`
  separator leaves in one `content[].text` path.)
- **No SDK.** Line-delimited JSON-RPC 2.0 is implemented in the file (as in
  `semantic-design-system`), because plugin installs never run `npm install`. It answers the
  2025-11-25 handshake and earlier revisions, and returns `-32601` for methods it does not
  serve (including the stateless 2026-07-28 `server/discover`), so hosts fall back exactly as
  they do for `mcp` 1.x.
- **Same subprocess rule** (below): validators that are not fed text get `stdio: "ignore"`,
  never `"inherit"`; `../tests/mcp-server.test.mts` pins the spawn site.
- Startup is one Node process with no imports beyond the standard library.
- **Deliberate differences**, none of which change a pass/fail verdict: validation-error
  text omits pydantic's `[type=…, input_value=…]` suffix and docs URL; usage lines name the
  `.mts` script; invalid UTF-8 on a validator's stdin becomes U+FFFD instead of a traceback;
  a malformed JSON-RPC line gets a `-32700`/`-32600` reply; `prompts/get` and
  `resources/read` are not served (no prompts or resources are offered).

Tests and type-check (dev only; the runtime needs nothing installed):

```bash
cd .. && npm install && npm test && npm run typecheck
```

## Inspect / debug

```bash
# MCP Inspector (interactive tool explorer):
npx @modelcontextprotocol/inspector uv run --with "mcp>=1.2.0" python server.py

# List registered tools:
uv run --with "mcp>=1.2.0" python -c "import asyncio, server; print([t.name for t in asyncio.run(server.mcp.list_tools())])"
```

## Requirements

- The `mcp` package, either major — `server.py` runs unchanged on 1.x and 2.x and is
  resolved automatically by `uv run --with "mcp>=1.2.0"`.
- `uv` on PATH for the default `.mcp.json` command. To use plain `python` instead, edit
  `.mcp.json` to `"command": "python", "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]`
  and ensure `mcp` is installed.
- **Python 3.14**, pinned by `.python-version`. `pyproject.toml` still declares
  `requires-python = ">=3.10"` — the server code needs nothing newer — but the venv `uv`
  builds here is pinned, for the reason in [Wire baseline](#wire-baseline) below. `uv`
  downloads 3.14 on first launch if the machine does not already have it. Both harness
  projections (`.mcp.json` and `.codex-plugin/mcp.json`) set `cwd` to this directory, so
  the pin applies to Claude and Codex alike.

The wrapped validators are standard-library only and need no packages.

## Wire baseline

`wire_baseline.py` drives the real server over stdio and writes a normalised transcript of
`initialize`, `tools/list`, and one `tools/call` per tool. `wire_baseline.json` is the
committed capture; diffing a fresh run against it is what proves an SDK or transport change
did not alter the wire.

```bash
uv run --with "mcp>=2.0.0" python wire_baseline.py --out /tmp/v2.json
diff wire_baseline.json /tmp/v2.json
```

It is deliberately outside pytest — every run pays a `uv` resolve.

**Why the interpreter is pinned.** Tool descriptions are the handler docstrings, and
CPython 3.13 changed the compiler to strip leading indentation from docstrings (3.10–3.12
keep it). The same server therefore emits differently formatted descriptions either side of
that change, and the baseline — diffed byte for byte — fails in all six descriptions for a
reason that has nothing to do with the server or the SDK. `requires-python = ">=3.10"` let
`uv` pick any interpreter when building the venv, so this failed silently the moment a venv
was rebuilt on an older Python. `.python-version` removes the choice; `MIN_PYTHON` in
`wire_baseline.py` refuses to capture below 3.13 rather than write a baseline that cannot
diff.

## Subprocess rule

**A subprocess of a stdio MCP server must never be handed the transport.** On stdio this
server's own stdin *is* the pipe the host talks to it on. `stdin=None` means *inherit*, and
a validator that inherits it stalls before executing any code — the child is released only
when the server's own pending read on that pipe completes, so in practice the tool call
never returns. Four of the six tools hung this way until 0.2.15; the two that feed a message
on stdin always got their own pipe, which made the failure look partial.

`_run` therefore passes `DEVNULL` to every validator that is not fed text. `../test_mcp_server.py`
asserts this against the source on every test run — no `uv` resolve, no server launch — because
the wire baseline that would otherwise catch it is not part of the suite.

## Startup cost

The host launches a stdio server **twice per connection**: a short-lived `server/discover`
process that negotiates the protocol revision and exits, then the session process. This is
host behaviour on both SDK majors — the server does not opt in and cannot decline it — and it
is paid once per connection, never per tool call.

Measured on Windows 11, Claude Code 2.1.237, warm, launch → first response:

| | `mcp` 1.29.0 | `mcp` 2.0.0 |
|---|---|---|
| per process (`uv run`, mean of 5) | 0.96 s | 1.42 s |
| per process (direct venv python) | 0.78 s | 1.14 s |
| per connection (both processes) | ~1.8 s | ~2.2 s |

The `uv` overlay accounts for only 0.10–0.23 s of that; the rest is the SDK import (680 ms
vs 913 ms). 2.x is dearer because it builds a full Pydantic model graph **per protocol
revision it supports**, and it supports two.

On 2.x the host uses the stateless 2026-07-28 exchange (no `initialize`); on 1.x it falls
back to the v1 handshake at 2025-11-25. Both are clean. List results come back with
`cacheScope=private`, `resultType=complete`, **`ttlMs=0`** — measured across two consecutive
connections, the host re-fetches `prompts/list`, `resources/list`, and `tools/list` every
time, so the cacheable-list-results half of the 2.x protocol buys nothing here today.
