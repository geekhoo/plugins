---
name: archive
description: >-
  Archive a completed `geeky-plan` package and finalize its docs structure.
  Use when a plan is fully implemented and implementation is complete.
---

# Archive Completed Feature Plan

## Prerequisites

This skill requires explicit command routing:

- The `/archive` command must be configured to invoke this skill by name or path.
- Without proper wiring, this skill will not respond to user commands.
- Verify command registration in your agent configuration before use.

## When to Use

Invoke `/archive` after `/geeky-implement` has completed a `geeky-plan` package.
The package should satisfy:

- All tasks completed in kanban
- Quality gates passing (or explicitly recorded as skipped)
- All checks documented in handoff
- Team sign-off recorded in handoff

## Arguments

Pass a planning folder path (recommended), e.g. `docs/notifications/`.
If no argument is provided, scan `docs/` for the most recent folder with:

- `implementation-plan.md`
- `handoff.md` marked complete

## Workflow

### 1. Identify the planning folder

- Resolve the target from arguments, or discover the most recently completed package in `docs/`.
- **Missing file checks (STOP if any fail):**
  - If `handoff.md` is missing: Report "Cannot archive: handoff.md not found in <folder>. Archive requires a completed handoff document." and STOP.
  - If `kanban.md` is missing: Report "Cannot archive: kanban.md not found in <folder>. Archive requires a task kanban." and STOP.
  - If `implementation-plan.md` is missing: Report "Cannot archive: implementation-plan.md not found in <folder>. Archive requires a planning document." and STOP.
- Read `handoff.md` and confirm status is "Complete".
- If status is not complete, warn and stop: "Cannot archive: handoff.md status is '<current_status>', not 'Complete'. Resolve implementation issues before archiving."

### 2. Create destination directories

Create:

- `archives/docs/<folder-name>-planning/`
- Keep `docs/<folder-name>/` for the final artifact set

### 3. Move planning-only artifacts to archive

Move these planning artifacts with `git mv` into `archives/docs/<folder-name>-planning/`:

- `kanban.md`
- `execution-schedule.md` (if present)
- `references.md`
- `tasks/` (entire directory)
- `tasks/T*.notes.md` (if present)
- `review-development-project-manager.md` (if present)
- `implementation-plan.md`
- `draft.md` (if present)
- Any `*-prompt.md` files (handoff-prompt, optimization-prompt, etc.)
- Any other plan-generation-only working docs that are not meant to remain canonical

### 4. Keep permanent docs in `docs/<folder-name>/`

Keep only the canonical final docs in `docs/<folder-name>/`:

- `feature-specification.md` (or your requirements document that was implemented)
- `handoff.md` (implementation summary)
- `README.md` (delivery summary)

### 5. Create / refresh README.md

Write `docs/<folder-name>/README.md` with:

- Spec title and completion date
- "What Was Delivered" (bullet list)
- Notes on reviews/optimizations that were applied
- "Delegation to Future Spec/Tasks" section
- Pointer to `archives/docs/<folder-name>-planning/`

### 6. Tidy directories

Remove now-empty directories under the source plan folder.

### 7. Update CLAUDE.md and AGENTS.md

In the `## Current State` section:

- Mark the archived folder as complete with task counts/status.
- Keep the new `docs/<folder-name>/` path as the canonical reference.
- Update the next folder pointer (if known).

### 8. Commit

CONDITIONAL:

- Linux/macOS (bash):

```bash
git add -A
git commit -m "chore: Archive completed planning package" -m "Move planning artifacts to archives/docs/<folder-name>-planning/" -m "Keep implementation specification, handoff, and README in docs/<folder-name>/" -m "Update CLAUDE.md / AGENTS.md current state"
```

- Windows (pwsh):

```pwsh
git add -A
git commit -m "chore: Archive completed planning package" -m "Move planning artifacts to archives/docs/<folder-name>-planning/" -m "Keep implementation specification, handoff, and README in docs/<folder-name>/" -m "Update CLAUDE.md / AGENTS.md current state"
```

### 9. Verify

- Confirm `implementation-plan.md` is in archive, not in the final folder.
- Confirm `tasks/` and task notes are fully archived.
- Confirm `feature-specification.md`, `handoff.md`, and `README.md` remain in `docs/<folder-name>/`.
- Confirm `CLAUDE.md` and `AGENTS.md` reflect final state.
- Confirm no broken references in final docs.

## Rules

- **Use `git mv`** for all file moves.
- **Never delete canonical artifacts** — move to `archives/` instead.
- **`archives/` is git-tracked** and intentionally excluded from AI context.
- **Do not archive incomplete work** — warn and stop.
- **Stop immediately if required files are missing** — report exact missing file(s) and do not proceed with partial archiving.
- **Behavior is conservative and traceable** — every move should be verifiable via git history.
- **README must be self-contained** so readers can understand outcomes without opening full task history.
