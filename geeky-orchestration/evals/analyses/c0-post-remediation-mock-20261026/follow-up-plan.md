# Minimal C0 follow-up plan

2026-10-26. Planning only, written directly without a skill. Source baseline: `d90bbd352d5722784180100bf5e431e91bc55210`. This plan reconciles the later Windows MXC observations with the accepted remediation; it does not rewrite the original frozen task contracts or historical acceptance.

**Outcome:** remove the confirmed terminal-record defect, exercise task-commit selection correctly, and make current claims match the evidence. Keep the existing runners, scorer, telemetry tools and workflow. Target roughly one focused engineering day, allowing up to two if fixture integration needs more work; estimate only. No model tuning, new framework or paid evaluation is needed for these corrections.

## What remains open

| Item | Evidence / current disposition | Smallest resolution |
|---|---|---|
| F1: finalized records retain `seed-oracle: in-progress` | Confirmed in both harnesses. `Start-EvalInvocation` replaces the active step without closing the successful seed step. | Repair that transition and add terminal-state assertions. |
| F2: exact deadline cutoff is unproved | Remaining-time/no-reset works, but observed attempt overruns include 0.56/0.77 seconds on 15-second cases and 1.22/2.54 seconds on 30-second cases. | Define the measured/request boundary precisely; preserve overrun evidence and test expired-recovery behavior. No invented grace period or absolute cutoff claim. |
| H1 fixture coverage gap | Fresh 4/4 commands pass at final docs commits because Done transitions are unrecognized; earlier implementation-commit validation is not demonstrated. | Capture actual task transitions in a supported trace shape, then assert positive and negative selected-commit behavior. |
| Positive fixture is not maintained in main | `c0-full` and its tests exist only in two isolated support checkouts. | Selectively integrate the necessary mock-only support with its guards and tests; preserve the original saved support/evidence. |
| Historical full scorer replay | Prior warning remains open; synthetic C0 results do not resolve missing retained validation-cache evidence. | Check existing retained inputs once. Replay from valid saved inputs if available; otherwise identify the exact missing input and keep that warning open. |
| Live telemetry/readback compatibility | Existing unit tests and eight-ID previews do not establish live delivery; `scores_verified` correctly remains false. | Retain as unverified. Resolve only through a separately authorized telemetry-only check if live publication is needed; never rerun a contestant to repair delivery. |
| Model behavior and speed | Scripted review/closeout is not model-compliance or savings evidence. | Preserve this limit; measure only during a separately authorized future evaluation. |

## Work order

### 1. Fix the lifecycle defect and align the deadline claim

Scope: `geeky-orchestration/evals/scripts/run-lifecycle.ps1`, existing `test_run_lifecycle.py`, and only the related QUICKSTART/runbook passages.

- Close the successfully completed prior step when entering capture. Do not convert failed/interrupted/unknown work to completed during finalization.
- Extend both harness test cases to require a completed seed step at capture and no orphaned `in-progress` post-processing entries in finalized records. Preserve seed failure, crash, timeout and post-processing exception semantics.
- Document the actual timing boundaries: remaining timeout is floored at invocation preparation; measured invocation time includes record handling and the synchronous MXC call through return; finalization is recorded separately. Another launch after budget exhaustion is prohibited. The measurements do not isolate startup from termination overhead or prove an upper bound on excess.
- Add a fake-host overrun case proving that elapsed time remains truthful, timeout remains the process outcome and an expired attempt receives no further recovery. This is accounting proof, not proof of exact host termination.

Done: existing lifecycle regressions pass, new assertions expose the old defect and pass the fix, and docs make no unsupported zero-overrun or universal cleanup claim. If an absolute process-stop deadline is required beyond this launch contract, record it as a separately scoped requirement; do not silently weaken the promise or invent a shutdown margin.

### 2. Make the existing full fixture a useful maintained regression

Scope: selectively reuse the seven-file mock-support change saved in `support/fixture-support.diff`; limit source edits to the existing mock actors, their tests and explicit mock-only runner wiring. Do not import the captured patch wholesale or alter accepted production lifecycle/scoring rules to satisfy the fixture.

- Preserve `SCRIPTED MOCK` labels, Python-only execution, `-MockAgent -NoTelemetry`, fresh isolated roots and denied egress for `c0-full`. Keep existing mock scenarios working; no model-executable fallback or credentials required.
- Record actual successful task/kanban transitions and their command results in the existing parser-supported shape. Do not manufacture timestamps, ownership or Done anchors. Keep source and required tests in the functional delivery commit.
- Positive fixture: H1 selects the intended implementation commit, and all declared commands pass there. Negative fixture: a required test added only later causes the selected earlier snapshot to fail even if final HEAD passes. Assert full selected SHAs; keep H1 unchanged.
- Retain original captured scores, snapshots and the previously disclosed final-commit limitation. New corrected fixture results go to a fresh derived-output folder.

Done: focused mock/trace/scorer regressions pass; supported Done evidence selects the intended snapshot; the negative case prevents final-HEAD substitution. New synthetic composites remain ineligible for a model ranking.

### 3. Verify only affected paths and reconcile the records

Use `C:/Python314/python.exe` with the verified pytest environment. Run the affected existing lifecycle/mock/scorer tests once after changes; save commands, exits and tested hashes. If real MXC confirmation is authorized with implementation, bound it to two full positive fixtures (one per harness) and one relevant timeout-plus-post-processing failure case, using new isolated roots. Do not repeat the entire 12-attempt matrix without a new failure requiring it.

Record current status in this analysis folder's handoff/README and link the follow-up from the earlier remediation handoff/board. Preserve original frozen plans and dated reviews. Distinguish **implementation accepted offline**, **real MXC integration findings**, **synthetic fixture results** and **still-unverified live behavior**.

Close F1 only with fresh passing evidence. Record F2's supported boundary and remaining absolute-cutoff limitation explicitly. Close the H1 fixture gap only when its selected implementation SHA is verified. Keep historical-replay, live-telemetry and model-behavior warnings open unless their own evidence exists. Do not turn retained counts, a dry-run publisher preview or a scripted PASS into fresh proof of those claims.

Stop when these bounded checks and record updates pass. One implementation writer avoids shared runner/mock files and test resources; independent review can use the saved diff/evidence afterward. No extra review layer or broad hardening pass.

## Sources and authorization

- [Integration report](report.md), [machine metrics](metrics.json), [accuracy review](review.md), [fixture support](support/README.md).
- [Original remediation handoff](../c0-claudex-001-win-20261026/remediation-20261026/handoff.md), including accepted offline evidence and the two accounting warnings.
- Source anchors: `run-lifecycle.ps1:48–116`; both runners' seed-oracle/capture boundaries; `test_run_lifecycle.py:225` (current success assertion lacks step-status checks); report's deterministic-scoring section for selected final commits.

The current user request authorizes grouped commits/push of existing completed work and this planning document. It does not authorize implementing this follow-up, promoting fixture code, running another workload, calling a provider/judge, or accessing/publishing live telemetry. Historical C0 scores remain 97.46 / 90.33 / 98.33.
