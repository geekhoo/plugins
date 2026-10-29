# Claude C0 overtime completion and verified scores

Claude completed the preserved implementation and final review under the owner's
explicit overtime authorization. Final candidate:
`fba5d30c5646457a398a271ff972b117d54d4982`; worktree clean. The continuation exited0,
final review is PASS with no required findings, 18 public tests passed, and the
independent oracle passed13/13 over three fresh repetitions. Codex remained stopped.

| Scope | Outcome | Active time | Parity | Quality | Adherence | Consistency |
|---|---|---:|---:|---:|---:|---:|
| Original `20261028T115941Z` | Timeout; original result preserved | 5999.150 s (99m59s) | 95.14 | 100 | 87.5 | 100 |
| Authorized overtime segment | Completed, final review PASS | 1082.148 s (18m02s) | Evaluated cumulatively | — | — | — |
| Initial plus overtime | Completed after authorized overtime | 7081.298 s (118m01s) | **98.44** | **100** | **96** | **100** |

Active time beyond the original6000-second budget is1081.298 seconds (18m01s).
The gap between the two workloads is excluded from active time. Overtime is not
hidden by resetting the initial result or presented as another clean initial attempt.

Settings remain Windows MXC, LiteLLM `vercel/gpt-6-luna`, high requested on main,
workers and reviewers, and Langfuse from startup. Source revision stayed
`0b1f5fbc0e84b110ea0f9fa59ddfa711b46cf53a`. The same workspace and frozen planning
contracts were retained; native conversation fork
`c8a10746-046e-4426-af92-100e673a4c11` resumes original
`427f3c87-4544-4f57-b766-ea52cb860b12`. The continuation capture is
`20261028T115941Z-overtime-20261028T143021Z`.

## Completion evidence

- All three final domains report PASS. The remaining usage-prefix assertion was
  validated and independently re-reviewed. Review report and handoff retain the
  original failures, fixes and final verdicts.
- Final committed validation: 18 pytest cases passed; help and compilation checks
  succeeded; DoD, kanban, task-schema and planning-folder gates passed.
- Candidate commits are spec `f3627c0`, plan `96359ae`, implementation `0ca67a2`,
  and final fix/closeout `fba5d30`.
- The earlier spec-stage generic commit-message gate failure remains a disclosed
  historical exception. Windows permission-denied testing remains a documented
  platform-conditional omission.
- The rubric's remaining numeric deduction is the fix-commit subject: it says
  “2 required review findings” where the prescribed pattern expects “critical.”
  This deterministic mismatch was retained; it was not manually overridden.

## Scoring provenance and Langfuse

The initial candidate was frozen with its complete Git state before continuation;
the completed candidate was separately frozen for reproducible evaluation.
Existing `score-run.py` validation was run at the task's implementation commit.
Comparable scores use the unchanged `parity-eval.py` formula, not the legacy
latency-weighted composite. All parity judgments are resolved and source-bound.

The automatic extractor mistook an early implementation-orchestrator brief's
instruction *not* to run `impl-review` for the final-review start. That wrongly
excluded actual coding, task review, DoD, kanban, commit-gate and pytest evidence.
Eleven narrowly scoped corrections use the evaluator's existing manual-evidence
interface, with native record IDs, timestamps, source hashes and commit bindings.
Actual initial timeout, dirty state and absent final report remain failures.
The scoring formula and evaluator source were not changed.

Native histories are deduplicated by UUID/message/tool identity with semantic
conflict checks. Diagnostic API-request copies are retained as provenance and
are not execution-call identity evidence. Telemetry process inputs exclude35
replayed tool observations; generation/accounting populations are not summed.
Token/cost totals remain unknown rather than using zero or overlapping counters.
SDK public-key metadata was redacted from derived exports before final scoring.

Ten initial-scope scores and ten cumulative-scope scores were published using
distinct scoped IDs and verified through exact Scores-v3 readback. Overtime,
original timeout, active segment durations and cumulative duration are explicit
in score metadata/comments. Cumulative harness coverage is complete.
Initial telemetry:20traces/953observations. Continuation telemetry:4traces/149observations.

Local evidence root: `outputs/c0-luna-overtime-20261028/`:
`results.json`, `verification.json`, `cleanup.json`, native-derivation/,
manual-review/, scoring-inputs/, and scores/{initial,cumulative}/. Each score
folder contains parity.json, evaluation-inputs.json, publication-result.json
and score-readback.json. The original126 terminal/snapshot pins and115 older
capture pins remain unchanged. No credential values were found in final artifacts.

Stale-document disposition: current root/plugin READMEs and readiness now point
here. The [original pair report](../c0-luna-sequential-20261028/README.md), its
timeout table and immutable captures remain historical and unchanged. Earlier
preparation authorization does not grant another run. No operator source commit,
push, Codex run or separate paid judge endpoint was used for this closeout.

Both evaluations are stopped. See [kanban](kanban.md), [handoff](handoff.md),
and [references](references.md).
