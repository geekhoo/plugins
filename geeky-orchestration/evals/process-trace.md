# Process trace

The process trace is the contract for evaluating a workflow on any harness or model (decision D111). Each run gets one Langfuse trace that records the workflow itself: stages, tasks, lane moves, review verdicts and gate results. A small post-run adapter writes it from that harness's native records. Everything harness-specific stays in the adapter. The aim is that a scorer reads this trace, the workspace and the oracle, and never a transcript.

`telemetry/process_trace.py` is the neutral validator and exporter. `telemetry/codex-process-events.py` is the Codex adapter.

```powershell
python geeky-orchestration/evals/telemetry/codex-process-events.py <run-folder> --workspace <git-checkout> --out <folder>/events.json
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

Review coverage is partial when a reviewer's final message has no anchored verdict line. Those turns produce no event.

Both are exported to their retained sessions under the name `geeky-orchestration.end-to-end`: 109 spans for DeepSeek and 87 for Luna, with no span missing on readback. Luna's exported timeline predates the `(by this commit)` label, so its text reads `T1: Ready -> Done` at 20:01:38; the span's `lane_evidence` metadata is correct. Spans cannot be re-sent, so this stays as it is.

## Limits

- Tested only on these two Codex runs. No Claude adapter exists, so agnosticism is a goal, not a demonstrated result.
- No scorer reads this trace yet. `score-run.py` and `parity-eval.py` are unchanged, and a scorer based on it would need its own score scope.
- Gates run as shell scripts rather than MCP tools are not recorded as gate events.
- Phase is not recorded, because existing phase parsing is unreliable.
- Dashboards can filter on metadata but not group by it.
- Total Cost stays $0.00 in Langfuse until model prices or per-generation cost are supplied.
