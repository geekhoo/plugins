# Score: 20261023T182024Z-5fa13924 (c1-csvledger)

Plugin `bee7b14`, codex / gpt-6.1-sol. Scored 2026-10-23T21:02:30Z by `score-run.py`. Workspace: given. Validation blocks reused recorded results. Manual verdicts: yes.

| Dimension | Weight | Score | Detail |
|---|---|---|---|
| Quality | 0.35 | 95.9 | P 1.000, S 0.725, D 1.00 |
| Adherence | 0.35 | 100.0 | 28/28 |
| Consistency | 0.20 | 100.0 | DPC 23/23 = 1.000, OC 1.00 |
| Task tier | 0.10 | 77.7 | L_run None ms, L_ref 2678 ms |
| **Composite** | | **96.3** | |

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
| adh.handoff_batch.T1 | ✓ | Done move call 146; handoff naming T1 in call 146 |
| adh.handoff_batch.T2 | ✓ | Done move call 247; handoff naming T2 in call 247 |
| adh.notes.T1 | ✓ | T1-core.notes.md |
| adh.notes.T2 | ✓ | T2-cli.notes.md |
| adh.task_review.T1 | ✓ | call 134 'core_phase_review' (reviewed-process-evidence) PASS |
| adh.task_review.T2 | ✓ | call 196 'cli_phase_review' (reviewed-process-evidence) not PASS; call 196 'cli_phase_review' (reviewed-process-evidence) PASS |
| adh.phase_verdict.P1 | ✓ | phase P1 ['T1']: reviewer call 134; READY TO ADVANCE recorded: handoff.md |
| adh.phase_verdict.P2 | ✓ | phase P2 ['T2']: reviewer call 196; READY TO ADVANCE recorded: handoff.md |
| adh.gates_before_done.T1 | ✓ | Done call 146; last code edit 119; check-dod runs [(145, True), (146, True)] |
| adh.gates_before_done.T2 | ✓ | Done call 247; last code edit 227; check-dod runs [(246, True), (247, True)] |
| adh.kanban_after_moves | ✓ | 6 lane-move calls; without validate-kanban: none |
| adh.commit_msg.a8a5f34 | ✓ | feat(core): implement validated ledger and exact money: OK: commit message valid. |
| adh.commit_msg.20ed68b | ✓ | feat(cli): deliver deterministic reports and categorization: OK: commit message valid. |
| adh.prescribed_msg.spec | ✓ | docs: author feature specification in spec-001-feature |
| adh.prescribed_msg.plan_review | ✓ | chore(plan): Plan review — align documents, fix sequencing |
| adh.prescribed_msg.critical_fix | ✓ | critical findings in impl-review; fix commit: fix(spec): Address 1 critical review findings from impl-review |
| adh.frozen_untouched | ✓ | git diff 1aa17d5..HEAD on frozen files: empty |
| adh.no_forbidden_git | ✓ | no push/--force/--amend/--no-verify in tool inputs |
| adh.one_concern_per_commit | ✓ | manual: Reviewed seven commit file groups: c4f054e specification; c34c933 planning; 1aa17d5 plan review; a8a5f34 T1 core; 20ed68b T2 CLI; 663206c sing |
| adh.no_orchestrator_code_edits | ✓ | none |
| adh.final_report_claims | ✓ | manual: session.jsonl:643 final report matches independently captured phase/final reviews and actual completed validation. cli_coder rollout-01a16a06- |
| adh.heartbeat_final | ✓ | .heartbeat status=done |
| adh.run_summary | ✓ | Run Summary heading in handoff.md |

## Decision points

| # | Decision point | W | Result | Evidence |
|---|---|---|---|---|
| dp01 | Research team: 3 parallel researchers | 1 | ✓ | 3 dispatches, max 3 concurrent |
| dp02 | Spec commit, prescribed message | 2 | ✓ | see adh.prescribed_msg.spec |
| dp03 | PM review artifact | 1 | ✓ | review-development-project-manager.md |
| dp04 | Plan-review subagents, phases 1 and 3 | 1 | ✓ | 2 plan-review dispatches |
| dp05 | Plan-review commit, exact message | 2 | ✓ | see adh.prescribed_msg.plan_review |
| dp07 | Batching <=3 parallel, justification noted | 1 | ✓ | max 2 concurrent coders; justification: T1 core APIs are a real dependency of T2 CLI, so no independent implementation b |
| dp08 | In Progress lane move with timestamp | 1 | ✓ | no In Progress move: none |
| dp09 | Task review, per task | 2 | ✓ | not reviewed: none |
| dp10 | DoD + kanban gates before Done (D86) | 2 | ✓ | failing: none |
| dp11 | Phase verdict from a phase review | 2 | ✓ | failing phases: none |
| dp12 | Commit gate ran before each commit (D79) | 1 | ✓ | 2 geeky-implement commits each preceded by check-commit |
| dp13 | One concern per commit, per phase | 1 | ✓ | manual: Each implementation phase has one functional commit: a8a5f34 T1 core and 20ed68b T2 CLI. Their tests and trackin |
| dp14 | Handoff at each Done move (D82) | 1 | ✓ | failing: none |
| dp15 | Run Summary appended | 1 | ✓ | see adh.run_summary |
| dp16 | Final review: 3 domain reviewers | 1 | ✓ | 3 impl-review reviewer dispatches |
| dp17a | Re-review after a critical fix | 1 | ✓ | manual: All three original final reviewers re-reviewed corrected product 663206c and returned PASS after C1: subagents/r |
| dp17b | Fix commit, prescribed message | 1 | ✓ | see adh.prescribed_msg.critical_fix |
| dp18 | .heartbeat finalized | 1 | ✓ | see adh.heartbeat_final |

## Task tier

| Task | attempts | V | R | d (s) | T | D | s | LOC | w |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 3 (calls [107, 109, 110]) | 0.50 | 1.0 | 198 | 0.83 | 1 | 76.7 | 542 | 0.579 |
| T2 | 1 (calls [163]) | 1.00 | 0.5 | 360 | 0.70 | 1 | 79.0 | 784 | 0.421 |
