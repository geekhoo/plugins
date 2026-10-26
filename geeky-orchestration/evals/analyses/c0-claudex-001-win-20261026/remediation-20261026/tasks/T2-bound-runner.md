# T2: Bound execution and preserve evidence

## Task Name
One attempt deadline and recoverable runner records.

## Priority
P0. Second task, completing execution protection before any future paid run can be considered.

## Context
Process review R1/R2/R8; `run-baseline.ps1:250–345`; `run-codex-baseline.ps1:238–354`. Claude reuses the full timeout on refusal and writes the result late. Codex already provides a prepared record and `finally`; extend that pattern. [Source index](../references.md).

## Module/System
Existing PowerShell evaluation runners and their local output records.

## In scope
- `evals/scripts/run-baseline.ps1`, `run-codex-baseline.ps1`.
- At most one shared PowerShell helper for remaining time and atomic metadata writing.
- New offline runner tests; narrow QUICKSTART/runbook corrections.
- The optional deadline/reserve check at existing `geeky-implement` dispatch/phase boundaries, integrated after T1's skill edits.

Paths are relative to `geeky-orchestration/`. Parent-owned plan tracking updates accompany delivery.

## Dependencies
T1 for sequencing and shared skill ownership; no code dependency prevents offline runner design. One `geeky-coder` writer; no parallel runner, telemetry or workflow edits. T3 consumes the record contract defined here.

## Technical Notes
1. Record prepared state before spawning, then running state with attempt/segment ID, authorization reference, allowed recovery count, initial UTC deadline, waiver, whitelisted nonsecret configuration fingerprint and invocation list. Reuse existing profile/model fields. Never serialize credentials or the full environment.
2. Preserve the existing zero-retry default and owner qualification waiver. Before every allowed launch, recompute remaining seconds using elapsed monotonic time; skip launching if less than one whole second remains. Never pass zero to MXC, where zero means unlimited. Validate positive budgets; do not round upward beyond the deadline.
3. Pass identical neutral `GEEKY_DEADLINE_UTC` and `GEEKY_CLOSEOUT_RESERVE_S` fields to either harness through existing environment argument construction. Record those values. Reserve is configurable, smaller than the attempt budget, and advisory; proposed next-C0 setting is 900 seconds. At existing skill dispatch/phase boundaries, read these optional fields and prioritize required acceptance/closeout when in reserve; preserve incomplete state when time is insufficient. Exhausting the reserve never passes a gate. Workflows without these fields behave as before. It never extends the hard deadline. Add no further prompt change beyond T1's versioned output simplification; case contracts stay unchanged.
4. Wrap launch, capture and finalization so the child exit/timeout is saved before oracle, parsing, telemetry or diagnostics. Record failures in those later steps separately. A telemetry failure must not replace a known process timeout or successful child exit; process exit still does not establish workflow acceptance.
5. Write JSON through a same-directory temporary file and atomic replacement. Preserve last valid metadata and partial stream/stderr; mark unfinished records interrupted/unknown after explicit reconciliation, never completed. Preserve native transcripts, Git HEAD/status and artifact hashes where available without resetting or editing the candidate. Check no surviving writer before a later continuation.

## Acceptance Criteria
- A fake 10-second attempt consuming eight seconds passes at most two seconds to an authorized recovery; expiry launches no additional child. Zero authorized recoveries always launches at most once.
- Both launch paths persist prepared/running records. Exceptions before launch, during capture, during oracle/telemetry and before final replacement retain truthful metadata and existing raw bytes.
- Prepared-only and waived qualification paths keep their current no-extra-probe semantics. No generic transient retry is added.
- A retained timeout remains timeout when post-processing fails. All incomplete capture/analysis states are explicit.
- Hard wall, informational token and advisory closeout settings are distinguishable in records and docs. Record finalization duration separately from contestant time; preserve existing step-specific timeouts and explicitly report unbounded steps, including current synchronous oracle execution.
- Deadline context is equivalent across harnesses; reserve expiry cannot mark an unmet gate complete. The skill's no-context path preserves ordinary workflow behavior.

## Tests/Validation Before Next Task
Add `evals/scripts/test_run_lifecycle.py` using the repository's pytest/subprocess pattern with fake clock/host injection. It must execute both runners through stubbed external boundaries, with all provider and live telemetry calls prohibited. Cover timeout rounding, retry counts, exceptions and atomic replacement. Command from plugin root:

```powershell
python -m pytest -q evals/scripts/test_run_lifecycle.py
```

Record exact command/results and touched file hashes. Existing preparation/waiver regressions are selected by the implementation's changed paths. Do not invoke either runner with real MXC, provider, candidate-oracle or live telemetry boundaries; actual runner scripts with fully stubbed boundaries are required here.

## Out of scope
New state-machine framework, event journal, generic retry/backoff, token supervisor, universal post-processing cancellation, host upgrade, cross-platform cleanup guarantee, paid smoke, auto-resume or historical record edits.

## Reviewer focus and stop conditions
Inspect actual host timeout arguments and exception paths; do not accept helper-only proof. Stop if the patch requires changing the MXC pin, weakening containment, recreating authorization, or silently discarding partial evidence. Preserve unknown outcomes after hard host death; `finally` is not a power-loss guarantee.

## Definition of Done
Offline AC evidence passes; the shared clock/record contract is documented for T3, and the optional skill check is consistent with T1. Save evidence in task notes. Task waits In Review until the phase reviewer accepts it.

## Estimate
0.75–1.5 focused engineering days, including tests; estimate only.
