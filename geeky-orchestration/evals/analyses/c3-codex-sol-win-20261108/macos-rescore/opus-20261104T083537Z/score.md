# Score: 20261104T083537Z (c3-minisql)

Plugin `52160ef`, claude-code / claude-opus-5-5. Scored 2026-11-08T20:06:08Z by `score-run.py`. Workspace: given. Validation blocks fresh rerun. Manual verdicts: none.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 40.0 | P 0.995, S 0.184, D 0.80 |
| Adherence | 0.35 | 0.0 | 60/86 |
| Consistency | 0.20 | 72.0 | DPC 13/20 = 0.650, OC 1.00 |
| Task tier | 0.10 | 87.1 | L_run 7627 ms, L_ref 2678 ms |
| **Composite** | | **37.1** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | yes | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | yes | Adherence = 0 |
| hg.false_completion_claim | needs_judge (no cap applied) | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 11 task file(s) found. |
| adh.task_schema | ✓ | OK: 11 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 11 task(s) tracked, 11 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=11 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.dod.T3 | ✓ | DOD_OK: T3 |
| adh.dod.T4 | ✓ | DOD_OK: T4 |
| adh.dod.T5 | ✓ | DOD_OK: T5 |
| adh.dod.T6 | ✓ | DOD_OK: T6 |
| adh.dod.T7 | ✓ | DOD_OK: T7 |
| adh.dod.T8 | ✓ | DOD_OK: T8 |
| adh.dod.T9 | ✓ | DOD_OK: T9 |
| adh.dod.T10 | ✓ | DOD_OK: T10 |
| adh.dod.T11 | ✓ | DOD_OK: T11 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T3 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T4 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T5 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T6 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T7 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T8 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T9 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T10 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T11 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✓ | T1-package-skeleton-errors-test-scaffold.notes.md |
| adh.notes.T2 | ✓ | T2-lexer.notes.md |
| adh.notes.T3 | ✓ | T3-catalog-csv-loader.notes.md |
| adh.notes.T4 | ✓ | T4-runtime-value-operations.notes.md |
| adh.notes.T5 | ✓ | T5-ast-and-parser.notes.md |
| adh.notes.T6 | ✓ | T6-output-formatting.notes.md |
| adh.notes.T7 | ✓ | T7-semantic-analyzer.notes.md |
| adh.notes.T8 | ✓ | T8-executor-and-library-api.notes.md |
| adh.notes.T9 | ✓ | T9-one-shot-cli.notes.md |
| adh.notes.T10 | ✓ | T10-interactive-repl.notes.md |
| adh.notes.T11 | ✓ | T11-acceptance-and-contract-edge-suite.notes.md |
| adh.task_review.T1 | ✓ | call 253 'Phase 1 review (T1-T4)' (description) PASS |
| adh.task_review.T2 | ✓ | call 253 'Phase 1 review (T1-T4)' (description) PASS |
| adh.task_review.T3 | ✓ | call 253 'Phase 1 review (T1-T4)' (description) PASS |
| adh.task_review.T4 | ✓ | call 253 'Phase 1 review (T1-T4)' (description) PASS |
| adh.task_review.T5 | ✓ | call 312 'Phase 2 review (T5, T6)' (description) PASS |
| adh.task_review.T6 | ✓ | call 312 'Phase 2 review (T5, T6)' (description) PASS |
| adh.task_review.T7 | ✓ | call 384 'Phase 3 review (T7, T8)' (description) PASS |
| adh.task_review.T8 | ✓ | call 384 'Phase 3 review (T7, T8)' (description) PASS |
| adh.task_review.T9 | ✓ | call 468 'Phase 4 review (T9-T11)' (description) PASS |
| adh.task_review.T10 | ✓ | call 468 'Phase 4 review (T9-T11)' (description) PASS |
| adh.task_review.T11 | ✓ | call 468 'Phase 4 review (T9-T11)' (description) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1', 'T2', 'T3', 'T4']: reviewer call 253; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T5', 'T6']: reviewer call 312; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P3 | ✓ | phase P3 ['T7', 'T8']: reviewer call 384; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P4 | ✓ | phase P4 ['T9', 'T10', 'T11']: reviewer call 468; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T3 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T4 | ✗ | Done call -; last code edit None; check-dod runs [] |
| adh.gates_before_done.T5 | ✗ | Done call -; last code edit None; check-dod runs [(333, True)] |
| adh.gates_before_done.T6 | ✗ | Done call -; last code edit None; check-dod runs [(333, True)] |
| adh.gates_before_done.T7 | ✗ | Done call -; last code edit None; check-dod runs [(415, True)] |
| adh.gates_before_done.T8 | ✗ | Done call -; last code edit None; check-dod runs [(415, True)] |
| adh.gates_before_done.T9 | ✗ | Done call -; last code edit None; check-dod runs [(498, True)] |
| adh.gates_before_done.T10 | ✗ | Done call -; last code edit None; check-dod runs [(498, True)] |
| adh.gates_before_done.T11 | ✗ | Done call -; last code edit None; check-dod runs [(498, True)] |
| adh.kanban_after_moves | ✗ | 22 lane-move calls; without validate-kanban: [220, 252, 282, 283, 284, 286, 287, 311, 333, 334, 358, 383, 415, 416, 431, 447, 467] |
| adh.commit_msg.49c7a62 | ✓ | feat(foundations): add package skeleton, errors, Result, tes: OK: commit message valid. |
| adh.commit_msg.284508e | ✓ | feat(foundations): add tokenizer implementing contract lexic: OK: commit message valid. |
| adh.commit_msg.cbc6d4c | ✓ | feat(foundations): add catalog, CSV loader and type inferenc: OK: commit message valid. |
| adh.commit_msg.f83b943 | ✓ | feat(foundations): add runtime value ops for arithmetic, 3VL: OK: commit message valid. |
| adh.commit_msg.9675aba | ✓ | docs(tracking): record phase 1 completion for spec-001-featu: OK: commit message valid. |
| adh.commit_msg.716a79f | ✓ | feat(frontend): add AST nodes and recursive-descent parser: OK: commit message valid. |
| adh.commit_msg.0e8ee58 | ✓ | feat(frontend): add CSV and table output formatting: OK: commit message valid. |
| adh.commit_msg.5240d8a | ✓ | docs(tracking): record phase 2 completion for spec-001-featu: OK: commit message valid. |
| adh.commit_msg.3e1e8d1 | ✓ | feat(semantics): add semantic analyzer and bound query plan: OK: commit message valid. |
| adh.commit_msg.9849793 | ✓ | feat(semantics): add staged executor and library API: OK: commit message valid. |
| adh.commit_msg.2a6e585 | ✓ | docs(tracking): record phase 3 completion for spec-001-featu: OK: commit message valid. |
| adh.commit_msg.b44ad6b | ✓ | feat(interfaces): add one-shot CLI and interactive REPL: OK: commit message valid. |
| adh.commit_msg.09d06c9 | ✓ | test(acceptance): add AC1-AC11 and contract edge-case suites: OK: commit message valid. |
| adh.commit_msg.89497bc | ✓ | docs(tracking): record phase 4 completion and run summary: OK: commit message valid. |
| adh.commit_msg.4e4f4a5 | ✓ | docs(tracking): record phase 4 block and implementation run : OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | ✗ | critical findings in impl-review; fix commit: fix(spec): Address 1 required review findings from impl-review |
| adh.frozen_untouched | ✓ | git diff fa99e5f..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✗ | tool-input matches: ['call 285: git worktree remove --force', 'call 333: git worktree remove --force', 'call 415: git worktree remove --force', 'call  |
| adh.one_concern_per_commit | judge? | judge: one concern per commit |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | judge? | judge: final report claims (D8) |
| adh.heartbeat_final | ✗ | .heartbeat status=None |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 4 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | judge? | max 3 concurrent coders; justification needs judge (dp07.justification) |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✗ | call 333: 2 check-commit run(s) for 3 commit(s) |
| dp13 | One concern per commit, per phase | 1 | judge? | judge |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11'] |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 8 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | judge? | judge |
| dp17b | Fix commit, prescribed message | 1 | ✗ | see adh.prescribed_msg.critical_fix |
| dp18 | .heartbeat finalized | 1 | ✗ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 (calls [217]) | 1.00 | 1.0 | 532 | 0.84 | 1 | 96.9 | 365 | 0.071 |
| T2 | 1 (calls [242]) | 1.00 | 1.0 | 355 | 0.90 | 1 | 97.9 | 281 | 0.063 |
| T3 | 1 (calls [239]) | 1.00 | 1.0 | 347 | 0.90 | 1 | 98.0 | 367 | 0.071 |
| T4 | 1 (calls [247]) | 1.00 | 1.0 | 334 | 0.90 | 1 | 98.0 | 407 | 0.075 |
| T5 | 1 (calls [307]) | 1.00 | 1.0 | 435 | 0.87 | 1 | 97.5 | 754 | 0.108 |
| T6 | 1 (calls [298]) | 1.00 | 1.0 | 428 | 0.87 | 1 | 97.5 | 189 | 0.054 |
| T7 | 2 (calls [349, 351]) | 0.75 | 1.0 | 1300 | 0.62 | 1 | 82.4 | 771 | 0.146 |
| T8 | 2 (calls [374, 378]) | 0.75 | 1.0 | 766 | 0.78 | 1 | 85.5 | 697 | 0.139 |
| T9 | 1 (calls [428]) | 1.00 | 1.0 | 1383 | 0.60 | 1 | 91.9 | 322 | 0.067 |
| T10 | 2 (calls [442, 445]) | 0.75 | 1.0 | 1180 | 0.65 | 1 | 83.1 | 225 | 0.093 |
| T11 | 1 (calls [455]) | 0.00 | 1.0 | 932 | 0.73 | 1 | 54.5 | 806 | 0.113 |

## Needs judge

Excluded from their denominators until a `--manual` verdict is given:

- `adh.one_concern_per_commit`
- `adh.final_report_claims`
- `dp07`
- `dp13`
- `dp17a`
