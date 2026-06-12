# geeky-orchestration

End-to-end feature delivery: **plan it, execute it, track it**, with strong contracts between phases and conservative parallelism.

## What's in the box

| Component | Type | Purpose |
|---|---|---|
| `spec-research` | skill | Researches a new spec with a parallel 3-subagent team (codebase, web best practices, architecture), then writes `SPEC-NNNN.md` + README stub in `docs/`. Runs *before* `geeky-plan`. |
| `geeky-plan` | skill | Produces a complete planning package: implementation plan, ordered task files, PM review, kanban, references, handoff. |
| `plan-review` | skill | 4-phase quality review of a `geeky-plan` package — document alignment, issue resolution, sequencing validation, final sanity pass. Run between planning and implementation. |
| `geeky-implement` | skill | Orchestrates execution: walks the kanban, delegates `geeky-coder` subagents (up to 3 in parallel), runs per-task validation, code review, and per-phase PM review, commits in small logical groups, never pushes. |
| `impl-review` | skill | Reviews *delivered code* (not planning docs) with 3 dynamically-chosen domain-expert subagents, each covering a distinct aspect of what was built. |
| `geeky-status` | skill | Read-only snapshot of a planning folder. Lane counts, blocked items, last handoff entry, suggested next step. No agents, no edits. |
| `archive` | skill | Archives a concluded spec: moves planning artifacts to `archives/`, creates the permanent `docs/spec-NNN-name/` folder (spec + handoff + README), updates CLAUDE.md current state. |
| `/spec-research`, `/geeky-plan`, `/plan-review`, `/geeky-implement`, `/impl-review`, `/geeky-status`, `/archive` | commands | Thin slash-command fronts that simply invoke the same-named skill with `$ARGUMENTS`. The full procedure lives in the skills (`skills/<name>/SKILL.md`) so that non-Claude agents — which read skills but not commands — can run the same workflow. |
| `geeky-coder` | agent | Portable coder subagent. Treats the orchestrator's brief as authoritative scope. Returns a structured summary. Safe to spawn in parallel against non-overlapping task surfaces. |
| `templates/task_template.md` | template | Canonical task shape consumed by `/geeky-plan`. |
| `scripts/validate-planning-folder.{ps1,py}` | gate | Folder completeness: verifies a folder has the artifacts `/geeky-implement` expects. |
| `scripts/validate-task-schema.{ps1,py}` | gate | Each `tasks/Tx-*.md` carries the required template sections (plan→implement boundary). |
| `scripts/validate-kanban.{ps1,py}` | gate | Kanban integrity: every task in exactly one lane, no dangling refs, WIP cap, lane coverage. |
| `scripts/check-dod.{ps1,py}` | gate | Definition-of-Done for one task: notes file exists, task in Done lane, handoff mentions it; prints the task's validation block to re-run. |
| `scripts/check-commit.{ps1,py}` | gate | Commit message is Conventional Commits + references a task (`Tasks: T<n>`). |
| `hooks/guard-planning-contract.{ps1,py}` | hook | PreToolUse guard for edits to frozen planning artifacts. Default `--mode warn` (advisory, surfaced via portable stdout+stderr); `--mode block` denies via Claude/Codex JSON (or exit 2 with `--exit-code`). |
| `AGENTS.md` + `geeky.manifest.json` | discovery | Framework-agnostic discovery layer: how non-Claude agents learn the contract and invoke the gates (human-readable + machine-readable). |
| `mcp/server.py` + `.mcp.json` | MCP server | `geeky_mcp` — stdio server exposing the six gates as MCP tools for any MCP-capable agent. Thin adapter over the same scripts. See [mcp/README.md](mcp/README.md). |

Every gate follows one contract: **arguments in, exit 0 = pass / exit 1 = fail, summary on stdout** (optional `--json` / `-Json`). Each ships paired Python + PowerShell with identical output and exit codes. See [docs/framework-agnostic-quality-gates.md](docs/framework-agnostic-quality-gates.md) for the design rationale.

## Pipeline

```
/spec-research <topic or spec-NNN>     → researches + writes SPEC-NNNN.md in docs/

/geeky-plan <spec or folder>          → produces docs/<feature>/...
   ├─ implementation-plan.md           (FROZEN after this point)
   ├─ feature-specification.md         (FROZEN)
   ├─ draft.md                         (FROZEN)
   ├─ references.md                    (FROZEN)
   ├─ kanban.md                        (mutable — status of truth)
   ├─ handoff.md                       (mutable — running log)
   ├─ review-development-project-manager.md
   └─ tasks/T1-...md  T2-...md  ...    (FROZEN — notes go in Tx-*.notes.md siblings)

/plan-review <folder>                  → 4-phase quality review of the planning package

/geeky-status <folder>                 → read-only snapshot

/geeky-implement <folder>              → walks kanban Ready → Done
   ├─ delegates geeky-coder per task (max 3 parallel when safe)
   ├─ re-runs each task's validation block itself
   ├─ runs code-review on each task's diff
   ├─ runs PM review at each phase boundary
   ├─ writes tasks/Tx-*.notes.md per task
   ├─ commits per phase, split into small logical commits
   └─ updates kanban.md + handoff.md continuously
                                       (never pushes)

/impl-review <folder|diff|branch>      → 3 domain-expert subagents review the delivered code

/archive <folder|spec-NNN>             → moves planning artifacts to archives/,
                                         finalizes docs/spec-NNN-name/, updates CLAUDE.md
```

## Operating profile (baked into `/geeky-implement`)

- **Autonomy:** fully autonomous until the backlog is empty or a task lands in Blocked.
- **Reviewer:** per-task code-review on every task's diff + PM-level review at each phase boundary.
- **Commits:** per phase, split into multiple small commits (one concern per commit). Never push, never amend, never `--no-verify`.
- **Parallelism:** up to 3 concurrent `geeky-coder` subagents, gated by a checklist (no shared deps, no file-surface overlap, no shared mutable artifacts).

Override per run via flags inside the argument string:
- `--phase=<name|number>` — scope to one phase
- `--dry-run` — preview the execution model, modify nothing
- `--serial` — disable parallelism for this run

## Contract between commands

The output of `/geeky-plan` is a **read-only contract** consumed by `/geeky-implement`. The implementer never edits:

- `implementation-plan.md`
- `feature-specification.md`
- `draft.md`
- `references.md`
- `tasks/Tx-*.md` (original task bodies)

If reality diverges from the plan mid-run, the task is moved to Blocked with a note in `kanban.md` and surfaced to the user. The bundled PreToolUse hook surfaces a warning if any tool attempts to write to a frozen artifact (default `--mode warn`); switch it to `--mode block` in `hooks/hooks.json` to deny such edits outright.

Mutable artifacts (updated continuously by `/geeky-implement`):
- `kanban.md` — single source of truth for lane status
- `handoff.md` — running log + Deferred follow-ups
- `tasks/Tx-*.notes.md` — per-task summary, validation log, review findings

## Install

This plugin ships in the `geekhoo-plugins` marketplace. Once that marketplace is added to your Claude Code config:

```
/plugin install geeky-orchestration@geekhoo-plugins
```

## Typical session

```
# Session 0 — research a new spec from scratch (optional)
/spec-research spec-009 notifications

# Session 1 — planning
/geeky-plan docs/my-feature/

# Review the plan before committing to it
/plan-review docs/my-feature/

# Inspect
/geeky-status docs/my-feature/

# Session 2 — execution (autonomous until Blocked or Done)
/geeky-implement docs/my-feature/

# Pick up on a different day
/geeky-status docs/my-feature/      # where are we?
/geeky-implement docs/my-feature/   # resume

# Try a single phase first
/geeky-implement docs/my-feature/ --phase=2 --dry-run
/geeky-implement docs/my-feature/ --phase=2

# Wrap up — expert review of the delivered code, then archive
/impl-review docs/my-feature/
/archive docs/my-feature/
```

## Cross-platform notes

Every gate and the PreToolUse hook ship as **paired Python + PowerShell** implementations with identical output and exit codes:

| Script | Windows-preferred (`.ps1`) | Cross-platform (`.py`) |
|---|---|---|
| Gates (`validate-planning-folder`, `validate-task-schema`, `validate-kanban`, `check-dod`, `check-commit`) | `scripts/*.ps1` | `scripts/*.py` |
| Hook (auto-run on every Edit/Write) | `hooks/guard-planning-contract.ps1` | `hooks/guard-planning-contract.py` |

**Gates:** the skills show both invocations in their prompts; the model picks the right one based on the host OS. Each exits `0` on pass / `1` on fail and accepts `--json` (`.py`) / `-Json` (`.ps1`) for machine-readable output. The `geeky_mcp` server (Python) wraps these for tool-style invocation.

**Hook (auto-run):** `hooks/hooks.json` calls the **Python** version by default — Python is the most universal runtime for hooks that must fire on every edit, and the Python hook handles edge cases (empty stdin, malformed JSON, backslash paths) cleanly. If you're on Windows and prefer the PowerShell hook, edit `hooks/hooks.json` and replace the command with:

```
pwsh -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/hooks/guard-planning-contract.ps1"
```

Requirements:
- The Python implementations need **Python 3.8+** on PATH as `python` (or `python3` — edit `hooks.json` if your environment uses the latter). No third-party packages required — stdlib only.
- The PowerShell implementations need **PowerShell 7+ (`pwsh`)**. Works on Windows out of the box; install `pwsh` separately on macOS/Linux if you prefer them there.

## Other notes

- `geeky-coder` is renamed from a generic `coder` agent to avoid clobbering any personal `coder` agent the user may have configured.
- Reviewer delegation looks for the same agent type `/geeky-plan` used (development project manager / planning-coordinator). If your environment doesn't ship one, the per-task `code-review` skill still runs; only the phase-boundary PM sweep degrades.
