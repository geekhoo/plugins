# Sources and execution references

Repository source baseline: `8fff98b0f087f148d4f416f512dc9988d61a57aa`, verified locally on 2026-10-26. Run conclusions below are retained historical evidence, not fresh evaluation results.

## Requested external reviews

Read the process review, research and structured capability/source files in full or by their relevant structured sections:

| Source | Location | SHA-256 |
|---|---|---|
| Process recommendations R1–R8 | [recommendations.md](C:/repos/.eval-tools/c0-claudex-001/process-review-20261026/recommendations.md) | `5739ca0576b9bc447f9323e88564ef26b680a8da46eaff5efe32b2bf511b070e` |
| MXC capability research | [research.md](C:/repos/.eval-tools/c0-claudex-001/mxc-capabilities-research-20261026/research.md) | `207883e9e9dce79f81c0c0fa114ccfbc4af8d1fb48dc3b1e7f754a87e5e46e8d` |
| Structured capabilities | [capabilities.json](C:/repos/.eval-tools/c0-claudex-001/mxc-capabilities-research-20261026/capabilities.json) | `029a037e5e66a353e14d2d7a5b5746a5197b28baca2fc351ed96f43329980078` |
| Source inventory | [sources.json](C:/repos/.eval-tools/c0-claudex-001/mxc-capabilities-research-20261026/sources.json) | `2bb866a8aa7a3e6c999d1e44d8ca8028ec5e754d56b340ec83828675800812c0` |

The pasted message is at `C:/Users/gerald.khoo/.codex/attachments/39cb8844-0f48-49b1-8483-b5b7d45053eb/Pasted text.txt`. It summarizes these reports; the reports and repository evidence govern this plan. External review files remain in their original locations. The task briefs retain the necessary decisions if those locations are unavailable later.

## C0 evidence read

- [Comparison](../comparison-report.md), especially outcome, timing/usage, completeness and remaining-limit sections; [structured metrics](../comparison-metrics.json), including unknowns and derivation.
- [Codex report](../codex/report.md):55–135 and [manual verdicts](../codex/manual-verdicts.json):10–63: selected commit, incorrect coverage claim, already-landed evaluator/telemetry repairs.
- [Provider-failure history](../claude-code/report.md):26–96: router/protocol boundary; route repair is not proof of matched backend.
- [Claude initial report](../claude-code/router-fixed/report.md) and [manual verdicts](../claude-code/router-fixed/manual-verdicts.json):14–44: unfinished acceptance and closeout.
- [Claude continuation report](../claude-code/closeout-20261026/report.md), [manual verdicts](../claude-code/closeout-20261026/manual-verdicts.json), [derivation inputs](../claude-code/closeout-20261026/evaluation-inputs.json), [hash erratum](../claude-code/closeout-20261026/review-metadata-erratum.json): completed fix/acceptance, mixed populations and preserved historical limits.

## Implementation anchors at the pinned HEAD

Paths relative to `geeky-orchestration/`:

| Task | Existing surface to reuse |
|---|---|
| T1 | `skills/geeky-implement/SKILL.md:53–75`, its `references/execution-protocol.md:168–205`; `skills/impl-review/SKILL.md:14–26,84,90–96,122,163`; `skills/plan-review/SKILL.md:20,36–64,76–78,100–130`; `evals/prompts/end-to-end.md:21` and `README.md:7–11`; `evals/telemetry/langfuse-evaluators/final_report_complete.judge.json` (five output criteria). |
| T2 | `evals/scripts/run-baseline.ps1:250–345` (retry/finalization); `run-codex-baseline.ps1:219–354` (prepared record/finally/waiver); existing implementation dispatch/phase boundaries (optional timing); external `mxc-sandbox/scripts/host/MxcClaude/Program.cs` (existing timeout-to-124 contract). |
| T3 | `evals/scripts/score-run.py:1068–1147` (`cached_validation`, already checks commit/task/command/source hashes); `parity-eval.py`; `evals/telemetry/langfuse-scores.py:scores/main`; `telemetry.ps1:Save-EvalTelemetry`; existing run/coverage helpers. |

Official MXC sources re-opened during planning: [stable policy](https://github.com/microsoft/mxc/blob/fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2/docs/containment-policy/1.0.0/policy.md), [lifecycle](https://github.com/microsoft/mxc/blob/fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2/docs/container-lifecycle.md). Use the report's pinned release; this plan makes no newest-version claim or cross-platform runtime claim.

## Records and command index

The plan maps all R1–R8 recommendations to a bounded task or explicit deferral. Side-review proposals O1–O3 were delivered in this chat from chat `01a1774f-805a-7672-816e-6d0a23a55b49`; the user requested their incorporation on 2026-10-26. Their underlying source anchors are listed under T1. O1 aligns required findings with terminal verdicts; O2 versions concise final output; O3 reuses planning evidence without dropping coverage. The revised plan retains three tasks and shifts optional clock consumption into T2 to remove T1's old dependency. Task-specific pytest commands are in the briefs; new test filenames are proposals, not already-existing proof. Planning gates: `scripts/validate-planning-folder.py`, `scripts/validate-task-schema.py`, `scripts/validate-kanban.py`, with this folder as `--path`. No real runner command is an automatic next step.

Formal review evidence, input hashes, independent reviewer IDs and exact installed-validator paths are in [review-plan.md](review-plan.md). Use `C:/Python314/python.exe` (pytest 9.1.1 verified 2026-10-26) or a verified equivalent for the task briefs' pytest commands; default PATH Python 3.13 lacks pytest. See the [handoff](handoff.md) for the PowerShell invocation. This is environment feasibility evidence, not an implementation test run.

Stale guidance to reconcile during implementation: retry recommendation in `evals/mxc-litellm-runbook.md` must state authorization/remaining deadline; QUICKSTART must distinguish hard limits from warnings; telemetry README must distinguish presence, coverage and exact readback. Align contradictory verdict/checkpoint instructions in `impl-review`, unconditional resume/final-reread wording in `plan-review`, and heartbeat ordering in the execution protocol. Update the prompt README for the presentation-only final paragraph change and D36 versioning; preserve no-coaching. Existing report criteria already ask for stage outcomes, numeric tests, commits, deviations and evidence, not repeated full reports; retain them where the compact fixture satisfies them. Preserve historical run/publication/preparation records.
