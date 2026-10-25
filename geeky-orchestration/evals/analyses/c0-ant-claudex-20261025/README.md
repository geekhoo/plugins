# C0 on ant-claudex, both harnesses: parity evaluation (2026-10-25)

The latest C0 run of each harness on LiteLLM `ant-claudex` (`auto_router/complexity_router`), in Linux MXC (mxc-sandbox 0.2.1). Both used plugin `434ef7e`, the canonical prompt, runner-default reasoning and telemetry to Langfuse (environment `mxc`). They were scored with `scripts/parity-eval.py`, the same harness-neutral evaluator as [the ant-claude pair](../c0-ant-claude-20261025/README.md); its Method section applies here.

The first Claude attempt (`baselines/c0-wordstat/20261025T052742Z`) is excluded. LiteLLM rejected its requests after 2.5 minutes (`user: requires a native Responses target`) before the router was fixed.

## Result

| | Codex (`20261025T052721Z-e0b9caff`) | Claude (`20261025T061414Z`) |
|---|---:|---:|
| **Parity composite** | **97.78** | **94.43** |
| Quality | 94.29 | 93.19 |
| Process adherence | 100.00 (34/34) | 92.50 (37/40) |
| Process consistency | 100.00 | 100.00 |
| Oracle | 13/13, stable over 3 | 13/13, stable over 3 |
| Exit | completed, 3690 s | **timeout at the 5400 s ceiling** |
| Langfuse coverage | complete (1010 obs) | complete (657 obs) |

Both harnesses ran all five stages with the prescribed reviewers, gates and commit messages. Neither orchestrator edited code itself, and neither rewrote history. The gap is completion:

- **Claude did not finish.** It reached the final `impl-review`, where its three reviewers returned PASS, PASS WITH WARNINGS and PASS WITH WARNINGS. While its fix worker was addressing the warnings, the 90-minute ceiling stopped it. That fails three checks: `a.run_completed`, `a.work_committed` (`review-impl.md` untracked, `handoff.md` modified) and `a.final_report_claims` (no final report to verify).
- **Quality.** Claude's code is smaller (74 vs 113 non-test LOC; reference 70). Two of its T4 validation commands point at a temp `sample.txt` that does not exist at that commit, so 11/13 validations rerun cleanly against Codex's 6/6.
- **Codex** disclosed one deviation: its PM-review subagent stalled, and it used the documented direct-review fallback. It also retried one coder spawn the runtime had rejected for an uppercase name.

Efficiency (not in the composite):

| | Codex | Claude (until stopped) |
|---|---:|---:|
| Wall time | 3690 s | 5400 s (ceiling) |
| Tokens, from Langfuse (total / cached reads / output) | 21.9M / 20.3M / 174k | 11.7M / 10.9M / 87k |
| Reasoning tokens | 146k | none reported |
| Median generation latency | 1.3 s | 9.7 s |
| Commits | 7 | 8 |

## Confounds

1. **Different backends per request.** `ant-claudex` routes each request by complexity, so the two harnesses' differently shaped requests can reach different models. The 7x latency gap suggests they often did. Same model *name*, not necessarily the same model.
2. **Reasoning.** Both ran at runner defaults: Codex `high` (146k reasoning tokens), Claude Code's default (none reported for an unrecognised model).
3. **One run each**, and Claude's ended at the time ceiling. A run with a higher ceiling would show whether it completes.

## Evaluator changes made for this comparison

- `scripts/codex-trace.py` accepts a child the parent interrupted and a spawn the runtime rejected. Before, score-run refused this whole Codex trace. The main thread must still finish.
- `scripts/parity-eval.py` adds `a.run_completed` and `a.work_committed`, applied to every run. The ant-claude pair passes both, so its scores are unchanged; its check counts move to 35/35 and 34/35.
- Stage boundaries: Codex re-reads the plan-review skill as soon as it dispatches the PM reviewer, which opens its plan-review window about 12 minutes early. Only the PM-review follow-up shifts, which is not counted, so no score moves.

## Langfuse

Ten session scores on each run (`parity_composite`, `quality`, `process_adherence`, ...), posted by `telemetry/langfuse-scores.py`:
- Codex session `01a17187-2819-7663-88d6-51b9021b2415`
- Claude session `e05aeb9e-7dc6-4c24-a781-0ce7b83c9393`
