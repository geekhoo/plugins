---
name: archive
description: >-
  Archive a completed `geeky-plan` package. Moves planning artifacts to
  `archives/`, keeps canonical docs in place.
---

# Archive Completed Feature Plan

## When to Use

Run `/archive` after `/geeky-implement` finishes a `geeky-plan` package. The package needs:

- All tasks Done in kanban
- Quality gates passing (or explicitly recorded as skipped)
- Checks documented in handoff
- Team sign-off in handoff

## Arguments

Pass a planning folder path, e.g. `docs/notifications/`.
No argument → scan `docs/` for the most recent folder with:

- `implementation-plan.md`
- `handoff.md` marked complete

## Workflow

### 1. Identify the planning folder

Resolve the target from arguments, or find the most recently completed package in `docs/`.

**Missing file checks — STOP if any fail:**
- `handoff.md` missing → "Cannot archive: handoff.md not found in <folder>."
- `kanban.md` missing → "Cannot archive: kanban.md not found in <folder>."
- `implementation-plan.md` missing → "Cannot archive: implementation-plan.md not found in <folder>."

Read `handoff.md` and confirm status is "Complete". If it isn't: "Cannot archive: handoff.md status is '<current_status>', not 'Complete'." Fix implementation issues first.

### 2. Create destination directories

- `archives/docs/<folder-name>-planning/`
- Keep `docs/<folder-name>/` for the final artifact set

### 3. Move planning-only artifacts to archive

`git mv` these into `archives/docs/<folder-name>-planning/`:

- `kanban.md`
- `execution-schedule.md` (if present)
- `references.md`
- `tasks/` (entire directory)
- `tasks/T*.notes.md` (if present)
- `review-development-project-manager.md` (if present)
- `implementation-plan.md`
- `draft.md` (if present)
- Any `*-prompt.md` files (handoff-prompt, optimization-prompt, etc.)
- Any other plan-generation working docs not meant to stay canonical

### 4. Keep permanent docs in `docs/<folder-name>/`

Only these stay:

- `feature-specification.md` (or the requirements doc that was implemented)
- `handoff.md` (implementation summary)
- `README.md` (delivery summary)

### 5. Create / refresh README.md

Write `docs/<folder-name>/README.md` with:

- Spec title and completion date
- "What Was Delivered" (bullet list)
- Notes on reviews or optimizations applied
- "Delegation to Future Spec/Tasks" section
- Pointer to `archives/docs/<folder-name>-planning/`

### 6. Tidy directories

Remove now-empty directories under the source plan folder.

### 7. Update CLAUDE.md and AGENTS.md

In the `## Current State` section:

- Mark the archived folder as complete with task counts/status
- Keep `docs/<folder-name>/` as the canonical reference path
- Update the next folder pointer if known

### 8. Commit

Same command on all platforms (bash and pwsh):

```bash
git add -A
git commit -m "chore: Archive completed planning package" -m "Move planning artifacts to archives/docs/<folder-name>-planning/" -m "Keep implementation specification, handoff, and README in docs/<folder-name>/" -m "Update CLAUDE.md / AGENTS.md current state"
```

### 9. Verify

- `implementation-plan.md` is in archive, not in the final folder
- `tasks/` and task notes are fully archived
- `feature-specification.md`, `handoff.md`, `README.md` remain in `docs/<folder-name>/`
- `CLAUDE.md` and `AGENTS.md` reflect final state
- No broken references in final docs

## Rules

- **Use `git mv`** for all file moves
- **Never delete canonical artifacts** — move to `archives/` instead
- **`archives/` is git-tracked** and intentionally excluded from AI context
- **Don't archive incomplete work** — warn and stop
- **Stop if required files are missing** — report what's missing, don't proceed with partial archiving
- **Every move is traceable** via git history
- **README must be self-contained** — readers should understand outcomes without opening the full task history
