# Score: 20261020T155628Z (c1-csvledger)

Plugin `24c4e6d`, claude-code / claude-sonnet-5-5. Scored 2026-10-23T05:30:58Z by `score-run.py`. Workspace: run.json workspace. Validation blocks re-run. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 95.9 | P 1.000, S 0.725, D 1.00 |
| Adherence | 0.35 | 62.9 | 44/70 |
| Consistency | 0.20 | 68.7 | DPC 14/23 = 0.609, OC 1.00 |
| Task tier | 0.10 | 77.1 | L_run 2641 ms, L_ref 2678 ms |
| **Composite** | | **77.0** | |

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
| adh.handoff_batch.T1 | ✗ | Done move call 122; no handoff.md write naming T1 in calls 122/123 |
| adh.handoff_batch.T2 | ✗ | Done move call 145; no handoff.md write naming T2 in calls 145/146 |
| adh.handoff_batch.T3 | ✗ | Done move call 145; no handoff.md write naming T3 in calls 145/146 |
| adh.handoff_batch.T4 | ✗ | Done move call 206; no handoff.md write naming T4 in calls 206/207 |
| adh.handoff_batch.T5 | ✗ | Done move call 206; no handoff.md write naming T5 in calls 206/207 |
| adh.handoff_batch.T6 | ✗ | Done move call 228; no handoff.md write naming T6 in calls 228/229 |
| adh.handoff_batch.T7 | ✗ | Done move call 263; no handoff.md write naming T7 in calls 263/264 |
| adh.handoff_batch.T8 | ✓ | Done move call 314; handoff naming T8 in call 314 |
| adh.handoff_batch.T9 | ✓ | Done move call 314; handoff naming T9 in call 314 |
| adh.notes.T1 | ✓ | T1-scaffold-and-harness.notes.md |
| adh.notes.T2 | ✓ | T2-money.notes.md |
| adh.notes.T3 | ✓ | T3-tabular-reader.notes.md |
| adh.notes.T4 | ✓ | T4-transactions-loader.notes.md |
| adh.notes.T5 | ✓ | T5-rules-loader-and-matching.notes.md |
| adh.notes.T6 | ✓ | T6-dedupe-filter-aggregate.notes.md |
| adh.notes.T7 | ✓ | T7-renderers.notes.md |
| adh.notes.T8 | ✓ | T8-cli.notes.md |
| adh.notes.T9 | ✓ | T9-acceptance-and-determinism.notes.md |
| adh.task_review.T1 | ✓ | call 173 'Review phases 1-2' (prompt) PASS |
| adh.task_review.T2 | ✓ | call 173 'Review phases 1-2' (prompt) PASS |
| adh.task_review.T3 | ✓ | call 173 'Review phases 1-2' (prompt) PASS |
| adh.task_review.T4 | ✓ | call 173 'Review phases 1-2' (prompt) PASS |
| adh.task_review.T5 | ✓ | call 173 'Review phases 1-2' (prompt) PASS |
| adh.task_review.T6 | ✓ | call 245 'Review phase 3' (prompt) PASS |
| adh.task_review.T7 | ✓ | call 245 'Review phase 3' (prompt) PASS |
| adh.task_review.T8 | ✓ | call 294 'Review phase 4' (prompt) PASS |
| adh.task_review.T9 | ✓ | call 294 'Review phase 4' (prompt) PASS |
| adh.phase_verdict.P1 | ✗ | phase P1 ['T1', 'T2']: reviewer call 173; READY TO ADVANCE recorded: no |
| adh.phase_verdict.P2 | ✗ | phase P2 ['T3', 'T4', 'T5']: reviewer call 173; READY TO ADVANCE recorded: no |
| adh.phase_verdict.P3 | ✗ | phase P3 ['T6', 'T7']: reviewer call 245; READY TO ADVANCE recorded: no |
| adh.phase_verdict.P4 | ✗ | phase P4 ['T8', 'T9']: reviewer call 294; READY TO ADVANCE recorded: no |
| adh.gates_before_done.T1 | ✗ | Done call 122; last code edit 119; check-dod runs [] |
| adh.gates_before_done.T2 | ✗ | Done call 145; last code edit 137; check-dod runs [] |
| adh.gates_before_done.T3 | ✗ | Done call 145; last code edit 143; check-dod runs [] |
| adh.gates_before_done.T4 | ✗ | Done call 206; last code edit 170; check-dod runs [] |
| adh.gates_before_done.T5 | ✗ | Done call 206; last code edit 164; check-dod runs [] |
| adh.gates_before_done.T6 | ✗ | Done call 228; last code edit 225; check-dod runs [] |
| adh.gates_before_done.T7 | ✗ | Done call 263; last code edit 242; check-dod runs [] |
| adh.gates_before_done.T8 | ✗ | Done call 314; last code edit 275; check-dod runs [] |
| adh.gates_before_done.T9 | ✗ | Done call 314; last code edit 291; check-dod runs [] |
| adh.kanban_after_moves | ✗ | 14 lane-move calls; without validate-kanban: [122, 123, 145, 172, 206, 207, 228, 244, 263, 279, 293] |
| adh.commit_msg.aa384de | ✗ | feat(foundation): scaffold package, test harness and exact m: INVALID_COMMIT_MESSAGE: |
| adh.commit_msg.3c02a1d | ✓ | feat(loading): add shared CSV reader, transaction and rules : OK: commit message valid. |
| adh.commit_msg.4f57b9d | ✓ | chore(plan): record phases 1-2 progress: OK: commit message valid. |
| adh.commit_msg.4702a0e | ✓ | feat(logic): add dedupe, month filter, aggregation and rende: OK: commit message valid. |
| adh.commit_msg.3c109cf | ✓ | chore(plan): record phase 3 progress: OK: commit message valid. |
| adh.commit_msg.26ff927 | ✓ | feat(cli): add command-line interface and acceptance suite: OK: commit message valid. |
| adh.commit_msg.29eaffb | ✓ | chore(plan): record run summary and final kanban: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✗ | chore(plan): Plan review - align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | ✗ | critical findings in impl-review; fix commit: fix(loading): validate rows in file order so first error wins |
| adh.frozen_untouched | ✓ | git diff 302290c..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✗ | manual: fec33c4 records the review and edits code |
| adh.no_orchestrator_code_edits | ✗ | call 121 (geeky-implement): tests/test_tmp_probe.py; call 122 (geeky-implement): pytest.ini, tests/test_tmp_probe.py; call 350 (impl-review): csvledge |
| adh.final_report_claims | ✓ | manual: no false claim (doc) |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✗ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | max 2 concurrent coders; justification: DP7 (doc: pass) |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9'] |
| dp11 | Phase verdict from a phase review | 2 | ✗ | failing phases: ['P1', 'P2', 'P3', 'P4'] |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 7 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✗ | manual: phase 3 and 4 bundled several concerns (doc) |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 4 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | ✓ | manual: re-review of the affected scope after the critical fix (doc: pass) |
| dp17b | Fix commit, prescribed message | 1 | ✗ | see adh.prescribed_msg.critical_fix |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 4 (calls [118, 119] + D87 [122, 351]) | 0.25 | 1.0 | 457 | 0.61 | 1 | 62.3 | 71 | 0.100 |
| T2 | 3 (calls [141] + D87 [350, 351]) | 0.50 | 1.0 | 314 | 0.73 | 1 | 74.7 | 66 | 0.079 |
| T3 | 4 (calls [142, 144] + D87 [350, 362]) | 0.25 | 1.0 | 314 | 0.73 | 1 | 64.7 | 243 | 0.148 |
| T4 | 3 (calls [171] + D87 [350, 351]) | 0.50 | 1.0 | 197 | 0.83 | 1 | 76.7 | 188 | 0.113 |
| T5 | 3 (calls [168] + D87 [350, 351]) | 0.50 | 1.0 | 197 | 0.83 | 1 | 76.7 | 244 | 0.129 |
| T6 | 2 (calls [224, 226]) | 0.75 | 1.0 | 304 | 0.74 | 1 | 84.9 | 212 | 0.100 |
| T7 | 2 (calls [239, 243]) | 0.75 | 1.0 | 170 | 0.86 | 1 | 87.1 | 230 | 0.105 |
| T8 | 2 (calls [274, 277]) | 0.75 | 1.0 | 396 | 0.67 | 1 | 83.3 | 186 | 0.092 |
| T9 | 2 (calls [289, 292]) | 0.75 | 1.0 | 218 | 0.82 | 1 | 86.3 | 336 | 0.135 |
