# Score: 20261023T182024Z-5fa13924 (c1-csvledger)

Plugin `bee7b14`, codex / gpt-6.1-sol. Scored 2026-10-23T19:01:04Z by `score-run.py`. Workspace: run.json workspace. Validation blocks re-run. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 95.9 | P 1.000, S 0.725, D 1.00 |
| Adherence | 0.35 | 81.5 | 22/27 |
| Consistency | 0.20 | 78.2 | DPC 16/22 = 0.727, OC 1.00 |
| Task tier | 0.10 | 40.0 | L_run None ms, L_ref 2678 ms |
| **Composite** | | **81.7** | |

## Hard gates

| Gate | Fired | Effect |
|---|---|---|
| hg.oracle | no | Quality <= 40 |
| hg.frozen | no | Adherence <= 30 |
| hg.forbidden_git | no | Adherence = 0 |
| hg.false_completion_claim | manual: No false final completion claim found. Main session.jsonl:643 is supported by actual 76-test/help outputs, independent phase and final verdicts, current matching artifact hashes, and committed clean closeout. Claims do not assert unrun platforms or clean harness diagnostics. Superseded 34/72-test evidence and initial review findings remain disclosed in historical records; complete audit in reviewer-claims-audit.json. | Adherence <= 50 |

## Adherence checks

| Check | Result | Evidence |
|---|---|---|
| adh.planning_folder | ✓ | OK: planning folder valid. 2 task file(s) found. |
| adh.task_schema | ✓ | OK: 2 task file(s) checked, 0 failing. |
| adh.kanban_final | ✓ | OK: 2 task(s) tracked, 2 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=0, Blocked=0, Done=2 |
| adh.dod.T1 | ✓ | DOD_OK: T1 |
| adh.dod.T2 | ✓ | DOD_OK: T2 |
| adh.handoff_batch.T1 | ✗ | no Done move found in the trace |
| adh.handoff_batch.T2 | ✗ | no Done move found in the trace |
| adh.notes.T1 | ✓ | T1-core.notes.md |
| adh.notes.T2 | ✓ | T2-cli.notes.md |
| adh.task_review.T1 | ✓ | call 130 'core_phase_review' (prompt) PASS |
| adh.task_review.T2 | ✓ | call 192 'cli_phase_review' (prompt) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1']: reviewer call 130; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T2']: reviewer call 192; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✗ | Done call -; last code edit None; check-dod runs [(141, True), (142, True)] |
| adh.gates_before_done.T2 | ✗ | Done call -; last code edit None; check-dod runs [(242, True), (243, True)] |
| adh.kanban_after_moves | ✓ | 1 lane-move calls; without validate-kanban: none |
| adh.commit_msg.a8a5f34 | ✓ | feat(core): implement validated ledger and exact money: OK: commit message valid. |
| adh.commit_msg.20ed68b | ✓ | feat(cli): deliver deterministic reports and categorization: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | n/a | no critical impl-review finding |
| adh.frozen_untouched | ✓ | git diff 1aa17d5..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs; reflog clean |
| adh.one_concern_per_commit | ✓ | manual: Reviewed seven commit file groups: c4f054e specification; c34c933 planning; 1aa17d5 plan review; a8a5f34 T1 core; 20ed68b T2 CLI; 663206c sing |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: session.jsonl:643 final report matches independently captured phase/final reviews and actual completed validation. cli_coder rollout-01a16a06- |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✗ | no Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✗ | 3 dispatches, max 0 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | max 0 concurrent coders; justification: T1 core APIs are a real dependency of T2 CLI, so no independent implementation b |
| dp08 | In Progress lane move with timestamp | 1 | ✗ | no In Progress move: ['T2'] |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✗ | failing: ['T1', 'T2'] |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 2 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: Each implementation phase has one functional commit: a8a5f34 T1 core and 20ed68b T2 CLI. Their tests and trackin |
| dp14 | Handoff at each Done move (D82) | 1 | ✗ | failing: ['T1', 'T2'] |
| dp15 | Run Summary appended | 1 | ✗ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | ✓ | manual override: All three original final reviewers re-reviewed corrected product 663206c and returned PASS after C1: su |
| dp17b | Fix commit, prescribed message | 1 | n/a | no critical finding |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 542 | 0.454 |
| T2 | 0 (calls []) | 0.00 | 1.0 | - | 0.00 | 1 | 40.0 | 784 | 0.546 |
