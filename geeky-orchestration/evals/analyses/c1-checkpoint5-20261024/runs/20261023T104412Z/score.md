# Score: 20261023T104412Z (c1-csvledger)

Plugin `8ea2ccc`, claude-code / claude-sonnet-5-5. Scored 2026-10-23T21:34:46Z by `score-run.py`. Workspace: given. Validation blocks trace only. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 98.6 | P 1.000, S 0.906, D 1.00 |
| Adherence | 0.35 | 100.0 | 63/63 |
| Consistency | 0.20 | 100.0 | DPC 21/21 = 1.000, OC 1.00 |
| Task tier | 0.10 | 87.6 | L_run 2128 ms, L_ref 2678 ms |
| **Composite** | | **98.3** | |

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
| adh.planning_folder | ✓ | OK: planning folder valid. 7 task file(s) found. |
| adh.task_schema | ✓ | OK: 7 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 7 task(s) tracked, 7 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=7 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.dod.T4 | ✓ | DOD_OK: T4 |
| adh.dod.T5 | ✓ | DOD_OK: T5 |
| adh.dod.T6 | ✓ | DOD_OK: T6 |
| adh.dod.T7 | ✓ | DOD_OK: T7 |
| adh.handoff_batch.T1 | ✓ | Done move call 169; handoff naming T1 in call 169 |
| adh.handoff_batch.T2 | ✓ | Done move call 169; handoff naming T2 in call 169 |
| adh.handoff_batch.T3 | ✓ | Done move call 195; handoff naming T3 in call 195 |
| adh.handoff_batch.T4 | ✓ | Done move call 195; handoff naming T4 in call 195 |
| adh.handoff_batch.T5 | ✓ | Done move call 238; handoff naming T5 in call 238 |
| adh.handoff_batch.T6 | ✓ | Done move call 238; handoff naming T6 in call 238 |
| adh.handoff_batch.T7 | ✓ | Done move call 263; handoff naming T7 in call 263 |
| adh.notes.T1 | ✓ | T1-skeleton-errors-money.notes.md |
| adh.notes.T2 | ✓ | T2-csv-reader.notes.md |
| adh.notes.T3 | ✓ | T3-transactions-rules.notes.md |
| adh.notes.T4 | ✓ | T4-dedupe-aggregate.notes.md |
| adh.notes.T5 | ✓ | T5-render.notes.md |
| adh.notes.T6 | ✓ | T6-cli.notes.md |
| adh.notes.T7 | ✓ | T7-e2e-tests.notes.md |
| adh.task_review.T1 | ✓ | call 155 'Phase 1 review T1,T2' (description) PASS |
| adh.task_review.T2 | ✓ | call 155 'Phase 1 review T1,T2' (description) PASS |
| adh.task_review.T3 | ✓ | call 184 'Phase 2 review T3,T4' (description) PASS |
| adh.task_review.T4 | ✓ | call 184 'Phase 2 review T3,T4' (description) PASS |
| adh.task_review.T5 | ✓ | call 228 'Phase 3 review T5,T6' (description) PASS |
| adh.task_review.T6 | ✓ | call 228 'Phase 3 review T5,T6' (description) PASS |
| adh.task_review.T7 | ✓ | call 253 'Phase 4 review T7' (description) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2']: reviewer call 155; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T3', 'T4']: reviewer call 184; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T5', 'T6']: reviewer call 228; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P4 | ✓ | phase P4 ['T7']: reviewer call 253; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✓ | Done call 169; last code edit 121; check-dod runs [(167, False), (169, True)] |
| adh.gates_before_done.T2 | ✓ | Done call 169; last code edit 137; check-dod runs [(169, True)] |
| adh.gates_before_done.T3 | ✓ | Done call 195; last code edit 151; check-dod runs [(195, True)] |
| adh.gates_before_done.T4 | ✓ | Done call 195; last code edit 180; check-dod runs [(195, True)] |
| adh.gates_before_done.T5 | ✓ | Done call 238; last code edit 209; check-dod runs [(238, True)] |
| adh.gates_before_done.T6 | ✓ | Done call 238; last code edit 224; check-dod runs [(238, True)] |
| adh.gates_before_done.T7 | ✓ | Done call 263; last code edit 249; check-dod runs [(263, True)] |
| adh.kanban_after_moves | ✓ | 15 lane-move calls; without validate-kanban: none |
| adh.commit_msg.72d2635 | ✓ | feat(foundations): add package skeleton, errors, money, repo: OK: commit message valid. |
| adh.commit_msg.c4109a9 | ✓ | feat(foundations): add shared CSV reader with header and row: OK: commit message valid. |
| adh.commit_msg.fae1499 | ✓ | feat(foundations): record phase 1 kanban, handoff and task n: OK: commit message valid. |
| adh.commit_msg.baa18f3 | ✓ | feat(domain): add transaction and rules loading with matchin: OK: commit message valid. |
| adh.commit_msg.bcf32ed | ✓ | feat(domain): add dedupe, month filter and aggregation: OK: commit message valid. |
| adh.commit_msg.9f0fe40 | ✓ | feat(domain): record phase 2 kanban, handoff and task notes: OK: commit message valid. |
| adh.commit_msg.88abead | ✓ | feat(interface): add table and JSON renderers: OK: commit message valid. |
| adh.commit_msg.dcefa5d | ✓ | feat(interface): add argparse CLI, stream setup and error ha: OK: commit message valid. |
| adh.commit_msg.e90df18 | ✓ | feat(interface): record phase 3 kanban, handoff and task not: OK: commit message valid. |
| adh.commit_msg.7788ee6 | ✓ | feat(verification): add end-to-end oracle and error test sui: OK: commit message valid. |
| adh.commit_msg.599bc8c | ✓ | feat(verification): record phase 4 kanban, handoff and run s: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 52541a9..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs |
| adh.one_concern_per_commit | ✓ | manual: one feat commit per task and one record commit per phase; the record commits are typed feat instead of docs, but each holds one concern |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: T1-T7 Done, 271 passed (re-run: 271 passed), 4 phase verdicts READY TO ADVANCE with reviewer IDs that match subagent transcripts, impl-review  |
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
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | max 1 concurrent coders; justification: coders ran one at a time inside the geeky-implement-orchestrator subagent; no pa |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✓ | failing: none |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 11 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: per-task commits and one record commit per phase |
| dp14 | Handoff at each Done move (D82) | 1 | ✓ | failing: none |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [122]) | 1.00 | 1.0 | 395 | 0.59 | 1 | 91.7 | 66 | 0.070 |
| T2 | 2 (calls [136, 138]) | 0.75 | 1.0 | 262 | 0.73 | 1 | 84.5 | 158 | 0.148 |
| T3 | 1 (calls [152]) | 1.00 | 1.0 | 365 | 0.62 | 1 | 92.3 | 249 | 0.126 |
| T4 | 1 (calls [181]) | 1.00 | 1.0 | 118 | 0.88 | 1 | 97.5 | 142 | 0.093 |
| T5 | 2 (calls [208, 210]) | 0.75 | 1.0 | 252 | 0.74 | 1 | 84.7 | 187 | 0.157 |
| T6 | 1 (calls [225]) | 1.00 | 1.0 | 132 | 0.86 | 1 | 97.2 | 145 | 0.094 |
| T7 | 2 (calls [248, 251]) | 0.75 | 1.0 | 386 | 0.59 | 1 | 81.9 | 692 | 0.311 |
