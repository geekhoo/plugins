---
name: geeky-implement
description: Use when asked to execute an existing `geeky-plan` planning package. This skill runs kanban tasks through `geeky-coder` subagents, applies validation + review gates, and commits completed work per phase.
---

Use the shared [workflow terminology](../../AGENTS.md#workflow-terminology).

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
- The orchestrator never edits product code or tests; every fix, including a reviewer's one-line suggestion, goes to `geeky-coder`. Non-blocking findings go to follow-ups.
- Do not push and do not use `--amend`.
- On every lane move, update `kanban.md` and run `validate-kanban`. Never move a task across more than one lane in a single edit. Before a Done move, write the task's notes file and run `check-dod`; move the task to Done only after `check-dod` exits 0 for it. On every Done or Blocked move, add a `handoff.md` line naming each task ID.
- **Main-thread budget:** workers return at most ~15 lines (verdict, files, evidence summary) and write detail to the task notes. Validation evidence (tested revision, commands, result lines) is always returned in full, and review verdicts are never shortened. Read successful command output through a tail (e.g. `Select-Object -Last 20`); read a failure in full. Do not re-read files a worker already summarised. Do each task's close-out (notes, lane move, gates, handoff line) in one tool call. Dispatch independent work in the same turn.
- Before every commit, run `check-commit`: `python "${CLAUDE_PLUGIN_ROOT}/scripts/check-commit.py" --message "<msg>"`. A non-zero exit blocks that commit until the message is fixed and the gate passes.
- **Re-invocation is a resume, never a restart.** Read kanban/handoff first; skip Done tasks; reconcile orphaned In Progress tasks against git/file ground truth (protocol step 2b).
- Prefer the bundled validator **scripts** over the `geeky_*` MCP tools (no permission prompts, immune to the plugin-root interpolation bug).
- Maintain the **heartbeat**: write `<folder>/.heartbeat` (JSON: `{"ts":"<ISO>","task":"T<x>","status":"running"}`) at run start, refresh `ts`+`task` at every task transition, set `status` to `"paused"` (deliberate stop) or `"done"` (run complete) before ending. External watchdogs key on this file.

## Review and batching rules

- Task review checks the task template's ACs and defined tests. Supporting reads do not expand the review into the full implementation chain.
- Phase review checks the phase requirements collectively and must answer **Can we move to the next phase?** The **READY TO ADVANCE** or **BLOCKED** verdict must come from a `geeky-orchestration:code-reviewer` subagent, for every phase including the last; record it with the reviewer's agent ID in the step-17 `handoff.md` phase block before advancing.
- Review cadence: ONE `code-reviewer` dispatch at each phase end reviews every task in the phase, with a separate verdict per task against its ACs and defined tests, and issues the phase verdict. There is no per-task review dispatch. A phase of more than 4 tasks, or one too large to review AC by AC in one pass, is split into dispatches of at most 4 related tasks.
- A task is eligible when every dependency is Done, or is In Review in the current phase with passing validation evidence. Tasks wait in In Review until the phase review; Done moves follow once it clears.
- Final implementation review uses `impl-review`; it does not replace the last phase review. Do not create a second final-review process.
- Send blocking findings to `geeky-coder`, batched by owner. Re-review only the affected tasks, in one dispatch; dependents of a changed task re-run their validation. Keep separate task verdicts and evidence; isolate shared test resources.
- Record a consequence for another task in that task's notes and in `handoff.md`.
- Verify saved test evidence before rerunning. Reuse it while the tested code, dependencies and relevant environment remain valid; record why a rerun is needed.

Blocking findings must cite the task contract and evidence. Repeated work needs a reason and the smallest useful check. After two unsuccessful correction cycles, diagnose the cause without extending existing retry limits. Once authorized gates pass, close out; optional improvements do not reopen acceptance. Keep these decisions in existing task notes.

## Long-run resilience

- **Session grain:** default to ONE phase (or wave) per session — checkpoint to `handoff.md`, set heartbeat `paused`, and continue in a fresh session — rather than one marathon run. Evidence: chained short sessions had zero stalls/auth incidents where a 91-hour mega-run had seven. Re-entry is cheap because re-invocation resumes (see Execution constraints).
- **Auth:** before a run expected to exceed ~1 hour, have the user `/login` first (preflight reminds you). On any 401/auth-expiry failure mid-run, the FIRST action is appending a resume block to `handoff.md` (current task, exact state, next command) — the session itself may be unrecoverable.
- **Quiet/stalled run — diagnose in order:** (1) API-error interruption — scan the log tail for `<synthetic>` model turns (real subtypes here: spend-limit / session-limit / 401 — NOT literal "529"), (2) validator/gate crash, (3) logic/plan. Checkpoint immediately (the turn may be killed). Fix by subtype: quota limits → raise/wait (a `/model` switch does NOT help); 401 → `/login`; genuine 529 capacity → `/model` (per-model) or wait. Full table in [references/execution-protocol.md](references/execution-protocol.md#failure-modes).

## Full protocol

Use this skill with deferred details in [references/execution-protocol.md](references/execution-protocol.md).
