# Spec — geeky_mcp on MCP SDK 2.x

## What

Move `geeky-orchestration/mcp/server.py` off its hard `mcp<2.0.0` pin so the same
file runs on both the 1.x and 2.x Python SDKs, and is ready to serve MCP protocol
revision **2026-07-28** the moment a client asks for it. The change is a dual-path
import plus an explicit `serverInfo.version`; the six tool definitions, their
schemas, and their wire output stay byte-identical.

## Context

`geeky_mcp` is a thin adapter: each of its six tools shells out to a stdlib-only
validator under `geeky-orchestration/scripts/` (or `hooks/`) with `--json` and
returns the parsed report. The scripts are the single source of truth; the server
adds no logic of its own. See [server.py](../../geeky-orchestration/mcp/server.py).

On 2026-08-20 the server was found dead at startup: `uv` resolved the then-unbounded
`mcp` requirement to 2.0.0, which renamed `mcp.server.fastmcp.FastMCP` to
`mcp.server.mcpserver.MCPServer`. The import failed before the MCP handshake and
Claude Code reported `CONNECTION_CLOSED` with no server-side error text. The fix
shipped in 0.2.12/0.2.13 was a hard pin to `mcp<2.0.0` in three places:

- [.mcp.json](../../geeky-orchestration/.mcp.json) — `--with "mcp<2.0.0"`
- [.codex-plugin/mcp.json](../../geeky-orchestration/.codex-plugin/mcp.json) — same
- [mcp/pyproject.toml](../../geeky-orchestration/mcp/pyproject.toml) — `mcp>=1.2.0,<2.0.0`

That pin is correct and stable, but it is a ceiling with no exit. This spec removes
the ceiling without a flag day.

## Requirements

1. `server.py` must import and run unchanged on `mcp` 1.29.0 **and** on `mcp` 2.x.
2. The `tools/list` payload — `name`, `description`, `inputSchema`, `outputSchema`,
   `annotations` — must be semantically identical under both SDKs. Key ordering may
   differ; content must not.
3. `tools/call` must return the same `content` text and `structuredContent` object
   under both SDKs.
4. `serverInfo.version` must be a non-empty, accurate string under both SDKs.
5. The dependency declarations must permit 2.x without *requiring* it, in all three
   places listed above.
6. Neither harness projection may drift: the Claude and Codex MCP configs must carry
   the same constraint.
7. `test_quality_gates.py` and the rest of the suite must pass unchanged.

## Design

### The one structural change

```python
try:                                                    # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:                                     # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

mcp = _Server("geeky_mcp", version=SERVER_VERSION)
```

Everything downstream is untouched. `MCPServer` exposes the same decorator surface
`geeky_mcp` already uses:

| Used by server.py | FastMCP 1.29 | MCPServer 2.0 |
|---|---|---|
| `@mcp.tool(name=..., annotations={...})` | yes | yes, identical signature plus `title`/`icons`/`meta`/`structured_output` |
| single Pydantic-model parameter | yes | yes |
| `dict[str, Any]` return → `structuredContent` | yes | yes |
| `mcp.run()` (stdio default) | yes | yes |

`annotations` accepts a plain `dict` on both — the existing `{"title": ..., **READONLY}`
literal needs no change.

### serverInfo.version

`FastMCP` reported the SDK version (`"1.29.0"`); `MCPServer.__init__` defaults
`version: str = ""` and reports an empty string. Both are wrong for a plugin server:
the useful number is the plugin's. `SERVER_VERSION` is read once at import from
`../.claude-plugin/plugin.json`, falling back to `"0.0.0"` if unreadable, and passed
explicitly. This also fixes the 1.x behaviour, which was reporting the SDK version.

### Dependency constraints

| File | From | To |
|---|---|---|
| `.mcp.json` | `--with "mcp<2.0.0"` | `--with "mcp>=1.2.0"` |
| `.codex-plugin/mcp.json` | `--with "mcp<2.0.0"` | `--with "mcp>=1.2.0"` |
| `mcp/pyproject.toml` | `mcp>=1.2.0,<2.0.0` | `mcp>=1.2.0` |

The upper bound is removed only because the shim makes both majors work. Removing it
without the shim would reintroduce the original outage.

## Decisions

**D1 — Dual-path shim, not a hard cut to 2.x.** *Reversible.*
Alternatives: (a) stay pinned at `<2.0.0`; (b) cut hard to `>=2.0.0`. (a) leaves a
dead-end ceiling. (b) is a flag day — every consumer that resolves an older `mcp`
(Codex, a `pip install mcp` from an older index, an offline wheel cache) breaks, and
that is exactly the failure this repo just spent a release fixing. The shim costs
four lines and has no downside: whichever SDK resolves, the server runs.

**D2 — Keep the floor at `>=1.2.0` rather than raising it.** *Reversible.*
Nothing in `server.py` uses an API newer than 1.2.0. Raising the floor would exclude
environments for no gain.

**D3 — `serverInfo.version` reads the plugin version, not the SDK version.**
*Reversible.* A client showing `geeky_mcp 0.2.14` can be matched against a release;
`1.29.0` (the old behaviour) tells the operator only which SDK resolved, which they
can get from the dependency lock anyway.

**D4 — Do not adopt any 2.x-only feature.** *Reversible.*
`MCPServer` adds middleware, extensions, elicitation, caching hints, subscriptions,
and `structured_output`. Using any of them would break the 1.x path and turn D1 into
a hard cut. `geeky_mcp` is a validator adapter and needs none of them.

**Assumption:** the six validator scripts and their `--json` contracts are unchanged
by this work. This spec touches transport and packaging only.

## Versions

| Component | Current | Target | Source |
|---|---|---|---|
| `mcp` (Python SDK) | 1.29.0 (pinned `<2.0.0`) | 1.29.0 **or** 2.0.0, whichever resolves | PyPI, verified locally |
| MCP protocol, 1.x path | 2025-11-25 | unchanged | `mcp.types.LATEST_PROTOCOL_VERSION` on 1.29.0 |
| MCP protocol, 2.x path | — | 2026-07-28 available | `mcp.types.LATEST_PROTOCOL_VERSION` on 2.0.0 |
| Python | `>=3.10` | unchanged | `mcp/pyproject.toml` |
| Claude Code | 2.1.237 | — | `claude --version` |

### What 2026-07-28 actually requires — measured, not assumed

The new revision is only reachable in **true stateless mode**. Measured against a
`MCPServer` on stdio:

| Client behaviour | Negotiated revision |
|---|---|
| `initialize` handshake, any `protocolVersion` | **2025-11-25** |
| `initialize` handshake, then `_meta` carrying 2026-07-28 | rejected, `-32600` "this connection serves the handshake protocol era" |
| **no `initialize`**, protocol version + clientInfo + capabilities in `_meta` on every request | **2026-07-28** — response gains `cacheScope` and `resultType` |

So migrating the SDK does **not** by itself upgrade the protocol. The revision in use
is chosen by the client. Until Claude Code's MCP client drops the handshake and moves
to stateless `_meta` requests, both SDKs deliver 2025-11-25 and the observable
behaviour of `geeky_mcp` is unchanged. That is the honest value case: this work buys
**readiness and an unblocked ceiling**, not a capability the user can see today.

## Invariants

1. **Wire compatibility.** `tools/list` and `tools/call` output must not change. Every
   consumer — [geeky-implement/references/execution-protocol.md](../../geeky-orchestration/skills/geeky-implement/references/execution-protocol.md),
   the orchestrator agent projections in `.agents/`, `.claude/`, `.codex/`, `.cursor/`,
   `.github/`, and `mcp/README.md` — encodes these tool names and argument shapes.
   Check: A/B the JSON under both SDKs and diff.
2. **Six tools, same names.** `geeky_validate_planning_folder`, `geeky_validate_task_schema`,
   `geeky_validate_kanban`, `geeky_check_dod`, `geeky_check_commit`,
   `geeky_check_frozen_artifact`. Check: assert the sorted name list.
3. **Read-only annotations survive.** All six carry `readOnlyHint: true`,
   `destructiveHint: false`, `idempotentHint: true`, `openWorldHint: false`.
4. **No new runtime dependency.** `mcp` plus its own transitive `pydantic` only.
5. **Harness parity.** `.mcp.json` and `.codex-plugin/mcp.json` carry the same
   constraint. Check: grep both for the same specifier.

## Error Behavior

- **Neither SDK importable** — unchanged from today: the process dies at import and the
  host reports a closed connection. Not worth catching; a server with no transport
  cannot report anything over that transport.
- **`plugin.json` unreadable when resolving `SERVER_VERSION`** — fall back to `"0.0.0"`
  and continue. A missing version string must never prevent the server from starting.
- **Validator failures** — unchanged. A non-zero exit from a script is a *validation
  failure* (`ok: false`), not a server error, and is returned as a normal result.

## Testing Strategy

1. **A/B wire diff (the load-bearing test).** Drive the real `server.py` over stdio
   under `--with "mcp<2.0.0"` and `--with "mcp>=2.0.0"`: `initialize`, `tools/list`,
   and one `tools/call` per tool against a fixture planning folder. Normalise key
   order, then diff. Any difference outside `serverInfo` fails the migration.
2. **Stateless probe.** Under 2.x only, issue a no-`initialize` request with
   `_meta` carrying 2026-07-28 and confirm the response negotiates that revision.
   Records the readiness claim as evidence rather than assertion.
3. **Existing suite.** `python -m pytest -q` at repo root — 45 tests, must stay green.
   `test_quality_gates.py` exercises the same validators the tools wrap.
4. **Live reconnect.** After release, confirm `/plugin` shows `geeky-orchestration:geeky`
   connected and one tool call returns a real report.

## Out of Scope

- Adopting 2.x-only features (middleware, extensions, elicitation, caching hints,
  subscriptions, MCP Apps). See D4.
- Any change to the six validator scripts, their `--json` contracts, or their CLI flags.
- The `semantic-design-system` MCP server — hand-written JS, no Python SDK, unaffected.
- HTTP/SSE transports. `geeky_mcp` is stdio-only and stays that way.
- Making Claude Code negotiate 2026-07-28. That is a client-side change we do not own.
