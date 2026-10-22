# Score: 20261022T065938Z (c1-csvledger)

Plugin `e674b86`, claude-code / claude-sonnet-5-5. Scored 2026-10-22T12:16:34Z by `score-run.py`. Workspace: run.json workspace. Validation blocks re-run. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 97.6 | P 1.000, S 0.843, D 1.00 |
| Adherence | 0.35 | 80.3 | 61/76 |
| Consistency | 0.20 | 67.3 | DPC 13/22 = 0.591, OC 1.00 |
| Task tier | 0.10 | 72.6 | L_run 2976 ms, L_ref 2678 ms |
| **Composite** | | **83.0** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: every completion claim is true (D8) | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 8 task file(s) found. |
| adh.task_schema | ✓ | OK: 8 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 8 task(s) tracked, 8 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=8 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.dod.T4 | ✓ | DOD_OK: T4 |
| adh.dod.T5 | ✓ | DOD_OK: T5 |
| adh.dod.T6 | ✓ | DOD_OK: T6 |
| adh.dod.T7 | ✓ | DOD_OK: T7 |
| adh.dod.T8 | ✓ | DOD_OK: T8 |
| adh.handoff_batch.T1 | ✓ | Done move call 161; handoff naming T1 in call 162 |
| adh.handoff_batch.T2 | ✓ | Done move call 161; handoff naming T2 in call 162 |
| adh.handoff_batch.T3 | ✓ | Done move call 161; handoff naming T3 in call 162 |
| adh.handoff_batch.T4 | ✓ | Done move call 161; handoff naming T4 in call 162 |
| adh.handoff_batch.T5 | ✓ | Done move call 212; handoff naming T5 in call 212 |
| adh.handoff_batch.T6 | ✓ | Done move call 212; handoff naming T6 in call 212 |
| adh.handoff_batch.T7 | ✓ | Done move call 258; handoff naming T7 in call 258 |
| adh.handoff_batch.T8 | ✓ | Done move call 258; handoff naming T8 in call 258 |
| adh.notes.T1 | ✓ | T1-scaffold-errors-csvio.notes.md |
| adh.notes.T2 | ✓ | T2-money.notes.md |
| adh.notes.T3 | ✓ | T3-transactions-dedup.notes.md |
| adh.notes.T4 | ✓ | T4-rules.notes.md |
| adh.notes.T5 | ✓ | T5-report-render.notes.md |
| adh.notes.T6 | ✓ | T6-cli.notes.md |
| adh.notes.T7 | ✓ | T7-oracle-tests.notes.md |
| adh.notes.T8 | ✓ | T8-error-usage-determinism-tests.notes.md |
| adh.events.T1 | ✗ | T1.events.jsonl: 0 entries |
| adh.events.T2 | ✗ | no tasks/T2.events.jsonl |
| adh.events.T3 | ✗ | no tasks/T3.events.jsonl |
| adh.events.T4 | ✗ | no tasks/T4.events.jsonl |
| adh.events.T5 | ✗ | no tasks/T5.events.jsonl |
| adh.events.T6 | ✗ | no tasks/T6.events.jsonl |
| adh.events.T7 | ✗ | no tasks/T7.events.jsonl |
| adh.events.T8 | ✗ | no tasks/T8.events.jsonl |
| adh.task_review.T1 | ✓ | call 135 'Review phase 1 (T1-T4)' (description) PASS |
| adh.task_review.T2 | ✓ | call 135 'Review phase 1 (T1-T4)' (description) PASS |
| adh.task_review.T3 | ✓ | call 135 'Review phase 1 (T1-T4)' (description) PASS |
| adh.task_review.T4 | ✓ | call 135 'Review phase 1 (T1-T4)' (description) PASS |
| adh.task_review.T5 | ✓ | call 193 'Review phase 2 (T5-T6)' (description) PASS |
| adh.task_review.T6 | ✓ | call 193 'Review phase 2 (T5-T6)' (description) PASS |
| adh.task_review.T7 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T8 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2', 'T3', 'T4']: reviewer call 135; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T5', 'T6']: reviewer call 193; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✗ | phase P3 ['T7', 'T8']: reviewer none; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✓ | Done call 161; last code edit 99; check-dod runs [(161, None)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T2 | ✓ | Done call 161; last code edit 112; check-dod runs [(161, None)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T3 | ✓ | Done call 161; last code edit 130; check-dod runs [(161, None)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T4 | ✓ | Done call 161; last code edit 160; check-dod runs [(161, None)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T5 | ✗ | Done call 212; last code edit 175; check-dod runs [] |
| adh.gates_before_done.T6 | ✗ | Done call 212; last code edit 191; check-dod runs [] |
| adh.gates_before_done.T7 | ✓ | Done call 258; last code edit 226; check-dod runs [(258, True)] |
| adh.gates_before_done.T8 | ✓ | Done call 258; last code edit 252; check-dod runs [(258, True)] |
| adh.kanban_after_moves | ✓ | 4 lane-move calls; without validate-kanban: none |
| adh.commit_msg.1f9ffd6 | ✓ | feat(core): scaffold package, errors and csv io layer: OK: commit message valid. |
| adh.commit_msg.4a8c632 | ✓ | feat(core): add exact money parsing and formatting: OK: commit message valid. |
| adh.commit_msg.e5e4757 | ✓ | feat(core): load and deduplicate transactions: OK: commit message valid. |
| adh.commit_msg.f877a0c | ✓ | feat(core): load rules and categorize: OK: commit message valid. |
| adh.commit_msg.f5252dc | ✓ | docs: record phase 1 completion and kanban state: OK: commit message valid. |
| adh.commit_msg.487822e | ✓ | feat(output): aggregate report data and render tables and JS: OK: commit message valid. |
| adh.commit_msg.2249865 | ✓ | feat(cli): add command line entry point: OK: commit message valid. |
| adh.commit_msg.c9c92b9 | ✓ | docs: record phase 2 completion: OK: commit message valid. |
| adh.commit_msg.455d4a0 | ✓ | fix(core): exact money for very long amounts; single-line in: OK: commit message valid. |
| adh.commit_msg.8e7e5b3 | ✓ | test(oracles): byte-exact oracle and acceptance tests: OK: commit message valid. |
| adh.commit_msg.15484d0 | ✓ | test(edge): error table, usage and edge-case tests: OK: commit message valid. |
| adh.commit_msg.d073f92 | ✓ | docs: record phase 3 completion and run summary: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 49feb3e..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✓ | manual: doc: 1/1 |
| adh.no_orchestrator_code_edits | ✗ | call 160 (geeky-implement): csvledger/rules.py; call 295 (impl-review): csvledger/csvio.py |
| adh.final_report_claims | ✗ | manual: report claims a reviewer verdict for every phase; phase 3 had none (process claim, no cap) |
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
| dp06 | Event logs created on dispatch | 1 | ✗ | missing/empty: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'] |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | max 2 concurrent coders; justification: DP7 (doc: pass) |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'] |
| dp09 | Task review, per task | 2 | ✗ | not reviewed: ['T7', 'T8'] |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T5', 'T6'] |
| dp11 | Phase verdict from a phase review | 2 | ✗ | failing phases: ['P3'] |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 162: 0 check-commit run(s) for 5 commit(s); call 212: 0 check-commit run(s) for 3 commit(s); call 258: 0 check-comm |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: DP13 (doc: pass) |
| dp14 | Handoff at each Done move (D82) | 1 | ✓ | failing: none |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 2 (calls [99] + D87 [295]) | 0.75 | 1.0 | 296 | 0.78 | 1 | 85.6 | 220 | 0.120 |
| T2 | 1 (calls [113]) | 1.00 | 1.0 | 225 | 0.83 | 1 | 96.6 | 64 | 0.047 |
| T3 | 1 (calls [131]) | 1.00 | 1.0 | 144 | 0.89 | 1 | 97.8 | 149 | 0.071 |
| T4 | 3 (calls [132, 134] + D87 [160]) | 0.50 | 1.0 | 141 | 0.89 | 1 | 77.9 | 215 | 0.148 |
| T5 | 2 (calls [172, 176]) | 0.75 | 1.0 | 239 | 0.82 | 1 | 86.4 | 281 | 0.137 |
| T6 | 2 (calls [190, 192]) | 0.75 | 1.0 | 150 | 0.89 | 1 | 87.7 | 250 | 0.128 |
| T7 | 3 (calls [219, 224, 227]) | 0.50 | 0.0 | 148 | 0.89 | 1 | 47.8 | 206 | 0.145 |
| T8 | 3 (calls [243, 251, 255]) | 0.50 | 0.0 | 274 | 0.79 | 1 | 45.9 | 423 | 0.205 |
