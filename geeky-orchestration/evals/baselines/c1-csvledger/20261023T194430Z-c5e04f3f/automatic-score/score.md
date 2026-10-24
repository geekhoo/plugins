# Score: 20261023T194430Z-c5e04f3f (c1-csvledger)

Plugin `bee7b14`, codex / gpt-6.1-sol. Scored 2026-10-23T20:09:20Z by `score-run.py`. Workspace: run.json workspace. Validation blocks re-run. Manual verdicts: none.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 100.0 | P 1.000, S 1.000, D 1.00 |
| Adherence | 0.35 | 57.1 | 16/28 |
| Consistency | 0.20 | 53.7 | DPC 8/19 = 0.421, OC 1.00 |
| Task tier | 0.10 | 10.0 | L_run None ms, L_ref 2678 ms |
| **Composite** | | **66.7** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | needs_judge (no cap applied) | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 3 task file(s) found. |
| adh.task_schema | ✓ | OK: 3 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 3 task(s) tracked, 3 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=3 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✓ | T1-validated-input.notes.md |
| adh.notes.T2 | ✓ | T2-exact-engine.notes.md |
| adh.notes.T3 | ✓ | T3-cli-acceptance.notes.md |
| adh.task_review.T1 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T2 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T3 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.phase_verdict.P1 | ✗ | phase P1 ['T1', 'T2']: reviewer none; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✗ | phase P2 ['T3']: reviewer none; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [(180, True), (181, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [(180, None), (181, True)] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [(246, True), (247, True)] |
| adh.kanban_after_moves | ✗ | 0 lane-move calls; without validate-kanban: none |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff a2e51d3..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | judge? | judge: one concern per commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | judge? | judge: final report claims (D8) |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✗ | 0 dispatches, max 0 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✗ | 0 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | judge? | max 0 concurrent coders; justification needs judge (dp07.justification) |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3'] |
| dp09 | Task review, per task | 2 | ✗ | not reviewed: ['T1', 'T2', 'T3'] |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3'] |
| dp11 | Phase verdict from a phase review | 2 | ✗ | failing phases: ['P1', 'P2'] |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | 0 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | judge? | judge |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 5 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 1 | 10.0 | 287 | 0.312 |
| T2 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 1 | 10.0 | 273 | 0.305 |
| T3 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 1 | 10.0 | 425 | 0.382 |

## Needs judge

Excluded from their denominators until a `--manual` verdict is given:

- `adh.one_concern_per_commit`
- `adh.final_report_claims`
- `dp07`
- `dp13`
