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
# Preferred — run from this directory so uv.lock governs the resolve:
uv run python server.py

# Or, with mcp installed into your environment:
pip install "mcp>=1.28.1,<3"
python server.py

# Or, once the package itself is installed:
geeky-mcp
```

In Claude Code the server starts automatically: `.mcp.json` at the plugin root registers
it as the `geeky` server with `cwd` set to this directory. It carries no `--with`
constraint — the dependency is declared once, in `pyproject.toml`.

## Inspect / debug

```bash
# MCP Inspector (interactive tool explorer):
npx @modelcontextprotocol/inspector uv run python server.py

# List registered tools:
uv run python -c "import asyncio, server; print([t.name for t in asyncio.run(server.mcp.list_tools())])"
```

## Requirements

- `mcp>=1.28.1,<3` — either major. `server.py` runs unchanged on 1.x and 2.x; see
  [Version binding](#version-binding) for why those bounds.
- `uv` on PATH for the default `.mcp.json` command. To use plain `python` instead, edit
  `.mcp.json` to `"command": "python", "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]`
  and ensure `mcp` is installed.
- **Python 3.14**, pinned by `.python-version`; `pyproject.toml` declares
  `requires-python = ">=3.13"`, matching `MIN_PYTHON` in `wire_baseline.py`, for the
  reason in [Wire baseline](#wire-baseline) below. `uv` downloads 3.14 on first launch if
  the machine does not already have it. Both harness projections (`.mcp.json` and
  `.codex-plugin/mcp.json`) set `cwd` to this directory, so the pin applies to Claude and
  Codex alike.

The wrapped validators are standard-library only and need no packages.

## Version binding

Every dependency in this repository is bound as an **explicit two-sided range**:
a floor at a version that has actually been verified here, and a ceiling at the next
release the upstream project itself treats as breaking. Written out longhand in both
ecosystems (`mcp>=1.28.1,<3`; `"playwright": ">=1.62.1 <1.63"`) rather than in npm's
caret/tilde shorthand, because `^` and `~` mean different things per ecosystem and per
project, and the ceiling is the part worth reading. Where a project's breaking unit is
not its major, the ceiling follows the project, not semver: Playwright ships breaking
changes in minors, so its ceiling is the next minor. The floor for `mcp` is 1.28.1 — the
first 1.x release with no outstanding security advisory (`GHSA-vj7q-gjh5-988w` was fixed
there), which is stricter than upstream's illustrative `mcp>=1.28,<2`. The ceiling is
`<3`, not `<2`, because the shim at the top of `server.py` exists precisely to run on
both majors and both are verified; `<2` would forbid the version the shim was written
for. The one deliberate exception is `requires-python`, which is left uncapped — capping
it makes resolvers refuse future interpreters for no gain. Ranges live in exactly one
place per dependency: `pyproject.toml` for Python, `package.json` for Node. Nothing
duplicates a constraint into a launcher command.

## What the lock covers

`uv.lock` pins `mcp` to the exact version the [wire baseline](#wire-baseline) was captured
against (1.29.0), and it **is** tracked — uv's own guidance is that a lockfile
"should be checked into version control"
([Structure and files](https://docs.astral.sh/uv/concepts/projects/layout)). It is a
resolution record, not a runtime artifact; `.venv/` is the runtime artifact and stays
ignored. The same split as `package-lock.json` versus `node_modules/`.

This matters here because `.mcp.json` sets `cwd` to this directory, so the server launches
via `uv run` as a *project* command — the code path that reads the lock. A shipped lock
therefore means every consumer runs the version the baseline documents. Without one they
would resolve from `pyproject.toml` alone, and `mcp>=1.28.1,<3` currently resolves to 2.x:
a different SDK major, and roughly 40% slower startup than the 1.29.0 figures in
[Startup cost](#startup-cost).

The two layers do different jobs and both are needed. The range is the compatibility
boundary — what the server is known to work against, and what a consumer without a lock
falls back to. The lock is the reproducibility pin. Refresh it deliberately with
`uv lock --upgrade`, then re-run the wire baseline before committing the result.

One caveat worth knowing: uv rejects a lockfile whose schema version exceeds what it
supports. This lock is schema `version = 1, revision = 3`. A consumer on a much older uv
would see an explicit schema error rather than a silent fallback.

## Wire baseline

`wire_baseline.py` drives the real server over stdio and writes a normalised transcript of
`initialize`, `tools/list`, and one `tools/call` per tool. `wire_baseline.json` is the
committed capture; diffing a fresh run against it is what proves an SDK or transport change
did not alter the wire.

```bash
uv run --with "mcp>=2.0.0,<3" python wire_baseline.py --out /tmp/v2.json
diff wire_baseline.json /tmp/v2.json
```

It is deliberately outside pytest — every run pays a `uv` resolve.

**Why the interpreter is pinned.** Tool descriptions are the handler docstrings, and
CPython 3.13 changed the compiler to strip leading indentation from docstrings (3.10–3.12
keep it). The same server therefore emits differently formatted descriptions either side of
that change, and the baseline — diffed byte for byte — fails in all six descriptions for a
reason that has nothing to do with the server or the SDK. The old `requires-python = ">=3.10"`
let `uv` pick any interpreter when building the venv, so this failed silently the moment a
venv was rebuilt on an older Python; it now reads `>=3.13`, the same floor `MIN_PYTHON` in
`wire_baseline.py` enforces, so the two agree instead of contradicting each other.
`.python-version` then pins the build interpreter to a single choice (3.14) on top of that
floor, and `MIN_PYTHON` refuses to capture below 3.13 rather than write a baseline that
cannot diff.

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
