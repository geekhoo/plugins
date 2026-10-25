# Score: 20261025T183455Z-geeky-resume-router-fixed-20261025T195444Z-recovered (c0-wordstat)

Plugin `c83d4b9`, claude-code / claudex-001. Scored 2026-10-25T21:27:49Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: none.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 96.7 | P 1.000, S 0.778, D 1.00 |
| Adherence | 0.35 | 65.0 | 26/40 |
| Consistency | 0.20 | 37.5 | DPC 7/19 = 0.368, OC 0.40 |
| Task tier | 0.10 | 73.7 | L_run 4386 ms, L_ref 2678 ms |
| **Composite** | | **71.5** | |

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
| adh.phase_verdict.P1 | ✗ | phase P1 ['T1', 'T2', 'T3', 'T4']: reviewer none; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call 332; last code edit 303; check-dod runs [(328, False), (333, True)] |
| adh.gates_before_done.T2 | ✗ | Done call 385; last code edit 354; check-dod runs [(387, True)] |
| adh.gates_before_done.T3 | ✗ | Done call 445; last code edit 417; check-dod runs [(447, True)] |
| adh.gates_before_done.T4 | ✗ | Done call 494; last code edit 467; check-dod runs [(495, True)] |
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
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review. align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 89eb091..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | judge? | judge: one concern per commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | judge? | judge: final report claims (D8) |
| adh.heartbeat_final | ✗ | .heartbeat status=running |
| adh.run_summary | ✗ | no Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✗ | 3 dispatches, max 1 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✗ | 0 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | judge? | max 1 concurrent coders; justification needs judge (dp07.justification) |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✗ | not reviewed: ['T2', 'T4'] |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp11 | Phase verdict from a phase review | 2 | ✗ | failing phases: ['P1'] |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 393: 0 check-commit run(s) for 1 commit(s); call 459: 0 check-commit run(s) for 1 commit(s); call 501: 0 check-comm |
| dp13 | One concern per commit, per phase | 1 | judge? | judge |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4'] |
| dp15 | Run Summary appended | 1 | ✗ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✗ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [382]) | 1.00 | 1.0 | 968 | 0.01 | 1 | 80.3 | 15 | 0.112 |
| T2 | 1 (calls [357]) | 1.00 | 0.0 | 154 | 0.84 | 1 | 66.9 | 173 | 0.238 |
| T3 | 2 (calls [414, 418]) | 0.75 | 1.0 | 396 | 0.60 | 1 | 81.9 | 191 | 0.352 |
| T4 | 1 (calls [468]) | 1.00 | 0.0 | 144 | 0.85 | 1 | 67.1 | 248 | 0.298 |

## Needs judge

Excluded from their denominators until a `--manual` verdict is given:

- `adh.one_concern_per_commit`
- `adh.final_report_claims`
- `dp07`
- `dp13`
