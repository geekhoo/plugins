# T2 implementation notes

State: bounded implementation and offline validation complete; **awaits parent task/phase review in In Review**. This note does not issue acceptance, move lanes, commit or push. No real MXC, contestant, provider, candidate oracle, judge or live telemetry was invoked.

Environment: Windows, PowerShell 7.6.5, `C:/Python314/python.exe`, Python 3.14, pytest 9.1.1. All commands below ran from `C:/Users/gerald.khoo/geekhoo-plugins/geeky-orchestration`. HEAD remains `53fb54b5f30ab0397c1fc154e83a6af942797322`; baseline `8fff98b0f087f148d4f416f512dc9988d61a57aa` was verified through Git, without reset. T1's working-tree edits were retained; only the two shared skill paths received the optional T2 context addition.

## Ownership and assumptions

One product writer owned T2. Parent owns kanban/handoff/heartbeat and integration/review/commits. Source `AGENTS.md`, canonical coder instructions, frozen task, plan and references were read first. The repository-root AGENTS.md does not exist; plugin source AGENTS.md supplies the shared terminology. No event journal was created. The memory registry was consulted for durable-source orientation; current paths, source and Git state were verified directly. No historical run or command was treated as fresh runtime evidence.

The deadline begins at the first prepared metadata write, before configuration/export/preflight; time spent subsequently preparing, checking the seed or handling an authorized refusal consumes the original budget. This is a conservative interpretation of one attempt deadline. Host-independent monotonic time determines the floored child timeout; the UTC value is neutral contestant context. AuthorizationReference is an optional record reference, never newly granted authorization. Default recovery count stays zero; Codex has no recovery launch added.

## Product changes and T3 record contract

Exactly eight product files changed:

- `evals/scripts/run-baseline.ps1`: positive budget validation preserves explicit zero as an error; early prepared record, protected configuration/launch/capture/analysis, floor remaining time for initial and authorized refusal launches, immediate child outcome persistence, separate postprocessing failures, atomic metadata merge. Existing refusal-only/exit-zero condition and default zero recoveries remain.
- `evals/scripts/run-codex-baseline.ps1`: same deadline context, early protected prepared/running records, durable child result before parsing and later work, retained process timeout/crash reason, explicit incomplete capture/analysis/diagnostic statuses, safe lock disposal. Qualification waiver still bypasses probes and clears runtime qualification claims; no extra probe or retry was added.
- `evals/scripts/run-lifecycle.ps1`: the single shared PowerShell helper supplies the monotonic clock, floored remaining seconds, small record operations and same-directory atomic replacement. It does not schedule, retry, publish or automatically reconcile anything.
- `evals/scripts/test_run_lifecycle.py`: actual runner subprocess fixtures with local fake executable/service boundaries; runner bytes are copied unchanged. Only the helper clock expression and atomic replacement operation are injected in disposable copies. Python/host calls outside the explicit fixture allowlist fail. Real Python is used only for pytest; local Git/tar seed/export operations remain real in disposable miniature repositories. Fixture seed commits are isolated test inputs; no product repository commit was created.
- `evals/QUICKSTART.md` and `evals/mxc-litellm-runbook.md`: narrow correction of timing/recovery/preparation/qualification expectations and the local record/recovery contract. Historical results are unchanged.
- `skills/geeky-implement/SKILL.md` and its existing `references/execution-protocol.md`: optional context consumption at existing dispatch/phase boundaries. T1's prompt and acceptance changes remain intact.

`run.json` keeps `geeky-eval.baseline/1` and adds `execution.schema = geeky-eval.execution/1`:

| Field | Meaning for T3 |
|---|---|
| `attempt_id`, `segment_id` | Local attempt/segment identities; never proof of a cumulative population by themselves. |
| `authorization_reference`, `allowed_recoveries`, `qualification_waiver` | Retained operator reference, bounded recovery allowance and existing waiver status/reason. Null authorization is unknown, not newly reconstructed authorization. |
| `initial_deadline_utc`, `hard_wall_budget_s`, `closeout_reserve_s`, `closeout_policy` | Original hard attempt deadline/budget and advisory reserve within it. No extension. |
| `configuration`, `configuration_sha256` | Whitelisted model/reasoning/worker/reviewer/provider/mock and budget/recovery settings. No credentials/full environment. Existing prompt/plugin/profile/model fields remain top-level. |
| `invocations[]` | Invocation ID, initial/refusal-recovery kind, positive floored timeout, UTC start/end, exit code and outcome. Empty means no child launch record. |
| `process_outcome` | `not-started`, `success`, `timeout`, `crash`, or `unknown`. This is separate from analysis/acceptance. |
| `capture_status`, `postprocessing`, `active_step`, `failure` | Raw-capture state and per-step completed/in-progress/failed/incomplete/pending statuses. Exception failures retain step/message. Nonzero native-capture/diagnostic results remain explicitly incomplete/failed. |
| `state` | Prepared, running, process-finished, deadline-exhausted, incomplete, or finalized metadata lifecycle. Finalized metadata is not workflow completion. |
| `workflow_acceptance` | Always `not-established`; a child success or elapsed reserve cannot accept a task/gate. |
| `contestant_time_s`, `attempt_elapsed_s`, `finalization_time_s` | Summed observed child intervals, elapsed budget consumption through child exit, and subsequent finalization duration. Unknown capture leaves contestant duration unknown. |
| `step_timeouts_s` | Oracle/Claude host flush/host telemetry/coverage/analysis are unbounded (null); existing Codex replay 900, sandbox hook 600 and telemetry polling wait 120 remain distinguishable. Poll wait is not a process-kill deadline. |
| `writer_pid`, `writer_host`, `reconciliation_required` | Local writer identity and conservative unknown-capture flag. They never authorize automatic continuation or prove absence of a surviving descendant. |
| `workspace_head`, `workspace_status`, `artifact_sha256` | Available final Git state and SHA-256 of retained output files/native captures, with no workspace reset or candidate edits. |

Child exit/timeout is persisted before oracle/parsing/telemetry/diagnostics. Timeout/crash stays the top-level process exit reason on every subsequent write. Analyzer output now uses its existing `--out derived/` option; only a valid derived record is merged into the canonical metadata through atomic replacement, preserving analyzer trace-completeness fields. `analysis.json` remains available at the conventional root path. Failed final replacement leaves the last valid record and raw files intact; an in-progress last record must be reconciled, not called completed. A hard host death cannot be repaired by `finally`. Before a separately authorized continuation, verify no surviving runner/MXC/contestant writer, then explicitly reconcile metadata/raw bytes/workspace; unknown remains unknown. No automatic continuation or paid replay is supplied here.

## Exact validation commands and results

Full stdout/stderr logs and exit codes are under `tasks/T2-evidence/`; `tested-state.json` contains the exact source SHA-256, revision, environment and principal commands. Successful final commands:

1. `& C:/Python314/python.exe -m pytest -q evals/scripts/test_run_lifecycle.py`
   - Exit 0; **43 passed in 172.98s (0:02:52)**. `T2-evidence/lifecycle-final.log`.
2. `& C:/Python314/python.exe -m pytest -q evals/scripts/test_codex_run2_prep.py evals/scripts/test_codex_auto_process.py`
   - Exit 0; **15 passed, 1 skipped in 13.85s**. `T2-evidence/preparation-regressions.log`. The optional retained-run read-only test was skipped because `CODEX_RUN2_SOURCE` was not provided; it is not actual runner proof. Actual preparation/waiver proof is in command 1.
3. `& pwsh -NoProfile -File evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/tasks/T1-evidence/check-prompt.ps1`
   - Exit 0. `T2-evidence/prompt-parity.log`. Executes only each actual runner's render/hash assignment ASTs. Both rendered SHA-256 values are `4d8ebd2f16b83a14c8f7278935105ab31e86b01e2b51098a7d7af0f07a17cf2e`; frozen historical render check also passes. No runner entry point/provider/telemetry executed.
4. PowerShell parse and whitespace check (full command):

   ```powershell
   $files = @('evals/scripts/run-baseline.ps1','evals/scripts/run-codex-baseline.ps1','evals/scripts/run-lifecycle.ps1')
   foreach ($file in $files) {
       $problems=$null
       [Management.Automation.Language.Parser]::ParseFile((Resolve-Path $file),[ref]$null,[ref]$problems) | Out-Null
       if ($problems) { $problems; exit 1 }
       Write-Output "PARSE PASS $file"
   }
   git diff --check -- evals/scripts/run-baseline.ps1 evals/scripts/run-codex-baseline.ps1 evals/scripts/run-lifecycle.ps1 evals/scripts/test_run_lifecycle.py evals/QUICKSTART.md evals/mxc-litellm-runbook.md skills/geeky-implement/SKILL.md skills/geeky-implement/references/execution-protocol.md
   ```

   - Exit 0; three parser PASS results and no whitespace defects. `T2-evidence/parse-diff.log` retains Git's ordinary line-ending notices.
5. `& C:/Python314/python.exe evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/tasks/T2-evidence/collect-evidence.py "$env:TEMP/pytest-of-gerald.khoo/pytest-685"`
   - Exit 0; **43 actual-runner fixtures retained, 86 copied runner files verified byte-identical to final source**. `T2-evidence/collection.log`. Small records, raw partial stream/stderr, host invocation arguments and prepared/failed-replacement observations are retained under `T2-evidence/samples/`; disposable Git repositories and environments were not copied.

Earlier development commands all used `& C:/Python314/python.exe -m pytest -x -q evals/scripts/test_run_lifecycle.py`, with full logs retained as `lifecycle-first.log` (exit 1, fixture quoted PowerShell flags bound positionally), `lifecycle-second.log` (exit 1, fixture advanced-function common parameter collided with pytest `-p`), `lifecycle-third.log` (exit 1 after 27 passing cases, authoring-time old fixture/new derived-output contract mismatch), and `lifecycle-fourth.log` (exit 0, 34 passing intermediate cases). These are diagnostic history, not final tested-state proof. Final suite and fixture verification above supersede them; no product change followed the final suite.

## AC mapping

| AC | Evidence and practical limit |
|---|---|
| 1: 10-second attempt, eight consumed, at most two recovery; expiry/zero-recovery launch bounds | `test_actual_claude_recovery_uses_floor_of_remaining`: 8 -> timeouts [10,2], 8.1 -> [10,1], 9.1/10 -> one launch; every invocation keeps the same UTC deadline. `test_no_authorized_recovery_never_relaunches`, `test_expired_attempt_never_launches`, `test_first_launch_also_floors_remaining_attempt_time` execute the real launch paths; both harnesses pass only positive floored host timeouts. |
| 2: prepared/running, exceptions and atomic raw retention | Both actual runners are observed from the fake seed boundary before launch and fake host at running. Configuration, seed, capture, oracle, telemetry, analysis and final-replacement faults are exercised by `test_actual_runners_preserve_truth_on_failures`. Nonempty partial stream/stderr survives. Failed replacement's last record is byte-equal to the pre-replacement snapshot; no orphan temp remains. Additional Codex preflight/build/native-capture failures exercise protected prelaunch/capture boundaries. |
| 3: preparation/waiver no-extra-probe semantics, no generic retries | `test_prepare_only_has_no_oracle_or_workload` for both harnesses proves zero oracle/host calls. `test_waiver_retains_no_extra_probe_semantics` executes the actual waived Codex path against a deny-by-default fake Python boundary, proving a single host launch and null diagnostics/false runtime qualification claims. Existing 15 preparation/auto-process regressions pass. |
| 4: retained timeout and explicit incomplete states | Four `test_timeout_survives_postprocessing_failure` cases cover both harnesses with oracle/telemetry failures after exit 124. `process_outcome`, top-level reason/code and invocation outcome retain timeout. Capture exception gives unknown/incomplete; later exceptions name their failing step; analysis failure is explicit. Saved final-replacement metadata conservatively retains in-progress status. |
| 5: hard wall vs informational tokens vs advisory reserve; separate duration; bounded/unbounded steps | Runtime records/docs distinguish these settings. `test_finalization_time_is_separate_and_cannot_extend_contestant_budget` proves both harnesses pass an eight-second child budget after two seconds setup, retain contestant=8/attempt=10/finalization=3, and never claim acceptance. Invalid zero/reserve budgets fail before launch. Existing synchronous steps are explicitly disclosed in `step_timeouts_s`/runbook; no fake test claims universal kill behavior. |
| 6: equivalent context and no acceptance from reserve | `test_actual_runner_prepared_and_running_deadline_context` checks actual host argument construction for the same two neutral variables and `workflow_acceptance=not-established` in both harnesses. Prompt AST parity passes. Skill context semantics were manually reviewed below; this does not claim future model compliance from a keyword test. |

## Optional skill semantics walkthrough

The skill/protocol additions consume fields only at the existing dispatch/phase boundaries. Both fields absent means normal eligibility, validation, phase/final review and commit procedure. Valid time outside reserve means normal authorized dispatch. Inside reserve, required acceptance/closeout takes priority over optional work. Insufficient required-work time means exact incomplete evidence/verdicts saved to notes/handoff and heartbeat paused, with no new work dispatch. Invalid context is surfaced and checkpointed. Neither reserve exhaustion nor hard deadline can accept a gate, move an unmet task to Done or replace a reviewer. These instructions add no new validator, event log, review layer or template/prompt coaching. The proposed 900-second reserve remains uncalibrated and separately authorized; default is zero.

## Deferred boundaries and remaining risks

No paid smoke, live service check, MXC pin/build/containment change, automatic resume, universal process-tree cleanup, token supervisor, historical record edit or telemetry/publisher change. Hard-death evidence can remain incomplete and requires explicit reconciliation. Oracles and specified host postprocessing remain synchronous/unbounded, as disclosed rather than disguised as hard-wall protection. Product documentation outside the two declared eval guides was not edited; parent owns repository-wide tracking records. T3 must preserve unknown populations and separately bind authorized continuation lineage, not infer cumulative acceptance from these local IDs.

## Shared phase review - 2026-10-26

Reviewer: /root/phase_review (read-only canonical code-reviewer). Verdict: PASS for AC1-AC6; 43 lifecycle passed; 15 preparation passed / 1 optional skip; prompt parity accepted. No blocking findings with confidence >=80; no optional changes requested. Phase: READY TO ADVANCE. Reviewer inspected the stable aggregate diff, untracked source/tests, saved commands/results and intentional sequential shared-file changes; no broad reruns or external calls. The full AC evidence remains in this note's mapping. Commit byte binding and final impl-review follow this phase gate.

## Parent commit binding - 2026-10-26

Phase commits: 6799ec22a0d202cdd05c98fe6db9eac2853816b2 (workflow), 572bc267d3d782fce720a19988283554a27c4729 (runners and required tests), 15760959e3bb6bb2094eb8e9a0153e200d9ecb28 (scopes/publisher and required tests; shared runbook). Parent compared all 19 product HEAD Git blobs with clean-filtered blobs computed from the tested working files, and separately verified all working-file SHA256 digests unchanged. No mismatch required an isolated rerun. Raw evidence is -text under existing .gitattributes; captured CRLF/trailing output bytes were retained. Product/notes whitespace passed with cr-at-eol and raw evidence excluded; raw diagnostic formatting is preserved, not reported as source whitespace success. Message gates passed before each commit. Final impl-review pending.

## Final acceptance and closeout - 2026-10-26

Task Done. /root/phase_review accepted its ACs/tests and the phase READY TO ADVANCE; all DoD/kanban gates passed. Final impl-review at 15760959e3bb6bb2094eb8e9a0153e200d9ecb28: /root/final_workflow PASS, /root/final_runner PASS, /root/final_accounting PASS WITH WARNINGS; Overall PASS, zero required findings. Two nonblocking accounting warnings retained (full scorer replay open; live compatibility/delivery unverified). Full domain findings/revision anchors are in ../review-impl.md. No optional fixes, test repetitions, new review process, paid run, publication or push. Later record-only commit preserves all 19 tested product code/test blobs; final plugin identity can be retrieved from git HEAD for a separately authorized future baseline.
