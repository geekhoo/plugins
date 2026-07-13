---
name: geeky-implement
description: Use when asked to execute an existing `geeky-plan` planning package. This skill runs kanban tasks through `geeky-coder` subagents, applies validation + review gates, and commits completed work per phase.
---

# geeky-implement

Use this skill only after `/geeky-plan` has produced a planning package.

## Input

`$ARGUMENTS`: path to a folder containing `implementation-plan.md`, `kanban.md`, `tasks/Tx-*.md`, `references.md`, and `handoff.md`.

Optional flags in `$ARGUMENTS`:
- `--phase=<name|number>`
- `--dry-run`
- `--serial`

## Runtime validation

**Step 0 — preflight the tooling itself** (guards against validator crashes stalling the run):

```bash
# Windows
pwsh -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/preflight.ps1" -Path "<folder>"

# macOS/Linux
python "${CLAUDE_PLUGIN_ROOT}/scripts/preflight.py" --path "<folder>"
```

If preflight FAILS, stop and report — do not start a run on broken tooling. Heed its warnings (stale handoff, active heartbeat from a prior run) and its long-run reminder (re-auth via `/login` before runs expected to exceed ~1 hour).

Then run the planning-folder validator (fail fast):

```bash
# Windows
pwsh -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.ps1" -Path "<folder>"

# macOS/Linux/Python
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"
```

If validation fails, stop and report. If a validator itself CRASHES (traceback, missing module), surface it in one line, fall back to manually checking the same criteria, and flag the plugin for a fix — never absorb a crash into a silent stall.

## Execution constraints

- Do not modify planning contract files (`implementation-plan.md`, `feature-specification.md`, `draft.md`, `references.md`, `tasks/Tx-*.md`).
- Use `geeky-coder` for implementation work and avoid pausing between tasks unless blocked.
- Do not push and do not use `--amend`.
- Update `kanban.md` and `handoff.md` on every task state change.
- **Re-invocation is a resume, never a restart.** Read kanban/handoff first; skip Done tasks; reconcile orphaned In Progress tasks against git/file ground truth (protocol step 2b).
- Prefer the bundled validator **scripts** over the `geeky_*` MCP tools (no permission prompts, immune to the plugin-root interpolation bug).
- Maintain the **heartbeat**: write `<folder>/.heartbeat` (JSON: `{"ts":"<ISO>","task":"T<x>","status":"running"}`) at run start, refresh `ts`+`task` at every task transition, set `status` to `"paused"` (deliberate stop) or `"done"` (run complete) before ending. External watchdogs key on this file.

## Long-run resilience

- **Session grain:** default to ONE phase (or wave) per session — checkpoint to `handoff.md`, set heartbeat `paused`, and continue in a fresh session — rather than one marathon run. Evidence: chained short sessions had zero stalls/auth incidents where a 91-hour mega-run had seven. Re-entry is cheap because re-invocation resumes (see Execution constraints).
- **Auth:** before a run expected to exceed ~1 hour, have the user `/login` first (preflight reminds you). On any 401/auth-expiry failure mid-run, the FIRST action is appending a resume block to `handoff.md` (current task, exact state, next command) — the session itself may be unrecoverable.

## Full protocol

Use this skill with deferred details in [references/execution-protocol.md](references/execution-protocol.md).
