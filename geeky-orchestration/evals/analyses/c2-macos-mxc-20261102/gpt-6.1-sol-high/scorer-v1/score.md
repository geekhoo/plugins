# Score: 20261101T211028Z (c2-linkvault)

Plugin `44d6afb`, claude-code / gpt-6.1-sol. Scored 2026-11-01T22:10:29Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 92.7 | P 1.000, S 0.516, D 1.00 |
| Adherence | 0.35 | 52.6 | 20/38 |
| Consistency | 0.20 | 46.3 | DPC 9/21 = 0.429, OC 0.60 |
| Task tier | 0.10 | 10.8 | L_run 5180 ms, L_ref 2678 ms |
| **Composite** | | **61.2** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: 3/3 blind judges pass. The report claims BLOCKED, not completion. It says impl-review is UNREACHED, only T1 is Done, T2 is Blocked, T3 and T4 are In Review, and e5c7276 is an explicitly 'unaccepted' checkpoint. The 512-pass figure is presented as evidence that does not override the reviewer. No task, test or commit is claimed that is missing: the kanban, git log and session.jsonl:488-492 all agree. The oracle's 136/136 pass does not contradict anything the report claimed. | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 4 task file(s) found. |
| adh.task_schema | ✓ | OK: 4 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 4 task(s) tracked, 4 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=2, Blocked=1, Done=1 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✗ | DOD_INCOMPLETE: T2 |
| adh.dod.T3 | ✗ | DOD_INCOMPLETE: T3 |
| adh.dod.T4 | ✗ | DOD_INCOMPLETE: T4 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T4 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✓ | T1-core-storage.notes.md |
| adh.notes.T2 | ✓ | T2-http-server.notes.md |
| adh.notes.T3 | ✓ | T3-cli-client.notes.md |
| adh.notes.T4 | ✓ | T4-contract-acceptance.notes.md |
| adh.task_review.T1 | ✓ | call 236 'Review foundation phase acceptance' (prompt) PASS; call 347 'Review service client acceptance phase' (prompt) not PASS |
| adh.task_review.T2 | ✗ | call 347 'Review service client acceptance phase' (prompt) not PASS |
| adh.task_review.T3 | ✗ | call 347 'Review service client acceptance phase' (prompt) not PASS |
| adh.task_review.T4 | ✗ | call 347 'Review service client acceptance phase' (prompt) not PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1']: reviewer call 236; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✗ | phase P2 ['T2', 'T3', 'T4']: reviewer none; READY TO ADVANCE recorded: T2-http-server.notes.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [(258, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.kanban_after_moves | ✗ | 0 lane-move calls; without validate-kanban: none |
| adh.commit_msg.8dc8471 | ✓ | feat(core): implement persistent link state and validation: OK: commit message valid. |
| adh.commit_msg.e5c7276 | ✓ | chore(checkpoint): preserve blocked service implementation: OK: commit message valid. |
| adh.commit_msg.1509e0b | ✓ | docs(handoff): finalize blocked run evidence: OK: commit message valid. |
| adh.prescribed_msg.spec | ✗ | docs(spec): author linkvault feature specification |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 8ce9e62..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✗ | manual: as a.one_concern_per_commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: as a.final_report_claims |
| adh.heartbeat_final | ✓ | .heartbeat status=paused |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✗ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: 3/3 blind judges pass. Only geeky-coder dispatches in session.jsonl: T1 alone (:363), T2+T3 together in |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3', 'T4'] |
| dp09 | Task review, per task | 2 | ✗ | not reviewed: ['T2', 'T3', 'T4'] |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp11 | Phase verdict from a phase review | 2 | ✗ | failing phases: ['P2'] |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 3 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✗ | manual: 0/3 blind judges pass. Phase 1 is clean (8dc8471 = T1 only, base 8ce9e62). Phase 2 was committed as the single c |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✗ | 0 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 775 | 0.270 |
| T2 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 0 | 0.0 | 816 | 0.278 |
| T3 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 0 | 0.0 | 523 | 0.223 |
| T4 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 0 | 0.0 | 550 | 0.228 |
