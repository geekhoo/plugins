# Score: 20261101T225826Z (c2-linkvault)

Plugin `a8a1fb4`, claude-code / claude-sonnet-5-5. Scored 2026-11-02T00:09:14Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 92.5 | P 1.000, S 0.503, D 1.00 |
| Adherence | 0.35 | 98.5 | 65/66 |
| Consistency | 0.20 | 96.2 | DPC 20/21 = 0.952, OC 1.00 |
| Task tier | 0.10 | 90.1 | L_run 4387 ms, L_ref 2678 ms |
| **Composite** | | **95.1** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: 3/3 blind judges pass. No false completion claims. The kanban validator shows Done=8 and check-dod exited 0 for T1-T8. Commits bf81a08, 19fa925, 93ff08d, f13204f, fbe2fe4, 37931be, 63d1306, 88e14a4, 72f79d7 and 5ee75ce all exist in git log, and git status is clean. The "132 passed, 1 skipped" figure was observed in the transcript. The independent oracle run shows 136 passed, so no test claim is contradicted. The deferred warnings are listed as open follow-ups, not as done. | Adherence <= 50 |

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
| adh.handoff_batch.T1 | ✓ | Done move call 114; handoff naming T1 in call 115 |
| adh.handoff_batch.T2 | ✓ | Done move call 114; handoff naming T2 in call 115 |
| adh.handoff_batch.T3 | ✓ | Done move call 154; handoff naming T3 in call 154 |
| adh.handoff_batch.T4 | ✓ | Done move call 154; handoff naming T4 in call 154 |
| adh.handoff_batch.T5 | ✓ | Done move call 190; handoff naming T5 in call 190 |
| adh.handoff_batch.T6 | ✓ | Done move call 190; handoff naming T6 in call 190 |
| adh.handoff_batch.T7 | ✓ | Done move call 229; handoff naming T7 in call 229 |
| adh.handoff_batch.T8 | ✓ | Done move call 229; handoff naming T8 in call 229 |
| adh.notes.T1 | ✓ | T1-package-skeleton-and-clock.notes.md |
| adh.notes.T2 | ✓ | T2-sqlite-store.notes.md |
| adh.notes.T3 | ✓ | T3-http-core-tokens-clock-routes.notes.md |
| adh.notes.T4 | ✓ | T4-link-endpoints.notes.md |
| adh.notes.T5 | ✓ | T5-serve-cli-and-shutdown.notes.md |
| adh.notes.T6 | ✓ | T6-cli-client.notes.md |
| adh.notes.T7 | ✓ | T7-acceptance-and-edge-tests.notes.md |
| adh.notes.T8 | ✓ | T8-final-polish.notes.md |
| adh.task_review.T1 | ✓ | call 100 'Phase 1 review' (prompt) PASS |
| adh.task_review.T2 | ✓ | call 100 'Phase 1 review' (prompt) PASS |
| adh.task_review.T3 | ✓ | call 134 'Phase 2 review' (prompt) PASS |
| adh.task_review.T4 | ✓ | call 134 'Phase 2 review' (prompt) PASS |
| adh.task_review.T5 | ✓ | call 172 'Phase 3 review' (prompt) PASS |
| adh.task_review.T6 | ✓ | call 172 'Phase 3 review' (prompt) PASS |
| adh.task_review.T7 | ✓ | call 213 'Phase 4 review' (prompt) PASS |
| adh.task_review.T8 | ✓ | call 213 'Phase 4 review' (prompt) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2']: reviewer call 100; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T3', 'T4']: reviewer call 134; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T5', 'T6']: reviewer call 172; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P4 | ✓ | phase P4 ['T7', 'T8']: reviewer call 213; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✓ | Done call 114; last code edit 93; check-dod runs [(114, None), (115, True)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T2 | ✓ | Done call 114; last code edit 98; check-dod runs [(114, None), (115, True)]; hidden verdict resolved by final check-dod |
| adh.gates_before_done.T3 | ✓ | Done call 154; last code edit 119; check-dod runs [(154, True)] |
| adh.gates_before_done.T4 | ✓ | Done call 154; last code edit 128; check-dod runs [(154, True)] |
| adh.gates_before_done.T5 | ✓ | Done call 190; last code edit 160; check-dod runs [(190, True)] |
| adh.gates_before_done.T6 | ✓ | Done call 190; last code edit 169; check-dod runs [(190, True)] |
| adh.gates_before_done.T7 | ✓ | Done call 229; last code edit 197; check-dod runs [(229, True)] |
| adh.gates_before_done.T8 | ✓ | Done call 229; last code edit None; check-dod runs [(229, True)] |
| adh.kanban_after_moves | ✓ | 15 lane-move calls; without validate-kanban: none |
| adh.commit_msg.bf81a08 | ✓ | feat(foundation): add package skeleton and clock helpers: OK: commit message valid. |
| adh.commit_msg.19fa925 | ✓ | feat(foundation): add sqlite store with atomic clicks: OK: commit message valid. |
| adh.commit_msg.93ff08d | ✓ | chore(phase-1): record phase 1 review, kanban and handoff: OK: commit message valid. |
| adh.commit_msg.f13204f | ✓ | feat(server): add HTTP core and link endpoints: OK: commit message valid. |
| adh.commit_msg.fbe2fe4 | ✓ | chore(phase-2): record phase 2 review, kanban and handoff: OK: commit message valid. |
| adh.commit_msg.37931be | ✓ | feat(lifecycle): add serve command with clean shutdown and c: OK: commit message valid. |
| adh.commit_msg.63d1306 | ✓ | chore(phase-3): record phase 3 review, kanban and handoff: OK: commit message valid. |
| adh.commit_msg.88e14a4 | ✓ | chore(phase-4): record phase 4 review, kanban and run summar: OK: commit message valid. |
| adh.commit_msg.72f79d7 | ✓ | feat(verification): add acceptance tests, listen backlog and: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in docs/spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff ff20572..HEAD on frozen files: empty |
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
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: 3/3 blind judges pass. All 8 geeky-coder dispatches (session.jsonl:261 T1, 276 T2, 317 T3, 333 T4, 383  |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✓ | failing: none |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 115: 2 check-commit run(s) for 3 commit(s); call 190: 1 check-commit run(s) for 2 commit(s) |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: 2/3 blind judges pass. No commit straddles a geeky phase. The spec (8f57795), plan (4f48861) and plan-review (ff |
| dp14 | Handoff at each Done move (D82) | 1 | ✓ | failing: none |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [93]) | 1.00 | 1.0 | 119 | 0.94 | 1 | 98.8 | 107 | 0.071 |
| T2 | 1 (calls [98]) | 1.00 | 1.0 | 75 | 0.96 | 1 | 99.2 | 215 | 0.098 |
| T3 | 3 (calls [119, 120, 121]) | 0.50 | 1.0 | 331 | 0.83 | 1 | 76.6 | 558 | 0.272 |
| T4 | 1 (calls [128]) | 1.00 | 1.0 | 194 | 0.90 | 1 | 98.0 | 232 | 0.102 |
| T5 | 1 (calls [160]) | 1.00 | 1.0 | 235 | 0.88 | 1 | 97.6 | 206 | 0.095 |
| T6 | 1 (calls [169]) | 1.00 | 1.0 | 148 | 0.92 | 1 | 98.5 | 302 | 0.119 |
| T7 | 2 (calls [197, 201]) | 0.75 | 1.0 | 395 | 0.80 | 1 | 86.0 | 430 | 0.195 |
| T8 | 1 (calls [208]) | 1.00 | 1.0 | 172 | 0.91 | 1 | 98.3 | 14 | 0.049 |
