# AGENTS.md — geeky-orchestration

Guidance for **any** AI coding agent (Claude Code, Codex CLI, Cursor, Windsurf,
Copilot CLI, Gemini CLI, or an SDK/LangGraph orchestrator) working with this
plugin's plan → execute → track workflow. Claude Code reads this via `@AGENTS.md`;
most other CLI agents read `AGENTS.md` natively.

## The workflow

1. **spec-research** — research and write `feature-specification.md`.
2. **geeky-plan** — create the frozen planning package.
3. **plan-review** — validate alignment, coverage, sequencing, and readiness.
4. **geeky-status** — read-only status and resumption orientation at any packet stage.
5. **geeky-implement** — execute Ready tasks with validation and review gates.
6. **impl-review** — review delivered code through three domain-specific lanes.
7. **archive** — move completed planning artifacts into the archive structure.

Use **geeky-orchestrator** when the requested entry point is unclear or when one
agent should administer the lifecycle. It examines repository evidence read-only
and recommends a workflow before mutation. Clear, explicit requests route to the
best matching skill after prerequisite checks. Material ambiguity is clarified;
stages are not auto-chained without end-to-end authorization.

Full procedures live in the portable Skills under `skills/<name>/SKILL.md`.

## The planning-folder contract

**Frozen** (never edit mid-run — they are the contract between plan and implement):
`implementation-plan.md`, `feature-specification.md`, `draft.md`, `references.md`,
and every `tasks/Tx-*.md` body. If the plan is genuinely wrong, surface it via the
kanban **Blocked** lane + `handoff.md` instead of editing the contract.

**Mutable** (update continuously during implement):
`kanban.md` (single source of truth for lane status), `handoff.md` (running log),
and `tasks/Tx-*.notes.md` (per-task notes — these are writable, unlike the task bodies).

## Deterministic quality gates (run these — don't self-report)

These replace "I updated the board / the task is done" with fail-stop checks.
Every gate: **arguments in, exit 0 = pass / exit 1 = fail, summary on stdout**,
optional `--json` / `-Json`. Each ships paired Python + PowerShell with identical
behavior. `geeky.manifest.json` is the machine-readable index of the same list.

Paths below are relative to this plugin root (`${CLAUDE_PLUGIN_ROOT}` in Claude Code).
Use `python3` where `python` is not on PATH; use `pwsh` (PowerShell 7+) for the `.ps1`.

| Gate | When | Python | PowerShell |
|---|---|---|---|
| Planning-folder valid | start of implement/status | `python scripts/validate-planning-folder.py --path "<folder>"` | `pwsh -File scripts/validate-planning-folder.ps1 -Path "<folder>"` |
| Task-file schema | end of plan; start of implement | `python scripts/validate-task-schema.py --path "<folder>"` | `pwsh -File scripts/validate-task-schema.ps1 -Path "<folder>"` |
| Kanban integrity | after every lane move | `python scripts/validate-kanban.py --path "<folder>"` | `pwsh -File scripts/validate-kanban.ps1 -Path "<folder>"` |
| Definition of Done | before moving a task to Done | `python scripts/check-dod.py --path "<folder>" --task <ID>` | `pwsh -File scripts/check-dod.ps1 -Path "<folder>" -Task <ID>` |
| Commit message | before each commit | `python scripts/check-commit.py <FILE>` | `pwsh -File scripts/check-commit.ps1 <FILE>` |

**Feedback loop:** when a gate exits non-zero, read its output, fix the artifact,
and re-run the same gate until it exits 0 before proceeding.

## How each agent type runs the gates

- **Claude Code:** the frozen-artifact guard fires automatically via
  `hooks/hooks.json` (PreToolUse). Run the validators above as explicit steps.
- **Other CLI agents (Codex, Cursor, Windsurf, Copilot, Gemini):** add an
  equivalent pre-edit/stop hook in your tool's config pointing at
  `hooks/guard-planning-contract.{py,ps1}` (it reads tool-call JSON on stdin,
  `--mode block` denies via JSON / exit 2). Invoke the validators as shell steps.
- **SDK / graph orchestrators (OpenAI Agents SDK, LangGraph):** call any validator
  with `subprocess.run([...])` inside a guardrail / node; raise a tripwire or
  `interrupt()` on a non-zero exit.
- **Any MCP-capable agent:** a bundled stdio MCP server (`geeky_mcp`, see `mcp/server.py`,
  registered in `.mcp.json`) exposes the gates as tools — `geeky_validate_planning_folder`,
  `geeky_validate_task_schema`, `geeky_validate_kanban`, `geeky_check_dod`,
  `geeky_check_commit`, `geeky_check_frozen_artifact` — for tool-style invocation with
  no per-framework hook config. Run it with `uv run --with mcp python mcp/server.py`
  (or `pip install mcp && python mcp/server.py`).

## Hard rules for implement

Never push to a remote. Never `--no-verify`, `--force`, or `--amend`. Respect each
task's declared `Dependencies:`. Stop and finalize state (kanban + handoff) when a
task moves to Blocked. Re-run each task's validation block yourself — do not trust
a coder's claim that it passed.
