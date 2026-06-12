---
name: archive
description: >-
  Archive a completed spec's planning artifacts and finalize its docs structure.
  Use when a spec is fully implemented and concluded — moves planning files to archives/,
  creates the permanent docs/spec-NNN-name/ folder with spec doc + handoff + README,
  and updates CLAUDE.md current state.
---

# Archive Completed Spec

## When to Use

Invoke with `/archive` after a spec is fully implemented, reviewed, and committed. The spec should have:
- All tasks completed
- Build passing with zero warnings
- All tests green
- Handoff document updated with final status

## Arguments

The user may pass a spec identifier (e.g., `/archive spec-003` or `/archive SPEC-0004`). If no argument is given, look for the most recent spec in `docs/specifications/` that has a completed handoff.

## Workflow

### 1. Identify the spec

- Parse the spec number from arguments, or scan `docs/specifications/` for the active spec
- Read the handoff document to confirm status is "Complete"
- If not complete, warn the user and stop

### 2. Create destination directories

```bash
mkdir -p archives/docs/spec-NNN-planning
mkdir -p docs/spec-NNN-name/
```

Use the spec's descriptive name for the docs folder (e.g., `spec-003-campaign-management`).

### 3. Move planning artifacts to archives

These files go to `archives/docs/spec-NNN-planning/`:
- `kanban.md`
- `execution-schedule.md`
- `implementation-plan.md`
- `tasks/` (entire directory)
- `references.md`
- `research-prompt.md`
- Any `*-prompt.md` files (handoff-prompt, optimization-prompt, etc.)
- Any other planning/working documents

Use `git mv` to preserve history.

### 4. Move permanent docs

These files stay in `docs/spec-NNN-name/`:
- `SPEC-NNNN-*.md` (the requirements document)
- `handoff.md` (execution summary)

Use `git mv` to preserve history.

### 5. Write a README

Create `docs/spec-NNN-name/README.md` with:
- Spec title and status (completed date)
- "What Was Delivered" section (bullet list of key deliverables)
- Any optimization/review passes that were applied
- "Delegation to Future Specs" section (what was deferred)
- Pointer to planning package location in archives

Read the spec doc and handoff to source this information.

### 6. Remove empty directories

```bash
rmdir docs/specifications/spec-NNN
```

If `docs/specifications/` is now empty, remove it too.

### 7. Update CLAUDE.md

In the `## Current State` section:
- Change the spec's entry from "Next" to "Complete" with task counts
- Add a reference to the new `docs/spec-NNN-name/` path
- Update the "Next" line to the subsequent spec (or remove if unknown)

### 8. Commit

```bash
git add -A
git commit -m "chore: Archive SPEC-NNNN planning artifacts, finalize docs structure

- Move planning artifacts to archives/docs/spec-NNN-planning/
- Keep spec doc + handoff + README in docs/spec-NNN-name/
- Update CLAUDE.md current state

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 9. Verify

- Confirm `docs/specifications/` is empty or removed
- Confirm `archives/docs/spec-NNN-planning/` has all planning files
- Confirm `docs/spec-NNN-name/` has spec doc, handoff, README
- Confirm CLAUDE.md reflects the new state
- Confirm build still passes (no broken file references)

## Rules

- **Always use `git mv`** to preserve file history
- **Never delete files** — they move to archives, not to oblivion
- **archives/ is git-tracked** but excluded from AI context (noted in CLAUDE.md and AGENTS.md)
- **Don't archive if spec is incomplete** — warn and stop
- **README should be self-contained** — a reader should understand what was delivered without reading the full spec
