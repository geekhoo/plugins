# Native Codex C0 — blocked at specification commit

Run `20261029T043904Z-28148c1d` stopped after354.494seconds. The agent explicitly
reports the spec draft incomplete and unaccepted; later stages are unreached.
Process exit0/turn.completed is not accepted workflow completion. No implementation
commit or wordstat package exists. Oracle0/13,13missing-package setup errors,
stable over3runs. Langfuse readback:4traces,100observations.

Native Responses/V2 worked: three actual research workers received opaque
messages, returned coherent reports, and structured waits completed. No bridge,
protocol or encryption error occurred. Luna/high,6000/60seconds and zero recoveries
were retained. Claude remained stopped.

The concrete blocker is a rule contradiction. Global AGENTS says the commit gate
runs before every commit; check-commit.py explicitly validates the geeky-implement
format and rejects messages without a task reference. spec-research prescribes
its documentation commit before implementation task IDs exist. The agent refused
to fabricate an ID or bypass the mandatory gate and stopped correctly.

Preparation failure: the operator verified native transport but failed to resolve
this already-visible workflow conflict before declaring the next attempt ready.
The earlier Claude run had disclosed the same commit-gate failure as a self-declared
exception. Current readiness is BLOCKED pending a legitimate pre-task commit rule
and regression proof for the exact prescribed spec message, while retaining task
references for implementation commits. No fix or retry is claimed here.

## Proposed unblock (specified, not yet applied)

Specified on 29 October 2026. The gate contradiction is the only blocker this run
exposed. The fix stays narrow:

- `check-commit.py` and `.ps1` accept `Tasks: none`, but only on `docs` commits. A
  non-docs commit carrying `Tasks: none` fails, and implementation commits still
  need `T<n>`.
- The spec-research commit gains `-m "Tasks: none (pre-planning specification)"`.
- The `AGENTS.md` gate row and the MCP docstring say the same.
- Regression tests cover the exact spec message through both gate twins.

Preparation exports committed HEAD only (`run-codex-baseline.ps1:5`), so the fix
has to be committed before the contestant can see it. The run setup otherwise
matches the Claude reference: Windows MXC, LiteLLM `vercel/gpt-6-luna`/high on all
eight roles, `-LitellmWireMode native`, 6000/60 seconds, one attempt, zero
recoveries, Langfuse from startup and prompt `124eba9b…`. The plugin SHA will
differ from `0b1f5fb` by that gate change alone; scoring is untouched. Overtime,
as granted to Claude, needs separate written authorization.

Native wire is proven through research only. The earlier bridge crash happened
in plan-review re-review with forked reviewers, a path native mode has not yet
exercised. Known friction, recorded rather than fixed: one heredoc-into-`apply_patch`
failure, and researchers without WebSearch/WebFetch. The paste-ready Codex kickoff
is [handoff.md](handoff.md).

Commit-gate blocker resolved by `629ae3f31dd230b859abaa2e9a2152ce1f3de5d5`; see [fix and fresh attempt record](../c0-commit-gate-fix-20261029/README.md).

Evidence: original [run record](../../baselines/c0-wordstat/20261029T043904Z-28148c1d/run.json)
and [stream](../../baselines/c0-wordstat/20261029T043904Z-28148c1d/stream.jsonl);
local `outputs/c0-codex-native-live-20261029/` contains results.json, cleanup.json,
terminal-evidence-pins.json and the final-workspace snapshot.50terminal/snapshot
files are pinned. No automatic retry, provider probe, source fix, commit or push
was performed. Existing preparation and raw historical evidence remain preserved.
