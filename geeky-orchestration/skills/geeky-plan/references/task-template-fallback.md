# Inline fallback task template

Fallback for when `${CLAUDE_PLUGIN_ROOT}/templates/task_template.md` cannot be read (the bundled template is canonical — prefer it; keep this file in sync with it). This fallback exists because of the known CLAUDE_PLUGIN_ROOT-interpolation bug: never delete it.

```markdown
Task Name:
[Clear action-based title]

Context:
[Why this task exists, what feature/user flow it supports]

Scope:

## In scope:

- [What is being changed and where]

## Out of scope:

- [What is intentionally NOT being changed]

Module/System:
[Where this belongs]

## Dependencies:

- [Tx-task-name or None]

## Technical Notes:

- [Constraints, invariants, links to plan sections]

## Acceptance Criteria:

-
-

Definition of Done:

- Code reviewed
- Tested (manual/unit)
- Deployed to staging
- No critical bugs

Tests/Validation Before Next Task:

- [Exact commands that must pass]

Estimate:
[S/M/L]

Priority:
[P0/P1/P2]
```
