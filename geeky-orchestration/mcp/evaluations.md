# geeky_mcp evaluations

These gates are **deterministic** over a planning folder, so evaluations are exact
input → output assertions rather than open-ended questions. Each case below was
verified end-to-end through the running MCP server (tools invoked via
`uv run --with mcp`).

## Fixture

A planning folder with:
- `implementation-plan.md`, `references.md`, `feature-specification.md`, `draft.md`, `handoff.md` (mentions T1)
- `tasks/T1-alpha.md`, `tasks/T2-beta.md` (both complete, from the task template)
- `tasks/T1-alpha.notes.md`
- `kanban.md` with lanes Backlog/Ready/In Progress/In Review/Blocked/Done, T2 in Ready, T1 in Done

## Cases

| # | Tool | Input | Expected |
|---|---|---|---|
| 1 | `geeky_validate_planning_folder` | folder=fixture | `ok=true`, `task_count=2`, `exit_code=0` |
| 2 | `geeky_validate_task_schema` | folder=fixture | `ok=true` (both task files carry all required sections) |
| 3 | `geeky_validate_kanban` | folder=fixture | `ok=true`, `lane_counts.Done=1`, `lane_counts.Ready=1` |
| 4 | `geeky_check_dod` | folder=fixture, task=T1 | `ok=true` (notes exist, in Done, handoff mentions T1) |
| 5 | `geeky_check_commit` | message="feat(plan): add gate\n\nTasks: T1" | `ok=true` |
| 6 | `geeky_check_commit` | message="nope" | `ok=false`, errors include bad subject + no task ref |
| 7 | `geeky_check_frozen_artifact` | file_path=.../implementation-plan.md | `frozen=true`, reason set |
| 8 | `geeky_check_frozen_artifact` | file_path=.../tasks/T1-alpha.notes.md | `frozen=false` |
| 9 | `geeky_validate_kanban` | folder with T3-gamma.md not in any lane | `ok=false`, error "T3 ... not placed in any kanban lane" |
| 10 | `geeky_check_dod` | task=T2 (no notes, not in Done) | `ok=false`, error "no per-task notes file" |

## Re-run

Recreate the fixture and call the tools (cases 1–8 are the bundled smoke check; 9–10
mutate the fixture as described). All ten were green at build time
(2026-06-01): planning-folder, task-schema, kanban, DoD, commit (pass+fail), and the
two frozen-artifact checks all returned the expected `ok`/`frozen`/`exit_code`.
