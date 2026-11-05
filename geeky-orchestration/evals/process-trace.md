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
- Board states come from the host-side watcher when its record reconciles, marked `lane_evidence: observed`, because the time is up to one poll after the write. Next comes a replay of the writes, then commits.
- A set of board states is trusted only if it agrees with every passing gate reading and every commit touching the board. For watcher states, a reading may match a state up to 120 seconds later, because one shell command can write the board and run the gate. Otherwise lane moves come from commits, marked `lane_evidence: commit-bound`, because the move happened at or before that time.
- A watcher record is ignored if it has no `stop` line or covers more than one board.
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

Mac MXC runs, Claude Code harness, read from `origin/opus/macos-mxc-c0` by adapter version 2. These are offline documents; nothing is exported. The runs used Python 3.9.6, which C2 does not meet, so they are not reference results.

| Run | Model, effort | Stage | Lane | Review | Gate |
|---|---|---|---|---|---|
| C0 `20261029T161528Z` | Sonnet 5.5, default | unknown: no planning commit | unknown | unknown | unknown |
| C0 `20261030T043030Z` | Sonnet 5.5, default | complete | partial, commit-bound: 3 shell board writes | partial | complete |
| C2 `20261101T192141Z` | Sonnet 5.5, high | complete | partial, commit-bound: 1 shell board write | partial | partial |
| C2 `20261101T225826Z` | Sonnet 5.5, medium | complete | partial, commit-bound: 3 shell board writes | partial | partial |
| C2 `20261102T053248Z` | GPT-6.1-sol, high, bridge | complete | partial, commit-bound: 12 shell board writes | partial | complete |
| C2 `20261101T211028Z` | GPT-6.1-sol, high | partial: blocked before final review | partial, commit-bound: 8 shell board writes | partial | partial |
| C2 `20261101T222922Z` | GPT-6.1-sol, medium | partial: implementation never started | complete: 3 writes, agree with gates and commits | unknown | partial |
| C2 `20261101T205532Z` | GPT-6.1-sol, high | unknown: no planning commit | unknown | unknown | unknown |
| C3 `20261104T083537Z` | Opus 5.5, high | complete | partial, commit-bound: 2 shell board writes | partial | partial |
| C3 `20261104T104418Z` | GPT-6.1-sol, high, bridge | partial: one commit closed plan and plan review | partial, commit-bound: 10 shell board writes | partial | partial |

## What the Mac runs showed

The wider results and lessons from that work are in [macos-mxc-findings.md](macos-mxc-findings.md).

The contract and exporter needed no change for a third operating system or for a non-Claude model behind Claude Code. The adapter did need fixes, all found by checking its output against the source records:

- **Gates that never ran.** Reading a gate's source or naming it in a message counted as a run. On 10 commands across the Mac and C1 runs, printed source text produced a result, some of them false failures. A gate now counts only when a statement runs it, or when the output holds its result line.
- **Linked board entries.** `- [ ] [T2 — Server](tasks/T2.md)` was not read as a task, which emptied the boards of two GPT runs.
- **Lost reviewer messages.** A background reviewer's notice can be missing, so the adapter now falls back to the reviewer's own retained transcript. On C3 GPT this recovered `PASS WITH WARNINGS` for two final review domains, as the run's commit note records.
- **Stages without evidence.** A zero-length stage now makes stage coverage `partial`, and `geeky-implement` needs a coder thread or a lane past Ready.

Lane coverage is complete on 1 of 10 runs, because shell board writes defeat replay here as well. These runs predate the watcher. Some reviewer messages still give no verdict: on the runs sampled, these include plan-alignment audits, which have no single verdict, and messages with one verdict per task. A gate stays `unknown` when its command prints no result line, such as `dodT3=0`.

## What the second harness showed

- **Holds across harnesses:** the contract and exporter needed no change for Claude. Stage boundaries, verdicts, gates and commit-bound lanes all came from one shared module, and the refactor left Codex output unchanged.
- **Does not hold: exact lane moves.** Only 1 of 8 retained runs, DeepSeek on 4 November, wrote its board in a form that can be replayed. Shell `.Replace` and `[regex]` edits defeat replay on Luna and all six Claude runs. This depends on how each model chooses to write a file, not on the harness.
- **Harness quirks stay in adapters:** early Claude MXC runs flag nearly every shell result `Exit code 5`, so the Claude adapter reads fixed gate text and never treats that flag as failure. Runs before `20261023T104412Z` kept no subagent transcripts, so their subagents' board writes and gates are invisible.

## Board watcher

`telemetry/board-watcher.py` observes the board from the host, so lane moves no longer depend on how a model writes the file. Both baseline runners start it just before launch and stop it after the last invocation. It runs outside the sandbox, changes no contestant configuration and writes `board-snapshots.jsonl` to the run folder. A watcher that fails to start only logs a warning.

Reading a file can make a contestant's rename fail on Windows, even with full sharing. A first version did this: 7 failed renames in 3,000 at a 0.25 s poll, against none without a reader. The watcher therefore finds changes by enumerating the directory, and opens the file and takes a full oplock as one atomic step, so a conflicting write or rename waits for the read to finish. If anyone else has the file open, the oplock is refused and the read happens on a later tick, which also keeps torn boards out of the record.

| Test | Result |
|---|---|
| 3,000 renames plus 3,000 direct writes, no reader | 0 failures |
| The same, with reads in a tight loop | 0 failures |
| The same, watcher polling at 0 s and at 0.25 s | 0 failures, 0 torn boards, final board captured |
| Codex mock (`c0-full`) through MXC `--isolated` | 4 board states, `board_source: watcher`, lane coverage `complete`, from 0 replayable writes |
| Claude mock (`c0-full`) through MXC `--isolated` | 4 board states, `board_source: watcher`, lane coverage `complete`, agrees with 4 gate readings and 2 commits |

A board state shorter than one poll can be missed. If a commit captured it, the record fails to reconcile and falls back; if not, the skipped step is invisible. Observed moves have `actor: unknown`, because a file snapshot does not say who wrote it.

Both are exported to their retained sessions under the name `geeky-orchestration.end-to-end`: 109 spans for DeepSeek and 87 for Luna, with no span missing on readback. Luna's exported timeline predates the `(by this commit)` label, so its text reads `T1: Ready -> Done` at 20:01:38; the span's `lane_evidence` metadata is correct. Spans cannot be re-sent, so this stays as it is.

## Limits

- Tested on retained runs from two Codex configurations and on Claude Code with Claude and GPT models, on Windows and macOS. No other harness has been tried, and no Claude process trace has been exported, including for Mac runs that do have telemetry sessions.
- The watcher has run only on mock contestants on Windows, on NTFS. No model-driven run has used it, and its Linux and macOS read path has not been run.
- No scorer reads this trace yet. `score-run.py` and `parity-eval.py` are unchanged, and a scorer based on it would need its own score scope.
- The Codex adapter does not yet record gates run as shell scripts; the Claude adapter does.
- Phase is not recorded, because existing phase parsing is unreliable.
- Dashboards can filter on metadata but not group by it.
- Total Cost stays $0.00 in Langfuse until model prices or per-generation cost are supplied.
