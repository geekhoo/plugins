# Score: 20261023T062603Z (c1-csvledger)

Plugin `fd67ca3`, claude-code / claude-sonnet-5-5. Scored 2026-10-23T07:14:54Z by `score-run.py`. Workspace: run.json workspace. Validation blocks re-run. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 96.3 | P 1.000, S 0.756, D 1.00 |
| Adherence | 0.35 | 95.7 | 66/69 |
| Consistency | 0.20 | 88.6 | DPC 18/21 = 0.857, OC 1.00 |
| Task tier | 0.10 | 89.1 | L_run 2337 ms, L_ref 2678 ms |
| **Composite** | | **93.8** | |

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
| adh.handoff_batch.T1 | ✓ | Done move call 133; handoff naming T1 in call 133 |
| adh.handoff_batch.T2 | ✓ | Done move call 133; handoff naming T2 in call 133 |
| adh.handoff_batch.T3 | ✓ | Done move call 174; handoff naming T3 in call 174 |
| adh.handoff_batch.T4 | ✓ | Done move call 174; handoff naming T4 in call 174 |
| adh.handoff_batch.T5 | ✓ | Done move call 228; handoff naming T5 in call 228 |
| adh.handoff_batch.T6 | ✓ | Done move call 228; handoff naming T6 in call 228 |
| adh.handoff_batch.T7 | ✓ | Done move call 272; handoff naming T7 in call 272 |
| adh.handoff_batch.T8 | ✓ | Done move call 272; handoff naming T8 in call 272 |
| adh.notes.T1 | ✓ | T1-scaffold-errors-money.notes.md |
| adh.notes.T2 | ✓ | T2-csv-loader.notes.md |
| adh.notes.T3 | ✓ | T3-parse-transactions-rules.notes.md |
| adh.notes.T4 | ✓ | T4-dedup-aggregate.notes.md |
| adh.notes.T5 | ✓ | T5-render.notes.md |
| adh.notes.T6 | ✓ | T6-cli-main.notes.md |
| adh.notes.T7 | ✓ | T7-acceptance-tests.notes.md |
| adh.notes.T8 | ✓ | T8-edge-case-tests.notes.md |
| adh.task_review.T1 | ✓ | call 121 'Phase 1 review' (prompt) PASS |
| adh.task_review.T2 | ✓ | call 121 'Phase 1 review' (prompt) PASS |
| adh.task_review.T3 | ✓ | call 160 'Phase 2 review' (prompt) PASS |
| adh.task_review.T4 | ✓ | call 160 'Phase 2 review' (prompt) PASS |
| adh.task_review.T5 | ✓ | call 210 'Phase 3 review' (prompt) PASS |
| adh.task_review.T6 | ✓ | call 210 'Phase 3 review' (prompt) PASS |
| adh.task_review.T7 | ✓ | call 260 'Phase 4 review' (prompt) PASS |
| adh.task_review.T8 | ✓ | call 260 'Phase 4 review' (prompt) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2']: reviewer call 121; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T3', 'T4']: reviewer call 160; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T5', 'T6']: reviewer call 210; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P4 | ✓ | phase P4 ['T7', 'T8']: reviewer call 260; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call 133; last code edit 104; check-dod runs [(133, False), (134, True)] |
| adh.gates_before_done.T2 | ✗ | Done call 133; last code edit 118; check-dod runs [(133, False), (134, True)] |
| adh.gates_before_done.T3 | ✓ | Done call 174; last code edit 145; check-dod runs [(134, None), (174, True)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T4 | ✓ | Done call 174; last code edit 156; check-dod runs [(174, True)] |
| adh.gates_before_done.T5 | ✓ | Done call 228; last code edit 189; check-dod runs [(174, None), (228, True)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T6 | ✓ | Done call 228; last code edit 206; check-dod runs [(228, True)] |
| adh.gates_before_done.T7 | ✓ | Done call 272; last code edit 237; check-dod runs [(228, None), (272, True)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T8 | ✓ | Done call 272; last code edit 256; check-dod runs [(272, True)] |
| adh.kanban_after_moves | ✓ | 14 lane-move calls; without validate-kanban: none |
| adh.commit_msg.3750aea | ✓ | feat(foundations): add package scaffold, errors and money fo: OK: commit message valid. |
| adh.commit_msg.3428326 | ✓ | feat(foundations): add shared CSV loader with header validat: OK: commit message valid. |
| adh.commit_msg.c5ceb7d | ✓ | chore(foundations): update kanban, handoff and task notes: OK: commit message valid. |
| adh.commit_msg.ec41062 | ✗ | feat(parsing): add transaction and rules parsing with catego: INVALID_COMMIT_MESSAGE: |
| adh.commit_msg.54fbadf | ✓ | feat(parsing): add deduplication and monthly aggregation: OK: commit message valid. |
| adh.commit_msg.5f9e103 | ✓ | chore(parsing): update kanban, handoff and task notes: OK: commit message valid. |
| adh.commit_msg.434f64d | ✓ | feat(output): add table and JSON rendering: OK: commit message valid. |
| adh.commit_msg.661fbb6 | ✓ | feat(cli): add argparse CLI, entry point and error mapping: OK: commit message valid. |
| adh.commit_msg.d6b1cad | ✓ | chore(cli): update kanban, handoff and task notes: OK: commit message valid. |
| adh.commit_msg.0576778 | ✓ | test(acceptance): add oracle and AC1-AC10 acceptance tests: OK: commit message valid. |
| adh.commit_msg.5cfc3f2 | ✓ | test(acceptance): add edge-case and error-table tests: OK: commit message valid. |
| adh.commit_msg.815f724 | ✓ | chore(acceptance): update kanban, handoff and task notes: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing; chore(plan): fix kanban lane references |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 289891b..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✓ | manual: per-task feat/test commits plus one chore commit per phase; 289891b only fixes kanban lane references |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: 8/8 Done, 4 phase reviews with READY TO ADVANCE, impl-review PASS, 227 tests (re-run: 227 passed); the 73-char commit subject is disclosed |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✗ | 1 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | max 0 concurrent coders; justification: coders ran one at a time; no parallel batch needed justifying |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 12 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: per-task commits and one docs commit per phase |
| dp14 | Handoff at each Done move (D82) | 1 | ✓ | failing: none |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [105]) | 1.00 | 1.0 | 181 | 0.83 | 1 | 96.5 | 78 | 0.059 |
| T2 | 2 (calls [116, 119]) | 0.75 | 1.0 | 58 | 0.94 | 1 | 88.9 | 163 | 0.119 |
| T3 | 1 (calls [146]) | 1.00 | 1.0 | 140 | 0.87 | 1 | 97.3 | 322 | 0.122 |
| T4 | 1 (calls [157]) | 1.00 | 1.0 | 53 | 0.95 | 1 | 99.0 | 182 | 0.086 |
| T5 | 3 (calls [185, 188, 191]) | 0.50 | 1.0 | 205 | 0.80 | 1 | 76.1 | 211 | 0.170 |
| T6 | 1 (calls [207]) | 1.00 | 1.0 | 73 | 0.93 | 1 | 98.6 | 299 | 0.116 |
| T7 | 2 (calls [235, 238]) | 0.75 | 1.0 | 394 | 0.62 | 1 | 82.5 | 230 | 0.137 |
| T8 | 2 (calls [254, 257]) | 0.75 | 1.0 | 103 | 0.90 | 1 | 88.0 | 436 | 0.190 |
