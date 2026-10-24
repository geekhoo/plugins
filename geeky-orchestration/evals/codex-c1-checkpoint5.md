# C1 checkpoint 5: measurement and records closeout

2026-10-24, Asia/Singapore. Scope: frozen six-Claude score reproduction and current records. No scorer, adapter runtime, skill, agent or rubric changes; no paid calls, MXC launches, case-test reruns, commits, pushes or cleanup.

## Evidence and status

- [Four-run repaired derivation](analyses/c1-consistent-rescore-20261024/README.md): Codex 1 Q/A/C/T = 95.9/100/100/77.7, composite 96.3; Codex 2 = 100/97.1/100/90.7, composite 98.0. Historical scores 81.7/89.8 remain untouched.
- [Frozen six-Claude verification](analyses/c1-checkpoint5-20261024/README.md): separate historical reproduction, with original inputs and source hashes checked. This supplements, rather than overwrites, the earlier source-unstable six-run report.
- [Run-2 self-evaluation](analyses/c1-consistent-rescore-20261024/run2-self-evaluation.md) remains an operator report, not independent runtime proof.
- The prior repaired suite recorded 306 tests plus 32 subtests. No tested scorer/adapter source changed in this closeout, so that suite is not repeated. This closeout does not establish a separate red-before/green-after test for every allegation in Claude's pasted report.

## Decisions on Claude's report

Claude's report is a review input from before the completed four-run repair. Its hand arithmetic and proposed new rules do not supersede saved source-bound results. Durable rulings are D94-D98 in [the decisions](../docs/agent-eval-decisions.md).

| Question | Decision and evidence |
|---|---|
| Q1 hook parity | Retain both Codex outcomes as calibration measurements with an explicit runtime-hook caveat. Both saved parity reports say `runtime_verified:false`; configured declarations and successful native fixtures do not prove hooks fired in the paid contestant. Hook trust/invocation and shell-write coverage are acceptance requirements for a future parity claim, not implemented or retroactively credited here. |
| Q1b capability parity | Component access is substantially equivalent, runtime behavior is not identical; see the bounded inventory below. D48 parity is not declared fully closed. |
| Q2 final-report claim | Keep FAIL: hook configuration existed. Lack of trust/runtime proof does not make the literal claim that configuration was unavailable true. The repaired score already preserves this failure. |
| Q3 timestamps | Keep the existing presence-only dp08 rule. Future-dated labels remain a contestant behavior finding. A plausibility tolerance needs a versioned rule applied symmetrically, outside this records closeout. D92's move/check/revert procedure is settled. |
| Q4 task granularity | Report 2/3 Codex tasks versus 7/10 selected Claude tasks and the differing adherence denominators; do not normalize or retune scores. |
| Q5 one concern / dp13 | Retain PASS: execution-protocol.md requires logical concerns, not that related tracking be absent from a functional commit. T2/T3 also contain tracking files; the separate 6f179ac closeout does not mean all tracking was separate. No unrelated functional concern was established. |
| Q6 pointers | New process evidence uses visible source text, record identity/hash and timestamp. Prefer the assistant verdict message over task-complete notifications. Original verdict files stay intact; the attachment's individual ordinal corrections have not all been independently re-audited here. |
| Q7 symmetry | Shared rubric/formulas remain unchanged; adapters normalize native representations. Six-run exact regression establishes observed Claude stability, not universal equivalence for every hypothetical trace shape. |
| Q8 publication | Retain the complete reviewed composites. Reject a blanket no-manual-verdict requirement: one_concern, dp13 and other checks are intentionally judgment-based. Twenty Codex-2 deterministic overrides were removed in the repaired derivation; source-backed judgment items remain. |
| Q9 comparability | No causal model-effect claim. Worker model, delegation and administration harness changed. Three oracle repeats are checks of one artifact, not three contestant runs. |
| Q10 tokens/cost | Preserve D53 and historical eligibility/ceiling flags. Codex remains calibration-only; report tokens, unknown monetary cost/API latency and call-count scope (Codex all threads; Claude main session). Do not silently recalibrate 12M or grant reference eligibility. |
| Q11 trusted-exec | Confirmed `danger-full-access`, `--ignore-user-config` and `--ignore-rules` in trusted-exec.py. The existing design relies on outer MXC plus explicit run profile, not an inner workspace-write sandbox. Record this D52 exception only for the retained MXC-contained runs; no standalone-host use or new containment assurance is approved. A denied-root check alone cannot prove all boundaries. |
| Q12 preservation | Historical hashes establish only their named file sets, not every shared dirty file. Check time and snapshot-write time are distinct. Future launch records should capture the dirty inventory before launch and record both times; no historical timestamps are invented. |

## Bounded parity inventory

Sources: both Codex runs' `parity-preflight.json` and capability notes; Claude 6 `stream.jsonl` system/init; adapter `README.md`, `trusted-exec.py` and the retained native evidence. These are saved observations, not new runtime tests.

| Surface | Claude 6 | Codex 1/2 | Consequence / equivalent |
|---|---|---|---|
| Plugin skills and agents | init lists all 8 geeky skills and 6 geeky agents | preflights list the same 8 skills and 6 registered projections | Same named workflow material; different pinned plugin SHAs remain disclosed. |
| Templates, scripts, guard, MCP source | Loaded plugin export; six geeky MCP gate tools listed, server connected | export-components/readability checks; configured MCP bootstrap and retained native checks | Shell validators/MCP gates supply the same workflow checks; static access is not proof of each invocation. |
| Agent restrictions | Canonical Claude projections preserve model/tool metadata | sync projections omit canonical tool/model restrictions; generated role layers select worker model/reasoning | Explicit model matrices and audits are the closest recorded equivalent; tool restrictions are not identical. |
| Built-in capabilities | init also lists Claude built-in skills/agents/tools and 3 bundled plugins | bundled skills/default cached plugins disabled; Codex-native tools and collaboration | Native harness capability differs. Do not claim an identical tool catalog or copy unrelated built-ins. |
| Guard | PowerShell hook supported; shell writes bypass it; O19 warning-delivery limitation | configured bridge, additionalContext patch warnings and trust setup; shell writes bypass it | Frozen-artifact git checks remain shared scoring evidence. Paid-run hook invocation/coverage parity remains unverified. |
| Environment | MXC isolated profile, PowerShell, Python, private temp/config, scoped Git | outer MXC, dedicated signed-in home plus run HOME, explicit profile, no root enumeration | Purpose-equivalent isolation with different grants/launch flags; auth and containment are not re-probed here. |
| Trace and usage | stream/session plus nested transcripts; init capability inventory | timestamped rollout and descendant copies, cumulative token events | Shared normalized checks; Codex API latency/cost unavailable, raw-duration fallback explicit. |

## Status of the ten reported defects

All ten are represented in the prior repaired derivation; no additional scorer edit is needed for this closeout. The evidence is the per-run `process-evidence.json`, derived score/task rows, cache bindings and frozen tests in the four-run report.

| Defects | Existing coverage / limit |
|---|---|
| 1 lane writes; 8 Run Summary | Physical-write filtering, variable-path handling and source-bound lane/handoff mappings; `test_process_replay.py` and `test_score_run.py`. Read-only wrappers are excluded. |
| 2 stages; 4 nested task ownership | Scoped activity plus visible source bindings and nested ancestry; `test_codex_stage_evidence.py`, `test_codex_trace.py`, `test_codex_run2_prep.py`. |
| 3 own commits | Exact commit/task/command cache binding; strict documentation-HEAD fallback rejection in `test_process_replay.py`. |
| 5 reviews; 7 repeated rounds; 8 critical fix | Repaired task/reviewer mappings and separate review rounds; Codex 1 T2 retains NEEDS FIXES then PASS (R=0.5), with critical-fix/re-review evidence. |
| 6 polled validation; 9 concurrency/counts | Saved task activity and attempts normalize observed results/lifetimes; derived rows retain Codex 2 attempts 1/1/2, serial coders and three final reviewers. This does not prove general handling of all polling shapes. |
| 10 plain commands | `test_plain_bullets_and_fenced_commands_preserve_contract_order`; empty extraction is not substantive 0/0 validation credit. |

The repaired concurrency breakdown is R1 maximum 2 coder lifetimes and R2 maximum 1, rather than accepting the attachment's blanket maximum-1 claim. Both satisfy the existing <=3 rule; no new concurrency inference or scoring change is made here.

Claude's R1 hand estimate differs from the repaired 96.3: saved replay counts T1's three attempts, T2's two review rounds, and task durations 198.2/360.3 seconds. The authoritative task rows preserve these inputs; no score was adjusted to fit the suggested range.

## Checkpoint 5 acceptance

- [x] All six Claude historical raw dimensions/composites reproduce with stable source hashes.
- [x] Current baseline procedure, lessons, decision record and scorecard link the repaired evidence.
- [x] Adapter README, kanban, handoff and references reflect both completed runs.
- [x] Original run evidence and scores remain preserved; no paid execution, commit or push.
- [x] Runtime parity, calibration and proposed rubric changes are explicitly separated from completed records work.

## Record reconciliation

Updated stale current-state text in `baseline-runs.md`, `lessons-learned.md`, `codex-c1-kickoff.md`, `codex-c1-run2-guide.md`, the plugin README, scorecard, and adapter README/kanban/handoff/references. Added D94-D98 and clarified O7/O18 without claiming general ATIF ingest or full runtime parity. Historical evidence, original scores, prior replay report and retrospective remain preserved and linked.

Remaining future work: prove automatic guard runtime/coverage parity, any versioned timestamp or granularity change, repeated controlled runs and Codex calibration. None blocks this bounded records closeout or authorizes another run. No skills/agents changed; the older AGENTS gate-order wording is recorded as historical drift and D92 remains authoritative.
