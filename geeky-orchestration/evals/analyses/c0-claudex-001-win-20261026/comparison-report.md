# C0 comparison of Codex and Claude Code

Codex completed its first scored C0 attempt in 47m26s with parity **97.46**. Claude Code's first scored attempt after the router repair passed the same hidden oracle but timed out after 90m02s with parity **90.33**. An authorized continuation completed Claude's workflow in another 29m38s. Its cumulative result is **98.33**, based on 119m40s of active execution. These are two initial-attempt outcomes and one resumed cumulative outcome. The continuation is not another clean initial attempt.

This comparison uses the saved JSON, native transcripts, Git objects, and scoring formulas. It makes no new provider calls and does not rerun candidate tests. Six raw stream/session hashes were recomputed and match their run records. Candidate commits were read directly, including Claude's historical timeout commit after its workspace advanced. The accompanying `comparison-metrics.json` preserves the available numeric breakdowns, checks, tool and gate counts, original accounting scopes, and unknowns. The analysis repository baseline was `4ec9691532cfd453fc977059648106f703e4cc56`.

## Outcomes at the evaluated commits

| Measure | Codex initial | Claude initial after router repair | Claude resumed cumulative |
|---|---:|---:|---:|
| Parity composite | 97.46 | 90.33 | 98.33 |
| Quality | 95.64 | 96.67 | 95.71 |
| Adherence | 97.83, 45/46 | 88.10, 37/42 | 100, 42/42 |
| Consistency | 100 | 83.16 | 100 |
| Weighted decision conformance | 19/19 | 15/19 | 19/19 |
| Stage order | 1.0 | 1.0 | 1.0 |
| Exit | 0, completed | 124, timeout | 0, completed |
| Active runtime | 2846s | 5402s | 7180s, includes 1778s continuation |
| Independent public tests | 93 passed | 56 passed, 2 skipped | 60 passed, 2 skipped |
| Hidden oracle | 13/13, three stable repetitions | 13/13, three stable repetitions | Fresh 13/13, three stable repetitions |
| Required task-commit commands | 9/10 pass | 7/7 pass | 7/7 pass at original task commits |
| Tasks and phases | 5 tasks, 3 phases | 4 tasks, 4 phases | Same 4 tasks, 4 phases |
| Final review | PASS, zero critical | Three replies, no consolidation | PASS WITH WARNINGS, zero critical |
| Candidate commits after seed | 12 | 10 | 13, including 3 new commits |
| Source Python nonblank lines | 77 | 90 | 98 |
| Test Python nonblank lines | 354 | 379 | 402 |
| Forbidden Git or frozen-contract violation in parity audit | None | None | None |

The evaluated heads are `521f69a0b194328cecc247e942abca02374640d4`, `e2c1317ed4443e970e6ea9f9c069b0c75342ae1c`, and `a12f55aafd14526e4191175184bd3e3bb15321fd`. LOC counts include comments and exclude blank lines. Source excludes tests and planning documents. Test counts reflect each candidate's chosen suite and parametrization; 93 versus 60 is not a common coverage percentage. Claude's two skips require POSIX and non-root unreadable-file behavior, which Windows cannot exercise. [Codex parity](codex/parity.json), [Claude initial parity](claude-code/router-fixed/parity.json), [Claude cumulative validation](claude-code/closeout-20261026/validation.json).

## Setup and the limits of comparison

Both used Windows MXC, LiteLLM alias `claudex-001`, the C0 wordstat case, and plugin snapshot `c83d4b941341b4094b6e7d2f4ac125e5c1b74154`. Codex CLI was 0.164.0. Claude Code was 2.1.304. Qualification was explicitly waived by the owner. There was no additional qualification run or external paid judge. The evaluation's manual judgments are source audits, not fresh model grades.

The canonical prompt hash matches, but recovery prompts and context differ. Codex used the canonical initial prompt. Claude's scored initial attempt used `geeky-resume` reconciliation after earlier transport failures. Its seed was `d06eb6d1cd2f5419d644550a004c2c3e873c3ea8`; Codex's seed was `062419d5b67e121e046d51525398871f766cdb68`. The continuation reused Claude's existing workspace and forked conversation context. These setup differences prevent a claim of identical clean starts.

The user requested default thinking. Codex's runner actually defaulted the main agent and all descendants to `high`. Claude records `default` without an explicit matching effort guarantee. Also, the alias is an adaptive `auto_router/complexity_router` route. The router changed before Claude's successful request path. Alias equality does not establish the same underlying backend, reasoning allocation, or pricing. The results describe these executions; they cannot identify a causal model or harness winner. [Codex setup and source references](codex/references.md), [Claude initial source references](claude-code/router-fixed/references.md).

Earlier Claude attempts belong to transport history. The original process ran 2328s and encountered HTTP 400 `MissingSessionID` before completing a specification. A bounded same-session recovery failed, then a fresh same-folder restart failed on its first request with zero tools and zero reported model tokens. Those attempts receive no comparable code-quality score. Their time and interventions are excluded from the scored initial-attempt and cumulative active-runtime comparisons. [Preserved provider-blocked history](claude-code/report.md).

## What each execution accomplished

Codex produced the specification, plan, plan review, core, CLI, tests, README, phase records, and final implementation review. Its five coders ran serially, with maximum coder concurrency one. All five tasks reached Done with recorded phase acceptance. The completed product passed the independent public suite and stable oracle.

Its deductions concern reproducibility and reporting. T1's selected commit `9336491` contains the core but lacks `tests/test_core.py`. The import command passes, while pytest exits 4 because the test file arrives in the next commit, `1d9e57e`. The evaluator retains the established H1 selection policy rather than selecting a later passing commit. Final HEAD still passes. The final response also says CLI-level CRLF and BOM tests are missing, although subprocess tests already cover both. A reviewer suggested a narrower direct `cli.main` test, and the final response overgeneralized that suggestion. This fails strict report accuracy, but does not establish false completion. [Task anchors](codex/validation-anchors.json), [source judgments](codex/manual-verdicts.json).

Claude's scored initial attempt completed four serial implementation tasks and ten linear commits. It passed all extracted validation commands at the task commits. All three final reviewers returned PASS WITH WARNINGS. The parent did not consolidate their findings, settle the remaining contract interpretation, write the Run Summary, finish the heartbeat, or produce a final result before timeout.

T4 exposes why Done and acceptance differ. Its phase reviewer returned BLOCKED because the dated final-test handoff entry was missing. The parent added the entry and marked the task Done, but did not obtain a revised READY TO ADVANCE verdict. Earlier phases' successful verdicts cannot establish T4 acceptance. Thus four Done cards and passing tests coexist with an incomplete workflow. [Initial source judgments](claude-code/router-fixed/manual-verdicts.json).

The continuation reconciled that state, consolidated final review, and delegated a real CLI correction. An arbitrarily long positive `--top` value previously reached Python's `int()` digit limit. The fix validates ASCII decimal digits, removes leading zeroes, rejects zero, and caps at `sys.maxsize`. Four cases cover huge input, leading zeroes, all zeroes, and non-ASCII digits. The cap preserves output for a realizable result list. New commits are `06fca83` for code and tests, `0a9b354` for final review and release records, and `a12f55a` for T4's revised verdict. The T4 reviewer checked `0a9b354` and independently returned PASS and READY TO ADVANCE. [Continuation report](claude-code/closeout-20261026/report.md), [source judgments](claude-code/closeout-20261026/manual-verdicts.json).

Both current workspaces have only an untracked runtime `.heartbeat`. Source audits exclude that file from work-committed checks. Neither candidate pushed. Frozen specifications, plans, references, and task contracts remained intact after their respective freeze points.

## Why the published scores differ

The comparable formula is `parity = (0.35Q + 0.35A + 0.20C) / 0.90`. It removes the legacy latency-based task tier. Quality is `Q = 70P + 15S + 15D`, where `P` is the oracle pass ratio, `S = min(1, 70/source_LOC)`, and `D = max(0, 1 - failed_task_validation_commands/5)`. One failed command gives `D=0.8`, not 0.9. Adherence is the percentage of applicable checks passed. Consistency is `100 * (0.8 * weighted_decision_conformance + 0.2 * stage_order)`. Five critical decision points carry weight two. All three results have correct stage order. [Parity formula](../../scripts/parity-eval.py), [quality and task formulas](../../scripts/score-run.py).

| Quality component | Codex | Claude initial | Claude cumulative |
|---|---:|---:|---:|
| Oracle P | 1 | 1 | 1 |
| Size S | 70/77 = 0.909091 | 70/90 = 0.777778 | 70/98 = 0.714286 |
| Validation D | 0.8, one failed command | 1, zero failures | 1, zero failures |
| Oracle contribution | 70 | 70 | 70 |
| Size contribution | 13.636364 | 11.666667 | 10.714286 |
| Validation contribution | 12 | 15 | 15 |
| Unrounded Q | 95.636364 | 96.666667 | 95.714286 |

The size term rewards fewer lines under this configured reference. It is not an independent maintainability finding. Claude's correction improves actual input handling while lowering Quality by 0.952381 because source grows from 90 to 98 lines. The hidden oracle and original task commands do not expose every edge case. Passing both does not prove absence of defects.

Codex loses one of 46 adherence checks for report accuracy. Claude initially loses five of 42: Run Summary, final heartbeat, P4 verdict, run completion, and final report. The last is missing closeout, not a demonstrated false completion claim. Consistency loses four weighted units: P4 acceptance carries two, Run Summary and heartbeat one each. The continuation supplies all five missing adherence outcomes and those four consistency units. No parity hard cap fires in these three audited results. [Codex score inputs](codex/score.json), [Claude initial score inputs](claude-code/router-fixed/score.json), [Claude cumulative score inputs](claude-code/closeout-20261026/score.json).

| Difference, in composite points | Quality contribution | Adherence contribution | Consistency contribution | Unrounded total |
|---|---:|---:|---:|---:|
| Codex minus Claude initial | -0.400673 | +3.784219 | +3.742690 | +7.126236 |
| Claude cumulative minus initial | -0.370370 | +4.629630 | +3.742690 | +8.001949 |
| Claude cumulative minus Codex | +0.030303 | +0.845411 | 0 | +0.875714 |

Codex's initial advantage is process completion despite Claude's slightly higher initial Quality. Claude's final advantage over Codex is almost entirely its accurate completed report. The composites before rounding are 97.4576196750, 90.3313840156, and 98.3333333333. Subtracting displayed final values gives 0.87, while rounding the unrounded difference gives 0.88. The weighted decomposition uses unrounded inputs and does not force a false agreement with subtraction after rounding.

## Task snapshots and diagnostic task metrics

| Candidate | Task and selected commit | Replayed required commands |
|---|---|---:|
| Codex | T1 core, `9336491` | 1/2 |
| Codex | T2 CLI, `1d88fec` | 3/3 |
| Codex | T3 CLI tests, `db59374` | 2/2 |
| Codex | T4 README, `2e1ef10` | 1/1 |
| Codex | T5 verification, `b115d84` | 2/2 |
| Claude, both evaluations | T1 scaffold, `0613177` | 1/1 |
| Claude, both evaluations | T2 counting, `186bb2a` | 2/2 |
| Claude, both evaluations | T3 CLI, `1e8168d` | 2/2 |
| Claude, both evaluations | T4 subprocess suite, `dc76b8a` | 2/2 |

No snapshot uses final-HEAD fallback. Claude's cumulative 7/7 reuses the original task contracts and commits; its new fix has separate focused and full-suite evidence. The focused CLI suite is 22 passed, one skipped. Independent cumulative public validation is 60 passed, two skipped.

The legacy `score.json` composites are 63.7734, 72.2200, and 77.9115, and task-tier scores are 74.5780, 73.7398, and 75.0669. They are diagnostic, not cross-harness rankings. Parser limitations miss dispatch shapes, map some reviews poorly, and formerly mistake Codex's pre-freeze planning changes for frozen edits. That legacy hard-cap flag is not a parity audit finding.

For completeness, task tier uses `100 * (0.4V + 0.3R + 0.2T + 0.1D)`, weighted half by changed-LOC share and half by validation-attempt share. V declines with attempts, R declines with review rounds, T adjusts duration using reference latency 2678ms and timeout 600s, and task D reflects final DoD. Diagnostic attempt counts are Codex `[1,0,2,1,0]` and Claude `[1,1,2,1]`. Missing parser attempts are not proof that work was untested. Codex task scores are `[50.75,40,83.71,93.75,40]`; Claude initial scores are `[80.29,66.86,81.94,67.08]`, becoming `[83.18,67.32,83.12,67.50]` in the cumulative diagnostic. Their change partly reflects latency and LOC weighting, not new task execution. Exact V, R, T, D, durations, attempts, LOC, and weights are retained in the companion metrics.

## Timing, usage, and cost scopes

| Native accounting measure | Codex initial | Claude initial | Claude continuation reported scope |
|---|---:|---:|---:|
| Input, including cached input | 12,640,818 | 16,078,812 | 4,071,232 |
| Cached input | 1,314,688 | 13,970,509 | 3,779,313 |
| Cache creation | 0 | 1,054,677 | 276,825 |
| Output | 225,348 | 493,621 | 87,756 |
| Reported reasoning subset | 67,365 | 0 reported | 0 reported |
| Total input plus output | 12,866,166 | 16,572,433 | 4,158,988 |
| Native model-call count, raw capture scope | 228 | 147 | 90, includes retained history |
| Native latency median | N/A, no samples | 4386ms, 166 samples | 5137ms, 93 samples |
| Parity observation latency median | 2656ms | 6961ms | 6650ms, cumulative observations |
| Native maximum idle gap | 227s | 260s | 29,863s, includes historical gap |
| Native API duration | N/A | 3,297,023ms | 1,217,741ms |
| Recorded cost estimate | N/A | $31.1856, unverified | $5.8892, unverified |
| Verified billed cost | N/A | N/A | N/A |

Cached and reasoning subsets must not be added again. Cache-creation fields follow harness accounting, and reported zero reasoning in Claude is not proof of zero reasoning work. Native calls and latency samples differ because they measure different record populations. Codex exceeded its 6M token threshold, which its runner labels informational pending calibration. Claude initial also exceeded 6M. The continuation reports below 6M in its own native scope. These fields are not comparable hard-stop budgets. The inherited Claude price estimate is not validated for this router alias. There is no defensible dollar-efficiency comparison.

On the recorded initial scopes, Claude took 1.898 times Codex's runtime and reported 28.81% more native tokens. Cumulative Claude active time is 2.523 times Codex's initial time. The resumed native capture's 90 parent request IDs comprise 42 new IDs timestamped at or after continuation start and 48 retained historical IDs, with zero shared IDs between those sets. These are parent-only request counts, not all worker calls. The 90 is a mixed capture count, not a new-continuation count. No cumulative Claude token or call total is asserted: forked history and session accounting overlap, and worker request populations have not been normalized. In particular, closeout parity combines cumulative runtime and commits with continuation-reported native tokens. Adding those fields to historical aggregates would create an unsupported total.

| Stage span from parity boundaries | Codex initial | Claude initial |
|---|---:|---:|
| Specification boundary span | 4m05s | 10m51s, includes resume reconciliation |
| Planning | 12m44s | 14m45s |
| Plan review | 14m10s | 14m16s |
| Implementation | 14m49s | 44m50s |
| Final review through process end | 1m26s | 5m06s, timeout |

Claude's specification boundary span includes `geeky-resume` reconciliation and is not pure research time. These spans use the corrected observation and Git-based parity boundaries, not the stale native stage parser. They include coordination, checks, and waiting. They do not measure pure coding or model thinking time. Small startup intervals precede the first boundary.

In Singapore time, Codex ran from 2026-10-25 23:48:05 to 2026-10-26 00:35:31. Claude initial ran on October 26 from 03:54:47 to 05:24:49, and the continuation ran from 13:42:22 to 14:12:00. The corresponding UTC intervals are October 25 15:48:05 to 16:35:31 for Codex, October 25 19:54:47 to 21:24:49 for Claude initial, and October 26 05:42:22 to 06:12:00 for the continuation. The intervening 8h17m33s is excluded from active runtime. Closeout native metadata contains a 502.9-minute impl-review span and 29,863-second idle maximum because the fork retained history across that gap. Those are not active closeout performance measurements.

## Agents, gates, and telemetry completeness

Native dispatch inventories record Codex with five coders, ten reviewers, three general-purpose agents, one explorer, and one architect. Claude initial records four coders, eight reviewers, three general-purpose agents, one explorer, and one architect. The forked native closeout inventory records five coders and ten reviewers with the same other categories, including retained historical agents. It is not a count of newly spawned continuation agents. Both initial coder sequences are serial, with justified dependencies. The parity concurrency judgment passes; it does not prove all research agents ran concurrently. [Codex coder lifetimes](codex/coder-lifetimes.json), [Claude lifetime audit](claude-code/router-fixed/manual-verdicts.json).

Recorded interventions are zero within each initial scored attempt and one for the authorized continuation. Claude also retains two earlier campaign interventions, which belong to the provider-failure history. Provider-refusal scores are zero in all three published sets. Native final-review round counts are one, one, and two respectively.

Native parser validation-run counts are 52 for Codex, split 14 main and 38 worker, and 26 for Claude initial, split 12 and 14. The forked closeout capture records 32, split 14 and 18. These include distinct captured histories and are not additive. Corrected parity implementation evidence counts 34 pytest runs for Codex and 17 for each Claude evaluation. The metrics retain every native tool distribution and gate outcome. Passing final gates does not erase recorded intermediate failures or unknown outcomes.

The native gate parser reports the following pass/fail/unknown counts. The forked closeout column includes retained history, and corrected parity may count batched commands differently.

| Gate | Codex | Claude initial | Forked closeout capture |
|---|---:|---:|---:|
| Planning-folder validation | 8/0/0 | 6/0/0 | 11/0/1 |
| Task-schema validation | 8/0/0 | 5/0/0 | 8/0/1 |
| Kanban validation | 25/1/0 | 20/1/0 | 25/1/1 |
| Commit-message validation | 11/1/0 | 5/2/0 | 8/2/0 |
| DoD checks | 5/0/0 | 4/1/1 | 17/1/2 |

| Langfuse session measure | Codex | Claude initial | Claude resumed session |
|---|---:|---:|---:|
| Observations | 536 | 892 | 1095 |
| Traces | 21 | 33 | 25 |
| Agent user IDs | 21 | 17 | 13 |
| Generation observations | 229 | 329 | 422 |
| Tool observations | 286 | 530 | 644 |
| Agent observations | 21 | 33 | 29 |
| Aggregate usage units | 12,896,556 | 19,349,407 | 19,651,335 |
| Truncated observations | 0 | 0 | 0 |
| Published scores verified | 10 | 10 | 10 |

Tracer roles differ from native dispatch classifications. Codex has five coder, ten reviewer, one orchestrator, and five unknown user types. Claude initial has four coder, eight reviewer, one orchestrator, and four unknown types. Unknowns remain unknown rather than being guessed from prompts. All 267 usage-bearing Claude initial generations and 325 usage-bearing resumed generations use `claudex-001`. Sixty initial no-usage placeholders say `claude`; they do not establish another backend. [Codex telemetry audit](codex/telemetry-audit.json), [Claude initial telemetry audit](claude-code/router-fixed/telemetry-audit.json), [continuation telemetry audit](claude-code/closeout-20261026/telemetry-audit.json).

The resumed Langfuse session includes old agents and events. Its observation total cannot be added to the previous session. Cumulative derivation retains 678 prior and 807 continuation observations, producing 1485 after source-aware filtering and tool deduplication by `metadata.tool_id`. It prefers the continuation source and preserves namespaced parent ancestry. Native derivation excludes 438 fork-rebased historical rows and retains 1612 logical rows. [Derivation manifest](claude-code/closeout-20261026/evaluation-inputs.json).

Original runner coverage flags remain preserved. Corrected audits establish complete required coverage for each initial attempt and explicitly cumulative coverage for the continuation. The resumed session alone misses four historical stages. Coverage completeness means captured evidence exists, not that the workflow finished. Codex's telemetry-only host-flush repair used `--allow-win32k`, made zero model calls, and did not change candidate performance. Parser corrections addressed compaction proposals, failed patches, batched gates, Windows paths, and UTC offsets without inventing execution results. The ten score readbacks confirm current parity values and preserve Claude's earlier 90.33. [Codex verified scores](codex/langfuse-scores-verified.json), [Claude initial verified scores](claude-code/router-fixed/langfuse-scores-verified.json), [Claude cumulative verified scores](claude-code/closeout-20261026/langfuse-scores-verified.json).

## Remaining evidence limits

The huge-value fixture uses three distinct words, so it would not detect every incorrect small cap. Windows stderr newline and encoding behavior, broader regression coverage, and timeout cleanup remain warnings. POSIX permission behavior remains untested here. No final oracle failure, critical final-review finding, or operator product edit is evidenced.

Claude's final review ledger labels two Git blob object IDs as SHA-256. Both objects reproduce the final files, but the algorithm label is wrong. The final response does not repeat it, so the strict final-response check passes while this separate ledger defect remains disclosed. The erratum records actual SHA-256 values without rewriting the candidate. [Hash-label erratum](claude-code/closeout-20261026/review-metadata-erratum.json).

The defensible result is completion and score evidence at each stated scope: Codex finished its initial execution, Claude initially timed out with working code and unfinished acceptance, and Claude completed acceptance plus an edge-case correction with additional authorized time. Backend identity, matched effort, billed cost, cumulative token efficiency, and comparative coverage percentages remain N/A because the available records do not establish them.
