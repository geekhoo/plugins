# Score: 20261022T125647Z (c1-csvledger)

Plugin `e572902`, claude-code / claude-sonnet-5-5. Scored 2026-10-23T21:34:31Z by `score-run.py`. Workspace: given. Validation blocks trace only. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 97.8 | P 1.000, S 0.855, D 1.00 |
| Adherence | 0.35 | 98.8 | 80/81 |
| Consistency | 0.20 | 100.0 | DPC 21/21 = 1.000, OC 1.00 |
| Task tier | 0.10 | 90.9 | L_run 2832 ms, L_ref 2678 ms |
| **Composite** | | **97.9** | |

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
| adh.planning_folder | ✓ | OK: planning folder valid. 10 task file(s) found. |
| adh.task_schema | ✓ | OK: 10 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 10 task(s) tracked, 10 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=10 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.dod.T4 | ✓ | DOD_OK: T4 |
| adh.dod.T5 | ✓ | DOD_OK: T5 |
| adh.dod.T6 | ✓ | DOD_OK: T6 |
| adh.dod.T7 | ✓ | DOD_OK: T7 |
| adh.dod.T8 | ✓ | DOD_OK: T8 |
| adh.dod.T9 | ✓ | DOD_OK: T9 |
| adh.dod.T10 | ✓ | DOD_OK: T10 |
| adh.handoff_batch.T1 | ✓ | Done move call 127; handoff naming T1 in call 127 |
| adh.handoff_batch.T2 | ✓ | Done move call 147; handoff naming T2 in call 147 |
| adh.handoff_batch.T3 | ✓ | Done move call 175; handoff naming T3 in call 175 |
| adh.handoff_batch.T4 | ✓ | Done move call 256; handoff naming T4 in call 256 |
| adh.handoff_batch.T5 | ✓ | Done move call 256; handoff naming T5 in call 256 |
| adh.handoff_batch.T6 | ✓ | Done move call 302; handoff naming T6 in call 302 |
| adh.handoff_batch.T7 | ✓ | Done move call 302; handoff naming T7 in call 302 |
| adh.handoff_batch.T8 | ✓ | Done move call 366; handoff naming T8 in call 366 |
| adh.handoff_batch.T9 | ✓ | Done move call 421; handoff naming T9 in call 421 |
| adh.handoff_batch.T10 | ✓ | Done move call 421; handoff naming T10 in call 421 |
| adh.notes.T1 | ✓ | T1-project-skeleton.notes.md |
| adh.notes.T2 | ✓ | T2-shared-csv-reader.notes.md |
| adh.notes.T3 | ✓ | T3-money-and-table-helpers.notes.md |
| adh.notes.T4 | ✓ | T4-transaction-parsing.notes.md |
| adh.notes.T5 | ✓ | T5-rules-parsing-and-matching.notes.md |
| adh.notes.T6 | ✓ | T6-dedupe-and-month-filter.notes.md |
| adh.notes.T7 | ✓ | T7-aggregation-and-renderers.notes.md |
| adh.notes.T8 | ✓ | T8-cli-wiring.notes.md |
| adh.notes.T9 | ✓ | T9-oracle-and-acceptance-tests.notes.md |
| adh.notes.T10 | ✓ | T10-error-and-edge-case-tests.notes.md |
| adh.task_review.T1 | ✓ | call 111 'Review T1' (description) not PASS; call 176 'Phase 1 review' (prompt) PASS |
| adh.task_review.T2 | ✓ | call 140 'Review T2' (description) PASS; call 176 'Phase 1 review' (prompt) PASS |
| adh.task_review.T3 | ✓ | call 166 'Review T3' (description) PASS; call 176 'Phase 1 review' (prompt) PASS |
| adh.task_review.T4 | ✓ | call 176 'Phase 1 review' (prompt) PASS; call 224 'Review T4' (description) PASS; call 303 'Phase 2 review' (prompt) PASS |
| adh.task_review.T5 | ✓ | call 176 'Phase 1 review' (prompt) PASS; call 225 'Review T5' (description) not PASS; call 250 'Re-review T5 fix' (description) PASS; call 303 'Phase  |
| adh.task_review.T6 | ✓ | call 176 'Phase 1 review' (prompt) PASS; call 283 'Review T6' (description) PASS; call 303 'Phase 2 review' (prompt) PASS |
| adh.task_review.T7 | ✓ | call 176 'Phase 1 review' (prompt) PASS; call 284 'Review T7' (description) PASS; call 303 'Phase 2 review' (prompt) PASS |
| adh.task_review.T8 | ✓ | call 303 'Phase 2 review' (prompt) PASS; call 346 'Review T8' (description) PASS; call 367 'Phase 3 review' (prompt) PASS |
| adh.task_review.T9 | ✓ | call 408 'Review T9' (description) PASS; call 422 'Phase 4 review' (prompt) PASS |
| adh.task_review.T10 | ✓ | call 409 'Review T10' (description) PASS; call 422 'Phase 4 review' (prompt) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2', 'T3']: reviewer call 176; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T4', 'T5', 'T6', 'T7']: reviewer call 176; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T8']: reviewer call 303; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P4 | ✓ | phase P4 ['T9', 'T10']: reviewer call 422; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✓ | Done call 127; last code edit None; check-dod runs [(127, True)] |
| adh.gates_before_done.T2 | ✓ | Done call 147; last code edit 137; check-dod runs [(147, True)] |
| adh.gates_before_done.T3 | ✓ | Done call 175; last code edit 163; check-dod runs [(175, True)] |
| adh.gates_before_done.T4 | ✓ | Done call 256; last code edit 221; check-dod runs [(256, True)] |
| adh.gates_before_done.T5 | ✓ | Done call 256; last code edit 248; check-dod runs [(256, True)] |
| adh.gates_before_done.T6 | ✓ | Done call 302; last code edit 276; check-dod runs [(256, None), (302, True)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T7 | ✓ | Done call 302; last code edit 279; check-dod runs [(256, None), (302, True)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T8 | ✓ | Done call 366; last code edit 364; check-dod runs [(366, True)] |
| adh.gates_before_done.T9 | ✓ | Done call 421; last code edit 405; check-dod runs [(421, True)] |
| adh.gates_before_done.T10 | ✓ | Done call 421; last code edit 402; check-dod runs [(421, True)] |
| adh.kanban_after_moves | ✗ | 20 lane-move calls; without validate-kanban: [128, 139, 165, 223, 282, 345, 407] |
| adh.commit_msg.e121079 | ✓ | feat(foundations): add package skeleton, error type and test: OK: commit message valid. |
| adh.commit_msg.fecf7a2 | ✓ | feat(foundations): add shared CSV reader with header and row: OK: commit message valid. |
| adh.commit_msg.7766445 | ✓ | feat(foundations): add exact money handling and table render: OK: commit message valid. |
| adh.commit_msg.9612aad | ✓ | docs(foundations): record phase 1 notes, kanban and handoff: OK: commit message valid. |
| adh.commit_msg.5cc9d82 | ✓ | feat(domain): add transaction file parsing and validation: OK: commit message valid. |
| adh.commit_msg.73f846f | ✓ | feat(domain): add rules parsing and category matching: OK: commit message valid. |
| adh.commit_msg.993c9a9 | ✓ | feat(domain): add duplicate removal and month filter: OK: commit message valid. |
| adh.commit_msg.03fb2f0 | ✓ | feat(domain): add aggregation and report/categorize renderer: OK: commit message valid. |
| adh.commit_msg.fae8e42 | ✓ | docs(domain): record phase 2 notes, kanban and handoff: OK: commit message valid. |
| adh.commit_msg.7d74686 | ✓ | feat(cli): wire argparse CLI, orchestration, streams and exi: OK: commit message valid. |
| adh.commit_msg.4508bd7 | ✓ | docs(cli): record phase 3 notes, kanban and handoff: OK: commit message valid. |
| adh.commit_msg.44184c9 | ✓ | test(verification): add byte-exact oracle and acceptance tes: OK: commit message valid. |
| adh.commit_msg.9a72886 | ✓ | test(verification): add error-table and edge-case end-to-end: OK: commit message valid. |
| adh.commit_msg.a33a962 | ✓ | docs(verification): record phase 4 notes, kanban and run sum: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 10176fa..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs |
| adh.one_concern_per_commit | ✓ | manual: one commit per task plus one docs commit per phase; 7d74686 carries T8's own review follow-up in rules.py |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: 4/4 phase verdicts from code-reviewer subagents, no orchestrator code edits (D87), 232 passed, impl-review PASS: all match the records |
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
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | max 2 concurrent coders; justification: max 2 concurrent coders; T4/T5, T6/T7, T9/T10 notes record no dependency and dis |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✓ | failing: none |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 14 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: per-task feat/test commits and a docs commit per phase |
| dp14 | Handoff at each Done move (D82) | 1 | ✓ | failing: none |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [109]) | 1.00 | 0.5 | 469 | 0.63 | 1 | 77.6 | 65 | 0.049 |
| T2 | 1 (calls [138]) | 1.00 | 1.0 | 102 | 0.92 | 1 | 98.4 | 156 | 0.070 |
| T3 | 2 (calls [162, 164]) | 0.75 | 1.0 | 151 | 0.88 | 1 | 87.6 | 193 | 0.112 |
| T4 | 2 (calls [220, 222]) | 0.75 | 1.0 | 73 | 0.94 | 1 | 88.8 | 144 | 0.100 |
| T5 | 2 (calls [219, 249]) | 0.75 | 1.0 | 179 | 0.86 | 1 | 87.2 | 221 | 0.118 |
| T6 | 1 (calls [277]) | 1.00 | 1.0 | 45 | 0.96 | 1 | 99.3 | 90 | 0.054 |
| T7 | 2 (calls [280, 281]) | 0.75 | 1.0 | 93 | 0.93 | 1 | 88.5 | 264 | 0.129 |
| T8 | 2 (calls [342, 344]) | 0.75 | 1.0 | 113 | 0.91 | 1 | 88.2 | 264 | 0.129 |
| T9 | 1 (calls [399]) | 1.00 | 1.0 | 227 | 0.82 | 1 | 96.4 | 291 | 0.102 |
| T10 | 1 (calls [403]) | 1.00 | 1.0 | 239 | 0.81 | 1 | 96.2 | 444 | 0.137 |
