---
name: align-docs
description: This skill should be used when the user asks to "align the docs", "reconcile the planning folder", "fix plan/kanban/tasks drift", or "update the handoff" — detect and reconcile drift across a planning folder and emit a dated alignment report.
user-invocable: true
argument-hint: "<path to docs/<feature> folder, or feature name>"
---

# Align Docs

Use when a geeky-style planning folder has drifted — task statuses, kanban lanes, plan sequencing, and the handoff log no longer agree. Goal: detect and fix drift, then report what changed. Read-only analysis first; edits only after the drift is enumerated.

Context: this targets the `/geeky-plan → /geeky-implement` workflow, where traceability and a chronological handoff log matter. The failure mode is drift between plan, kanban, tasks, and handoff.

## Workflow

### 1. Locate the planning folder
- Resolve from `$ARGUMENTS` (a path like `docs/app_v2_kg`, or a feature name to search under `docs/`).
- Expect these artifacts: `implementation-plan.md` (or `plan.md`), `kanban.md`, `references.md`, `handoff.md`, and a `tasks/` directory.
- If any are missing, list what's missing and stop — that's an `INVALID_PLANNING_FOLDER` condition; the fix is to run `/geeky-plan` to completion, not to fabricate artifacts.

### 2. Build the truth table (read-only)
Cross-reference, do not edit yet:
- **Tasks vs kanban:** every `tasks/T*.md` should appear in exactly one kanban lane. Flag tasks in no lane, in multiple lanes, or lanes referencing non-existent tasks.
- **Task schema:** each task file should have its required sections (e.g. *In scope*, *Dependencies*, *Acceptance Criteria*). Flag missing sections — this is what triggers `INVALID_TASK_SCHEMA`.
- **Plan vs tasks:** plan sequencing/phases should match task dependencies. Flag ordering contradictions and stale task IDs referenced in the plan.
- **References:** quoted file paths, line numbers, and links in `references.md` and the plan should still resolve against the current codebase (use git status/diff to spot moved or renamed files).
- **Handoff:** is the latest state reflected? Note the last entry date.

### 3. Report before fixing
Write `<folder>/alignment-report-<YYYY-MM-DD>.md` listing every drift found, grouped by artifact, each with the conflicting values and the proposed reconciliation. Present a summary to the user.

### 4. Apply fixes (after the report)
- Reconcile kanban lanes to actual task state; fix duplicate/missing lane entries.
- Repair task schema sections.
- Update plan sequencing and stale references.
- Append a dated entry to `handoff.md` summarizing what was aligned (chronological, never rewrite history).
- Re-run any project validator (e.g. `/geeky-status`) to confirm clean.

### 5. Commit
Per the user's atomic-commit preference: small, logically-grouped commits (e.g. one for kanban, one for tasks, one for plan/handoff) with clear messages. Don't lump unrelated edits.

## Notes
- On Windows use forward slashes in the Bash tool and avoid backslash paths.
- This skill quality-checks alignment; it does not redesign the plan. If the plan itself is wrong, surface that and defer to `/geeky-plan`.
