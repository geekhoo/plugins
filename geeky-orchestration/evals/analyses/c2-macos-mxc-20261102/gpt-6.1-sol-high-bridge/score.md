# Score: 20261102T053248Z (c2-linkvault)

Plugin `e0aa470`, claude-code / gpt-6.1-sol. Scored 2026-11-02T07:18:56Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 92.4 | P 1.000, S 0.490, D 1.00 |
| Adherence | 0.35 | 100.0 | 41/41 |
| Consistency | 0.20 | 96.7 | DPC 23/23 = 1.000, OC 0.83 |
| Task tier | 0.10 | 80.2 | L_run 6273 ms, L_ref 2678 ms |
| **Composite** | | **94.7** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: 3/3 blind judges pass. The report claims the work is blocked: the final impl-review is NEEDS FIXES, there is no Python 3.11+ evidence, and the release checkbox is unchecked. kanban.md lists 4 tasks Done and the release gates are left unchecked, which matches the report. The '50 concurrent redirects' acceptance claim is backed by the test (Barrier(50), 50 workers). The oracle's 136 passes agree with the product being correct, so nothing is claimed that was not done. | Adherence <= 50 |

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
| adh.handoff_batch.T1 | ✓ | Done move call 241; handoff naming T1 in call 241 |
| adh.handoff_batch.T2 | ✓ | Done move call 353; handoff naming T2 in call 353 |
| adh.handoff_batch.T3 | ✓ | Done move call 354; handoff naming T3 in call 354 |
| adh.handoff_batch.T4 | ✓ | Done move call 446; handoff naming T4 in call 446 |
| adh.notes.T1 | ✓ | T1-domain-storage.notes.md |
| adh.notes.T2 | ✓ | T2-http-server.notes.md |
| adh.notes.T3 | ✓ | T3-cli-client.notes.md |
| adh.notes.T4 | ✓ | T4-contract-acceptance.notes.md |
| adh.task_review.T1 | ✓ | call 223 'Review phase one task acceptance' (prompt) PASS; call 294 'Review server and client phase' (prompt) not PASS; call 402 'Review final impleme |
| adh.task_review.T2 | ✓ | call 223 'Review phase one task acceptance' (prompt) PASS; call 294 'Review server and client phase' (prompt) not PASS; call 339 'Re-review corrected  |
| adh.task_review.T3 | ✓ | call 294 'Review server and client phase' (prompt) not PASS; call 339 'Re-review corrected server framing' (reviewed-process-evidence) PASS |
| adh.task_review.T4 | ✓ | call 223 'Review phase one task acceptance' (prompt) PASS; call 294 'Review server and client phase' (prompt) not PASS; call 402 'Review final impleme |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1']: reviewer call 223; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T2', 'T3']: reviewer call 339; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T4']: reviewer call 223; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✓ | Done call 241; last code edit None; check-dod runs [(241, True)] |
| adh.gates_before_done.T2 | ✓ | Done call 353; last code edit 334; check-dod runs [(353, True)] |
| adh.gates_before_done.T3 | ✓ | Done call 354; last code edit None; check-dod runs [(354, True)] |
| adh.gates_before_done.T4 | ✓ | Done call 446; last code edit None; check-dod runs [(446, True)] |
| adh.kanban_after_moves | ✓ | 12 lane-move calls; without validate-kanban: none |
| adh.commit_msg.e06a8d7 | ✓ | feat(foundations): add strict domain and SQLite storage: OK: commit message valid. |
| adh.commit_msg.770df75 | ✓ | feat(service): implement exact HTTP API and clean lifecycle: OK: commit message valid. |
| adh.commit_msg.55932f8 | ✓ | feat(client): add CLI and precise HTTP client behavior: OK: commit message valid. |
| adh.commit_msg.7e52c81 | ✓ | feat(acceptance): prove process contract and document usage: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in docs/spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | ✓ | critical findings in impl-review; fix commit: fix(spec): Address 1 required review findings from impl-review |
| adh.frozen_untouched | ✓ | git diff 335a4a1..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✓ | manual: as a.one_concern_per_commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: as a.final_report_claims |
| adh.heartbeat_final | ✓ | .heartbeat status=paused |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: 3/3 blind judges pass. Only one concurrent coder batch. session.jsonl lines 369 and 370 are two geeky-c |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✓ | failing: none |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 4 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: 3/3 blind judges pass. Commits follow the phases in order: spec (9057943), plan package (b0bb094), plan-review a |
| dp14 | Handoff at each Done move (D82) | 1 | ✓ | failing: none |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 5 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | ✓ | manual: 3/3 blind judges pass. The first impl-review round (a8c0dfc6 persistence/domain, ad47fe67 HTTP, a4cbb87c CLI) ra |
| dp17b | Fix commit, prescribed message | 1 | ✓ | see adh.prescribed_msg.critical_fix |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 2 (calls [585, 589]) | 0.75 | 1.0 | 212 | 0.92 | 1 | 88.5 | 1026 | 0.489 |
| T2 | 1 (calls [335]) | 1.00 | 1.0 | 93 | 0.97 | 1 | 99.3 | 874 | 0.300 |
| T3 | 0 (calls []) | 0.00 | 0.5 | - | 0.00 | 1 | 25.0 | 572 | 0.087 |
| T4 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 815 | 0.124 |
