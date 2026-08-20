# Plan — geeky_mcp on MCP SDK 2.x

Source: [spec.md](./spec.md). Read it first — this plan assumes its decisions
(D1–D4) and does not re-argue them.

Repo: `C:\Users\kcgee\plugins` (branch `main`). Windows; the Bash tool needs
forward-slash paths. Four tasks, strictly sequential — each depends on the one
before it.

## Shared context for every task

- `geeky_mcp` is a thin adapter. Each of its six tools shells out to a stdlib-only
  validator under `geeky-orchestration/scripts/` (or `hooks/`) with `--json` and
  returns the parsed report. **Do not move logic into the server.**
- The server is launched by `uv run --with <spec> python .../mcp/server.py` with
  `cwd` set to `geeky-orchestration/mcp/`. `uv` treats that directory as a project
  (it has a `pyproject.toml`), so the `--with` specifier and the `pyproject.toml`
  dependency are resolved **together** — both must permit the version you want.
- Running `uv run` in that directory creates `geeky-orchestration/mcp/.venv`. It is
  gitignored. Leave the tree as you found it.
- Repo release convention: a functional change bumps the plugin version in
  `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and the matching entry
  in the root `.claude-plugin/marketplace.json`. `test_plugin_metadata.py` enforces
  that the three agree.
- Commit convention: `type(scope): summary (version)`, small and logically grouped.
  Never `--no-verify`. Do not push without an explicit ask.

## Shared decision, stated once

The server must keep working on `mcp` 1.x **and** 2.x from a single file. Every task
below is constrained by that: no 2.x-only API may be introduced, and no change may
require an upper bound to be reinstated. If a task appears to need one, stop and
escalate rather than pinning.

---

## T1 — Capture a wire baseline before touching anything

**Goal.** A runnable harness that drives the real `server.py` over stdio and dumps a
normalised `tools/list` + `tools/call` transcript, plus a committed baseline captured
from today's known-good `mcp<2.0.0`.

**Context.** The whole migration rests on one claim: the wire format does not change.
That claim is only checkable against a baseline taken *before* the code changes.
Writing the harness first also means T2 is verified by something that existed before
the edit, not by something written to agree with it.

**Relevant files.**
- `geeky-orchestration/mcp/server.py` — the server under test, unmodified in this task
- `geeky-orchestration/test_quality_gates.py` — the existing pattern for building a
  throwaway planning folder with `tempfile.TemporaryDirectory()`; reuse it rather
  than inventing a fixture layout
- New: `geeky-orchestration/mcp/wire_baseline.py` (harness) and
  `geeky-orchestration/mcp/wire_baseline.json` (captured baseline)

**Proposed approach.** The harness builds a temporary planning folder (kanban.md,
`tasks/T1-*.md`, handoff.md — enough for the validators to return a real report),
then sends over stdio: `initialize`, `notifications/initialized`, `tools/list`, and
one `tools/call` per tool. It writes a JSON document with keys sorted recursively and
`serverInfo` excluded, since that field is expected to change. Absolute temp paths
must be rewritten to a stable placeholder or the baseline will never reproduce.

**Acceptance criteria.**
- Running the harness twice in a row on the same SDK produces byte-identical output.
- The baseline contains all six tools and one call result per tool.
- No absolute path, temp directory name, or timestamp appears in the baseline.
- `serverInfo` is absent from the normalised output.

**Verify.**
```bash
cd C:/Users/kcgee/plugins/geeky-orchestration/mcp && uv run --with "mcp<2.0.0" python wire_baseline.py --out wire_baseline.json && uv run --with "mcp<2.0.0" python wire_baseline.py --out /tmp/again.json && diff wire_baseline.json /tmp/again.json && echo REPRODUCIBLE
```

**Out of scope.** Wiring the harness into pytest. It is a migration instrument, run
on demand; adding it to the suite would make every test run pay a `uv` resolve.

**Source reference.** spec.md → Testing Strategy §1, Invariants 1–3.

---

## T2 — Dual-path SDK import and an explicit serverInfo.version

**Goal.** `server.py` imports and runs on both SDK majors, and reports the plugin's
own version rather than the SDK's or an empty string.

**Context.** `mcp` 2.0 renamed `mcp.server.fastmcp.FastMCP` to
`mcp.server.mcpserver.MCPServer`. The two classes expose the same decorator surface
this server uses — `@mcp.tool(name=..., annotations={...})` with a single Pydantic
model parameter, a `dict` return, and `mcp.run()` — so a try/except import is
sufficient. `annotations` accepts a plain `dict` on both; the existing
`{"title": ..., **READONLY}` literal needs no change.

`FastMCP` reported the SDK version in `serverInfo.version`; `MCPServer` defaults it to
the empty string. Neither is useful. Read the plugin version once at import from
`../.claude-plugin/plugin.json` and pass it explicitly.

**Relevant files.**
- `geeky-orchestration/mcp/server.py` lines 29 and 42 (the import and the constructor)
  — these two lines plus a small version helper are the entire change
- `geeky-orchestration/.claude-plugin/plugin.json` — source of the version string

**Proposed approach.**
```python
try:                                                    # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:                                     # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server
```
then `mcp = _Server("geeky_mcp", version=SERVER_VERSION)`. Resolve `SERVER_VERSION`
from `PLUGIN_ROOT / ".claude-plugin" / "plugin.json"`.

**Error behavior this task owns.** If `plugin.json` is missing or unparseable,
`SERVER_VERSION` falls back to `"0.0.0"` and the server starts normally — a version
string must never be the reason a server fails to boot. If *neither* SDK imports,
let it fail: the process has no transport on which to report anything, and the host
already surfaces that as a closed connection.

**Acceptance criteria.**
- The server completes an `initialize` handshake and lists six tools under both
  `--with "mcp<2.0.0"` and `--with "mcp>=2.0.0"`.
- The T1 harness output under 2.x matches the committed baseline exactly.
- `serverInfo.version` equals the version in `.claude-plugin/plugin.json` under both
  SDKs, and is never the empty string.
- No 2.x-only API appears anywhere in the file.

**Verify.**
```bash
cd C:/Users/kcgee/plugins/geeky-orchestration/mcp && uv run --with "mcp>=2.0.0" python wire_baseline.py --out /tmp/v2.json && diff wire_baseline.json /tmp/v2.json && echo WIRE-IDENTICAL
```
Then confirm the readiness claim the spec makes — under 2.x only, a request carrying
no `initialize` and a `_meta` protocol version of `2026-07-28` must negotiate that
revision (the result gains `cacheScope` and `resultType`):
```bash
cd C:/Users/kcgee/plugins/geeky-orchestration/mcp && printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientInfo":{"name":"probe","version":"1"},"io.modelcontextprotocol/clientCapabilities":{}}}}' | uv run --with "mcp>=2.0.0" python server.py 2>/dev/null | grep -c cacheScope
```

**Out of scope.** Adopting middleware, extensions, elicitation, caching hints,
subscriptions, or `structured_output` (spec D4). Any of them turns the shim into a
hard cut.

**Source reference.** spec.md → Design, Requirements 1–4, D1 and D3.

---

## T3 — Widen the three dependency constraints

**Goal.** Remove the `<2.0.0` ceiling everywhere, keeping both harnesses in lockstep.

**Context.** The pin exists in three places because the Claude config, the Codex
config, and the project metadata are resolved independently — the 0.2.12 release
patched only the first and shipped a still-broken Codex projection. Treat these three
as one edit.

**Relevant files.**
- `geeky-orchestration/.mcp.json` → `args`, the `--with` value
- `geeky-orchestration/.codex-plugin/mcp.json` → same
- `geeky-orchestration/mcp/pyproject.toml` → `dependencies`, and the run comment
  below it that repeats the command

**Proposed approach.** `"mcp<2.0.0"` → `"mcp>=1.2.0"` in both MCP configs;
`"mcp>=1.2.0,<2.0.0"` → `"mcp>=1.2.0"` in `pyproject.toml`. Update the comment in
`pyproject.toml` so it does not keep advertising the pinned command.

**Acceptance criteria.**
- No tracked file contains `mcp<2.0.0`.
- Both MCP configs carry byte-identical specifiers.
- Both remain valid JSON.
- With the ceiling gone, `uv` resolves `mcp` 2.x and the server still starts.

**Verify.**
```bash
cd C:/Users/kcgee/plugins && git ls-files | xargs grep -l "mcp<2.0.0" ; python -c "import json;[json.load(open(f)) for f in ['geeky-orchestration/.mcp.json','geeky-orchestration/.codex-plugin/mcp.json']];print('JSON OK')"
```
The `grep -l` must print nothing.

**Out of scope.** Raising the `>=1.2.0` floor (spec D2).

**Source reference.** spec.md → Design → Dependency constraints, Requirements 5–6,
Invariant 5.

---

## T4 — Release and confirm on the live host

**Goal.** Ship it and observe it working, rather than inferring that it works.

**Context.** The installed plugin cache is version-keyed. Until the version is bumped
*and* pushed, the running Claude Code keeps serving the old copy and no amount of
local verification reflects what the user gets.

**Relevant files.**
- `geeky-orchestration/.claude-plugin/plugin.json`, `geeky-orchestration/.codex-plugin/plugin.json`,
  root `.claude-plugin/marketplace.json` — the three version surfaces
- `geeky-orchestration/AGENTS.md`, `docs/framework-agnostic-quality-gates.md`,
  `geeky.manifest.json`, `mcp/README.md`, `mcp/evaluations.md`, `mcp/server.py`,
  `.gitignore` — these eight sites quote the run command and currently show the
  pinned form
- `docs/geeky-mcp-sdk-2x/spec.md` — record the outcome of the stateless probe

**Proposed approach.** Bump all three version surfaces together. Sweep the eight
documentation sites to the unpinned command. Note: `geeky.manifest.json` holds the
command inside a JSON string — use single quotes there, not double, or the file stops
parsing and `test_plugin_metadata.py` fails.

**Acceptance criteria.**
- The three version surfaces agree and the suite passes.
- No tracked file advertises a command that differs from the one in `.mcp.json`.
- After push and plugin update, `/plugin` shows `geeky-orchestration:geeky` connected.
- One real tool call through Claude Code returns a validator report.

**Verify.**
```bash
cd C:/Users/kcgee/plugins && python -m pytest -q
```
Then, after pushing and updating the plugin, call `geeky_validate_kanban` against a
real planning folder from inside Claude Code and confirm a report comes back. Do not
mark this task done on a local run alone — the local run does not exercise the
installed cache.

**Out of scope.** Pushing without an explicit ask.

**Source reference.** spec.md → Testing Strategy §3–4, Requirement 7.

---

## What this plan deliberately does not deliver

Claude Code negotiates the protocol revision, not the server. Until its MCP client
drops the `initialize` handshake for stateless `_meta` requests, both SDK majors
serve **2025-11-25** and `geeky_mcp` behaves exactly as it does today. Completing
these four tasks buys a removed ceiling and measured readiness — not a change the
user can observe. Judge it on that basis.
