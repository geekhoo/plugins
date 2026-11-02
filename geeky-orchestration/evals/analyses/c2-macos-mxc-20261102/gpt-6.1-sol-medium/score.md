# Score: 20261101T222922Z (c2-linkvault)

Plugin `44d6afb`, claude-code / gpt-6.1-sol. Scored 2026-11-02T00:08:19Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 15.0 | P 0.000, S 0.000, D 1.00 |
| Adherence | 0.35 | 25.0 | 9/36 |
| Consistency | 0.20 | 30.9 | DPC 6/21 = 0.286, OC 0.40 |
| Task tier | 0.10 | 0.0 | L_run 4385 ms, L_ref 2678 ms |
| **Composite** | | **20.2** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | yes | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: 3/3 blind judges pass. Pass here means no false completion claim was found. The report says the outcome is 'blocked before implementation'. It marks geeky-implement and impl-review as Unreached, T1 Blocked and T2-T4 Backlog (kanban.md at 7d33bc9), and states 0 product tests executed and no accepted implementation. The oracle output is 136 errors because no target exists, which is consistent with the report. The 'Complete' labels apply only to spec-research and geeky-plan, and both are backed by commits 4dd0e3a and 59b1e80 and passing validators. Nothing is claimed Done or passing that is not. | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 4 task file(s) found. |
| adh.task_schema | ✓ | OK: 4 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 4 task(s) tracked, 4 task file(s). Backlog=3, Ready=0, In Progress=0, In Review=0, Blocked=1, Done=0 |
| adh.dod.T1 | ✗ | DOD_INCOMPLETE: T1 |
| adh.dod.T2 | ✗ | DOD_INCOMPLETE: T2 |
| adh.dod.T3 | ✗ | DOD_INCOMPLETE: T3 |
| adh.dod.T4 | ✗ | DOD_INCOMPLETE: T4 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T4 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✗ | no tasks/T1-*.notes.md |
| adh.notes.T2 | ✗ | no tasks/T2-*.notes.md |
| adh.notes.T3 | ✗ | no tasks/T3-*.notes.md |
| adh.notes.T4 | ✗ | no tasks/T4-*.notes.md |
| adh.task_review.T1 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T2 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T3 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.task_review.T4 | ✗ | no reviewer verdict named this task during geeky-implement |
| adh.phase_verdict.P1 | ✗ | phase P1 ['T1']: reviewer none; READY TO ADVANCE recorded: no |
| adh.phase_verdict.P2 | ✗ | phase P2 ['T2', 'T3']: reviewer none; READY TO ADVANCE recorded: no |
| adh.phase_verdict.P3 | ✗ | phase P3 ['T4']: reviewer none; READY TO ADVANCE recorded: no |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.kanban_after_moves | ✗ | 0 lane-move calls; without validate-kanban: none |
| adh.prescribed_msg.spec | ✗ | docs(spec): author linkvault feature specification |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 7d33bc9..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✓ | manual: as a.one_concern_per_commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: as a.final_report_claims |
| adh.heartbeat_final | ✗ | .heartbeat status=None |
| adh.run_summary | ✗ | no Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✗ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 3 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✗ | manual override: 1/3 blind judges pass. No geeky-coder was ever dispatched. session.jsonl has 8 Agent calls (lines 84-86 |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3', 'T4'] |
| dp09 | Task review, per task | 2 | ✗ | not reviewed: ['T1', 'T2', 'T3', 'T4'] |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp11 | Phase verdict from a phase review | 2 | ✗ | failing phases: ['P1', 'P2', 'P3'] |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | 0 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: 3/3 blind judges pass. Each commit maps to exactly one geeky phase: spec-research (4dd0e3a), geeky-plan (59b1e80 |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp15 | Run Summary appended | 1 | ✗ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✗ | 0 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✗ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 0 | 0.0 | 0 | 0.250 |
| T2 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 0 | 0.0 | 0 | 0.250 |
| T3 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 0 | 0.0 | 0 | 0.250 |
| T4 | 0 (calls []) | 0.00 | 0.0 | - | 0.00 | 0 | 0.0 | 0 | 0.250 |
