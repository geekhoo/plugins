# C0 remediation: minimum effort, maximum effect

Status: planning only, revised 2026-10-26 to incorporate the three side-review proposals. Source baseline: `8fff98b0f087f148d4f416f512dc9988d61a57aa`.

Implement three bounded changes in the existing workflow skills, runners and score publisher. Put the low-cost instruction/output fixes first, runner protection second and scoped accounting third. Estimated engineering effort is **2.5–5 focused days** (approximately 3–5 days for scheduling), including offline verification and review; this is a planning estimate, not measured throughput. All three tasks and the existing review gates must complete before considering a separately authorized evaluation/publication.

The desired outcome is a run that obeys its authorized deadline, leaves usable evidence when interrupted, completes the existing acceptance steps promptly, and reports only what the evidence supports. No score improvement or completion within 90 minutes is promised.

## What the two C0 runs actually establish

| Evidence | Consequence for this plan |
|---|---|
| Codex finished in 47m26s, parity 97.46; T1's selected commit passed only 1/2 commands because its test file arrived later. | Prevent mismatches between tested files and committed task delivery. Keep the historical deduction. |
| Codex incorrectly described existing CLI CRLF/BOM coverage as missing. Claude's review ledger mislabeled Git blobs as SHA-256. | Tighten the final claim check and hash labels; no new judge or reporting framework. |
| Claude timed out at 90m02s with working code but incomplete phase acceptance and closeout, parity 90.33. Its authorized 29m38s continuation completed at cumulative parity 98.33. | Persist reviewer results as they arrive and finish the existing closeout sequence; preserve initial and cumulative outcomes separately. |
| Claude's refusal loop currently passes the original timeout again. This is a source-confirmed risk, not the demonstrated cause of the scored C0 timeout. | Pass remaining time on every allowed invocation; keep automatic recovery disabled by default. |
| Continuation captures contain both fresh and inherited history. | Label populations and reject unsupported sums. |
| Router repair, Codex host-flush repair, parser corrections and Claude's large-positive `--top` fix already landed. | Preserve them as regression evidence and recovery instructions, not new repair projects. |

See [references](references.md) for source reports, source hashes and implementation anchors.

## Three tasks, reordered for early benefit

| Order | Change | Expected effect | Estimate |
|---|---|---|---|
| [T1](tasks/T1-streamline-workflow.md) | Resolve verdict ambiguity; reuse valid planning review; save replies promptly; verify commit/claim evidence; simplify final output under a new prompt version. | Remove concrete sources of repeated work and stranded closeout without weakening gates. | 1–2 days |
| [T2](tasks/T2-bound-runner.md) | One attempt deadline; early durable record; preserve process outcome; integrate optional deadline/reserve checks. | Prevent timeout resets and missing/misleading records after exceptions. | 0.75–1.5 days |
| [T3](tasks/T3-scope-and-readback.md) | Small evidence-scope manifest; scope-safe score IDs/readback; reuse current telemetry replay. | Prevent double counting, score overwrites and paid reruns for telemetry recovery. | 0.75–1.5 days |

One implementation phase, one writer at a time: T1 → T2 → T3. T1 no longer waits on clock plumbing: its instruction/output changes stand alone. T2 owns both clock production and its optional skill integration, avoiding a dependency back into an unfinished T1. T3 consumes both contracts. Shared skill paths and acceptance state make concurrent writers unsafe. Read-only reviewers may assess disjoint workflow, runner and accounting areas after writes stop. Parent owns integration/final acceptance; required workflow review gates remain in force.

The retained comparison records planning plus plan review at **26m54s for Codex** and **29m01s for Claude initial**. Codex's combined span is about 57% of its initial runtime; its five sequential coder lifetimes total about five minutes. These are different populations and include legitimate review, validation and coordination. They justify examining repeated reads and ambiguous instructions first; they do not establish wasted time or a savings percentage. [Stage spans](../comparison-report.md), [coder lifetimes](../codex/coder-lifetimes.json).

## Incorporated side-review proposals

| Proposal | Concrete decision in T1 | Guard against scope growth |
|---|---|---|
| O1: terminal verdict | Required findings resolved + complete passing evidence means consolidated PASS; nonblocking domain warnings remain visible separately. | An unmet requirement blocks regardless of severity label. Keep all required reviewers/gates. |
| O2: one final report | Change only the canonical prompt's final-output paragraph for future baselines; compactly report stage verdicts/evidence, numeric test results, commits/final revision and deviations/interventions, linking existing artifacts. | Preserve the five existing report criteria, no coaching, no remote judge changes and no historical reinterpretation. Record a new prompt hash under D36. |
| O3: final planning sanity | Use existing findings/verdicts and a complete diff to recheck changed documents and affected references. Retain initial coverage of all six sanity dimensions. | Preserve both reviewers, all validators, existing full-recheck triggers and conservative fallback for stale/unknown inputs. No caching service. |

The added scope is approximately half to one engineering day within T1's revised estimate. It adds no task, review layer or framework. During the next separately authorized evaluation, compare retained stage spans and review-dispatch counts; examine repeated reads only where existing traces support them. No new instrumentation is required and savings remain unmeasured.

## Defaults that keep the work small

- Wall budget: one UTC deadline, with monotonic elapsed time while the runner is alive. Backoff/recovery consumes the same budget. A later authorized continuation has its own segment and deadline, linked to the frozen initial result.
- Retries: zero by default, as today. Preserve explicitly authorized bounded refusal recovery, fixing only its budget handling. Do not add automatic 400/auth/429/5xx recovery.
- Token/idle thresholds: label current executable behavior accurately. Keep historical informational token limits informational; no new live token-budget supervisor or arbitrary ceiling increase.
- Closeout reserve: expose a configurable advisory reserve with neutral deadline context. Proposed next-C0 setting is 900 seconds within the existing 5400-second budget. This is an uncalibrated starting value, not a proven optimum or an extra allowance. Persist incomplete state if required work cannot finish; never manufacture acceptance to beat the clock.
- Evidence: extend `run.json` with a small versioned execution section and invocation records. Keep raw captures and separate analysis outputs. Atomic metadata writes plus retained partial output are sufficient for this iteration; no event-sourcing service or new per-task event log.
- Scope: require explicit initial/continuation/cumulative labels where applicable. Unknown ownership, cumulative usage, backend identity or billed cost remains unknown.
- Telemetry: local captures plus existing replay are the recovery source. Presence, required coverage and verified scores are distinct states. Do not build a durable outbox or another tracer.
- Prompt/versioning: T1 explicitly replaces the previous plan's blanket unchanged-prompt boundary with one presentation-only edit to the final paragraph. Case contracts and workflow requirements remain intact. Both harnesses use the same revised template/hash for equivalent input, and future records retain prompt/plugin fingerprints. Historical C0 requirements and scores stay frozen.

## Disposition of all eight review recommendations

| Review item | Minimum implementation | Deliberately deferred |
|---|---|---|
| R1 authorization/budget | T2: declared recovery count, deadline, waiver/config references; remaining-time check. | General recovery policy engine and live hard-token enforcement. |
| R2 crash-safe evidence | T2: prepared/running records, atomic writes, independent capture/post-processing outcomes. | Per-event journal, power-loss durability guarantees, universal process-tree cleanup. |
| R3 lineage/scopes | T3: bounded manifest for sources, intervals, derivations and reported metric populations. | Universal trace graph and automatic arbitrary-fork reconstruction. |
| R4 closeout reserve | T2 supplies and consumes neutral clock context at existing dispatch/phase boundaries; T1 establishes orderly closeout. | Background scheduler or forced early acceptance. |
| R5 evidence-bound claims | T1 verifies tested/committed files and concise claim anchors; T3 reuses existing cache. | Replacement validation cache, new claim database, new paid judge. |
| R6 telemetry replay | T3 uses existing replay and exact score readback, recording pending delivery. | Batch acknowledgement/outbox infrastructure and tracer rewrite. |
| R7 coordination overhead | T1 uses phase batching, validated review reuse, unambiguous terminal verdicts and concise final output. | New overhead instrumentation/dashboard, forced parallel coding, gate removal. |
| R8 truthful policy docs | Update only touched guidance alongside each task. | Whole-estate documentation reconciliation. |

## Validation and stop line

Use fake clocks, local fake executables, injected failures, cached C0 artifacts and mocked telemetry clients. Assertions must exercise both runners and actual argument construction, not just search source strings. Unit/fixture checks do not call a provider, judge, live telemetry endpoint or candidate program. Optional MXC smoke validation uses only a local no-network child on the available host, after the changed host arguments pass offline tests; it is not an added native qualification gate.

Completion requires: nonblocking warnings terminate at consolidated PASS while unmet requirements remain blocking; planning reuse preserves full review coverage and invalidates stale evidence; compact final reports retain all five evidence criteria and have a new prompt version; exhausted/unauthorized recovery launches zero extra children; interrupted runs retain raw bytes/truthful state; old phase verdicts cannot justify later Done claims; the historical Codex T1 failure and all three parity values remain unchanged; mixed historical metrics cannot be added; score publication is idempotent within scope and cannot overwrite another scope; mocked readback detects missing/mismatched values.

Stop expanding when these checks pass. A real future evaluation is a separate authorization and evidence step. Offline fixtures cannot establish that an LLM will obey every checkpoint, that a reserve is sufficient, or that Linux/macOS integration is working.

## MXC boundary

Reuse the current pinned host. Its common contract already provides process execution/I/O, timeout, cwd/environment and positive path grants; these support the runner changes. The [pinned Microsoft policy](https://github.com/microsoft/mxc/blob/fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2/docs/containment-policy/1.0.0/policy.md) and [lifecycle reference](https://github.com/microsoft/mxc/blob/fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2/docs/container-lifecycle.md) distinguish shared settings from backend-specific behavior. No MXC upgrade, SDK migration, broader platform rollout, network-policy redesign or uniform descendant-kill guarantee is needed for this plan.

## Records and boundaries

This packet and the repository/C0 README links are planning records. The original run reports, raw inputs, scores, erratum and publication records remain historical evidence. Their disclosed defects are not edited away. On implementation, reconcile touched passages in `evals/QUICKSTART.md`, `evals/mxc-litellm-runbook.md`, `evals/telemetry/README.md`, `evals/prompts/README.md` and the affected skills; identify each updated passage in the handoff. The prompt's final-output paragraph is the sole allowed canonical-prompt change. Broader preparation handoffs and old recommendations remain dated history, with this packet as the bounded follow-up.

This planning deliverable grants no implementation, evaluation or push authority. The explicitly invoked plan-review workflow separately authorizes its required packet corrections and local planning commit. Implementation readiness and paid-run authorization are separate. [Kanban](kanban.md), [review](review-plan.md) and [handoff](handoff.md) record the current state.
