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

## Workflow terminology

Use these meanings across skills, briefs and reports. They describe the orchestration
domain; retain the target project's own domain language. Existing filenames, schema
fields and checkpoint markers remain unchanged.

| Term | Meaning |
|---|---|
| Planning package | Specification, plan, task contracts and tracking artifacts for one approved outcome. "Packet" is an alias; planning folder is its location. |
| Workflow stage | A lifecycle activity such as planning, implementation or final implementation review. Numbered "phases" inside a skill are procedure steps, not implementation phases. |
| Implementation phase | A group of tasks whose combined requirements are reviewed before advancement. "Wave" means a scheduling group unless the plan explicitly equates it with a phase. |
| Task | A bounded unit with an ID, scope, dependencies, acceptance criteria (ACs) and required validation. |
| Requirement / AC / Definition of Done | Required outcome or constraint / observable condition for satisfying it / completion conditions for the task. Required tests supply evidence; they do not replace ACs. |
| Task contract | The frozen task body and applicable approved requirements. A task brief conveys that contract to a worker. |
| Validation | Checks of the work. Validation evidence records what ran or was observed, against which inputs, and the result; a PASS claim alone is not evidence. |
| Review | Judgment of evidence against an assigned scope. Task review checks ACs/tests; phase review decides readiness to advance; final implementation review uses `impl-review`. Plan review evaluates the planning package. |
| Acceptance | The decision that required outcomes and gates for the stated scope are satisfied. Task Done, phase READY TO ADVANCE and final review PASS have different scopes; none grants release or deployment approval. |
| Finding | An evidenced discrepancy. A blocking finding prevents the current contract from being met; an optional improvement is a follow-up. Severity labels retain their review-stage meanings, not an automatic cross-stage mapping. |
| Execution batch / review batch | Tasks dispatched together / tasks sharing a reviewer assignment. A shared review batch holds all members' progression until the whole batch clears, preserving individual verdicts. Review-batch members may not depend on each other. |
| Orchestrator / worker / reviewer | Coordinates and accepts work / performs a bounded assignment / evaluates it. `geeky-coder` is the implementation worker; PM describes a planning or phase-review perspective. |
| Task event log | One `tasks/T<n>.events.jsonl` per task for consequential collaboration events, preserving the sender. It does not replace task notes or Kanban state. |

## The planning-folder contract

**Frozen** (never edit mid-run — they are the contract between plan and implement):
`implementation-plan.md`, `feature-specification.md`, `draft.md`, `references.md`,
and every `tasks/Tx-*.md` body. If the plan is genuinely wrong, surface it via the
kanban **Blocked** lane + `handoff.md` instead of editing the contract.

**Mutable** (update continuously during implement):
`kanban.md` (single source of truth for lane status), `handoff.md` (running log),
and `tasks/Tx-*.notes.md` (per-task notes — these are writable, unlike the task bodies).

Task collaboration uses one append-only `tasks/T<n>.events.jsonl` per task. Follow the execution protocol for entries and cross-task notifications; existing notes remain unchanged.

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
| Commit message | before each commit | `python scripts/check-commit.py --message "<msg>"` (or `<FILE>`) | `pwsh -File scripts/check-commit.ps1 -Message "<msg>"` (or `<FILE>`) |

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
  no per-framework hook config. Run it with `uv run --with "mcp>=1.2.0" python mcp/server.py`
  (or `pip install mcp && python mcp/server.py`).

## Hard rules for implement

Never push to a remote. Never `--no-verify`, `--force`, or `--amend`. Respect each
task's declared `Dependencies:`. Stop and finalize state (kanban + handoff) when a
task moves to Blocked. Verify task validation evidence against the tested revision,
commands and results; a coder's bare PASS claim is insufficient. Reuse valid evidence
and record the reason for any rerun. Task review checks ACs and defined tests. Phase
review checks collective requirements and must return READY TO ADVANCE before the
next phase starts; that verdict comes from a reviewer subagent whose agent ID is
recorded, and the last phase is included. Final implementation review uses `impl-review`.
The orchestrator never edits product code or tests; fixes go to `geeky-coder`. Batch independent
work and compatible fixes while preserving each task's verdict and resource isolation.
