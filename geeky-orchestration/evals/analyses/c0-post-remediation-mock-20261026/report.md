# Post-remediation C0 mock evaluation — Windows MXC, 2026-10-26

**Both full scripted C0 fixtures passed 13/13 oracle tests, stable over three repetitions each, through real Windows MXC.** Each also passed 17 candidate tests and four validation commands at each task's scorer-selected final candidate commit. Twelve runner attempts through real MXC, comprising thirteen top-level workload invocations, were recorded across unchanged-source controls, full fixtures and negative cases. These are deterministic Python mock workloads, not live Claude/Codex model evaluations.

**A real terminal-metadata defect remains:** finalized records retain `postprocessing.seed-oracle: in-progress`. The integration tests also measured host termination overhead beyond the nominal attempt deadline. Neither finding is hidden by the positive C0 result.

## Scope, provenance and non-charge boundary

Accepted source and committed plugin revision: `d90bbd352d5722784180100bf5e431e91bc55210`. All 19 accepted product file SHA-256 fingerprints remain unchanged in the main checkout. No source-repository commit or push was made during this evaluation. Candidate-workspace commits are disposable test actions.

The original mock controls ran from the unchanged main checkout. A separate pinned sparse checkout added seven fixture-support files/edits; its bytes were copied and hash-verified into a second checkout so the two full runs could execute concurrently without shared mutable repositories, workspaces, homes or MXC state. The runner support adds explicit `c0-full` dispatch, telemetry guards and denied egress, avoids User-token lookup in Claude mock mode, and exposes Codex negative scenarios. Accepted lifecycle logic, cases/oracles, scoring formulas, skills and pinned MXC source/binaries remain unchanged. [Fixture support manifest](support/fixture-support-manifest.json), [exact support diff](support/fixture-support.diff), [fixture notes](support/README.md), [source fingerprints](source-fingerprints.json). Fixture support was **not promoted to the main checkout**.

Controllers used `-MockAgent -NoTelemetry`, fresh homes, and a verified pinned MXC build; they removed provider/Langfuse keys and used only a dummy OAuth sentinel for unchanged Claude's conditional User-token lookup. The actual workload executable was Python with the copied mock script, with no fallback to model execution. The real Codex binary was called only for version metadata. The `c0-full` runs additionally denied network egress. No inference endpoint, paid judge, live telemetry read/upload, or score publication was invoked. Billing-account readback was not performed; no claim about unrelated account activity is made.

Claude's original 99-call/630,023-token/$0.7112 fields are synthetic mock/parser outputs, not charges. Its full fixture has zero synthetic tokens/cost, yet the analyzer counts 27 assistant turns as `model_calls`; the fixture itself explicitly records 0 provider/model calls. Codex records zero mock usage and unavailable parser call counts. These fields are preserved and labeled, not overwritten to make them look like billing proof.

## Actual MXC result matrix

Oracle values below are per repetition when available; recorded runs repeat final oracle checks three times. Controller success is never used as contestant acceptance.

| Run | Child exit / reason | Host timeout seconds per invocation | Final C0 oracle | Metadata state |
|---|---|---|---|---|
| [claude-original](evidence/claude-original/run.json) | 0 / completed | 177 | 1 passed / 12 failed / 0 errors | finalized |
| [codex-original](evidence/codex-original/run.json) | 0 / completed | 177 | 0 passed / 0 failed / 13 errors | finalized |
| [claude-crash](evidence/claude-crash/run.json) | 3 / crash | 43 | 0 passed / 0 failed / 13 errors | finalized |
| [claude-timeout](evidence/claude-timeout/run.json) | 124 / timeout | 13 | 0 passed / 0 failed / 13 errors | finalized |
| [claude-refusal-zero](evidence/claude-refusal-zero/run.json) | 0 / provider_refusal | 43 | 0 passed / 0 failed / 13 errors | finalized |
| [claude-refusal-one](evidence/claude-refusal-one/run.json) | 0 / completed | 40, 36 | 0 passed / 0 failed / 13 errors | finalized |
| [codex-fail](evidence/codex-fail/run.json) | 1 / crash | 56 | 0 passed / 0 failed / 13 errors | finalized |
| [claude-timeout-injection-missed](evidence/claude-timeout-injection-missed/run.json) | 124 / timeout | 28 | 0 passed / 0 failed / 13 errors | finalized |
| [claude-timeout-oracle-fault](evidence/claude-timeout-oracle-fault/run.json) | 124 / timeout | 27 | not finalized: injected failure | incomplete |
| [claude-c0-full](evidence/claude-c0-full/run.json) | 0 / completed | 297 | 13 passed / 0 failed / 0 errors | finalized |
| [codex-c0-full](evidence/codex-c0-full/run.json) | 0 / completed | 296 | 13 passed / 0 failed / 0 errors | finalized |
| [codex-timeout](evidence/codex-timeout/run.json) | 124 / timeout | 12 | 0 passed / 0 failed / 13 errors | finalized |

The unchanged Claude `all,happy` control recorded 70 checks without mock failures but produced a stub, explaining 1/13 oracle success. Unchanged Codex `all` passed 8/8 runtime checks but generated no wordstat solution, explaining 13 oracle errors. These controls establish traversal/toolchain behavior, not C0 acceptance. The Windows venv launcher actually started under the pinned host; the older source comment alone did not establish a launcher failure.

## Full scripted C0 fixtures

Both independent workspaces contain contract-derived wordstat source/tests, five saved stage records, a current phase READY verdict, three saved domain replies, a consolidated PASS report, a Run Summary and a done heartbeat. Every review judgment is explicitly **SCRIPTED MOCK**. Real validator, pytest and candidate Git commands ran; no model reviewer was dispatched. Source and tests share the implementation commit. The actual child deadline/reserve environment exactly matches the runner record.

- Claude candidate commits: `e499bb0`, `e3d0961`, `cf2ac57`.
- Codex candidate commits: `e734137`, `b7b7841`, `c5b4f73`.
- Both workspaces were clean after completion; their summaries, command ledgers and scripted artifacts are snapshotted under [Claude evidence](evidence/claude-c0-full/) and [Codex evidence](evidence/codex-c0-full/).
- The isolated fixture's local regression suite passed **25 tests**, including old mock behavior, copied-to-config entrypoints, contract cases, deadline capture, telemetry rejection and mocked negative controls. [Log](support/verified-tests.log).

The two full runs still correctly keep the runner's `workflow_acceptance: not-established` and `reference_eligible: false`. The external artifact checks establish this scripted fixture's success; they do not turn it into a live-agent evaluation or native CLI discovery proof.

## Remediation behavior directly observed

- A single attempt ID, authorization reference and UTC deadline persist across allowed refusal recovery. Zero recoveries produced exactly one invocation. One authorized recovery produced exactly two invocations with timeouts **40 then 36 seconds**, sharing the original 45-second budget.
- Real Claude crash retained exit 3/reason crash; real Codex failing checks retained exit 1/reason crash. Both preserve captured evidence independently of analysis/acceptance.
- Real timeouts retained exit 124/reason timeout for both harnesses. Raw bytes and partial native traces remain available.
- A verified host-side oracle append fault after timeout retained `process_outcome: timeout`, child exit 124, capture bytes, `state: incomplete` and `postprocessing.oracle: failed`. [Injection verification](commands/claude-timeout-oracle-fault-verified-injection.json), [record](evidence/claude-timeout-oracle-fault/run.json). The earlier operator injection attempt used an unsupported PowerShell parameter and missed the window; it applied no fault and is retained as an additional timeout control, not claimed as successful fault injection.
- Every recorded run explicitly left workflow acceptance unestablished; mock process success did not silently accept failed C0 outputs.

## Findings and limits

### F1 — terminal step status is stale (P2, reproduced)

All finalized records retain `postprocessing.seed-oracle: in-progress`, even though seed checking completed before capture. For example [Claude original](evidence/claude-original/run.json) and [Codex original](evidence/codex-original/run.json), and both full fixtures. The source path is `run-lifecycle.ps1`: `Start-EvalInvocation` switches `active_step` to capture without completing the prior seed step; subsequent `Set-EvalStep` can no longer close it. `active_step: analysis` remains a last-step marker and does not prove a live process.

A bounded follow-up is to close the prior in-progress step at the capture boundary and assert that finalized records have no in-progress postprocessing entries. **No accepted main-source fix was made in this observation task.** Earlier offline acceptance is not evidence that this runtime inconsistency is absent.

### F2 — supplied timeout is bounded, exact deadline is not proved

The 15-second Claude attempt passed 13seconds to MXC, but measured contestant interval14.0298s and attempt elapsed15.5557s; finalization was separately3.1389s. Codex passed12seconds within a 15-second attempt and measured attempt elapsed15.7726s. Startup/termination overhead therefore exceeded the nominal budget by about0.56s/0.77s. Remaining-time flooring and no-reset behavior were observed; an exact zero-overrun or total-run wall-time guarantee was not. Synchronous oracle/finalization remains outside the contestant timeout as documented.

### F3 — mocks and scores have explicit limits

Original mocks are not full C0 positive fixtures and do not test model obedience. The isolated support provides a deterministic test actor, not a replacement model benchmark. No conclusion is drawn about model obedience, calibrated closeout reserve, live networking/telemetry delivery, paid native qualification, Linux/macOS behavior, or general descendant-cleanup guarantees. A post-run check found no matching live Python/MXC workloads for these test roots.

## Deterministic scoring and scope preview

The scorer was exercised in two modes, in separate derived outputs: trace-only `--no-rerun`, then fresh local task validation with the known pytest environment. Fresh validation passed **4/4 commands at the tasks' scorer-selected final candidate commits** for each fixture and produced artifact Quality 100. Both tasks selected `cf2ac57` for Claude and `c5b4f73` for Codex, with basis `last commit naming it (no Done move)`. The implementation commits are `e3d0961` and `b7b7841`; these passing final-snapshot commands do not establish validation at the earlier delivery. The trace-only pass's two apparent validation defects were superseded by that fresh evidence, without editing the retained draft.

**No QACT/parity ranking is accepted.** Four scorer items still require judgment, and scripted traces/empty telemetry observations do not establish live workflow adherence or consistency. Draft numeric composites remain machine artifacts only. No paid judge was called and no manual PASS was invented.

Fresh explicit initial scope sidecars bind the run, source hashes, attempt/segment/authorization, prompt/plugin identity and fixture evidence. With telemetry disabled, observations are explicitly empty and required coverage is unknown. Usage/calls/latency/backend/cost remain null in scoped output. Each harness's publisher dry run produced 8 preview IDs; repeat IDs matched, evaluator-version IDs differed, and `scores_verified` remained false. **No HTTP request or publication occurred.** [Scope-preview ledger](commands/scoped-preview-results.json), [derived scoped artifacts](scoped/).

## Evidence and continuation

[Machine metrics](metrics.json) list all 12 actual runs, original paths, budgets, outcomes, timeouts, durations, oracle counts and fixture labels. [Evidence manifest](evidence-manifest.json) binds the saved snapshots to exact SHA-256 bytes; 116 original declared artifact hashes were checked. [Controllers/logs](commands/) and [scoring outputs](scoring/) preserve commands, exit status, exceptions and previews. Captures are model-free test data and remain separate from historical live C0 scores 97.46/90.33/98.33.

No accepted main product code was changed, no source-repository commit/push was made, and the isolated fixture patch remains available for a separately scoped promotion decision. No further test or model run is scheduled. Report accuracy review is recorded in `review.md`.
