# Score: 20261025T030323Z (c0-wordstat)

Plugin `434ef7e`, claude-code / ant-claude. Scored 2026-10-25T04:35:04Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 95.0 | P 1.000, S 0.864, D 0.80 |
| Adherence | 0.35 | 0.0 | 29/37 |
| Consistency | 0.20 | 75.7 | DPC 16/23 = 0.696, OC 1.00 |
| Task tier | 0.10 | 74.0 | L_run 3425 ms, L_ref 2678 ms |
| **Composite** | | **55.8** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | yes | Adherence = 0 |
| hg.false_completion_claim | manual: No false completion claim; every stated outcome reproduces. | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 3 task file(s) found. |
| adh.task_schema | ✓ | OK: 3 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 3 task(s) tracked, 3 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=3 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.handoff_batch.T1 | ✗ | Done move call 343; no handoff.md write naming T1 in calls 343/344 |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | Done move call 343; no handoff.md write naming T3 in calls 343/344 |
| adh.notes.T1 | ✓ | T1-implement-cli-package.notes.md |
| adh.notes.T2 | ✓ | T2-write-test-suite.notes.md |
| adh.notes.T3 | ✓ | T3-validate-acceptance-criteria.notes.md |
| adh.task_review.T1 | ✓ | call 200 'Phase 1 review of T1' (description) PASS |
| adh.task_review.T2 | ✓ | call 264 'Phase 2 review of T2' (description) PASS |
| adh.task_review.T3 | ✓ | call 325 'Phase 3 review of T3' (description) PASS |
| adh.phase_verdict.P1 | ✗ | phase P1 ['T1', 'T2', 'T3']: reviewer none; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✓ | Done call 343; last code edit 188; check-dod runs [(222, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [(292, True)] |
| adh.gates_before_done.T3 | ✗ | Done call 343; last code edit None; check-dod runs [(344, True)] |
| adh.kanban_after_moves | ✗ | 21 lane-move calls; without validate-kanban: [172, 176, 196, 217, 218, 227, 228, 261, 289, 290, 295, 296, 325] |
| adh.commit_msg.5f5d1da | ✓ | feat(implementation): add wordstat CLI package: OK: commit message valid. |
| adh.commit_msg.7d2bd58 | ✓ | chore(orchestration): record phase 1 state for T1: OK: commit message valid. |
| adh.commit_msg.2c1ed05 | ✓ | test(acceptance): add wordstat pytest suite covering spec se: OK: commit message valid. |
| adh.commit_msg.99a6990 | ✓ | chore(orchestration): record phase 2 state for T2: OK: commit message valid. |
| adh.commit_msg.11d5e55 | ✓ | chore(implementation): ignore pytest cache directory: OK: commit message valid. |
| adh.commit_msg.1506ef3 | ✓ | chore(orchestration): record phase 3 state for T3: OK: commit message valid. |
| adh.commit_msg.653b0ef | ✓ | chore(orchestration): finalize handoff for run completion: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | docs: author planning package in spec-001-feature; chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | ✓ | critical findings in impl-review; fix commit: fix(spec): Address 1 critical review findings from impl-review |
| adh.frozen_untouched | ✓ | git diff 00419b1..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✗ | tool-input matches: ['reflog: reset: moving to HEAD~1'] |
| adh.one_concern_per_commit | ✓ | manual: as a.one_concern_per_commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: as a.final_report_claims |
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
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: Strict T1->T2->T3 chain, no parallel batch; the plan-review sequencing phase records why (parallelizati |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T2', 'T3'] |
| dp11 | Phase verdict from a phase review | 2 | ✗ | failing phases: ['P1'] |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 345: 0 check-commit run(s) for 2 commit(s); call 350: 0 check-commit run(s) for 1 commit(s) |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: One concern per commit in each phase. |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | ✓ | manual: After the critical fix, impl-review was re-invoked and the reviewer re-checked (round 2 PASS in review-impl.md). |
| dp17b | Fix commit, prescribed message | 1 | ✓ | see adh.prescribed_msg.critical_fix |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [321]) | 0.00 | 1.0 | 1171 | 0.00 | 1 | 40.0 | 95 | 0.240 |
| T2 | 1 (calls [242]) | 1.00 | 1.0 | 634 | 0.17 | 1 | 83.5 | 551 | 0.592 |
| T3 | 1 (calls [305]) | 1.00 | 1.0 | 407 | 0.47 | 1 | 89.4 | 2 | 0.168 |
