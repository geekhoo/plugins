# C3 Codex Sol/high on Windows MXC, 8 November 2026

Scored 9 November 2026 by the operator. This is the first fresh Windows C3 Codex run to finish in one attempt with runner diagnostics passing and live telemetry. It isn't reference-eligible. Two factual metrics are published to Langfuse under a separate scope; no composite is.

## Run

| Field | Value |
|---|---|
| Run | `20261108T150341Z-463d8062`, one authorized attempt, no recoveries |
| Evidence | `C:\Repos\c3-sol-mapfix-20261107\geeky-orchestration\evals\baselines\c3-minisql\20261108T150341Z-463d8062\` (local, uncommitted); launch folder `C:\Repos\c3-sol-live-20261108-01` |
| Harness, model | Codex 0.164.0 in MXC, `chatgpt/gpt-6.1-sol` high for every role, LiteLLM through the local mapping bridge, 200k context |
| Plugin, prompt | `eed7230`; prompt SHA-256 `124eba9b…`, the canonical LF value |
| Budget | 21,600 s hard wall, 1,800 s closeout reserve |
| Wall time | 6,163 s contestant, 120 s finalization |
| Tokens | 31.24M across 22 threads, 15.11M of it cached input; 410 model calls; ceiling 50M, informational |
| Final head | `ef2fe4e`, clean; 10 commits after the seed |
| Runner verdict | `exit_reason: completed`, `diagnostics_passed: true`, `runtime_parity_verified: true`, `reference_eligible: false`, `workflow_acceptance: not-established` |
| Langfuse session | `c3-minisql/codex/20261108T150341Z-463d8062`, environment `mxc-win`, sent live |

## Scores

| Score | Composite | Quality | Adherence | Consistency | Task tier |
|---|---|---|---|---|---|
| Frozen QACT with judge verdicts ([score.md](score.md)) | **74.8** | 88.9 | 72.2 | 72.2 | 40.0 |
| Parity `parity-eval.py` with judge verdicts ([parity.json](parity.json)), diagnostic only | 86.01 | 88.86 | 96.23 | 63.16 | |

The frozen score is `score-run.py` at `main` (`8410dad`, the same scorer bytes as `eed7230`) with no scorer changes and the default size reference. It reran every validation block with `C:\repos\.eval-tools\agent-py` against a clone of `solution.bundle`. The five judge items and the hard-gate judgment are in [manual.json](manual.json). All of them pass.

**Quality 88.9.** The oracle passes 182 of 182 and skips 1, stable over 3 runs (the skip is the case-insensitive filesystem test). All task validation commands pass at their task commits. The contestant's suite reruns at `ef2fe4e` as 955 passed, 1 skipped, which matches the Run Summary. The size term S is 0.257: 1,167 non-test LOC against the 300-line default reference.

**Why Adherence and Consistency are low.** This is the same parser gap as the 7 November run. `codex-process.py` doesn't read board moves made with `apply-patch` inside `exec_command`, so it sees no In Progress or Done moves. It also misses the coder dispatches, which leaves the task tier at 40.0 with zero attempts. Thirteen Adherence checks and three decision points fail on missing evidence:

- `adh.handoff_batch` and `adh.gates_before_done`, for each of T1–T6
- `adh.kanban_after_moves`
- `dp08`, `dp10` and `dp14`

`dp12` also fails. The scorer finds no `check-commit` run before the spec commit at call 212. In the transcript, the first commit-gate call (`session.jsonl:209`) comes after that commit (`:187`). This record doesn't establish whether a hook ran the gate.

## Real defects

1. **Spec commit message.** `docs(spec): author minisql feature specification` isn't the prescribed message, so `dp02` and `adh.prescribed_msg.spec` fail. The 7 November run used the same subject.
2. **Fix commit message.** `fix(spec): Address 1 required review findings from impl-review` doesn't match the prescribed critical-fix form, so `dp17b` fails.
3. **T5/T6 Done before DoD.** At `session.jsonl:1249` (16:23:39 UTC) a single command moved T5 and T6 to Done and then tried to run DoD and kanban validation. The patch failed on a stale heartbeat line, but the board edit had already gone through, and its guard exited before the checks ran. A readback at `:1263` shows both tasks in Done. `DOD_OK` for both appears only at `:1272` (16:24:00). The Run Summary calls this a repaired stale heartbeat patch. The frozen score already fails these checks on missing evidence, so the defect doesn't change it. The parity scorer passes `dp10` anyway.

The final review found one required defect (F1, large decimal integers). Commit `4244b5c` fixed it, and `/root/final_f1_rereview` re-reviewed both affected domains with PASS WITH WARNINGS. Overall, impl-review passes. The bridge logged 420 requests: 410 `ok` and 10 `upstream_transport_error` (`ConnectionAbortedError` after streaming began). The run recovered from those and completed.

## Langfuse

Telemetry ran live this time. Host readback ([session-summary.json](langfuse/session-summary.json)) shows 22 traces and 1,169 observations: 418 generations, 729 tool calls and 22 agents. Nothing was truncated or duplicated. The user IDs are `codex/orchestrator`, `codex/coder`, `codex/reviewer` and `codex/unknown`. Langfuse generation totals sum to 31,724,095 tokens against the analyzer's 31,236,183. The two counts aren't reconciled.

**Parity is diagnostic only.** [parity-eval.py:32](../../scripts/parity-eval.py) finds the spec stage by its exact prescribed subject, and defect 1 breaks that again. Spec-research gets no end time, geeky-plan gets no start, and plan-review collapses to zero width at 15:21:03. As a result `dp01` and `dp04` count 0 dispatches and the order term is 0. The implementation and review stages do get bounds this time, which is why parity Adherence is 96.23 here against 47.17 on 7 November. Judge IDs use the `a.` prefix ([manual-parity.json](manual-parity.json)). The 86.01 isn't comparable with the macOS C3 pair (Opus 36.84, Sol 76.67).

**Published.** Following the 7 November pattern, two factual session scores went out under scope `c3-codex-sol-source-reviewed-20261108-463d8062-v1`, evaluator `c3-factual/1`. Exact Scores v3 readback verified both ([publication-result.json](langfuse/publication-result.json)):

| Score | Value | ID |
|---|---|---|
| `oracle_pass_rate` (config `fe4ba7b1…`) | 1.0 | `a899f3c9ac74bce2c7b4a56deac02a0c` |
| `c3_quality_qact_v1` | 88.86 | `95d7dc254c75cb52474b7e36c99267dc` |

[prepare.py](langfuse/prepare.py) builds the payload offline. [publish.ps1](langfuse/publish.ps1) checks for existing IDs, writes a claim file, posts both, and reads them back. The QACT 74.8 and parity 86.01 composites aren't published. No historical score was touched.

## Comparison

| | 7 Nov `9e506686` | 8 Nov `463d8062` |
|---|---|---|
| Attempt | crash plus recovery continuation | one clean attempt |
| Plugin, prompt | `6567fa3`, LF | `eed7230`, LF `124eba9b` |
| Wall time | about 6,613 s | 6,163 s |
| Tokens | 38.41M | 31.24M |
| Oracle | 182/182, 1 skip | 182/182, 1 skip |
| Frozen QACT | 76.0 (Q 89.1, A 73.6, C 77.1, T 36.4) | 74.8 (Q 88.9, A 72.2, C 72.2, T 40.0) |
| Diagnostics | failed (`skill_invoked`) | passed |
| Telemetry | host replay | live |
| Final review | PASS round 1 | NEEDS FIXES, then PASS after F1 |

The frozen composites compare because the scorer, rubric and reference are the same.

## Against the macOS C3 pair

The macOS pair ran Claude Code 2.1.318 on plugin `52160ef` and Python 3.9.6, and published parity scores (Opus 36.84, Sol 76.67). To put all three runs on one rubric, I rescored both with the same frozen `score-run.py`, the default 300-line reference, validation reruns on agent-py, and no judge verdicts. The evidence came from `origin/opus/macos-mxc-c0`, and the outputs are in [macos-rescore/](macos-rescore/). This run's matching no-judge score is in [strict/](strict/).

| Frozen QACT, no judge verdicts | Mac Opus `20261104T083537Z` | Mac Sol `20261104T104418Z` | Win Codex Sol `463d8062` |
|---|---|---|---|
| Composite as scored | 37.1 | 60.2 | **73.6** |
| Quality, as scored | 40.0 (oracle gate) | 40.0 (oracle gate) | 88.9 |
| Quality, before the gate | 84.4 (P 0.995, S 0.184, D 0.80) | 88.3 (P 0.995, S 0.248, D 1.00) | 88.9 (P 1.000, S 0.257, D 1.00) |
| Adherence | 0.0 (forbidden-git gate); 69.8 before it | 72.5 | 71.2 |
| Consistency | 72.0 | 71.4 | 68.0 |
| Task tier | 87.1 | 65.2 | 40.0 (no latency measured) |
| Composite, both gates removed | 77.1 | 77.1 | 73.6 |
| Non-test LOC | 1,630 | 1,210 | 1,167 |
| Oracle | 181 passed, 1 failed, 1 skipped | 181 passed, 1 failed, 1 skipped | 182 passed, 1 skipped |

**Quality.** Both Mac runs are capped at 40 because `test_ac1_import_scan` needs Python 3.10+, so the cap comes from the host. Before the gate, Mac Sol and this run are within 0.6 points of each other. Opus loses on size and on D: T11's `python -m pytest -q` fails at its task commit in the Windows rerun. I didn't investigate that failure.

**Adherence and Consistency.** All three runs fail the same board-move checks: `adh.gates_before_done` and `adh.handoff_batch` for each task, `adh.kanban_after_moves`, and decision points `dp08`, `dp10`, `dp12` and `dp14`. So the scorer misses board moves on the Claude Code runs too. The Codex parser gap described above holds, but it doesn't push this run down relative to the Mac pair. What separates the runs:

- **This run:** the spec and fix commit messages aren't the prescribed ones (`dp02`, `dp17b`).
- **Mac Sol:** handoff has no Run Summary (`dp15`). It had no critical findings, so the fix message check doesn't apply.
- **Mac Opus:** it ran `git worktree remove --force` five times, which fires the forbidden-git gate. It also left no final heartbeat (`dp18`) and used the same non-prescribed fix subject as this run.

**Task tier doesn't compare.** The Codex process data has no per-task attempt latency, so T falls back to 40. The Mac runs have measured latency.

**Bottom line.** As scored, this run leads at 73.6 against 60.2 and 37.1, and most of that gap is the Mac host's Python. With both gates removed the Mac pair sits at 77.1, and this run is 3.5 points behind. Task tier alone accounts for 2.5 to 4.7 of those points, and it isn't measured on Codex. On the checks that do compare, the three runs land within a few points of each other. Each configuration has one run, and the harness, plugin, host and route all differ, so this doesn't rank the models.

## Other evaluation

`C:\Repos\c3-fresh-eval-20261109-01\report.md`, written by an earlier agent, gives 90.34. That figure passes `--ref-loc 1800`, which makes S 1.0 and Quality 100. It also uses a reconstructed process sidecar. The frozen rubric's default reference is 300 lines, so 90.34 doesn't compare with 76.0 or 74.8. Its findings on T5/T6 ordering and the bridge errors agree with this record.

## Files

| File | Content |
|---|---|
| [score.md](score.md), [score.json](score.json) | frozen QACT output with judge verdicts |
| [manual.json](manual.json) | judge verdicts and their evidence |
| [parity.json](parity.json), [manual-parity.json](manual-parity.json) | diagnostic parity output and its judge verdicts |
| [langfuse/session-summary.json](langfuse/session-summary.json) | host readback of the live session |
| [langfuse/](langfuse/) prepare, publish, claim, readback and result files | the two published scores |
| [strict/](strict/) | frozen QACT without judge verdicts, for the macOS comparison |
| [macos-rescore/](macos-rescore/) | frozen QACT of both macOS C3 runs, no judge verdicts |
