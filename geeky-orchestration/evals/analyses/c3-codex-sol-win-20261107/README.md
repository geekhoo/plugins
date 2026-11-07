# C3 Codex Sol/high on Windows MXC, 6–7 November 2026

Scored 8 November 2026 by the operator. This is the first Windows C3 Codex run that finished the workflow. It isn't reference-eligible. Two factual metrics are published to Langfuse under a separate scope; no composite is.

## Run

| Field | Value |
|---|---|
| Run | `20261107T150925Z-9e506686`, a session continuation of `20261106T165015Z-21d7f10f` |
| Evidence | `C:\Repos\c3-sol-mapfix-20261107\geeky-orchestration\evals\baselines\c3-minisql\20261107T150925Z-9e506686\` (local, uncommitted) |
| Recovery record | `C:\Repos\c3-sol-recovery-20261107-4f28b9c1\final-report.md` |
| Harness, model | Codex 0.164.0 in MXC, `chatgpt/gpt-6.1-sol` high for every role, LiteLLM through the local mapping bridge |
| Plugin | `6567fa3` |
| Wall time | parent 3,708 s (crashed on `bridge_mapping_error`) plus recovery 2,905 s, about 6,613 s of the 21,600 s budget |
| Tokens | 38.41M across 22 threads, 15.21M of it cached input; ceiling 50M, informational |
| Final head | `f5d6602`, clean; 5 recovery commits, 10 after the seed |
| Runner verdict | `exit_reason: diagnostics-failed`, `reference_eligible: false`, `runtime_parity_verified: false`, `telemetry.enabled: false` |
| Langfuse session | `c3-minisql/codex/20261107T150925Z-9e506686` on `langfuse.markefin.com`, environment `mxc-win`, replayed from the host on 8 November |

## Scores

| Score | Composite | Quality | Adherence | Consistency | Task tier |
|---|---|---|---|---|---|
| Frozen QACT with judge verdicts ([score.md](score.md)) | **76.0** | 89.1 | 73.6 | 77.1 | 36.4 |
| Evidence-corrected, not comparable | 87.0 | 89.1 | 96.2 | 92.4 | 36.4 |
| Parity `parity-eval.py` with judge verdicts ([parity.json](parity.json)), diagnostic only | 59.53 | 89.06 | 47.17 | 29.47 | |

The frozen score is `score-run.py` at `main` with no scorer changes. Judge verdicts for the four judge items are in [manual.json](manual.json), and all four pass. The rerun used `C:\repos\.eval-tools\agent-py`, the runner's own interpreter. With the host Python 3.13, which has no pytest, Quality drops to 74.1 because every validation command fails.

**Quality 89.1.** The oracle passes 182 of 182 and skips 1, stable over 3 runs (the skip is the case-insensitive filesystem test). All 9 per-task validation commands pass at their task commits. The size term S is 0.271: 1,108 non-test LOC against the 300-line reference.

**Why Adherence and Consistency are low.** `codex-process.py` reads board moves only as literal PowerShell `.Replace('## Done', …)` edits. This run moved cards with `codex.exe --codex-run-as-apply-patch` inside `exec_command`, so the scorer sees no In Progress or Done moves at all. Thirteen checks fail on missing evidence:

- `adh.handoff_batch` and `adh.gates_before_done`, for each of T1–T6
- `dp08`, `dp10` and `dp14`

The C2 DeepSeek run of 4 November hit the same gap (its `review/post-run/report.md`), so this is a known scorer limit, not a new one.

`done_gates.py` (in this folder, read-only) rebuilds the facts from the patch payloads in `session.jsonl`. For every task, the first Done insertion carries `handoff.md` and `.heartbeat` in the same patch, a `DOD_OK` for that task comes before it, and a kanban validation follows it. Every In Progress insertion carries an `in_progress:` timestamp. Counting those checks as passed gives the evidence-corrected row. `adh.kanban_after_moves` stays failed because only the Done moves were checked. The task tier stays at 36.4 because per-task attempt latency wasn't rebuilt. That row exists to locate the gap. It isn't a score to publish or compare.

## Real defects

1. **Spec commit message.** `docs(spec): author minisql feature specification` isn't the prescribed message, so `dp02` and `adh.prescribed_msg.spec` fail. Both runs of the scorer agree.
2. **Premature T4 Done.** The parent run moved T4 to Done at 17:51 UTC on 6 November, before its phase commit, with semantic code left staged. The recovery moved it back through In Review, committed `b7e4438` and re-entered Done at 15:12 UTC on 7 November. The Run Summary doesn't mention this; `handoff.md` records it separately.
3. **Runner diagnostics.** `diagnostic-report.json` fails `skill_invoked`, so the expected denied-skills-root error counts as unapproved. The recovery report traces this to `codex-trace.py` suppressing raw skill reads that `paid-diagnostic-audit.py` then requires. That is an evidence-contract mismatch in operator tooling, not contestant behaviour. It still blocks reference eligibility.

## Langfuse

The run launched with `telemetry.enabled: false`, so it sent nothing live. On 8 November the operator replayed copies of all 22 rollouts from the host with [replay.ps1](langfuse/replay.ps1). The script uses the repo's `Resolve-EvalTelemetry` and `codex-flush.py` under D111 identity, loading only the six Langfuse key and URL variables. The session was empty beforehand. Readback ([session-summary.json](langfuse/session-summary.json)) shows 35 traces and 1,672 observations: 458 generations, 1,179 tool calls, 35 agents. Nothing was truncated or duplicated, and the user IDs are `codex/orchestrator`, `codex/coder`, `codex/reviewer` and `codex/unknown`. The session's main thread starts with the parent run on 6 November, so it covers both segments. The scrub recorded 0 redactions before upload.

**Parity is diagnostic only.** [parity-eval.py:32](../../scripts/parity-eval.py) finds stage boundaries by the exact spec subject `docs: author feature specification in …`. This run's spec subject is the non-prescribed one (defect 1). As a result every stage after spec-research has no bounds, and about 35 dispatch and gate checks count zero events. `parity-eval.py` also crashes on a null `run.json.tokens`. So it ran on a scratch copy of `run.json` with `tokens: {}`, the scratch workspace clone at `f5d6602` and the Langfuse session ID. Its judge IDs use an `a.` prefix ([manual-parity.json](manual-parity.json)). The 59.53 isn't comparable with the macOS C3 pair (Opus 36.84, Sol 76.67).

**Published.** Following the C2 pattern, two factual session scores went out under scope `c3-codex-sol-source-reviewed-20261107-9e506686-v1`, evaluator `c3-factual/1`, and were verified by exact Scores v3 readback ([publication-result.json](langfuse/publication-result.json)):

| Score | Value | ID |
|---|---|---|
| `oracle_pass_rate` (config `fe4ba7b1…`) | 1.0 | `5f0fa68a9c06294f72905e85f6198f30` |
| `c3_quality_qact_v1` | 89.06 | `ffd6f305fa71b97e2aef136e2f2b246c` |

The QACT 76.0 and parity 59.53 composites aren't published, because parser limits, not behaviour, drive both down. No historical score was touched.

## Comparison with the macOS C3 reference

The macOS pair ran Claude Code on Python 3.9.6 with plugin `52160ef`. Their Quality is capped at 40 by `test_ac1_import_scan`, and their published figures are parity scores, not QACT. Don't compare composites. Facts that do compare: this run used 38.41M tokens (macOS Sol 22.36M, Opus 38.96M), passed its final review in round 1 like macOS Sol, and is the only C3 run with a clean oracle.

## Files

| File | Content |
|---|---|
| [score.md](score.md), [score.json](score.json) | frozen QACT output with judge verdicts |
| [manual.json](manual.json) | judge verdicts and their evidence |
| [done_gates.py](done_gates.py) | read-only reconstruction of per-task Done-move gates |
| [parity.json](parity.json), [manual-parity.json](manual-parity.json) | diagnostic parity output and its judge verdicts |
| [langfuse/](langfuse/) | replay script, session readback summary, score bodies, preflight, claim, readback and result |
