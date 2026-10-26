# T1: Remove review ambiguity and repeated work

## Task Name
Streamline existing planning/review/closeout instructions and the final output contract.

## Priority
P0. First task: the smallest directly evidenced instruction fixes, with no runner dependency.

## Context
Codex report: selected T1 snapshot and CRLF/BOM claim. Claude router-fixed manual verdicts: T4 BLOCKED and missing closeout. Process review R4/R5/R7. Side-review proposals O1–O3: terminal-verdict ambiguity, repeated final reports and redundant final planning reread. The side review is supported by the pinned skill/prompt sources; causation of Claude's timeout and actual time savings remain unproven. [Source index](../references.md).

## Module/System
Existing planning/implementation/review skills and the canonical prompt's final-output paragraph; no new workflow stage.

## In scope
- `skills/geeky-implement/SKILL.md`, `skills/impl-review/SKILL.md` and `skills/plan-review/SKILL.md` at the specific checks below.
- `skills/geeky-implement/references/execution-protocol.md`, specifically the existing commit boundary and end-of-run sequence.
- `evals/prompts/end-to-end.md`: final-output paragraph only; align `evals/prompts/README.md` and baseline-version references.
- Local scenario/compact-report fixtures and affected existing tests. Inspect `evals/telemetry/langfuse-evaluators/final_report_complete.judge.json` for contract compatibility; preserve its five evidence requirements and the disabled rule. No remote evaluator change.

## Dependencies
None. One `geeky-coder` writer. T2 follows and supplies the optional deadline/reserve integration, so timing support cannot delay these independent fixes. Follow existing phase commit protocol; this plan adds no mandatory per-task commit timing.

## Technical Notes
Implement in this order within the task:

1. **One terminal verdict.** Map domain PASS WITH WARNINGS to consolidated Overall PASS only when every required finding is resolved and required evidence passes. Any unmet requirement/mandatory constraint remains NEEDS FIXES regardless of severity label; unknown or missing reviewer evidence cannot pass. Keep nonblocking warnings/suggestions as follow-ups. Align the domain template, Overall template and critical-fix rule so a mislabeled required finding cannot be ignored. Do not rerun review merely to eliminate optional warnings.
2. **Valid review reuse.** In `plan-review`, move the six existing final-sanity dimensions into the initial whole-folder alignment assignment if not already covered. Keep the independent sequencing assignment. Save input revisions/file hashes and findings in existing `review-plan.md` sections. The final parent pass checks unresolved findings, reviewer verdicts, the complete document diff and affected references, then reruns all three validators after sequencing corrections. Report what was reused versus rechecked.
3. **Preserve conservative invalidation.** A completion marker alone never proves current validity. Local mechanical fixes require changed-content/reference checks. Requirement/AC/task-scope/coverage edits invalidate alignment; dependency/order/phase/gate/resource/validation-feasibility edits invalidate sequencing. Keep the current full-recheck triggers for more than five changed files or cross-document task-ID/dependency/order changes. Missing baseline/diff, untracked additions omitted from the diff, conflicts or unbounded impact require a full sanity pass and fresh affected reviewer verdicts. No generic cache or new findings database.
4. **Persist replies immediately.** Resolve the `impl-review` conflict between persist-as-arrives and Phase 4 wait-all: write each returned domain with reviewer ID, reviewed revision and completion marker; then consolidate saved sections. Reuse unchanged domains. A resolved phase blocker requires a revised verdict for that same phase before Done; an earlier phase verdict cannot substitute.
5. **Bind commits and claims.** At execution-protocol step 16, compare committed code/tests with tested revisions/file hashes; group required code and tests into a functional delivery. Reuse matching evidence; rerun affected mismatches in an isolated tree. Keep full commit/command/result anchors and existing H1 semantics. Check final claims against sources and reviewer scope; distinguish direct-call from subprocess coverage and Git object IDs from file SHA-256.
6. **Finish closeout in order.** In step 18, place the Run Summary, lane reconciliation and current required verdicts before heartbeat done. Preserve truthful paused/interrupted state when incomplete. Keep current phase/final review counts and required gates; add no checklist or hardening pass.
7. **One concise final response.** Replace only the canonical prompt's request to reproduce every workflow report with one completion report containing: overall outcome; a table of each stage's verdict/unreached status, artifact path and brief supporting command/gate result/reviewer verdict; final numeric test results/evidence; commits made and final revision; deviations, blockers, interventions and deferred warnings, or an explicit statement that none occurred. Detailed artifacts remain where each skill already requires them. Include substantive verdicts/counts/commits and the evidence basis for every passing stage in the response, because the current report evaluator sees output text, not the linked files. This is presentation-only: no workflow coaching, hidden scoring instructions, new acceptance rule or missing-stage concealment.
8. **Version the changed experiment.** A changed prompt is a new future baseline under D36. Verify both harnesses render the same revised template and record its hash through their existing hash paths; record the changed plugin fingerprint as well. Preserve old prompt bytes/requirements and all C0 scores. Do not silently compare the future prompt version as the same experiment, migrate historical IDs or enable a judge.

## Acceptance Criteria
- Domain verdicts containing only nonblocking warnings yield consolidated PASS; an unmet requirement, missing evidence or unresolved required finding yields NEEDS FIXES even if labeled a warning. Optional suggestions cause no extra fix/review loop.
- Planning scenarios cover unchanged inputs, local mechanical fixes, changed requirements, changed dependencies/task IDs and stale/unknown baselines. Reuse respects the invalidation rules, preserves both independent reviewers and reruns final validators after all corrections.
- An isolated fixture with a test file absent from committed task delivery is rejected; later final-HEAD success cannot justify that snapshot.
- A fixture with T4 BLOCKED plus T3 READY remains unaccepted until the revised T4 verdict is supplied.
- Three saved, unchanged final-review replies require consolidation only; a changed dependency invalidates only its affected domain.
- The C0 CRLF/BOM and Git-blob examples produce precise claims/labels, preserving original evidence and erratum.
- No new reviewer dispatch is required when existing acceptance and review evidence remains valid. Timing/reserve integration belongs to T2.
- A compact final-report fixture satisfies all five existing report criteria. Omitted numeric test evidence, omitted commits, unsupported PASS or an unreached stage hidden as complete is rejected; links alone are insufficient.
- Only the canonical prompt's final-output paragraph changes. New prompt hash differs from the historical version and matches between equivalent harness renders; case contracts, scoring formulas and historical requirements stay unchanged.

## Tests/Validation Before Next Task
Use compact synthetic task/review/report fixtures and existing validators where they apply. Walk through every AC scenario against the edited instructions and current five report criteria, recording expected decisions and anchors. Do not use an LLM evaluation call or keyword-only tests as behavioral proof. Verify rendered prompt equality, new hash and unchanged historical files locally. Run affected existing gates/tests:

```powershell
python -m pytest -q test_quality_gates.py test_score_run.py
```

These tests protect existing acceptance/scoring semantics. Add executable tests only for changed deterministic behavior, including any changed report-check code; if the existing output criteria already accept the compact report, retain them unchanged. Instruction walk-throughs establish consistency, not future model compliance or judge accuracy. Do not run/calibrate a paid judge.

## Out of scope
New review layer, scoring/H1 changes, reduced reviewer counts, gate removal, relaxed full-recheck triggers, forced parallel coding, canonical prompt coaching, contestant fixes, broader tests, historical commit repair, generic review cache, new instrumentation or paid judges.

## Reviewer focus and stop conditions
Reject duplicated skill prose that adds no actionable check. Preserve existing phase batching and commit protocol. Stop if a proposed fix requires rewriting past task anchors, accepting BLOCKED work, or deleting a required gate to save time.

## Definition of Done
Affected instructions and all AC scenarios agree; targeted tests and local prompt-version checks pass. Retain known limits on model compliance/savings. Task waits In Review for phase acceptance; this task alone is not readiness for another paid evaluation.

## Estimate
1–2 focused engineering days including original checkpoint fixes, the three added proposals and offline review; estimate only.
