# T3 implementation and offline validation

Verdict: implementation ready for parent task/phase review. No task acceptance,
phase advancement, final-review verdict, publication authorization or paid-run
authorization is inferred. Parent owns kanban/handoff/heartbeat and commits.
No commit, push, provider/judge/contestant invocation, candidate validation/oracle,
live telemetry read/publication or historical derivation-script execution occurred.

## Changed behavior and bounded interpretation

- `evals/scripts/evaluation_scope.py` validates a small `geeky-eval.inputs/1`
  sidecar: initial/continuation/cumulative identity, parent, authorized intervals,
  hashed sources and ancestry, explicit ownership, and default/override metric
  source/population/additive/completeness labels. Duplicate source identities,
  duplicate logical ownership, cycles, unbound inputs, changed hashes and
  unsupported metric addition fail closed. Missing sources produce unknown
  completeness and block dependent evaluation/publication. No arbitrary merger
  is supplied. Source-reviewed declarations require hashed review evidence;
  their correctness still depends on source review, never timestamps alone.
- `parity-eval.py --scope` binds all supplied run/observation/score/manual files
  before evaluation and emits the sidecar labels. Mismatched or incomplete
  populations yield null/N/A efficiency values; no cumulative usage is inferred.
  Prompt/plugin hashes bind the configuration. Future T2 execution records also
  require matching attempt, segment and authorization reference. The historical
  formula AST is unchanged; legacy unscoped evaluation remains available.
- Publisher `--scope` is required even for preview. IDs hash the structured tuple
  `[session, scope, evaluator-version, score-name]`; no legacy ID is written.
  Existing scoped IDs with different bindings/values block all POSTs. New POSTs
  are followed by exact Scores v3 GET readback, including pagination, session
  subject, name, data type, typed value, scope/evaluator and sidecar/parity hashes.
  BOOLEAN writes remain 0/1, while v3 readback requires JSON booleans, per the
  installed `@langfuse/cli` 4.35.0 API contract. Unsupported readback, missing IDs,
  mismatches and HTTP/DNS/partial delivery stay pending with exit 3; no retry or
  fallback claims delivery. `--output` preserves that status; dry run is preview.
- `Save-EvalTelemetry` retains `delivered` as observations > 0 only, separates
  presence/required coverage/scores, and clears stale counts and claims on failed
  recovery. It never establishes score readback. Fake execution exercises the
  actual PowerShell function twice for DNS, zero-observation, partial-coverage
  and covered cases, with a deny-by-default fake Python boundary.
- Telemetry README now describes those states, scope fields and existing
  no-inference Codex/Claude flush/replay commands. Parent explicitly confirmed
  the packet's telemetry/runbook DoD permits the one-line command correction at
  `evals/mxc-litellm-runbook.md:145`: add `--scope <evaluation-inputs.json>` and
  `--output <analysis-dir>/score-readback.json`. This is T3's sole runbook edit;
  all earlier T2 runbook changes are preserved. No frozen task/plan was edited.

## Exact validation and tested state

Workdir: `C:/Users/gerald.khoo/geekhoo-plugins/geeky-orchestration`.
HEAD: `53fb54b5f30ab0397c1fc154e83a6af942797322` with existing T1/T2 working-tree
changes preserved. Python `C:/Python314/python.exe` 3.14.7, pytest 9.1.1,
PowerShell 7.6.5, Windows 11 build 26300. The complete product/evidence file
SHA-256 map, exact commands, exit codes and result text are in
`T3-evidence/tested-state.json`. This identifies uncommitted tested bytes, not
an uncreated commit. Logs contain stdout and stderr.

1. `& C:/Python314/python.exe -m pytest -q test_score_run.py evals/scripts/test_parity_eval.py evals/scripts/test_codex_trace.py evals/scripts/test_process_replay.py evals/telemetry/test_langfuse_run.py evals/telemetry/test_langfuse_coverage.py evals/telemetry/test_langfuse_scores.py`
   - Exit 0: **130 passed, 1 skipped in 16.47s**.
     `T3-evidence/required-suite-final.log` and `.exit.txt`.
     The optional native-proof fixture requires `CODEX_NATIVE_PROOF`; its skip
     supplies no new native/runtime proof. No service was contacted by tests.
2. `& C:/Python314/python.exe evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/tasks/T3-evidence/check-retained.py`
   - Exit 0: **retained-invariants-verified**.
     `T3-evidence/retained-invariants-final.log`, `.exit.txt` and
     `T3-evidence/retained-invariants.json`. Read-only Git/source access and local
     reconstruction only; the frozen `derive_inputs.py` was read and hash-checked,
     never imported or executed because it rewrites raw `run.json`.
3. `& pwsh -NoProfile -File evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/tasks/T3-evidence/check-static.ps1`
   - Exit 0: PowerShell parse, five Python AST parses and touched-file
     `git diff --check` passed. `T3-evidence/static.log` and `.exit.txt`.
     Git emitted ordinary LF-to-CRLF notices for two Markdown files.

An initial scoped development run passed 26 tests (`development.log`); the first
required suite passed 128 (`required-suite.log`). Final 130-case evidence above
supersedes intermediate successful runs after scope-collision, T2 identity and
stale-count checks were added. Initial checker authoring failures were a wrong
parent-directory index (`ModuleNotFoundError: evaluation_scope`, exit 1), then
missing the frozen derivation's explicit malformed-JSON-row skip
(`JSONDecodeError: Unterminated string`, exit 1). Both were corrected in the
isolated checker; original captures were never changed. Their full error outputs
are retained in the agent tool transcript; those early scratch log paths were
subsequently overwritten and are not presented as durable final evidence.

## Retained evidence and AC mapping

| AC | Evidence and limits |
|---|---|
| 1. Scores, formulas, denominators, hashes and selected failures unchanged | Read-only checker asserts comparison and all three retained parity objects are equal; recomputes **97.46 / 90.33 / 98.33** from retained raw quality and check populations. Adherence fractions **45/46, 37/42, 42/42**; weighted consistency denominator **19** each. Current parity formula AST equals HEAD. All four historical evaluator hashes match Git HEAD bytes with original Windows newline representation; comparison's hash records are untouched. Codex T1 still has validation exits **[4,0]**, including the selected `python -m pytest tests/test_core.py -q` failure. This is source-bound retained evidence, not a fresh candidate test. |
| 2. Logical rows/observations/parent populations | Native source SHA-256 match the frozen manifest. Isolated reconstruction gives **438 excluded history rows, 1612 logical rows**, logical SHA **e6af0c50875a4cd766753e037ff87e21f8f6a3b32ab7a715f48ec420a029c876** preserving CRLF. Observation reconstruction equals retained objects and exact SHA **2755c9f7560376c190a1764119cc9681227f7d6e01995d676fa5f91e632243b3**: **1485 = 807 continuation + 678 previous**. Raw current parent assistant IDs partition into **42 fresh, 48 historical, 0 shared**; explicitly not an all-agent total. This reproduces the frozen source-reviewed C0 derivation; cutoff alone is not general novelty proof. |
| 3. Mixed metrics/N/A | `test_scope_labels_block_mixed_cumulative_metrics` and retained isolated scope verify cumulative wall time **7180s**/commits survive while tokens/calls/latency/backend/cost are null for unsupported populations. Metadata carries continuation population labels. Original `comparison-metrics.json` unknowns remain N/A; no historical report rewritten. |
| 4. Idempotent scoped IDs and exact readback | Fake urllib HTTP exercises the real Client encoding: two publications use identical scoped IDs, cumulative and evaluator-version variants differ, and the legacy score remains unchanged. Missing ID, wrong input hash/value/type/session, wrong scope/evaluator/parity hash, unsupported v3 and scope-ID reuse with changed input all fail verification. Changed bindings cause GET-only preflight, zero POSTs. |
| 5. Recovery pending/no inference | Fake DNS and partial POST remain pending. Actual Save-EvalTelemetry function executes twice with DNS failure, hook `exit 0` plus no observations, partial coverage and covered observations; stale local summaries cannot establish delivery. Every fake executable call is explicitly restricted to existing `langfuse-run.py` and `langfuse-coverage.py`; no contestant/provider executable is invoked. Scores remain independently pending. |

Original manifest SHA: `a20b1e8d8099a7d7890b29f3b0b16ba289de7c4f99b4cf09f443929085cd8685`.
Original comparison SHA: `d01e02ad310dfbd96903f9c22b1aa763c5edfb99570cdfa84a2ad41517f215a4`.
The checker fingerprints historical analysis/native files before and after and
asserts no change. A final read-only `git diff --exit-code --` over the historical
comparison, Codex/Claude analysis and baselines also exited 0.

## Evidence placement and deferred boundaries

Large reconstructed payloads are at the verified ignored path
`C:/Users/gerald.khoo/geekhoo-plugins/outputs/remediation-20261026/T3-derived`.
Parent requested this placement; the resolved move destination was checked to
remain under repository `outputs` before Move-Item. Original sources were never
moved/deleted. The packet retains reconstruction code, compact source/derived
hash manifest, logs and tests; do not commit the redundant ~50MB payload.

Full `score-run.py` replay acceptance remains **open**: the retained analysis and
scoring-input folders have no `validation-cache.json`, and candidate validations
and oracles are expressly prohibited. All invariants actually proven are listed
above. No cache redesign or invented candidate verdict is supplied. No live
instance compatibility/delivery, future model compliance, billed cost, universal
fork merge, outbox or historical migration is claimed. Task/phase/final review
and repository tracking reconciliation remain with the parent.

## Shared phase review - 2026-10-26

Reviewer: /root/phase_review (read-only canonical code-reviewer). Verdict: PASS for AC1-AC5; 130 passed / 1 optional skip; retained invariant and static checks passed. No blocking findings with confidence >=80; no optional changes requested. Phase: READY TO ADVANCE. Reviewer inspected the stable aggregate diff, untracked source/tests, saved commands/results and intentional sequential shared-file changes; no broad reruns or external calls. The full AC evidence remains in this note's mapping. Commit byte binding and final impl-review follow this phase gate.

## Parent commit binding - 2026-10-26

Phase commits: 6799ec22a0d202cdd05c98fe6db9eac2853816b2 (workflow), 572bc267d3d782fce720a19988283554a27c4729 (runners and required tests), 15760959e3bb6bb2094eb8e9a0153e200d9ecb28 (scopes/publisher and required tests; shared runbook). Parent compared all 19 product HEAD Git blobs with clean-filtered blobs computed from the tested working files, and separately verified all working-file SHA256 digests unchanged. No mismatch required an isolated rerun. Raw evidence is -text under existing .gitattributes; captured CRLF/trailing output bytes were retained. Product/notes whitespace passed with cr-at-eol and raw evidence excluded; raw diagnostic formatting is preserved, not reported as source whitespace success. Message gates passed before each commit. Final impl-review pending.

## Final acceptance and closeout - 2026-10-26

Task Done. /root/phase_review accepted its ACs/tests and the phase READY TO ADVANCE; all DoD/kanban gates passed. Final impl-review at 15760959e3bb6bb2094eb8e9a0153e200d9ecb28: /root/final_workflow PASS, /root/final_runner PASS, /root/final_accounting PASS WITH WARNINGS; Overall PASS, zero required findings. Two nonblocking accounting warnings retained (full scorer replay open; live compatibility/delivery unverified). Full domain findings/revision anchors are in ../review-impl.md. No optional fixes, test repetitions, new review process, paid run, publication or push. Later record-only commit preserves all 19 tested product code/test blobs; final plugin identity can be retrieved from git HEAD for a separately authorized future baseline.
