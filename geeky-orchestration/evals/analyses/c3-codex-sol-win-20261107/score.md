# Score: 20261107T150925Z-9e506686 (c3-minisql)

Plugin `6567fa3`, codex / chatgpt/gpt-6.1-sol. Scored 2026-11-07T17:24:30Z by `score-run.py`. Workspace: given. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 89.1 | P 1.000, S 0.271, D 1.00 |
| Adherence | 0.35 | 73.6 | 39/53 |
| Consistency | 0.20 | 77.1 | DPC 15/21 = 0.714, OC 1.00 |
| Task tier | 0.10 | 36.4 | L_run None ms, L_ref 2678 ms |
| **Composite** | | **76.0** | |

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
| adh.planning_folder | ✓ | OK: planning folder valid. 6 task file(s) found. |
| adh.task_schema | ✓ | OK: 6 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 6 task(s) tracked, 6 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=6 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.dod.T4 | ✓ | DOD_OK: T4 |
| adh.dod.T5 | ✓ | DOD_OK: T5 |
| adh.dod.T6 | ✓ | DOD_OK: T6 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T4 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T5 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T6 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✓ | T1-language-foundation.notes.md |
| adh.notes.T2 | ✓ | T2-csv-data.notes.md |
| adh.notes.T3 | ✓ | T3-result-formatting.notes.md |
| adh.notes.T4 | ✓ | T4-semantic-analysis.notes.md |
| adh.notes.T5 | ✓ | T5-ordered-executor.notes.md |
| adh.notes.T6 | ✓ | T6-api-cli-acceptance.notes.md |
| adh.task_review.T1 | ✓ | call 162 'review_phase1' (prompt) PASS; call 290 'review_phase2' (prompt) not PASS |
| adh.task_review.T2 | ✓ | call 290 'review_phase2' (prompt) not PASS; call 328 'review_phase2_recovery' (prompt) PASS |
| adh.task_review.T3 | ✓ | call 290 'review_phase2' (prompt) not PASS; call 328 'review_phase2_recovery' (prompt) PASS |
| adh.task_review.T4 | ✓ | call 409 'review_phase3' (prompt) PASS; call 523 'review_phase4' (prompt) PASS |
| adh.task_review.T5 | ✓ | call 523 'review_phase4' (prompt) PASS; call 626 'review_phase5' (prompt) PASS |
| adh.task_review.T6 | ✓ | call 523 'review_phase4' (prompt) PASS; call 626 'review_phase5' (prompt) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1']: reviewer call 162; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T2', 'T3']: reviewer call 328; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T4']: reviewer call 409; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P4 | ✓ | phase P4 ['T5']: reviewer call 523; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P5 | ✓ | phase P5 ['T6']: reviewer call 523; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [(202, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [(347, True)] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [(347, True)] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [(433, True), (456, True)] |
| adh.gates_before_done.T5 | ✗ | Done call -; last code edit None; check-dod runs [(567, True)] |
| adh.gates_before_done.T6 | ✗ | Done call -; last code edit None; check-dod runs [(648, True)] |
| adh.kanban_after_moves | ✗ | 0 lane-move calls; without validate-kanban: none |
| adh.commit_msg.ad0fa64 | ✓ | feat(language): implement source-aware SQL foundation: OK: commit message valid. |
| adh.commit_msg.89f5123 | ✓ | feat(csv): load and render typed CSV data deterministically: OK: commit message valid. |
| adh.commit_msg.b7e4438 | ✓ | feat(semantic): bind and validate typed query plans: OK: commit message valid. |
| adh.commit_msg.9b67158 | ✓ | feat(execution): evaluate typed queries in contract order: OK: commit message valid. |
| adh.commit_msg.0452c3a | ✓ | feat(interface): expose API and deterministic CLI and REPL: OK: commit message valid. |
| adh.prescribed_msg.spec | ✗ | docs(spec): author minisql feature specification |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 54d23ec..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs |
| adh.one_concern_per_commit | ✓ | manual: One feat commit per phase (P2 commit covers T2+T3 as one phase), then docs(review) and docs(workflow) heartbeat; no mixed concerns. |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: Run Summary claims 1328 passed/1 skipped; operator rerun at f5d6602 gives 1328 passed, 1 skipped. DoD-before-Done and kanban-after-move claims |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✗ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: T2/T3 spawned together (2 concurrent, cap 3); justification at handoff.md:113 (no mutual dependencies,  |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 5 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: Five phase commits, each one phase's concern. |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 996 | 0.203 |
| T2 | 0 (calls []) | 0.00 | 0.5 | - | 0.00 | 1 | 25.0 | 379 | 0.129 |
| T3 | 0 (calls []) | 0.00 | 0.5 | - | 0.00 | 1 | 25.0 | 216 | 0.109 |
| T4 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 814 | 0.181 |
| T5 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 783 | 0.177 |
| T6 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 988 | 0.202 |
