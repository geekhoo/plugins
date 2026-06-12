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

Run validators first (fail fast):

```bash
# Windows
pwsh -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.ps1" -Path "<folder>"

# macOS/Linux/Python
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"
```

If validation fails, stop and report.

## Execution constraints

- Do not modify planning contract files (`implementation-plan.md`, `feature-specification.md`, `draft.md`, `references.md`, `tasks/Tx-*.md`, `handoff.md`).
- Use `geeky-coder` for implementation work and avoid pausing between tasks unless blocked.
- Do not push and do not use `--amend`.
- Update `kanban.md` and `handoff.md` on every task state change.

## Full protocol

Use this skill with deferred details in [references/execution-protocol.md](references/execution-protocol.md).
