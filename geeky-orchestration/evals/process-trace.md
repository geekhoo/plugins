# Process trace

The process trace is the contract for evaluating a workflow on any harness or model (decision D111). Each run gets one Langfuse trace that records the workflow itself: stages, tasks, lane moves, review verdicts and gate results. A small post-run adapter writes it from that harness's native records. Everything harness-specific stays in the adapter. The aim is that a scorer reads this trace, the workspace and the oracle, and never a transcript.

| File | Knows |
|---|---|
| `telemetry/process_trace.py` | The contract: validates a document and exports it |
| `telemetry/process_events.py` | What can be asserted: board replay, reconciliation, stages, verdicts. No harness knowledge |
| `telemetry/codex-process-events.py` | Codex rollouts: tool calls, patches, MCP gate output |
| `telemetry/claude-process-events.py` | Claude transcripts: `Write` and `Edit`, `Agent` calls and task notifications, shell gate text |

```powershell
python geeky-orchestration/evals/telemetry/codex-process-events.py <run-folder> --workspace <git-checkout> --out <folder>/events.json
python geeky-orchestration/evals/telemetry/claude-process-events.py <run-folder> --workspace <git-checkout> --out <folder>/events.json
python geeky-orchestration/evals/telemetry/process_trace.py <folder>/events.json --out <folder> --export
```

The first command makes no network call. Without `--export` the second only validates. Export needs the `LANGFUSE_CODEX_*` variables and writes a claim file. It refuses a session that already has a process trace, because Langfuse v4 warns against re-sending a span id.

## Trace shape

One trace per run, in the run's session, with new span ids. Actor traces are not changed.

| Observation | Name | Type | Metadata |
|---|---|---|---|
| Run | `geeky-orchestration.end-to-end` | `chain` | `workflow_schema`, `adapter`, `adapter_version`, `coverage_stage`, `coverage_lane`, `coverage_review`, `coverage_gate`, run identity |
| Stage | `stage:<stage>`, five fixed names | `chain` | `workflow_stage`, `stage_evidence`, `stage_source` |
| Task | `task` | `span` | `workflow_stage`, `task_id`, `owner_actor` |
| Lane move | `lane.move` | `event` | `task_id`, `from_lane`, `to_lane`, `actor`, `source_ref`, `lane_evidence` when not exact |
| Review | `review.verdict` | `event` | `review_scope`, `verdict`, `actor`, `agent_type`, `source_ref` |
| Gate | `gate:<gate>`, from a fixed list | `event` | `gate_name`, `gate_result`, `task_id`, `actor`, `source_ref` |

Three Langfuse behaviours, each tested on the deployment, shaped this:

- Session replay shows chat-format text only, so the root's output is a readable timeline as chat messages.
- The trace's Tree view shows the hierarchy, so stages, tasks and events nest there.
- The Metrics API cannot group by metadata, so fixed values that need grouping go in span names. Metadata can still filter.

## Identity for new runs

| Field | Value |
|---|---|
| `sessionId` | `<case>/<harness>/<stamp>`, one continuous contestant invocation. Resumed segments stay separate sessions, tied by `run_group_id` |
| `userId` | `<harness>/<role>`, with roles `orchestrator`, `coder`, `reviewer`, `planner`, `unknown`, and `<harness>/workflow` for the process trace |
| Actor trace name | `<stage>/<scope>/<role>` where known, from a fixed scope list; `orchestrator` for the root |
| Model and provider | Metadata and tags, not IDs. The model the gateway reports stays in the observation's model field |

Exact threads stay reachable through `agent_id` in metadata. Retained sessions keep their old IDs, because observations cannot be changed after export. The process trace uses `<harness>/workflow` in old sessions too. The tracers do not emit this identity yet.

## Rules for adapters

- Assert only what can be reconciled. Unobserved facts are absent and coverage says `unknown`. A partial source says `partial`. Never turn an unknown into a pass or a fail.
- Stage ends come from artifacts: the first commit adding `feature-specification.md`, then `implementation-plan.md`, then the plan-review commit. Final review starts with the first reviewer thread after every task stands in Done.
- A replayed board is trusted only if it agrees with every passing `geeky_validate_kanban` reading and every commit touching the board. Otherwise lane moves come from commits, marked `lane_evidence: commit-bound`, because the move happened at or before that time.
- Failed writes are skipped. A board write the adapter cannot replay, such as a PowerShell regex edit, makes lane coverage `partial`. The adapter does not execute it.
- `source_ref` points at the native record, so a person can audit any fact.
- Times are UTC. Langfuse shows them in the viewer's time zone.

## Results on retained runs

| Run | Stage | Lane | Review | Gate |
|---|---|---|---|---|
| C2 DeepSeek `20261104T041838Z-d22d38ec` | complete | complete: 18 patches, 1 failed and skipped, agrees with 21 gate readings and 6 commits | partial | complete |
| C2 Luna `20261101T190137Z-5b0dc756` | complete | partial, commit-bound: 9 shell board writes | partial | partial |

| C1 Claude `20261020T114232Z` | complete | partial, commit-bound: 7 shell board writes | partial | complete |
| C1 Claude `20261020T155628Z` | complete | partial, commit-bound: 7 shell board writes | partial | partial |
| C1 Claude `20261022T065938Z` | complete | partial, commit-bound: 4 shell board writes | partial | partial |
| C1 Claude `20261022T125647Z` | complete | partial, commit-bound: 2 shell board writes | partial | partial |
| C1 Claude `20261023T062603Z` | complete | partial, commit-bound: 5 shell board writes | partial | partial |
| C1 Claude `20261023T104412Z` | complete | partial, commit-bound: 10 shell board writes | partial | complete |

Review coverage is partial when a reviewer's final message has no anchored verdict line, or no closing message was retained. Those turns produce no event.

Claude stage boundaries are within about 75 seconds of the analyzer on all six runs. The Claude events are offline documents. Those run records hold no telemetry session, so nothing has been exported for them.

## What the second harness showed

- **Holds across harnesses:** the contract and exporter needed no change for Claude. Stage boundaries, verdicts, gates and commit-bound lanes all came from one shared module, and the refactor left Codex output unchanged. Adapter sizes are 167 and 203 lines, against 278 shared.
- **Does not hold: exact lane moves.** Only 1 of 8 retained runs, DeepSeek on 4 November, wrote its board in a form that can be replayed. Shell `.Replace` and `[regex]` edits defeat replay on Luna and all six Claude runs. This depends on how each model chooses to write a file, not on the harness.
- **Harness quirks stay in adapters:** early Claude MXC runs flag nearly every shell result `Exit code 5`, so the Claude adapter reads fixed gate text and never treats that flag as failure. Runs before `20261023T104412Z` kept no subagent transcripts, so their subagents' board writes and gates are invisible.

For exact lane moves on future runs, the board needs observing from outside the contestant, for example a host-side file watcher. That needs no contestant change and works for any harness or model. It is not built or tested.

Both are exported to their retained sessions under the name `geeky-orchestration.end-to-end`: 109 spans for DeepSeek and 87 for Luna, with no span missing on readback. Luna's exported timeline predates the `(by this commit)` label, so its text reads `T1: Ready -> Done` at 20:01:38; the span's `lane_evidence` metadata is correct. Spans cannot be re-sent, so this stays as it is.

## Limits

- Tested on two Codex configurations and one Claude configuration, all retained runs. No other harness has been tried, and the Claude adapter has not run on a run with telemetry.
- No scorer reads this trace yet. `score-run.py` and `parity-eval.py` are unchanged, and a scorer based on it would need its own score scope.
- The Codex adapter does not yet record gates run as shell scripts; the Claude adapter does.
- Phase is not recorded, because existing phase parsing is unreliable.
- Dashboards can filter on metadata but not group by it.
- Total Cost stays $0.00 in Langfuse until model prices or per-generation cost are supplied.
