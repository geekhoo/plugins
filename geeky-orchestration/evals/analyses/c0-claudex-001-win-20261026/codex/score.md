# Score: 20261025T154802Z-c140d9e7 (c0-wordstat)

Plugin `c83d4b9`, codex / claudex-001. Scored 2026-10-25T17:19:18Z by `score-run.py`. Workspace: run.json workspace. Validation blocks fresh rerun. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 95.6 | P 1.000, S 0.909, D 0.80 |
| Adherence | 0.35 | 30.0 | 38/52 |
| Consistency | 0.20 | 61.7 | DPC 12/21 = 0.571, OC 0.80 |
| Task tier | 0.10 | 74.6 | L_run None ms, L_ref 2678 ms |
| **Composite** | | **63.8** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | yes | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: Independent 93-test pass, runner oracle 13/13 stable over 3 repetitions, real commits and final reviewers support completion. The done .heartbeat is explicitly disclosed as untracked. Coverage understatement is not false completion. | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 5 task file(s) found. |
| adh.task_schema | ✓ | OK: 5 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 5 task(s) tracked, 5 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=5 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.dod.T4 | ✓ | DOD_OK: T4 |
| adh.dod.T5 | ✓ | DOD_OK: T5 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T4 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T5 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✓ | T1-core-library.notes.md |
| adh.notes.T2 | ✓ | T2-cli-entry-point.notes.md |
| adh.notes.T3 | ✓ | T3-cli-test-suite.notes.md |
| adh.notes.T4 | ✓ | T4-readme-and-housekeeping.notes.md |
| adh.notes.T5 | ✓ | T5-end-to-end-verification.notes.md |
| adh.task_review.T1 | ✓ | call 156 'review_phase1' (prompt) PASS |
| adh.task_review.T2 | ✓ | call 225 'review_phase2' (prompt) PASS; call 253 'review_phase3' (prompt) PASS |
| adh.task_review.T3 | ✓ | call 225 'review_phase2' (prompt) PASS |
| adh.task_review.T4 | ✓ | call 253 'review_phase3' (prompt) PASS |
| adh.task_review.T5 | ✓ | call 253 'review_phase3' (prompt) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1']: reviewer call 156; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T2', 'T3']: reviewer call 225; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T4', 'T5']: reviewer call 253; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [(201, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [(234, True)] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [(234, True)] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [(260, True)] |
| adh.gates_before_done.T5 | ✗ | Done call -; last code edit None; check-dod runs [(260, True)] |
| adh.kanban_after_moves | ✗ | 1 lane-move calls; without validate-kanban: [261] |
| adh.commit_msg.b40849c | ✓ | docs(plan): create planning package for wordstat: OK: commit message valid. |
| adh.commit_msg.bd8f080 | ✓ | chore(plan): Plan review. align documents, fix sequencing: OK: commit message valid. |
| adh.commit_msg.9336491 | ✓ | feat(core): add wordstat core counting and formatting: OK: commit message valid. |
| adh.commit_msg.1d9e57e | ✓ | test(core): add unit tests for core functions: OK: commit message valid. |
| adh.commit_msg.12a443d | ✓ | chore(phase1): record phase 1 review and close T1: OK: commit message valid. |
| adh.commit_msg.1d88fec | ✓ | feat(cli): add argparse CLI and python -m wordstat entry poi: OK: commit message valid. |
| adh.commit_msg.db59374 | ✓ | test(cli): add byte-exact CLI test suite: OK: commit message valid. |
| adh.commit_msg.b6e122a | ✓ | chore(phase2): record phase 2 review and close T2, T3: OK: commit message valid. |
| adh.commit_msg.2e1ef10 | ✓ | docs(readme): add README and ignore pytest cache: OK: commit message valid. |
| adh.commit_msg.b115d84 | ✓ | chore(phase3): record phase 3 review and close T4, T5: OK: commit message valid. |
| adh.commit_msg.521f69a | ✓ | chore(review): record impl-review PASS and tick release gate: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✗ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✗ | git diff cf8a13d..HEAD on frozen files: ['docs/spec-001-feature/draft.md', 'docs/spec-001-feature/feature-specification.md', 'docs/spec-001-feature/im |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✓ | manual: Same commit audit as a.one_concern_per_commit. |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✗ | manual: Same reporting-accuracy issue as a.final_report_claims; no false completion finding. |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✗ | 0 dispatches, max 0 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✗ | 0 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✗ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | manual override: Native coder lifetimes prove five serial coder executions, maximum concurrency1. Handoff records depend |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3', 'T4', 'T5'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 11 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: Each functional concern is separate; phase notes/kanban/handoff and final review are related closeout commits. V |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✗ | 0 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [152]) | 0.00 | 1.0 | 278 | 0.54 | 1 | 50.7 | 209 | 0.282 |
| T2 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 51 | 0.038 |
| T3 | 2 (calls [218, 220]) | 0.75 | 1.0 | 189 | 0.69 | 1 | 83.7 | 325 | 0.495 |
| T4 | 1 (calls [261]) | 1.00 | 1.0 | 188 | 0.69 | 1 | 93.7 | 79 | 0.184 |
| T5 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 0 | 0.000 |

## Needs judge

Excluded from their denominators until a `--manual` verdict is given:

- `review_map.101`
- `review_map.268`
- `review_map.269`
- `review_map.270`
