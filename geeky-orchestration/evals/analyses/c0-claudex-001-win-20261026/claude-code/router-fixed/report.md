# Claude C0 after the router change

Historical attempt. The later [authorized continuation](../closeout-20261026/report.md)
completed final review and closeout at cumulative parity 98.33. This timeout's
raw evidence and Langfuse score 90.33 remain unchanged.

The authorized retry used `geeky-resume` in the existing Windows MXC folder set,
LiteLLM `claudex-001`, and default thinking. It reached implementation and final
review, then timed out at 5402 seconds (exit 124). The router's previous
MissingSessionID failure did not recur. This was a paid run; qualification was
waived by the owner and no qualification/probe or external paid judge was run.

**Audited parity: 90.33.** Quality 96.67, Adherence 88.10 (37/42), Consistency
83.16. All judgment items are resolved in [manual-verdicts.json](manual-verdicts.json).
The legacy score-run process composite is diagnostic; only [parity.json](parity.json)
is the comparable cross-harness score.

| Evidence | Result |
|---|---|
| Hidden oracle | 13/13, repeated three times with identical counts |
| Independent final public tests | 56 passed, 2 skipped, exit 0 |
| Task-commit validation | 7/7 extracted executable commands pass at the four task commits; no final-HEAD fallback |
| Tasks | Four Done, four serial native coder lifetimes; dependency chain explicitly justified |
| Candidate history | Ten linear commits; no observed forbidden Git operation or frozen-file edit |
| Final candidate SHA | `e2c1317ed4443e970e6ea9f9c069b0c75342ae1c` |
| Remaining worktree state | Only untracked `docs/spec-001-feature/.heartbeat` |
| Runtime | 2026-10-25 19:54:47 to 21:24:49 UTC / 2026-10-26 03:54:47 to 05:24:49 Singapore |

The two skips are the POSIX/non-root unreadable-file checks, unavailable on
Windows. Tests cover exact stdout bytes, BOM, CRLF input, JSON, argument/error
handling, and non-reading stdin. Temporary mutation checks performed by the
candidate caught deliberately broken stdin and stdout behavior. No product
changes were made by the operator to help the candidate.

The workflow did not finish. All three final reviewers returned PASS WITH
WARNINGS, but there is no consolidated `review-impl.md`, no Run Summary, no final
report/result record, and the heartbeat still says running/T4. The end-to-end
reviewer raised a conditional contract-interpretation concern that the parent
did not resolve. T4's phase reviewer returned BLOCKED for a missing dated final
test entry. The parent wrote the entry and marked T4 Done, but did not obtain a
revised READY TO ADVANCE verdict. The audited score retains that failure rather
than borrowing earlier phases' verdicts. The false-completion hard gate does
not fire: the parent never claims that final review or the whole workflow finished.

Deferred findings include Windows stderr CRLF/encoding behavior, the unexecuted
POSIX permission branch, and test timeout cleanup. Passing the oracle does not
resolve the outstanding final-review interpretation. Stale top-level candidate
status text and unchecked release gates remain as produced by the candidate.

## Langfuse

[Open the session](https://langfuse.markefin.com/project/cmvmyexpu0001o01ubyvac5jw/sessions/claude-mxc-win-c0-wordstat-20261025T183455Z-geeky-resume-router-fixed-20261025T195444Z).

- Session: `claude-mxc-win-c0-wordstat-20261025T183455Z-geeky-resume-router-fixed-20261025T195444Z`.
- Environment: `mxc-win`; 17 distinct agent user IDs (orchestrator, four coders,
  eight reviewers, four source types kept unknown).
- 33 traces, 892 observations: 329 generations, 530 tools, 33 agent observations.
  The tracer emits multiple orchestrator turn traces sharing the same user.
- All 267 generation observations with token usage have model `claudex-001`.
  Sixty no-usage placeholders are labeled `claude`; two further claudex-001
  generations have no usage. Those placeholders are not proof of another routed model.
- Runner/native-session accounting: 147 calls, 16, 572, 433 total tokens,
  including 13, 970, 509 cached input and 493, 621 output. Langfuse's broader
  parent/worker aggregate reports 19, 349, 407 total usage units. These are different
  accounting scopes and are not billed-cost evidence. The inherited Claude
  pricing estimate is not validated for the router alias; actual cost is unknown.
- All ten session scores were published and independently read back using the
  Langfuse CLI: [verified values](langfuse-scores-verified.json).

An initial live read timed out; forcing IPv4 for the local Node CLI restored
access. No gateway configuration was changed by the operator during this retry.

## Evaluation audit

The original parser missed a phase/task table under an Approach heading, a
plan-review dispatch without a Skill invocation, and an explicit impl-review
Skill boundary. The coverage parser also missed Claude Read-tool Windows paths.
Those source-bound parser gaps were corrected with regression tests. Original
derived outputs are retained as `*-before-parser-correction.*`; raw stream and
session hashes still match the runner's originals. The corrected coverage report
is complete; original run metadata remains unchanged and records the earlier
false misses. Coverage completeness means the required telemetry points were
captured, not that the workflow finished.

Targeted evaluator/coverage regressions: 52 passed, three historical integration
tests deselected. Codex parity was replayed using the same updated evaluator and
remains 97.46. Claude's own task-validation snapshots were 0613177, 186bb2a,
1e8168d and dc76b8a, with no task-completion anchor override needed.

The comparison is descriptive. Claude had resume context and a router change
before its attempt; the same alias does not prove the same underlying backend.
It is not a controlled causal ranking of models or harnesses.

See [kanban.md](kanban.md), [handoff.md](handoff.md), [references.md](references.md),
[telemetry-audit.json](telemetry-audit.json), and [source-manifest.json](source-manifest.json).
The earlier provider-blocked reports remain historical evidence. No shared-repo
commit or push occurred during evaluation. Repository publication is now
authorized under the [alignment record](../../alignment-report-2026-10-26.md).
No further paid retry is running or scheduled.
