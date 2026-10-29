# Fresh sequential C0 results, 27 October 2026

**Both attempts are terminal; neither delivered an implementation.** Codex ran
first, then Claude after its terminal cleanup. Both used Langfuse from startup.
No contestant retry, continuation or operator recovery was performed.

| Result | Codex | Claude Code |
|---|---|---|
| Run ID | 20261026T202318Z-fc8f0aa8 | 20261026T202649Z |
| Requested model, every role | claudex-001 | claudex-001 |
| Effort | Explicit high for main/workers/reviewers | Runner-default thinking |
| Budget / reserve | 6000s / 60s advisory | 6000s / 60s advisory |
| Contestant interval | 89.34s | 5999.01s, approximately 100 minutes |
| Native exit | 0, but workflow incomplete | 124, timeout |
| Runner verdict | turn-failed / is_error=true | timeout / is_error=true |
| Furthest substantive stage | Research started | Plan review partially completed |
| Post-seed commits | 0 | 2 documentation commits; 0 implementation commits |
| Oracle | 0/13; 13 missing-package setup errors, stable 3x | 0/13; 13 missing-package setup errors, stable 3x |
| Langfuse readback | 4 traces / 41 observations | 12 traces / 367 observations |
| Strict composite | Withheld: incomplete error-marked stream | Null: incomplete, with four unresolved judgment checks |

Run IDs are UTC. The native intervals on 27 October in Singapore were approximately
04:23:22–04:24:51 for Codex and 04:26:52–06:06:51 for Claude. Native run.json timestamps
and execution intervals are authoritative; launcher exit codes alone are not acceptance.

## What happened

Codex successfully started three research workers through the mapping bridge.
All actual contexts used claudex-001/high; spawn calls carried explicit
encrypted_function_args=[]. No decryption error recurred. One stream interruption
caused a client reconnect, after which the main response contained a literal,
malformed wait_agent tool-call string as ordinary output_text. That call was not
executed. The main turn completed and all three workers were interrupted during
teardown, leaving only the seed files. The captured record cannot attribute the
earlier stream closure to a particular upstream component. See the detailed
Codex audit in the local evidence folder.

Claude used its entire budget on workflow documentation and reviews:

- Specification/research: roughly 30 minutes; committed
  `0f6fb45609fee496790fbdc1200ad40bc88730b2`.
- Planning: roughly 45 minutes, including PM review and resolving ten notes;
  committed `e9f16269869a15c13d589c25948dce049f7bfba4`.
- Plan review: the remaining roughly 25 minutes. Alignment returned PASS WITH
  NOTES, four mechanical suggestions were corrected, and sequencing returned
  PASS. Three deterministic planning validators passed again just before the
  timeout. The overall plan-review disposition was not consolidated or committed.

The evidence shows ordinary review/fix/revalidation work, not an endless repeated
review loop. At cutoff T1 remained Ready and T2/T3 Backlog. Implementation and
final implementation review never started. No wordstat/ package exists.

| Workflow stage | Codex | Claude |
|---|---|---|
| spec-research | Started, incomplete | Complete, specification commit saved |
| geeky-plan | Unreached | Complete, package commit saved |
| plan-review | Unreached | Partial; no final overall acceptance |
| geeky-implement | Unreached | Unreached |
| impl-review | Unreached | Unreached |

Claude left three tracked documentation changes and an untracked review-plan.md.
The workspace, Git bundle, raw captures and a byte-checked 15-file working-tree
snapshot are preserved. The stale handoff claim that plan-review had not started
was not repaired inside the contestant's evidence.

## Telemetry and accounting

Both sessions were read back successfully through the observations API, with no
pagination truncation. Codex has 11 generations and 26 tool observations; Claude
has 153 generations and 202 tool observations. Exporter presence does not prove
complete workflow coverage: the implementation/coder/final-review points were
not reached. No scores were published and no judge was run.

Claude's native result totals are zero because timeout prevented its final result
event; those are not zero-usage evidence. Langfuse reports 7,780,317 total tokens
(854,200 input, 6,868,416 cache-read input and 57,701 output). These are telemetry
totals, not independently reconciled billing. They exceed the case's historical
6M informational threshold even though the timeout runner's zero-based field
says otherwise. Codex's reported usage is retained without inventing missing
cost or reconciling overlapping cached/reasoning fields into a new bill.

## Source, scope and preservation

Both workflow exports use source commit
`4228c3f73fc3894c86725cf42900406c1d2d981f`, canonical prompt SHA256
`4d8ebd2f16b83a14c8f7278935105ab31e86b01e2b51098a7d7af0f07a17cf2e`.
Local operator mapping/lifecycle changes were separately bound by the 33-file
source manifest. Source and original dirty files were verified unchanged before
reporting edits. All 66 terminal capture files are pinned. Earlier failed/aborted
records and historical scores remain untouched.

One pre-contestant setup failed with zero invocations/provider calls: the Windows
venv Python redirector PID differed from the bridge interpreter. The lifecycle
helper was corrected to launch the native base interpreter; five local lifecycle
tests passed before refreshed source pins and the actual Codex attempt. This was
not a paid contestant retry. The prior setup record is preserved separately.

The existing claudex-001 qualification waiver was retained with its original
reason; no broader native qualification is claimed. The same router alias does
not establish identical backend models or matched effort between harnesses.
No repository commit or push was made; contestant documentation commits are
inside the isolated Claude workspace only. No evaluation or bridge process remains.

## Evidence

Repository-local ignored evidence: `outputs/c0-fresh-sequential-mapped-20261027/`:
authorization.json, source-pin.json, codex-outcome.md, both controller/launch logs,
both observation readbacks, telemetry-readback-summary.json, both strict scoring
logs, terminal-output-pins.json, runtime-source-preservation.json,
claude-working-tree.json and claude-workspace-snapshot/. Final report/verification
files in that folder bind the source, results and preservation checks.

Native records:
[Codex run](../../baselines/c0-wordstat/20261026T202318Z-fc8f0aa8/run.json),
[Claude run](../../baselines/c0-wordstat/20261026T202649Z/run.json).
See [kanban](kanban.md), [handoff](handoff.md), [references](references.md).
