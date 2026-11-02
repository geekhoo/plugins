# Score: 20261101T192141Z (c2-linkvault)

Plugin `44d6afb`, claude-code / claude-sonnet-5-5. Scored 2026-11-02T00:06:13Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 91.8 | P 1.000, S 0.455, D 1.00 |
| Adherence | 0.35 | 73.2 | 52/71 |
| Consistency | 0.20 | 81.0 | DPC 16/21 = 0.762, OC 1.00 |
| Task tier | 0.10 | 82.6 | L_run 5604 ms, L_ref 2678 ms |
| **Composite** | | **82.2** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: 3/3 blind judges: no false completion claim. Kanban Done=9 at HEAD f966dc0 with a clean tree; every reported commit SHA exists; suite re-run at 371b36b; oracle 136 passed (oracle-output.txt); AC1-AC12 each have a test. The report discloses the unrun-on-3.11+/Windows limits, the bundled T8/T9 commit and carried-forward warnings. | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 9 task file(s) found. |
| adh.task_schema | ✓ | OK: 9 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 9 task(s) tracked, 9 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=9 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.dod.T4 | ✓ | DOD_OK: T4 |
| adh.dod.T5 | ✓ | DOD_OK: T5 |
| adh.dod.T6 | ✓ | DOD_OK: T6 |
| adh.dod.T7 | ✓ | DOD_OK: T7 |
| adh.dod.T8 | ✓ | DOD_OK: T8 |
| adh.dod.T9 | ✓ | DOD_OK: T9 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T4 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T5 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T6 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T7 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T8 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T9 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✓ | T1-package-skeleton-clock.notes.md |
| adh.notes.T2 | ✓ | T2-sqlite-store.notes.md |
| adh.notes.T3 | ✓ | T3-validators.notes.md |
| adh.notes.T4 | ✓ | T4-http-core-admin-routes.notes.md |
| adh.notes.T5 | ✓ | T5-link-endpoints.notes.md |
| adh.notes.T6 | ✓ | T6-serve-command-shutdown.notes.md |
| adh.notes.T7 | ✓ | T7-cli-client.notes.md |
| adh.notes.T8 | ✓ | T8-acceptance-suite.notes.md |
| adh.notes.T9 | ✓ | T9-final-verification-docs.notes.md |
| adh.task_review.T1 | ✓ | call 204 'Phase 1 review T1-T3' (description) PASS |
| adh.task_review.T2 | ✓ | call 204 'Phase 1 review T1-T3' (description) PASS |
| adh.task_review.T3 | ✓ | call 204 'Phase 1 review T1-T3' (description) PASS |
| adh.task_review.T4 | ✓ | call 289 'Phase 2 review T4-T6' (description) PASS |
| adh.task_review.T5 | ✓ | call 289 'Phase 2 review T4-T6' (description) PASS |
| adh.task_review.T6 | ✓ | call 289 'Phase 2 review T4-T6' (description) PASS |
| adh.task_review.T7 | ✓ | call 368 'Phase 3 review T7-T9' (description) PASS |
| adh.task_review.T8 | ✓ | call 368 'Phase 3 review T7-T9' (description) PASS |
| adh.task_review.T9 | ✓ | call 368 'Phase 3 review T7-T9' (description) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2', 'T3']: reviewer call 204; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T4', 'T5', 'T6']: reviewer call 289; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T7', 'T8', 'T9']: reviewer call 368; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [(223, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [(223, True)] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [(223, True)] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [(315, True)] |
| adh.gates_before_done.T5 | ✗ | Done call -; last code edit None; check-dod runs [(315, True)] |
| adh.gates_before_done.T6 | ✗ | Done call -; last code edit None; check-dod runs [(315, True)] |
| adh.gates_before_done.T7 | ✗ | Done call -; last code edit None; check-dod runs [(391, True)] |
| adh.gates_before_done.T8 | ✗ | Done call -; last code edit None; check-dod runs [(391, True)] |
| adh.gates_before_done.T9 | ✗ | Done call -; last code edit None; check-dod runs [(391, True)] |
| adh.kanban_after_moves | ✓ | 17 lane-move calls; without validate-kanban: none |
| adh.commit_msg.890f6b5 | ✓ | feat(foundation): add package skeleton and strict clock: OK: commit message valid. |
| adh.commit_msg.a85ef94 | ✓ | feat(foundation): add sqlite store with exact schema and ato: OK: commit message valid. |
| adh.commit_msg.4083fae | ✓ | feat(foundation): add slug, URL and request-body validators: OK: commit message valid. |
| adh.commit_msg.dfb3723 | ✓ | chore(kanban): record Phase 1 completion: OK: commit message valid. |
| adh.commit_msg.a1e6c93 | ✓ | feat(server): add HTTP pipeline, auth, rate limiter and link: OK: commit message valid. |
| adh.commit_msg.9f84c1a | ✓ | feat(server): add serve command, ready line, exit codes, shu: OK: commit message valid. |
| adh.commit_msg.8825fe6 | ✓ | chore(kanban): record Phase 2 completion: OK: commit message valid. |
| adh.commit_msg.8f6a24a | ✓ | feat(client): add CLI client commands, option fallbacks, exi: OK: commit message valid. |
| adh.commit_msg.92e1ee3 | ✓ | docs: add README usage notes and stdlib/stdout hygiene tests: OK: commit message valid. |
| adh.commit_msg.371b36b | ✓ | chore(kanban): record Phase 3 completion and run summary: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in docs/spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 4efada4..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✗ | manual: as a.one_concern_per_commit |
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
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 3 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: 3/3 blind judges: of 9 geeky-coder dispatches only T2 and T3 ran concurrently (session.jsonl:564, :566; |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 10 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✗ | manual: 0/3 blind judges pass. No commit straddles phases (planning cb14e35, plan-review 4efada4, P1 890f6b5/a85ef94/408 |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [184]) | 1.00 | 1.0 | 195 | 0.92 | 1 | 98.4 | 115 | 0.047 |
| T2 | 1 (calls [198]) | 1.00 | 1.0 | 129 | 0.95 | 1 | 99.0 | 229 | 0.064 |
| T3 | 1 (calls [197]) | 1.00 | 1.0 | 123 | 0.95 | 1 | 99.0 | 146 | 0.051 |
| T4 | 3 (calls [242, 244, 245]) | 0.50 | 1.0 | 1025 | 0.59 | 1 | 71.8 | 636 | 0.183 |
| T5 | 1 (calls [268]) | 1.00 | 1.0 | 694 | 0.72 | 1 | 94.5 | 970 | 0.174 |
| T6 | 3 (calls [284, 285, 286]) | 0.50 | 1.0 | 483 | 0.81 | 1 | 76.2 | 239 | 0.124 |
| T7 | 1 (calls [325]) | 1.00 | 1.0 | 1224 | 0.51 | 1 | 90.3 | 380 | 0.086 |
| T8 | 5 (calls [335, 336, 344, 345, 351]) | 0.00 | 1.0 | 972 | 0.61 | 1 | 52.3 | 0 | 0.147 |
| T9 | 1 (calls [363]) | 1.00 | 1.0 | 278 | 0.89 | 1 | 97.8 | 636 | 0.124 |
