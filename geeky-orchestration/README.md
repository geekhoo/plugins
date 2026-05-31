# geeky-orchestration

End-to-end feature delivery: **plan it, execute it, track it**, with strong contracts between phases and conservative parallelism.

## What's in the box

| Component | Type | Purpose |
|---|---|---|
| `/geeky-plan` | command | Produces a complete planning package: implementation plan, ordered task files, PM review, kanban, references, handoff. |
| `/geeky-implement` | command | Orchestrates execution: walks the kanban, delegates `geeky-coder` subagents (up to 3 in parallel), runs per-task validation, code review, and per-phase PM review, commits in small logical groups, never pushes. |
| `/geeky-status` | command | Read-only snapshot of a planning folder. Lane counts, blocked items, last handoff entry, suggested next step. No agents, no edits. |
| `geeky-coder` | agent | Portable coder subagent. Treats the orchestrator's brief as authoritative scope. Returns a structured summary. Safe to spawn in parallel against non-overlapping task surfaces. |
| `templates/task_template.md` | template | Canonical task shape consumed by `/geeky-plan`. |
| `scripts/validate-planning-folder.{ps1,py}` | script | Pre-run sanity check. Verifies a folder has the artifacts `/geeky-implement` expects. Two implementations with identical behavior and exit codes: PowerShell (Windows-preferred) and Python (cross-platform). |
| `hooks/guard-planning-contract.{ps1,py}` | hook | PreToolUse warn-only guard. Warns (does not block) before edits to frozen planning artifacts. Two implementations available; `hooks.json` calls the Python version by default for cross-platform reliability — see Cross-platform notes below. |

## Pipeline

```
/geeky-plan <spec or folder>          → produces docs/<feature>/...
   ├─ implementation-plan.md           (FROZEN after this point)
   ├─ feature-specification.md         (FROZEN)
   ├─ draft.md                         (FROZEN)
   ├─ references.md                    (FROZEN)
   ├─ kanban.md                        (mutable — status of truth)
   ├─ handoff.md                       (mutable — running log)
   ├─ review-development-project-manager.md
   └─ tasks/T1-...md  T2-...md  ...    (FROZEN — notes go in Tx-*.notes.md siblings)

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

If reality diverges from the plan mid-run, the task is moved to Blocked with a note in `kanban.md` and surfaced to the user. The bundled PreToolUse hook prints a warning if any tool attempts to write to a frozen artifact — it does not block (warn-only by design).

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
# Session 1 — planning
/geeky-plan docs/my-feature/

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
```

## Cross-platform notes

The validator and the PreToolUse hook each ship in **two equivalent implementations**:

| Script | Windows-preferred | Cross-platform default |
|---|---|---|
| Validator (manual, invoked by commands) | `scripts/validate-planning-folder.ps1` | `scripts/validate-planning-folder.py` |
| Hook (auto-run on every Edit/Write) | `hooks/guard-planning-contract.ps1` | `hooks/guard-planning-contract.py` |

**Validator:** `/geeky-implement` and `/geeky-status` show both invocations in their prompts; the model picks the right one based on the host OS. Both produce identical output and exit codes (`0` valid, `1` invalid).

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
