# MXC documentation and current state

Reviewed on **3 November 2026 (Asia/Singapore)** at `main`, HEAD `ea94635d2f76918f4a01699aea3e356f90954033`. This checkout already contained uncommitted source changes and local evaluation evidence. HEAD alone does not identify those working changes.

Later addition, 5 November 2026: the [macOS MXC findings](../../geeky-orchestration/evals/macos-mxc-findings.md) cover runs kept on branch `opus/macos-mxc-c0` as a point of reference for C3, and [decision D112](../../geeky-orchestration/docs/agent-eval-decisions.md) records that ruling. The review below is unchanged.

## Where testing began

| Point | Git or retained evidence | Time in Singapore |
|---|---|---|
| First MXC host implementation | `554c50acb90ecf15f161dc8f88e9ad12c8f015eb` | 20 October 2026, 13:16:35 |
| Baseline procedure | `3a1d8aa3fed469de1294a6ca8639a5506b5418b1` | 20 October 2026, 15:11:57 |
| Claude/MXC baseline runner | `01846e963e817977711e6bc2ef795b25d7c2f17a` | 20 October 2026, 18:54:10 |
| First retained C1 contestant run | `20261020T114232Z`, plugin `24c4e6daa6199be8196970ece35c79d6f184e8a4` | 20 October 2026, 19:42:34 |

The first run's [`run.json`](../../geeky-orchestration/evals/baselines/c1-csvledger/20261020T114232Z/run.json) records `started_utc` as `2026-10-20T11:42:34.6757449Z`. The [first C1 comparison](../../geeky-orchestration/evals/baselines/c1-csvledger/comparison-20261021T0530Z.md) identifies the model, harness and MXC isolation. Earlier case kits and evaluation design were committed that morning, before the host existed.

The documentation review starts at the parent of the first host commit, `c957a431e4e1144b4280cee92d15bb90646e21ee`, and follows changes through the reviewed HEAD plus existing working changes. The inventory holds **459 documentation paths**. The original scope had 457: 90 existing guides, skills and agent documents; 359 historical evidence paths; and eight deleted command wrappers. Two older canonical agent documents were added so their source locators could remain consistent across all six agents. Six Codex TOML registrations were checked alongside the Markdown projections.

## Source behavior checked during the refresh

| Area | Current source behavior | Guide |
|---|---|---|
| Workflow gates and phase review | DoD checks run after the task enters Done, in the same step; failure moves it back out. Phase review covers every task and the last phase. More than four tasks, or an oversized diff, requires smaller reviewer dispatches under the existing execution protocol. | [End-to-end workflow](../../geeky-orchestration/docs/end-to-end-workflow.md) |
| Workflow budget | The implementation target is cumulative and advisory: 75% of `(hard wall budget - closeout reserve)`. Deadline and reserve can report remaining time; a stage target additionally needs the total hard wall budget. Required gates remain required. | [Implementation skill](../../geeky-orchestration/skills/geeky-implement/SKILL.md) |
| MCP launcher | The Codex plugin manifest starts `uv run --with "mcp>=1.2.0" python server.py` with `cwd: "./mcp"`. | [MCP guide](../../geeky-orchestration/mcp/README.md) |
| Codex runner | The runner defaults to `gpt-6.1-sol`/high. Worker settings inherit the main settings when no worker override is supplied. Run profiles set request and stream retries to two; native probes keep zero retries. | [Adapter guide](../../geeky-orchestration/evals/adapters/codex/README.md) |
| Native compatibility | The committed proxy lowers `agent_message` into framed user input and handles plaintext collaboration. Profile generation and the bridge server had additional local modifications at review time. Source configuration alone does not prove delivery during a particular live run. | [C0 readiness](../../geeky-orchestration/evals/c0-readiness.md) |
| Codex guard | The adapter bridge invokes the frozen-artifact guard in warn mode for recognized patch paths. Shell edits bypass that bridge. | [Adapter guide](../../geeky-orchestration/evals/adapters/codex/README.md) |
| Sandbox isolation | Private Claude config persists. The request enables default environment inheritance; explicit environment values are available to the workload. Windows host loopback is separately opt-in for headless runs. Git Bash hook failures and successful explicitly configured PowerShell hooks are dated observations. | [Sandbox guide](../../mxc-sandbox/README.md) |
| Score delivery | Publication requires an explicit evaluation-inputs scope. Available metrics are published; missing values are omitted. POST alone leaves delivery pending until exact Scores v3 readback succeeds. | [Evaluator guide](../../geeky-orchestration/evals/telemetry/langfuse-evaluators/README.md) |

The source references and review actions are in [references.md](references.md) and [findings.md](findings.md). The [case documents](../../geeky-orchestration/evals/cases/) retain their requirements. A C0 specification's broad telemetry requirement does not mean every runner mode collects telemetry: preparation-only and telemetry-disabled execution remain distinct.

## Later local campaign records

The following evidence is in ignored `outputs/` folders on the reviewed machine. It is not included in a fresh clone. These are retained local assessments and publication readback records, inspected without rerunning contestants, recomputing scores or querying Langfuse. Original tracked closeout records retain their earlier state.

| Campaign | Retained outcome and limitation | Local evidence |
|---|---|---|
| C0 Codex/Luna | The tracked closeout initially withheld parity. A later source-reviewed rescore records **95.18**, with publication/readback. The later **97.41** attribution diagnostic was not published as a replacement. Lifecycle acceptance is a separate field. | [Publication result](../../outputs/c0-native-run-20261031/rescore-20261031/publication-result.json), [atlas data](../../outputs/workflow-atlas-20261101/atlas-data.json) |
| C0 Codex/DeepSeek | Full run `20261031T135148Z-897805b1` followed the earlier smoke. Review PASS with warning and oracle 13/13 over three runs; strict comparative parity remained withheld. The qualification waiver belonged to that attempt. | [Run record](../../outputs/c0-deepseek-responses-openai-20261031/README.md), [lessons](../../outputs/c0-deepseek-responses-openai-20261031/lessons-20261101.md) |
| C1 Codex/DeepSeek and normalized campaign | Review PASS after a fix and passing oracle. Telemetry was disabled during execution and replayed later. Reviewed parity depends on explicit judgments; the campaign reports 27 separately scoped score publications with readback and preservation of prior scores. Conditions differ across runs. | [Campaign report](../../outputs/c1-deepseek-20261101-4e7db6a1/report.md), [publication record](../../outputs/c1-deepseek-20261101-4e7db6a1/normalized-c1-v4/publication-20261101-6ac197b2/README.md) |
| C2 Codex/Luna | Final review PASS and oracle 136/136 over three runs. Local records retain provisional reviewed Quality **96.87** and its publication/readback. Signal-coverage and environment-equivalence limits remain; no normalized composite is established. | [Evaluation](../../outputs/c2-luna-live-20261102-8f7362c1/evaluation/report.md) |
| C2 Codex/DeepSeek | Initial bridge-mapping crash with oracle 42/136. An authorized same-session wire-mode continuation later recorded review PASS with warnings, 177 tests and final oracle 136/136 over three runs. Preserve the initial failure and continuation separately. No normalized composite is established. | [Evaluation](../../outputs/c2-deepseek-live-20261102-39b6e2d4/evaluation/report.md) |

The C1/C2 reports retain `workflow_acceptance: not-established` and reference/runtime parity limitations where recorded. A review verdict, oracle total or published metric does not fill those fields. The [normalized C1 workflow](../../geeky-orchestration/evals/normalized-c1.md) and its scorer are untracked local additions at this review point.

[C2 diagnostic verification](../../outputs/c2-fix-verification-20261102/) records experiments with size references and coverage attribution. Those saved outputs do not establish that a candidate repair is present in the current source. Consult the current scorer and coverage adapter before applying their conclusions to another campaign.

## Review record

- [Inventory](inventory.csv): every path's last Git commit and author date, initial dirty state, review scope and action. These are pre-refresh Git dates; uncommitted edits have no new commit date.
- [Codex registrations](registrations.csv): six TOML registrations checked with the canonical agent source.
- [Findings](findings.md): stale documents, corrections and owning source evidence.
- [Kanban](kanban.md), [handoff](handoff.md) and [references](references.md): completion, validation and reproducible source pointers.

Eight Terra 6.1 agents reviewed disjoint batches read-only. The parent collated their reports and applied changes serially. Six canonical agents received portable source locators, and all 30 harness registrations were regenerated; the implementation orchestrator also received the phase-review summary correction. Historical captures were inventoried with selected index inspection, not re-audited in full; case assertions were traced by requirement family without executing oracles. Existing code changes, raw run evidence and score files were preserved. The review itself grants no run or publication authority. The owner subsequently authorized small local documentation commits, explicitly excluding unrelated changes and push.
