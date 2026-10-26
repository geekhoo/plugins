# Score: scoring-input (c0-wordstat)

Plugin `c83d4b9`, claude-code / claudex-001. Scored 2026-10-26T06:22:40Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 95.7 | P 1.000, S 0.714, D 1.00 |
| Adherence | 0.35 | 73.3 | 33/45 |
| Consistency | 0.20 | 56.2 | DPC 13/21 = 0.619, OC 0.33 |
| Task tier | 0.10 | 75.1 | L_run 5137 ms, L_ref 2678 ms |
| **Composite** | | **77.9** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: Final consolidated PASS WITH WARNINGS/zero critical findings exists;release checklist checked;done heartbeat;reviewer explicitly issues revised T4 READYTOADVANCE. No unsupported clean-tree or skipped-coverage claim. | Adherence <= 50 |

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
| adh.handoff_batch.T1 | ✗ | Done move call 332; no handoff.md write naming T1 in calls 332/333 |
| adh.handoff_batch.T2 | ✗ | Done move call 385; no handoff.md write naming T2 in calls 385/386 |
| adh.handoff_batch.T3 | ✗ | Done move call 445; no handoff.md write naming T3 in calls 445/446 |
| adh.handoff_batch.T4 | ✗ | Done move call 494; no handoff.md write naming T4 in calls 494/495 |
| adh.notes.T1 | ✓ | T1-scaffold-package.notes.md |
| adh.notes.T2 | ✓ | T2-counting-core.notes.md |
| adh.notes.T3 | ✓ | T3-cli-entrypoint.notes.md |
| adh.notes.T4 | ✓ | T4-subprocess-acceptance.notes.md |
| adh.task_review.T1 | ✓ | call 311 'Phase 1 review of T1 scaffold' (description) PASS |
| adh.task_review.T2 | ✗ | call 365 'Phase 2 review of T2 counting core' (description) not PASS |
| adh.task_review.T3 | ✓ | call 427 'Phase 3 review of T3 CLI entrypoint' (description) PASS |
| adh.task_review.T4 | ✗ | call 481 'Phase 4 review of T4 subprocess acceptance' (description) not PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1']: reviewer call 311; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✗ | phase P2 ['T2']: reviewer none; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T3']: reviewer call 427; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P4 | ✓ | manual override: Source-bound reviewer a5fa51b4a664cae32 returns T4 PASS and READY TO ADVANCE in subagent transcript54,reviewing0a9b354. Meta binds ca |
| adh.gates_before_done.T1 | ✗ | Done call 332; last code edit 303; check-dod runs [(328, False), (333, True), (564, True), (650, True), (673, True)] |
| adh.gates_before_done.T2 | ✗ | Done call 385; last code edit 354; check-dod runs [(387, True), (564, True), (651, True), (673, True)] |
| adh.gates_before_done.T3 | ✗ | Done call 445; last code edit 417; check-dod runs [(447, True), (564, True), (652, True), (673, True)] |
| adh.gates_before_done.T4 | ✗ | Done call 494; last code edit 467; check-dod runs [(495, True), (564, True), (653, True), (673, True), (697, True)] |
| adh.kanban_after_moves | ✗ | 16 lane-move calls; without validate-kanban: [293, 361, 391, 394, 424, 445, 449, 453, 477] |
| adh.commit_msg.0613177 | ✓ | feat(scaffold): add wordstat package skeleton and ignore pyt: OK: commit message valid. |
| adh.commit_msg.9ece905 | ✓ | chore(plan): record T1 done and T2 ready in kanban and hando: OK: commit message valid. |
| adh.commit_msg.186bb2a | ✓ | feat(counting): add decode, counting core and output formats: OK: commit message valid. |
| adh.commit_msg.7e47ef7 | ✓ | chore(plan): record T2 done and T3 ready in kanban and hando: OK: commit message valid. |
| adh.commit_msg.1e8168d | ✓ | feat(cli): add argparse entrypoint, stdout policy and exit c: OK: commit message valid. |
| adh.commit_msg.26bc58f | ✓ | chore(plan): record T3 done and T4 in progress in kanban and: OK: commit message valid. |
| adh.commit_msg.dc76b8a | ✓ | test(subprocess): add end-to-end acceptance tests: OK: commit message valid. |
| adh.commit_msg.e2c1317 | ✓ | chore(plan): record T4 done and final verification in handof: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in docs/spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 89eb091..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✓ | manual: Earlier ten coherent commits retained. New06fca83 changes only CLI parsing and focused tests;0a9b354 consolidates review/release records;a12f5 |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: Final resume-stream9638 matches actual candidate HEADa12f55a,60passed/2platformskips,22focusedpassed/1skip,exact JSON assertion,validators and |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✗ | 3 dispatches, max 1 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✗ | 0 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: Original four coders ran serially through documented predecessor dependencies. One later fix coder a75b |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✗ | not reviewed: ['T2', 'T4'] |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | manual override: Source-bound reviewer a5fa51b4a664cae32 returns T4 PASS and READY TO ADVANCE in subagent transcript54,r |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 393: 0 check-commit run(s) for 1 commit(s); call 459: 0 check-commit run(s) for 1 commit(s); call 501: 0 check-comm |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: Earlier ten coherent commits retained. New06fca83 changes only CLI parsing and focused tests;0a9b354 consolidate |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 5 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [382]) | 1.00 | 1.0 | 968 | 0.16 | 1 | 83.2 | 15 | 0.111 |
| T2 | 1 (calls [357]) | 1.00 | 0.0 | 154 | 0.87 | 1 | 67.3 | 173 | 0.229 |
| T3 | 2 (calls [414, 418]) | 0.75 | 1.0 | 396 | 0.66 | 1 | 83.1 | 236 | 0.376 |
| T4 | 1 (calls [468]) | 1.00 | 0.0 | 144 | 0.88 | 1 | 67.5 | 248 | 0.285 |
