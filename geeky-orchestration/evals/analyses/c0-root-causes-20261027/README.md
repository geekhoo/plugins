# C0 failure investigation and offline changes, 27 October 2026

Both evaluations remain stopped. Parallel investigations and an independent
review used `gpt-6.1-terra` with `xhigh`, as requested. No evaluation, provider,
judge or live telemetry operation was performed for this work. Source HEAD is
`4228c3f73fc3894c86725cf42900406c1d2d981f`; fixes remain uncommitted.

| Failure | Established cause or gap | Change | Remaining limitation |
|---|---|---|---|
| Codex ended after literal wait markup | Completed assistant text contained the bridge-advertised wait name; no structured wait ran. The mapper accepted this text as ordinary output. | Reject the observed advertised-name signature in JSON, completed messages and split SSE deltas; return sanitized `bridge_tool_call_as_text`. Common prompt explicitly requires actual tool invocations. | The upstream representation producer is unknown. This is detection and preventive guidance, not a demonstrated repair of model/router tool formatting. |
| Claude used the wall before coding | Research/planning/review never consumed the supplied deadline. Extensive research, reports, thinking and independent reviews occupied the whole run. | Read-only budget helper, total-budget propagation in both runners, checks through all three planning skills, child deadline briefs, bounded source collection and concise review evidence. | Stage targets are advisory and live obedience/savings remain unverified. Required gates remain required. |

See [Codex evidence](codex.md) and [Claude evidence](claude.md). Research took
28.7 minutes, planning 44.9 and partial plan review 25.6. Recorded main-agent
thinking was about 1,653 seconds across 67 unique requests; concurrent worker
thinking is not additive. The evidence does not establish an endless review loop
or separate exact provider/network/model latency. Langfuse storage worked in the
historical pair and was not its blocker.

The helper reports remaining time, usable time after reserve, invalid/expired
context and advisory cumulative stage targets: 15% research, 30% through plan,
40% through plan review, 90% through implementation and 100% final review.
These are proposed prioritization heuristics, not measured completion estimates.
Reserve stops new stages/delegation and checkpoints incomplete state; no target
or clock grants acceptance or extra time. No context means ordinary workflow;
legacy deadline/reserve without total has no invented stage targets.

The new common prompt requires this helper. Because contestants export committed
HEAD while prompts come from the operator worktree, both runners now reject an
absent or substantively different helper or planning skill in that export.
Comparison normalizes CRLF/LF; fresh evidence hashes retain original bytes.
Consequently current working-tree fixes cannot be launched through an old HEAD
export. Commit a reviewed revision only when authorized, then refresh source,
prompt and tool pins and prepare fresh workspaces. No launch is authorized here.

The Codex guard never constructs or executes calls from prose. It may reject a
legitimately quoted exact signature. Previously streamed text can already reach
the client; the offending event and completion are withheld. Native client
retries remain outside the bridge's control. Raw upstream bodies were never
captured; investigate the LiteLLM route/parser configuration before attributing
the original malformed format to a particular component.

## Verification and preservation

Offline verification: 86 helper, bridge/lifecycle and readiness tests passed;
55 runner subprocess tests with local fake executable boundaries passed; three
additional CRLF/content-drift/missing-export regression tests passed. No real MXC
or contestant is invoked by these tests. Independent review identified one
Windows newline issue, fixed and re-reviewed with no remaining required findings.
The final evidence file records exact commands and capture preservation checks.

Evidence is in `outputs/c0-root-causes-20261027/`: focused-tests.log,
runner-tests-observed.txt, export-tests.log, inventory/, verification.json and
verify.py. Inventory reports local tools/pins only; it grants no qualification or
launch authority and does not prove the separate committed-export prerequisite.

Root/plugin READMEs, readiness, lessons, runbook and adapter README now point to
this follow-up. Old readiness prompt hashes and earlier prepared launches are
marked historical/stale; terminal run reports, scores and raw captures remain
unchanged. See [kanban](kanban.md), [handoff](handoff.md), [references](references.md).
