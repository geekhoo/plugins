# T3: Keep accounting and publication trustworthy

## Task Name
Explicit evaluation scope and verified score delivery using existing tools.

## Priority
P1; required before new comparisons/publication.

## Context
Process review R3/R5/R6/R8; continuation `evaluation-inputs.json`; comparison timing/usage section. Existing cache validates task SHA, full commit, command and source/output hashes. Score IDs currently use session/name only; telemetry `delivered` means observations > 0. [Source index](../references.md).

## Module/System
Evaluation metadata, parity/report outputs and existing Langfuse publication/replay.

## In scope
- `evals/scripts/parity-eval.py` and a small scope validator/helper if needed; reuse `analyze-run.py`, `codex-trace.py` and existing source-reviewed derivations.
- `evals/telemetry/langfuse-scores.py`, narrow `telemetry.ps1`/README changes.
- Existing parity/trace/telemetry tests and new score-publisher tests.
- No `score-run.py` cache redesign; change its consumers only when necessary.

## Dependencies
T2's attempt/segment metadata and T1's evidence/output conventions. Sequential writer. Fake telemetry clients only during implementation verification. Scope metadata records prompt hash and plugin fingerprint so the future output contract cannot be mistaken for the historical C0 baseline.

## Technical Notes
1. Generalize the existing `evaluation-inputs.json` into a small validated sidecar: schema, scope ID/kind, parent scope, authorized segment intervals, source paths/hashes, cutoff/ownership derivation and source ancestry. Label reported runtime, tokens, calls, latency/idle spans, commits and coverage with source/population and additive status. A shared default scope plus overrides is sufficient; do not wrap every internal event.
2. For resumed inputs, accept explicit source-reviewed ownership where automatic extraction is unsupported. Reject ambiguous duplicate ownership and unsupported addition; never use timestamps alone to infer novelty. Reuse the existing C0 logical input and observation derivation rather than building a universal merger. Missing sources make completeness unknown and block claims that require them.
3. Preserve all historic files/IDs. New publication requires an explicit scope. Derive deterministic IDs from session + scope + evaluator version + score name, attaching input/parity hashes in metadata. Repeated publication of the same scope is idempotent; a different scope/version cannot overwrite the initial attempt. Historical legacy IDs remain read-only unless separately authorized for migration.
4. After an authorized publication, read back expected IDs and compare session, scope, evaluator/input hashes, names and values. Missing/mismatched results remain pending/failed. Implement this with the current client, not another service; mock HTTP in tests.
5. Distinguish observations present, required coverage and scores verified. Retain compatibility for the existing `delivered` field but document its limited meaning. A zero-exit hook or stable poll count cannot establish complete delivery. Use existing flush/replay from healthy local captures; leave outages pending and provide the existing operator command. No inference is allowed in telemetry recovery.

## Acceptance Criteria
- Retained C0 scores remain Codex 97.46, Claude initial 90.33, Claude cumulative 98.33; formulas, denominators, original input hashes and selected-task failures remain unchanged.
- Source fixture retains 438 excluded history rows, 1612 logical rows and 1485 observations (678 previous + 807 continuation). Parent requests are labeled 42 fresh + 48 historical, not 90 fresh or an all-agent total.
- Cumulative time/commits cannot be combined silently with continuation tokens; unknown cumulative tokens/backend/cost remain N/A.
- Fake publication twice produces the same IDs in one scope; initial/cumulative scopes differ. Fake GET responses with one missing ID, wrong hash or wrong value fail verification.
- DNS failure, partial delivery and hook exit 0 without observations remain pending; repeated telemetry recovery invokes no contestant/provider executable.

## Tests/Validation Before Next Task
From plugin root, use existing files plus the new publisher test module:

```powershell
python -m pytest -q test_score_run.py evals/scripts/test_parity_eval.py evals/scripts/test_codex_trace.py evals/scripts/test_process_replay.py evals/telemetry/test_langfuse_run.py evals/telemetry/test_langfuse_coverage.py evals/telemetry/test_langfuse_scores.py
```

Validate retained manifest counts/hashes and comparison scores in an isolated derived-output directory. Use cached evidence only; do not execute candidate validation/oracles, fetch live Langfuse data, publish scores, or rerun a contestant. If retained derivation inputs are unavailable, report exactly which invariants were checked and leave full replay acceptance open.

## Out of scope
Historical score migration/republication, formula changes, generic trace graph, arbitrary fork support, outbox/acknowledgement infrastructure, new tracer, live network repair, dashboard and billed-cost estimation.

## Reviewer focus and stop conditions
Check ambiguous ownership and scope-ID collisions, legacy compatibility and publication error handling. Reject unsupported success/completeness claims. Stop on changed source hashes, altered historical verdicts, required live calls or missing replay evidence.

## Definition of Done
Scoped metadata and publisher tests pass offline; retained C0 invariants are checked; touched telemetry/runbook guidance is reconciled. All three tasks receive a phase verdict, then final implementation review under the existing workflow. No paid-run or publication authorization is inferred.

## Estimate
0.75–1.5 focused engineering days, including tests; estimate only.
