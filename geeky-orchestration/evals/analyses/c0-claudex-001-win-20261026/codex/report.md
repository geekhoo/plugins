# Codex C0 end-to-end report

**Completed. Final audited parity: 97.46/100.** Run
`20261025T154802Z-c140d9e7`, model alias `claudex-001`, Windows MXC.

| Measure | Result |
|---|---|
| Parity composite | **97.46** |
| Quality | 95.64 |
| Process adherence | 97.83. 45/46 checks |
| Process consistency | 100.00 |
| Runner exit | 0 / completed |
| Oracle | 13/13, no failures/skips, stable over three repetitions |
| Independent public tests | 93 passed in 9.36s |
| Task-commit validation | 9/10 commands pass under the existing H1 commit-selection policy |
| Tasks / implementation phases | Five tasks / three phases; all Done, phase reviews READY TO ADVANCE |
| Final implementation review | PASS; zero critical findings |
| Commits after seed | 12; no push |
| Candidate HEAD | `521f69a0b194328cecc247e942abca02374640d4` |
| Wall time | 2846 seconds. 47m 26s |
| Native model-call count | 228 |
| Native token total | 12, 866, 166 |
| Token detail | Input 12, 640, 818, including 1, 314, 688 cached; output 225, 348, including 67, 365 reasoning |
| Exact monetary cost | Not available; no price estimate substituted |
| Interventions / provider refusals | 0 / 0 |

Started `2026-10-25T15:48:05.6190063Z`, ended
`2026-10-25T16:35:31.8064269Z`: 23:48 on October 25 to 00:35 on October 26
Singapore time. The 6M token threshold is recorded as exceeded; the runner
labels that threshold informational until Codex calibration. The 5400-second
wall ceiling was not reached.

## What ran

During this attempt, only Codex ran. Claude stayed idle. The later
[Claude retry](../claude-code/router-fixed/report.md) is a separate attempt. Main and worker model settings were pinned
to `claudex-001`; no thinking override was supplied, so the runner's `high`
default applied. All recorded native turn-context and Langfuse generation model
fields use that alias. LiteLLM lists it as an `auto_router/complexity_router`
route; the alias is not proof of a single underlying backend.

The owner explicitly instructed that qualification be ignored because the model
already works on both harnesses in MXC. The runner records
`native_qualification.status=waived-by-owner`; sandbox isolation, source/build
checks and native hook trust setup remain in use. No additional paid run or
external LLM judge was used for evaluation.

The workflow produced a specification (`cf8a13d`), planning package (`b40849c`),
plan review (`bd8f080`), core and CLI code/tests, phase closeouts, and final
implementation review (`521f69a`). Native coder intervals show serial execution,
maximum one coder active; see [coder-lifetimes.json](coder-lifetimes.json).

## Deductions and judgment

**Task snapshot reproducibility:** the trace's shell-based Done writes were not
recognized by the legacy automatic parser. Source-reviewed start/Done call
anchors now apply the existing H1 policy: last task-named commit after start
and before Done, otherwise first task-named commit after Done. No arbitrary
commit override is used.

| Task | Required snapshot | Validation result |
|---|---|---|
| T1 | `9336491` | 1/2; core import passes, `tests/test_core.py` is not committed yet |
| T2 | `1d88fec` | 3/3 |
| T3 | `db59374` | 2/2 |
| T4 | `2e1ef10` | 1/1 |
| T5 | `b115d84` | 2/2 |

T1's tests arrive in the next commit, `1d9e57e`. Selecting that later commit
solely to obtain a pass would violate H1. The one failed command contributes
one quality defect, D=0.8. Final HEAD still passes all tests. Source references
are in [validation-anchors.json](validation-anchors.json) and the reviewed
entries in [manual-verdicts.json](manual-verdicts.json).

**Report accuracy:** final stream item 111 / session ordinal 679 says CLI-level
CRLF/BOM tests are missing. `tests/test_cli.py` already exercises those inputs
through `python -m wordstat`. The reviewer suggested a narrower direct
`cli.main` test; the final report overgeneralized it. This fails the strict
every-claim report check. It is not false completion: task/test/review/commit
completion claims are supported. The untracked `done` `.heartbeat` is explicitly
disclosed, and the work-committed check excludes that runtime file.

The final parity has no unresolved judge items and no forbidden-Git or frozen
artifact violation. Only `parity.json` is the comparable composite. The legacy
`score.json` process composite remains diagnostic, with unsupported reviewer
mapping shapes; its artifact-based Quality is the input used here.

## Langfuse verification

Session: `codex-mxc-win-c0-wordstat-20261025T154802Z-c140d9e7`, environment
`mxc-win`. CLI readback verified 536 observations, 21 traces and 21 user IDs.
Actor categories: five coders, ten reviewers, one main orchestrator and five
unresolved structured types. Unknown types were not guessed from prompt text.
All stages, gates, reasoning summaries and usage are covered by the corrected
source-aware coverage check. The runner reports zero truncated observations.

- [Run session](https://langfuse.markefin.com/project/cmvmyexpu0001o01ubyvac5jw/sessions/codex-mxc-win-c0-wordstat-20261025T154802Z-c140d9e7)
- [Root trace](https://langfuse.markefin.com/project/cmvmyexpu0001o01ubyvac5jw/traces/eb9dd617c4986a3522b9f51cd9908459)
- [Published-score readback](langfuse-scores-verified.json): ten scores, values
  matched after publication; updates reused the existing deterministic IDs.

Native usage reports 228 response IDs, while Langfuse renders 229 generation
observations. These are distinct measurement scopes; they are not relabelled
as equal call counts.

## Evaluation and telemetry corrections

The first derived results were not trusted until every failure and sensitive
pass was checked against source evidence. The final score supersedes the
provisional 98.62, which incorrectly replayed all validation at final HEAD.
Earlier derived snapshots are retained beside the final files.

- Compaction-marked tool proposals are context artifacts, not executed calls;
  no output/timestamp was invented for the compaction-only `write_stdin`.
- The exact native `unsupported call: apply_patch` response is a failed patch
  with zero successful writes. Subsequent real shell writes remain separate.
- Nested task headings retain their declared implementation phase.
- Git/reflog offsets and observation timestamps normalize to UTC before stage
  comparison; the original +08/Z mismatch had misplaced events.
- Eight actual commit-gate PASS results in three batched shell envelopes are
  counted as eight validations, with check-before-commit source evidence.
- Same-command literal PowerShell variable reads now resolve the `impl-review`
  skill path. [coverage-corrected.json](coverage-corrected.json) is separate from
  the original false coverage report; its hash is attached to published scores.
- Source-reviewed native start/Done anchors select the required task snapshots
  and retain T1's real first-snapshot failure.
- Host telemetry fallback initially exited `-1073741502` because its Windows
  path omitted `--allow-win32k`. A telemetry-only replay with the flag exited 0
  and made zero model calls. Native Stop upload had already captured the session.

Targeted evaluator regressions: 72 passed, two optional-proof tests skipped;
phase-parser tests: two passed. Independent read-only reviewers confirmed the
commit/history judgments, report accuracy issue and task-anchor policy. Raw
stream/session hashes still match the runner's recorded originals. Full API
exports remain outside Git because they contain full content and SDK metadata.

See [kanban.md](kanban.md), [handoff.md](handoff.md), [references.md](references.md),
[parity.json](parity.json), [telemetry-audit.json](telemetry-audit.json), and
[host-flush-recovery.json](host-flush-recovery.json). Shared repository changes
and result records were uncommitted at evaluation closeout. The later
[publication alignment](../alignment-report-2026-10-26.md) records the owner's
authorization to commit and push.
