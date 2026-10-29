# Claude C0 planning latency: captured evidence and policy change

This is an offline analysis of the terminal attempt `20261026T202649Z` at plugin
commit `4228c3f73fc3894c86725cf42900406c1d2d981f`. No evaluation, provider,
telemetry, judge or contestant was launched for this analysis. The historical
capture remains unchanged. Both fresh evaluations remain stopped.

## Observed timeline and outcome

[`run.json`](../../baselines/c0-wordstat/20261026T202649Z/run.json) records a
5,999.01-second contestant interval, 6,000-second hard wall, 60-second advisory
reserve, exit 124 and no acceptance. The source-bound stage analysis in
[`analysis.json`](../../baselines/c0-wordstat/20261026T202649Z/analysis.json)
places research at 28.7 minutes (20:27:36–20:56:18 UTC), planning at 44.9
minutes (20:56:18–21:41:10), and partial plan review at 25.6 minutes
(21:41:10–22:06:47). These are workflow intervals, not additive estimates of
provider time. Two documentation commits `0f6fb45609fee496790fbdc1200ad40bc88730b2`
and `e9f16269869a15c13d589c25948dce049f7bfba4` preceded cutoff. No wordstat
implementation was made. The [fresh sequential analysis](../c0-fresh-sequential-20261027/README.md)
records a partial review, not an endless review loop; final disposition and
implementation never occurred.

## Drivers and limits

- **Deadline absent from planning policy — high confidence.** The historical
  runner records `initial_deadline_utc` and reserve in `run.json`; at the pinned
  source, research, plan and plan-review contain no instruction to consume them.
  Implement had a later deadline policy, but that stage was never reached. The
  60-second reserve is advisory, and the capture does not demonstrate that the
  agent reacted to it. This is an actionable propagation gap, not proof that
  propagation alone would have yielded implementation.
- **Required staged work and expansive reports — high confidence as observed
  activity, uncertain avoidable time.** Research dispatched three distinct
  workers; the captured observation export contains 31 WebFetch operations by
  its two researchers, plus four by the later alignment reviewer. The
  [workspace snapshot](../../../../outputs/c0-fresh-sequential-mapped-20261027/claude-workspace-snapshot/docs/spec-001-feature/)
  contains a 23,147-byte specification and a 13,807-byte PM review for three
  tasks. The PM review found actionable coverage issues including an untested
  exit path and wrong Unicode literals as well as suggestions; therefore this
  work cannot be characterized wholesale as unnecessary. Its ten findings
  were addressed, then an independent alignment review and sequencing review
  were performed. Independence and deterministic validators remain required.
  Concise source-bounded briefs and deferring optional additions can reduce
  expansion, but their savings are unmeasured.
- **Material model-side thinking — high confidence recorded; cause and overlap
  uncertain.** Counting each `requestRef` once using the maximum recorded
  `thinkingDurationMs` in the raw [main session](../../baselines/c0-wordstat/20261026T202649Z/session.jsonl)
  gives 67 requests and 1,652.9 seconds of recorded main thinking; a research
  worker records 860.2 seconds across eight requests and a maximum 255.4-second
  request. Worker durations overlap each other and the parent; they must not be
  added to produce wall time. These fields reflect recorded model thinking, not
  a proven partition of server compute, network and scheduling latency.
- **Volume and token evidence — high confidence for captured observations,
  not a billing reconciliation.** The saved
  `outputs/c0-fresh-sequential-mapped-20261027/claude-observations.json` contains
  153 generation and 202 tool observations. Generation usage totals 854,200
  input, 6,868,416 cache-read input and 57,701 output tokens (7,780,317 total);
  152 generations contain thinking metadata totaling 899,272 reported
  characters. Those are exported observation totals, potentially overlapping
  accounting fields; reasoning tokens and actual bill are not established. The
  native run reports zero tokens because no final result event arrived, not
  because usage was zero. The analyzer's 12.638-second median is based on 76
  latency samples and its 873-second max idle gap is not proof of idle compute
  or provider failure. Observation generation timestamps include 38 zero-duration
  entries; they cannot establish an exact latency decomposition.
- **Validation and review repetition — bounded concern, not an infinite loop.**
  Analysis records four invocations of each planning validator across stages;
  all recorded results passed. The snapshot shows independent reviews and
  concrete fixes, so removing correctness gates or assuming all validation was
  redundant would be unsupported. The previous policy already allowed bounded
  rechecks after mechanical changes; no broad automatic re-review bypass is added.

## Change and recommendations

The three planning skills now call a common offline `workflow-budget.py` at
entry, task/phase boundaries, after lengthy direct work, and around child
dispatch/waits. They inspect all statuses, propagate actual absolute deadline,
reserve and advisory target to child briefs, checkpoint incomplete work on
reserve/expiry, and do not grant acceptance for missing gates. No deadline means
unbounded rather than an invented clock. Research narrows each angle to material
questions and stops collecting sources once answered; review requests concise,
actionable evidence while retaining its independent lanes and validators. An
advisory milestone is a prioritization signal, not a fixed cutoff, guarantee,
or authority to weaken required checks. These are common workflow policies for
both harnesses, not a case-specific timeout increase.

The shared helper is now wired into the workflow, both runners pass
`GEEKY_HARD_WALL_BUDGET_S`, and the canonical prompt provides common budget
guidance. The source/export hash guard rejects stale HEAD policies. The caller
must inspect JSON status even when reserve returns exit 0. Any future comparison
must use fresh authorized runs and comparable model, effort, prompt, time and
telemetry settings. No live effectiveness or wall-time improvement is claimed here.

Two temporary offline policy checks passed and were removed because they mirrored
the Markdown instructions. Final verification relies on the retained
`test_workflow_budget.py` behavioral tests, real-runner tests with fake
subprocesses, and independent read-only policy review. These do not execute an
LLM, prove deadline obedience, or simulate cancellation of a blocking native call.
