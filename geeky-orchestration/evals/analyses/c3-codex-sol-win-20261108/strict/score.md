# Score: 20261108T150341Z-463d8062 (c3-minisql)

Plugin `eed7230`, codex / chatgpt/gpt-6.1-sol. Scored 2026-11-08T18:13:47Z by `score-run.py`. Workspace: given. Validation blocks fresh rerun. Manual verdicts: none.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 88.9 | P 1.000, S 0.257, D 1.00 |
| Adherence | 0.35 | 71.2 | 37/52 |
| Consistency | 0.20 | 68.0 | DPC 12/20 = 0.600, OC 1.00 |
| Task tier | 0.10 | 40.0 | L_run None ms, L_ref 2678 ms |
| **Composite** | | **73.6** | |

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
| adh.notes.T1 | ✓ | T1-foundation.notes.md |
| adh.notes.T2 | ✓ | T2-frontend.notes.md |
| adh.notes.T3 | ✓ | T3-semantic.notes.md |
| adh.notes.T4 | ✓ | T4-engine.notes.md |
| adh.notes.T5 | ✓ | T5-terminal.notes.md |
| adh.notes.T6 | ✓ | T6-contract.notes.md |
| adh.task_review.T1 | ✓ | call 189 'review_phase1' (prompt) PASS; call 256 'review_phase2' (prompt) PASS; call 320 'review_phase3' (prompt) PASS |
| adh.task_review.T2 | ✓ | call 189 'review_phase1' (prompt) PASS; call 256 'review_phase2' (prompt) PASS; call 320 'review_phase3' (prompt) PASS |
| adh.task_review.T3 | ✓ | call 256 'review_phase2' (prompt) PASS; call 320 'review_phase3' (prompt) PASS |
| adh.task_review.T4 | ✓ | call 320 'review_phase3' (prompt) PASS |
| adh.task_review.T5 | ✓ | call 470 'review_phase4' (prompt) PASS |
| adh.task_review.T6 | ✓ | call 470 'review_phase4' (prompt) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2']: reviewer call 189; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T3']: reviewer call 256; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T4']: reviewer call 320; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P4 | ✓ | phase P4 ['T5', 'T6']: reviewer call 470; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [(204, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [(204, True)] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [(269, True)] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [(335, True)] |
| adh.gates_before_done.T5 | ✗ | Done call -; last code edit None; check-dod runs [(500, None), (504, True)] |
| adh.gates_before_done.T6 | ✗ | Done call -; last code edit None; check-dod runs [(500, None), (504, True)] |
| adh.kanban_after_moves | ✗ | 0 lane-move calls; without validate-kanban: none |
| adh.commit_msg.9fe0690 | ✓ | feat(foundation): add CSV data, errors and deterministic for: OK: commit message valid. |
| adh.commit_msg.cf17100 | ✓ | feat(frontend): add source-spanned tokenizer and SQL parser: OK: commit message valid. |
| adh.commit_msg.5b87451 | ✓ | feat(semantic): bind names and enforce static SQL rules: OK: commit message valid. |
| adh.commit_msg.e08e4c8 | ✓ | feat(engine): execute typed queries and expose connection AP: OK: commit message valid. |
| adh.commit_msg.29858b4 | ✓ | feat(cli): add deterministic command and REPL interfaces: OK: commit message valid. |
| adh.commit_msg.df129c8 | ✓ | test(contract): close integrated minisql acceptance coverage: OK: commit message valid. |
| adh.prescribed_msg.spec | ✗ | docs(spec): author minisql feature specification |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | ✗ | critical findings in impl-review; fix commit: fix(spec): Address 1 required review findings from impl-review |
| adh.frozen_untouched | ✓ | git diff b45fa44..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs |
| adh.one_concern_per_commit | judge? | judge: one concern per commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | judge? | judge: final report claims (D8) |
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
| dp07 | Batching <=3 parallel, justification noted | 1 | judge? | max 0 concurrent coders; justification needs judge (dp07.justification) |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 212: 0 check-commit run(s) for 1 commit(s) |
| dp13 | One concern per commit, per phase | 1 | judge? | judge |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 4 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | judge? | judge |
| dp17b | Fix commit, prescribed message | 1 | ✗ | see adh.prescribed_msg.critical_fix |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 496 | 0.150 |
| T2 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 853 | 0.199 |
| T3 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 826 | 0.195 |
| T4 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 754 | 0.185 |
| T5 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 400 | 0.137 |
| T6 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 369 | 0.133 |

## Needs judge

Excluded from their denominators until a `--manual` verdict is given:

- `adh.one_concern_per_commit`
- `adh.final_report_claims`
- `dp07`
- `dp13`
- `dp17a`
