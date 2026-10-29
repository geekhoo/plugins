# Luna/high C0 results — both stopped

The authorized Codex run ended on an unrecoverable bridge error. The following
fresh Claude run produced working code but exhausted its deadline before final
review acceptance. Neither run establishes an accepted end-to-end workflow or a
comparative composite score.

| Harness | Run | Workload duration | Terminal result | Independent oracle | Langfuse readback |
|---|---|---:|---|---|---|
| Codex | `20261028T114114Z-eb4361e5` | 946.080 s | Exit 1, crash; `bridge_mapping_error` | 0/13 passed; 13 missing-package setup errors; stable over 3 | 8 traces, 258 observations; presence verified, coverage unknown |
| Claude | `20261028T115941Z` | 5999.150 s | Exit 124, timeout during final review | 13/13 passed; stable over 3 | 20 traces, 953 observations; required coverage met |

Settings: `c0-wordstat`, Windows MXC, LiteLLM `vercel/gpt-6-luna`, high requested
for main, workers and reviewers; 6000-second hard budget, 60-second advisory
reserve, zero host recoveries. Source and prompt pins match on both runs:
`0b1f5fbc0e84b110ea0f9fa59ddfa711b46cf53a` and
`124eba9b416324a052c8e25031f1660200f52a05a74c9a1d9ce13527b270ddde`.
The [Luna-only qualification waiver](../c0-luna-preparation-20261028/qualification-waiver.json)
remains a waiver, not qualification proof.

## Codex outcome

Real structured V2 research dispatches and waits worked. Three research workers
completed, specification commit `29a576f` was made, and planning validators passed
after corrections. During required alignment re-review, two child turns and then
the main turn failed on the sanitized `bridge_mapping_error`. The saved error
does not identify the underlying mapper defect. Five native client reconnect
messages occurred; no operator retry or resume was launched. No `wordstat/`
implementation exists. Native contexts for main and seven children record Luna/high.

## Claude outcome

Research, planning, plan review, implementation and task/phase acceptance completed.
The coder was dispatched at 12:56:08 UTC, approximately 56 minutes after run start.
T1/phase review returned PASS/READY TO ADVANCE, DoD and kanban passed, and
`0ca67a2` committed the implementation. Spec and plan commits are `f3627c0` and
`96359ae`.

Final `impl-review` required test-only changes: stronger argparse usage assertions
and file-error tests without an unsupported UTF-8 stderr-path assumption. I/O
re-review passed; test-quality re-review requested `b"usage: wordstat"`. That final
edit was applied and **18 tests passed in 2.90 s at 13:38:22 UTC**, but affected-domain
re-review and overall PASS did not finish. Persisted `review-impl.md` remains
NEEDS FIXES; the latest test corrections are uncommitted. The last reserve check
had 24 seconds left. The final checkpoint edit did not persist before timeout.

An earlier spec commit-message gate failed and was followed by a commit under
a self-declared deferred warning. The passing later reviews do not erase that
observed procedural deviation. The completion heartbeat reflects T1, not final
workflow acceptance. The outer Claude controller exited 0, while the authoritative
workload record says exit 124/timeout.

## Operator incident and evidence boundaries

Before the intended Codex run, a dot-sourced credential loader overwrote a harness
selection variable and prematurely started Claude run `20261028T113704Z`. The
operator stopped its process tree after four unique assistant responses, preserved
its original record/capture, fixed loader scoping and verified both branches offline.
The owner explicitly authorized one fresh Claude replacement after Codex. That
replacement is the Claude row above. The aborted launch is not silently counted as
a clean attempt or merged into either final result; its usage/billing is not reconciled.

Local evidence lives under `outputs/c0-luna-live-20261028/`: `authorization.json`,
`operator-interruption.json`, `results.json`, `verification.json`, both controller
and cleanup records, raw terminal pins, and snapshots of both final workspaces.
Original captures remain under `evals/baselines/c0-wordstat/<run>/`. The operator
incident's original record retains its last running state; the interruption and
controller sidecars reconcile the observed abort without rewriting original bytes.

All 115 historical capture files remain unchanged; 126 current terminal/snapshot
files are hash-pinned. No credential values were found in captured artifacts.
No further contestant, paid probe, judge, score publication, source commit or push
was performed. Claude's zero token/cost fields result from missing final-result
accounting and must not be interpreted as zero usage. Billing and token totals are
not reconciled. No cross-harness composite is published.

Stale documents: current root/plugin READMEs and readiness now point here. The
preparation report and earlier dated analyses remain preserved as history; they
grant no new launch or recovery authority. See [kanban](kanban.md),
[handoff](handoff.md), and [references](references.md).
