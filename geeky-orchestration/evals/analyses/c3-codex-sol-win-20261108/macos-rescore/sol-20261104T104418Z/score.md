# Score: 20261104T104418Z (c3-minisql)

Plugin `52160ef`, claude-code / gpt-6.1-sol. Scored 2026-11-08T20:06:12Z by `score-run.py`. Workspace: given. Validation blocks fresh rerun. Manual verdicts: none.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 40.0 | P 0.995, S 0.248, D 1.00 |
| Adherence | 0.35 | 72.5 | 37/51 |
| Consistency | 0.20 | 71.4 | DPC 13/19 = 0.684, OC 0.83 |
| Task tier | 0.10 | 65.2 | L_run 8580 ms, L_ref 2678 ms |
| **Composite** | | **60.2** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | yes | Quality <= 40 |
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
| adh.notes.T1 | ✓ | T1-language-foundation.notes.md |
| adh.notes.T2 | ✓ | T2-csv-catalog.notes.md |
| adh.notes.T3 | ✓ | T3-deterministic-formatting.notes.md |
| adh.notes.T4 | ✓ | T4-typed-query-engine.notes.md |
| adh.notes.T5 | ✓ | T5-cli-repl.notes.md |
| adh.notes.T6 | ✓ | T6-contract-acceptance.notes.md |
| adh.task_review.T1 | ✓ | call 256 'Review foundation tasks and phase gate' (prompt) not PASS; call 378 'Re-review corrected foundation phase gate' (prompt) PASS; call 487 'Rev |
| adh.task_review.T2 | ✓ | call 256 'Review foundation tasks and phase gate' (prompt) not PASS; call 378 'Re-review corrected foundation phase gate' (prompt) PASS; call 487 'Rev |
| adh.task_review.T3 | ✓ | call 256 'Review foundation tasks and phase gate' (prompt) not PASS; call 378 'Re-review corrected foundation phase gate' (prompt) PASS; call 487 'Rev |
| adh.task_review.T4 | ✓ | call 487 'Review typed engine task and phase gate' (prompt) PASS; call 602 'Review delivery phase acceptance' (prompt) PASS |
| adh.task_review.T5 | ✓ | call 602 'Review delivery phase acceptance' (prompt) PASS |
| adh.task_review.T6 | ✓ | call 602 'Review delivery phase acceptance' (prompt) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2', 'T3']: reviewer call 378; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T4']: reviewer call 487; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T5', 'T6']: reviewer call 602; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T5 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T6 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.kanban_after_moves | ✗ | 0 lane-move calls; without validate-kanban: none |
| adh.commit_msg.833df55 | ✓ | feat(frontend): implement positioned lexer and AST parser: OK: commit message valid. |
| adh.commit_msg.5351266 | ✓ | feat(catalog): load CSV tables with exact inference and erro: OK: commit message valid. |
| adh.commit_msg.a7e18cd | ✓ | feat(formatting): render deterministic CSV and tables: OK: commit message valid. |
| adh.commit_msg.43bb331 | ✓ | feat(engine): bind and execute the complete typed SQL subset: OK: commit message valid. |
| adh.commit_msg.c47e637 | ✓ | feat(frontend): reject Unicode numeric continuations at lite: OK: commit message valid. |
| adh.commit_msg.fa49a89 | ✓ | feat(cli): deliver byte-exact one-shot and REPL interfaces: OK: commit message valid. |
| adh.commit_msg.03df2fd | ✓ | feat(acceptance): verify the complete minisql contract: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in docs/spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 9f22281..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs |
| adh.one_concern_per_commit | judge? | judge: one concern per commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | judge? | judge: final report claims (D8) |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✗ | no Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | judge? | max 1 concurrent coders; justification needs judge (dp07.justification) |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 652: 0 check-commit run(s) for 1 commit(s); call 653: 0 check-commit run(s) for 1 commit(s); call 655: 0 check-comm |
| dp13 | One concern per commit, per phase | 1 | judge? | judge |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'] |
| dp15 | Run Summary appended | 1 | ✗ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | n/a | no critical finding |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [377]) | 1.00 | 0.5 | 412 | 0.89 | 1 | 82.9 | 1254 | 0.614 |
| T2 | 0 (calls []) | 0.00 | 0.5 | - | 0.00 | 1 | 25.0 | 538 | 0.049 |
| T3 | 0 (calls []) | 0.00 | 0.5 | - | 0.00 | 1 | 25.0 | 308 | 0.028 |
| T4 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 1618 | 0.148 |
| T5 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 695 | 0.063 |
| T6 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 1067 | 0.097 |

## Needs judge

Excluded from their denominators until a `--manual` verdict is given:

- `adh.one_concern_per_commit`
- `adh.final_report_claims`
- `dp07`
- `dp13`
