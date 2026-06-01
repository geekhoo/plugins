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
uv run --with mcp python server.py

# Or, with mcp installed into your environment:
pip install mcp
python server.py
```

In Claude Code the server starts automatically: `.mcp.json` at the plugin root registers
it as the `geeky` server using `uv run --with mcp`.

## Inspect / debug

```bash
# MCP Inspector (interactive tool explorer):
npx @modelcontextprotocol/inspector uv run --with mcp python server.py

# List registered tools:
uv run --with mcp python -c "import asyncio, server; print([t.name for t in asyncio.run(server.mcp.list_tools())])"
```

## Requirements

- Python ≥ 3.10 and the `mcp` package (resolved automatically by `uv run --with mcp`).
- `uv` on PATH for the default `.mcp.json` command. To use plain `python` instead, edit
  `.mcp.json` to `"command": "python", "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]`
  and ensure `mcp` is installed.

The wrapped validators are standard-library only and need no packages.
