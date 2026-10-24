# Score: 20261020T114232Z (c1-csvledger)

Plugin `24c4e6d`, claude-code / claude-sonnet-5-5. Scored 2026-10-23T21:29:58Z by `score-run.py`. Workspace: given. Validation blocks trace only. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 97.9 | P 1.000, S 0.860, D 1.00 |
| Adherence | 0.35 | 68.3 | 43/63 |
| Consistency | 0.20 | 65.7 | DPC 12/21 = 0.571, OC 1.00 |
| Task tier | 0.10 | 58.9 | L_run 2714 ms, L_ref 2678 ms |
| **Composite** | | **77.2** | |

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
| adh.handoff_batch.T1 | ✗ | Done move call 149; no handoff.md write naming T1 in calls 149/150 |
| adh.handoff_batch.T2 | ✗ | Done move call 160; no handoff.md write naming T2 in calls 160/161 |
| adh.handoff_batch.T3 | ✗ | Done move call 186; no handoff.md write naming T3 in calls 186/187 |
| adh.handoff_batch.T4 | ✗ | Done move call 186; no handoff.md write naming T4 in calls 186/187 |
| adh.handoff_batch.T5 | ✗ | Done move call 204; no handoff.md write naming T5 in calls 204/205 |
| adh.handoff_batch.T6 | ✗ | Done move call 219; no handoff.md write naming T6 in calls 219/220 |
| adh.handoff_batch.T7 | ✓ | Done move call 233; handoff naming T7 in call 233 |
| adh.notes.T1 | ✓ | T1-scaffold-and-errors.notes.md |
| adh.notes.T2 | ✓ | T2-csv-reader.notes.md |
| adh.notes.T3 | ✓ | T3-transactions-and-dedup.notes.md |
| adh.notes.T4 | ✓ | T4-rules-engine.notes.md |
| adh.notes.T5 | ✓ | T5-money-report-render.notes.md |
| adh.notes.T6 | ✓ | T6-cli-entrypoint.notes.md |
| adh.notes.T7 | ✓ | T7-acceptance-tests.notes.md |
| adh.task_review.T1 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T2 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T3 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T4 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T5 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T6 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T7 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.phase_verdict.P1 | ✗ | phase P1 ['T1', 'T2']: reviewer none; READY TO ADVANCE recorded: no |
| adh.phase_verdict.P2 | ✗ | phase P2 ['T3', 'T4']: reviewer none; READY TO ADVANCE recorded: no |
| adh.phase_verdict.P3 | ✗ | phase P3 ['T5', 'T6']: reviewer none; READY TO ADVANCE recorded: T6-cli-entrypoint.notes.md |
| adh.phase_verdict.P4 | ✗ | phase P4 ['T7']: reviewer none; READY TO ADVANCE recorded: no |
| adh.gates_before_done.T1 | ✓ | Done call 149; last code edit None; check-dod runs [(149, True)] |
| adh.gates_before_done.T2 | ✗ | Done call 160; last code edit 156; check-dod runs [(186, True)] |
| adh.gates_before_done.T3 | ✓ | Done call 186; last code edit 176; check-dod runs [(186, True)] |
| adh.gates_before_done.T4 | ✓ | Done call 186; last code edit 183; check-dod runs [(186, True)] |
| adh.gates_before_done.T5 | ✓ | Done call 204; last code edit 203; check-dod runs [(204, True)] |
| adh.gates_before_done.T6 | ✓ | Done call 219; last code edit 216; check-dod runs [(219, True)] |
| adh.gates_before_done.T7 | ✓ | Done call 233; last code edit 232; check-dod runs [(233, True)] |
| adh.kanban_after_moves | ✓ | 7 lane-move calls; without validate-kanban: none |
| adh.commit_msg.75d9b91 | ✓ | feat(foundation): scaffold package, errors and test harness: OK: commit message valid. |
| adh.commit_msg.08ffcab | ✓ | feat(foundation): add shared CSV table reader: OK: commit message valid. |
| adh.commit_msg.c9d0d39 | ✓ | feat(domain): parse transactions and deduplicate: OK: commit message valid. |
| adh.commit_msg.2466a9d | ✓ | feat(domain): load rules and categorize: OK: commit message valid. |
| adh.commit_msg.f7f1767 | ✓ | chore(implement): record phase 1-2 progress in kanban and no: OK: commit message valid. |
| adh.commit_msg.8886c56 | ✓ | feat(output): add aggregation and table/JSON rendering: OK: commit message valid. |
| adh.commit_msg.453d390 | ✓ | chore(implement): record T5 progress: OK: commit message valid. |
| adh.commit_msg.abdae5a | ✓ | feat(cli): add argparse CLI and orchestration: OK: commit message valid. |
| adh.commit_msg.3aa53ac | ✓ | chore(implement): record T6 progress: OK: commit message valid. |
| adh.commit_msg.d46b1ca | ✓ | test(acceptance): add end-to-end acceptance and error-matrix: OK: commit message valid. |
| adh.commit_msg.29e8096 | ✓ | chore(implement): complete run, update kanban and handoff: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff f9b0a05..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs |
| adh.one_concern_per_commit | ✓ | manual: comparison-20261022T0800Z: one concern per commit 1/1 |
| adh.no_orchestrator_code_edits | ✗ | call 203 (geeky-implement): csvledger/report.py |
| adh.final_report_claims | ✓ | manual: comparison-20261021T0530Z: final report claims verified 1/1; 0800Z: no false process claim |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✗ | no Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | max 2 concurrent coders; justification: DP7 batching justification noted (doc: pass) |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✗ | not reviewed: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'] |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T2'] |
| dp11 | Phase verdict from a phase review | 2 | ✗ | failing phases: ['P1', 'P2', 'P3', 'P4'] |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 187: 1 check-commit run(s) for 5 commit(s); call 205: 0 check-commit run(s) for 2 commit(s); call 219: 0 check-comm |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: DP13 one concern per commit per phase (doc: pass) |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp15 | Run Summary appended | 1 | ✗ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [147]) | 1.00 | 0.0 | 270 | 0.78 | 1 | 65.6 | 67 | 0.066 |
| T2 | 1 (calls [158]) | 1.00 | 0.0 | 64 | 0.95 | 1 | 69.0 | 166 | 0.095 |
| T3 | 1 (calls [177]) | 1.00 | 0.0 | 49 | 0.96 | 1 | 69.2 | 171 | 0.097 |
| T4 | 1 (calls [184]) | 1.00 | 0.0 | 110 | 0.91 | 1 | 68.2 | 166 | 0.095 |
| T5 | 3 (calls [197, 201] + D87 [203]) | 0.50 | 0.0 | 102 | 0.92 | 1 | 48.3 | 304 | 0.228 |
| T6 | 2 (calls [214, 217]) | 0.75 | 0.0 | 105 | 0.91 | 1 | 58.3 | 243 | 0.164 |
| T7 | 2 (calls [231, 232]) | 0.75 | 0.0 | 241 | 0.80 | 1 | 56.0 | 543 | 0.254 |
