# C0 on ant-claude, both harnesses: parity evaluation (2026-10-25)

First complete end-to-end C0 runs in Linux MXC (mxc-sandbox 0.2.1). Both used LiteLLM `ant-claude` (`mimo-v2.6-flash`), the same plugin (`434ef7e`), the same canonical prompt (sha256 `7c3ed1b8…`) and ran concurrently on one host. Telemetry went to Langfuse (environment `mxc`).

## Result

| | Codex run 6 | Claude run 4 |
|---|---:|---:|
| **Parity composite** | **98.75** | **59.15** (96.93 without the hard gate) |
| Quality (score-run) | 96.80 | 94.96 |
| Process adherence | 100.00 (35/35) | **0.00** hard gate; 97.14 uncapped (34/35) |
| Process consistency | 100.00 | 100.00 |
| Oracle | 13/13, stable over 3 | 13/13, stable over 3 |
| Judge items (5) | all pass | all pass |
| Langfuse coverage | complete (659 obs) | complete (828 obs) |

Both harnesses ran every stage and gate the workflow prescribes, with independent reviewers at each phase. They differ in one rule and one quality detail:

- **Claude rewrote a commit.** During `geeky-plan` it ran `git reset --soft HEAD~1` to unstage `review-plan.md` and recommitted the planning package. That is amend by other means, so the forbidden-git hard gate (D24, reflog `reset:`) sets adherence to 0. It is the only process failure on either side.
- **Quality:** Claude's code is smaller (81 vs 89 non-test LOC; reference 70), but one T1 validation command (`python -m wordstat --json /tmp/sample.txt`) depends on a temp file that is not created at that commit, so 5/6 validations rerun cleanly against Codex's 7/7.

Efficiency (not in the composite):

| | Codex | Claude |
|---|---:|---:|
| Wall time | 3383 s | 4175 s |
| Tokens (input / cached / output) | 20.8M / 20.1M / 187k | 16.7M / 15.3M / 425k |
| Median generation latency (Langfuse) | 3.5 s | 7.2 s |
| Commits | 9 | 12 |
| Provider refusals resumed | 0 | 1 |

## Method

`score-run.py` reads each harness's raw transcript through its own parser. Its Codex parser expects Windows PowerShell board edits and a delegated implement orchestrator; on Linux, Codex used bash and ran `geeky-implement` itself, so ~20 process checks scored "not found" (score-run composites: Codex 68.26, Claude 55.77, **not comparable**). Its task-tier latency also exists only for Claude.

`scripts/parity-eval.py` evaluates both runs through one code path:

- **Quality** from score-run (oracle, size, validation reruns: artifact-based, so already neutral).
- **Process** from the Langfuse observations both tracers emit in one shape, the git history and the final artifacts, rechecked with the plugin's own gate scripts.
- **Stage boundaries** from the reflog, which survives Claude's history rewrite. A stage starts at the earlier of its commit and the first invocation of its skill after the previous commit. Reads of several stages' skills within 5 s count as pre-reading: Codex reads every SKILL.md up front, and Claude commits a stage late.
- **Composite** = (0.35 Q + 0.35 A + 0.20 C) / 0.90, score-run's weights without the latency-based task tier.
- **Judge items** (one concern per commit, final-report claims, false completion claim, batching justification) were checked by hand against the workspaces under one rubric. They are in `*/manual-verdicts.json`.

Every failing check, and the sensitive passes (orchestrator code edits, stage windows), were checked against the raw evidence before scoring. Three bugs found that way were fixed:
- parity-eval: empty Codex implement window and wrong phase map;
- parity-eval: zero-length Claude plan-review window;
- score-run: missed Claude's docs-only critical-fix commit.

## Confounds (what is not equal)

1. **Reasoning effort.** Codex ran with `reasoning = high` for the main thread and workers (62k reasoning tokens). Claude ran at default with 0 thinking tokens: Claude Code does not recognise `ant-claude` and requested no thinking budget. This is the largest setup difference; equalise it (e.g. `MAX_THINKING_TOKENS` for Claude, or Codex at its default effort) before reading quality or efficiency gaps as harness effects.
2. **One run each.** No variance estimate (D60 wants three runs per configuration).
3. **Provider refusal.** Claude was stopped once by the provider's intermittent content filter and resumed (`interventions = 1`). Codex was not.
4. **Auth path.** Claude run 4 sent the LiteLLM key as `ANTHROPIC_AUTH_TOKEN`, a pre-fix setting; it does not change the model.
5. **Harness-native differences** are the subject of the comparison: system prompts, tools, Claude's `Agent` vs Codex's `spawn_agent`, and the `general-purpose` role registered for Codex.

## Langfuse

- **Session scores:** 10 per run on each session, with one score config each (`parity_composite`, `quality`, `process_adherence`, `process_adherence_uncapped`, `process_consistency`, `oracle_pass_rate`, `forbidden_git_operation`, `harness_coverage_complete`, `provider_refusals`, `final_report_claims_verified`), posted by `telemetry/langfuse-scores.py`.
- **Evaluators:** see `telemetry/langfuse-evaluators/`. The LLM judge `final_report_complete` and its rule exist but are paused/disabled until an LLM connection is configured. The `forbidden_git_operation` code evaluator needs code evaluation enabled on the server.

## Files

- `*/score.json`, `*/score.md`: score-run with the judge verdicts (harness-specific; see Method).
- `*/parity.json`: the parity evaluation with every check and its evidence.
- `*/manual-verdicts.json`: judge verdicts.
- Langfuse observations (115 MB) are not committed; refetch with `telemetry/langfuse-run.py --full`.
