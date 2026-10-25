# Score: 20261025T061414Z (c0-wordstat)

Plugin `2838079`, claude-code / ant-claudex. Scored 2026-10-25T07:47:06Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 93.2 | P 1.000, S 0.946, D 0.60 |
| Adherence | 0.35 | 75.0 | 30/40 |
| Consistency | 0.20 | 84.8 | DPC 17/21 = 0.810, OC 1.00 |
| Task tier | 0.10 | 82.9 | L_run 6531 ms, L_ref 2678 ms |
| **Composite** | | **84.1** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: No completion was claimed. | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 4 task file(s) found. |
| adh.task_schema | ✓ | OK: 4 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 4 task(s) tracked, 4 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=4 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.dod.T4 | ✓ | DOD_OK: T4 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T4 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✓ | T1-counting-core.notes.md |
| adh.notes.T2 | ✓ | T2-cli-and-entry.notes.md |
| adh.notes.T3 | ✓ | T3-contract-coverage-tests.notes.md |
| adh.notes.T4 | ✓ | T4-final-integration-validation.notes.md |
| adh.task_review.T1 | ✓ | call 240 'Phase 1 Core review T1 T2' (description) PASS |
| adh.task_review.T2 | ✓ | call 240 'Phase 1 Core review T1 T2' (description) PASS |
| adh.task_review.T3 | ✓ | call 312 'Phase 2 code review T3+T4' (description) PASS |
| adh.task_review.T4 | ✓ | call 312 'Phase 2 code review T3+T4' (description) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2']: reviewer call 240; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T3', 'T4']: reviewer call 312; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [(260, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [(261, True)] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [(326, True)] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [(327, True)] |
| adh.kanban_after_moves | ✗ | 0 lane-move calls; without validate-kanban: none |
| adh.commit_msg.377dcc7 | ✓ | feat(core): wordstat counting core, formatters, and pytest h: OK: commit message valid. |
| adh.commit_msg.2ed0291 | ✓ | feat(core): wordstat CLI, entry point, and CLI subprocess te: OK: commit message valid. |
| adh.commit_msg.16b785e | ✓ | chore(core): record Phase 1 completion in planning artifacts: OK: commit message valid. |
| adh.commit_msg.addaf72 | ✓ | feat(prove): contract coverage tests for wordstat edge matri: OK: commit message valid. |
| adh.commit_msg.96604d3 | ✓ | chore(prove): record Phase 2 completion in planning artifact: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 01168ea..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✓ | manual: as a.one_concern_per_commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✗ | manual: as a.final_report_claims |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: Strict T1->T4 chain; implementation-plan and review-plan record why there is no parallel wave. |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3', 'T4'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 5 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: One concern per commit in each phase. |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 4 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [210]) | 1.00 | 1.0 | 1027 | 0.30 | 1 | 86.0 | 119 | 0.236 |
| T2 | 1 (calls [233]) | 1.00 | 1.0 | 718 | 0.51 | 1 | 90.2 | 171 | 0.285 |
| T3 | 1 (calls [278]) | 1.00 | 1.0 | 1109 | 0.24 | 1 | 84.8 | 244 | 0.353 |
| T4 | 1 (calls [305]) | 0.00 | 1.0 | 358 | 0.76 | 1 | 55.1 | 0 | 0.125 |
