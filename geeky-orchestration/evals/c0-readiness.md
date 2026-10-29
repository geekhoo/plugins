# C0 operator readiness and verification

**Current native Codex C0 gate blocker: RESOLVED.** Fix `629ae3f` passes 10 tests
and 12 paired subprocess subtests. Offline inventory returned `inventory-ready`
with no errors. Fresh preparation at committed HEAD is pending before the
owner's one authorized native attempt. See [current work](analyses/c0-commit-gate-fix-20261029/README.md).
The rotated Codex Langfuse keys passed one read-only existing-session check.

Historical blocked result: the earlier authorized native run
`20261029T043904Z-28148c1d` completed its agent turn but explicitly stopped with
specification unaccepted. Global AGENTS requires `check-commit` before every
commit; that implementation-format validator requires a task reference before
spec-research has created task IDs. Native V2 delegation/waits worked. The earlier
native preparation missed this known rule conflict and is not completion-ready.
See [run outcome](analyses/c0-codex-native-run-20261029/README.md). Both evaluations
are stopped; no retry or source change was made during this attempt.

The blocker is now fixed: `Tasks: none` is accepted on `docs` commits only,
the spec-research commit includes it, and both gate twins have regression proof.
Re-prepare the native profile at the new HEAD. The
[Codex kickoff](analyses/c0-codex-native-run-20261029/handoff.md) covers fix,
preparation and one authorized launch. Readiness stays BLOCKED until that fix
lands; that source gate is now satisfied, while fresh profile verification remains pending.

Latest [focused Codex preparation](analyses/c0-codex-native-preparation-20261029/README.md),
2026-10-29: Luna's prepared Codex profile uses explicit native Responses/V2,
bypassing the mapping bridge that failed in the captured run. All eight roles
remain Luna/high;6000/60 seconds, one attempt and zero recoveries. Seven focused
offline checks pass. Full native C0 completion remains unverified and no run is
authorized by this preparation. Operator runner/test changes are uncommitted;
fresh source/tool pins and the exact held command are in local
`outputs/c0-codex-native-preparation-20261029/`. Historical captures are unchanged.

Latest [authorized Claude overtime closeout](analyses/c0-luna-overtime-20261028/README.md)
completed at candidate `fba5d30`, with final-review PASS, 18 public tests and
13/13 oracle tests stable over three repetitions. Additional active time was
1082.148 seconds; cumulative active time7081.298 seconds. Source-reviewed parity
is95.14 for the preserved initial timeout and98.44 cumulatively. Twenty scoped
scores were published/read back with overtime metadata. This cumulative result
retains the original timeout and does not replace the original budgeted outcome.
Codex stayed stopped; no further run or recovery is scheduled.

Latest [Luna/high runtime results](analyses/c0-luna-sequential-20261028/README.md):
the owner-authorized pair is terminal. Codex failed on `bridge_mapping_error`
during plan review (946 seconds, no implementation); Claude reached the hard
limit during final review (5999 seconds), with 13/13 oracle tests stable over
three repetitions. Both traced to Langfuse. Source remained
`0b1f5fbc0e84b110ea0f9fa59ddfa711b46cf53a`; no live fixes or source commits were
made. The initial operator-aborted Claude launch and explicitly authorized fresh
replacement are preserved separately. No additional attempt, recovery, judge or
score publication is authorized. Preparation recipes below are historical inputs,
not permission to reuse the consumed attempts. Both evaluations are stopped.

Latest [Luna/high preparation](analyses/c0-luna-preparation-20261028/README.md),
2026-10-28: runner/workflow fixes are committed and the owner explicitly waived
qualification for this Windows MXC C0 pair using `vercel/gpt-6-luna` at high for
main, workers and reviewers. The new [waiver](analyses/c0-luna-preparation-20261028/qualification-waiver.json)
does not establish qualification or grant launch authority. Fresh official
preparation and private build copies are recorded under local
`outputs/c0-luna-final-preparation-20261028/`; old draft commands are superseded.
Both evaluations remain stopped. Preparation configures Langfuse hooks but performs
no provider call, MXC workload, live telemetry operation or judge call.

Latest [minimal Claude/MXC Messages probes](analyses/mxc-claude-messages-20261027/README.md):
Luna/GLM/Haiku/MiMo passed real MCP/tool_result/final-marker roundtrips on Claude
2.1.311; MiniMax/DeepSeek returned provider-resource 404s. An initial relay path
mistake is preserved separately. Both C0 evaluations remain stopped; these are
selected diagnostic checks, not full workflow qualification.

Latest [minimal reasoning normalization](analyses/bridge-reasoning-normalization-20261027/README.md):
178 regressions and three actual HTTP-bridge checks passed for MiniMax, DeepSeek
and MiMo. This is selected bridge proof, not native upstream or full workflow
qualification. Source is uncommitted; old prepared source pins are stale. Both
evaluations remain stopped.

Latest [bounded retest](analyses/litellm-bounded-retest-20261027/README.md): Luna's
selected opaque receive passed with a meaningful altered-value negative; the API
did not explicitly reject tampering. Larger caps finished the formerly limited
generations, exposing wire-shape failures. Thinking none remains unverified on
MiniMax/DeepSeek/MiMo despite being requested. Both C0 evaluations remain stopped;
these selected endpoint checks do not qualify a complete workflow.

Latest separately authorized diagnostic: [six small model probes](analyses/litellm-six-models-20261027/README.md).
All six basic routes returned HTTP 200; selected bridge cases passed for Luna,
GLM and Haiku. Other low-cap results remain inconclusive and native V2 findings
are recorded separately. Eighteen client requests do not prove underlying gateway
attempts/billing; DeepSeek's error reports 20 internal attempts. No evaluation
was started and these results are not full workflow qualification.

New offline tooling, 2026-10-27: [Responses/Codex V2 diagnostics](tools/responses_contract/README.md).
Plans/replay run without credentials/network. Endpoint probing is a separate
explicit command for later authorization; no endpoint was tested while creating
these tools. They are not C0 launches or native workflow qualification. Both
evaluations remain stopped.

Latest offline follow-up, 2026-10-27: [root-cause investigation](analyses/c0-root-causes-20261027/README.md).
Both evaluations remain stopped. Research, planning and plan review now consume
the shared budget; both runners pass the total as well as deadline/reserve. The
canonical prompt has changed, so historical prompt hashes below are historical.
The bridge rejects the observed tool-call text with a dedicated error; its
upstream origin remains unresolved. No fresh live compatibility claim is made.
Preparation rejects missing or substantively different budget helper/skills in
the committed export. Current fixes are uncommitted and must be included in a
reviewed source commit when authorized; do not reuse the old prepared launches.
Generate new source/prompt pins after that step. Inventory alone does not prove
this export gate, runtime obedience, qualification or live readiness.

2026-10-27 update: the [Codex V2 wire mapping fix](analyses/codex-v2-litellm-mapping-20261027/README.md)
has offline tests and one successful synthetic streaming LiteLLM request. Both
evaluations remain stopped. This request was separately authorized for the
mapping fix; it is not a C0 run, role/workflow qualification or telemetry proof.
The inventory now fingerprints the mapper and its host lifecycle helper.
Historical inventory/source pins and prepared launch artifacts below remain
preserved and must be refreshed before any future authorized evaluation.

Historical state, 2026-10-26: local inventory and mock verification pass. **LIVE HELD.**
This record grants no paid run, provider or judge call, sign-in, live telemetry
write, or schedule. The canonical contestant prompt was unchanged at that checkpoint.

## What is verified

Run from `C:\Users\gerald.khoo\geekhoo-plugins` on Gerald's Windows machine:

```powershell
C:/Python314/python.exe geeky-orchestration/evals/scripts/check-c0-readiness.py --output outputs/c0-readiness
C:/Python314/python.exe geeky-orchestration/evals/scripts/check-c0-readiness.py --mock-test --output outputs/c0-readiness
```

The first command inventories files, local executable versions, pins and rendered
prompt bytes. It runs no MXC workload. The second also runs existing local telemetry
fixtures and an actual publisher dry-run fixture with fake HTTP and no live client.
Each command creates a distinct directory beneath ignored `outputs/`. Unsupported
live/launch options fail argument parsing. Neither result authorizes a run.

At source HEAD `599e07c4886ada12938eefe5d0f4b76ca0a6d0ec`, the default command
returned `inventory-ready`; the mock command returned `mocktested-ready`, 28 passed.
The new focused readiness suite passed 10 tests. These checks did not repeat the
earlier 147-test suite or any MXC attempt.

| Local evidence | SHA-256 |
|---|---|
| `outputs/c0-readiness/20261026T153948Z-b98fcd69/readiness.json` | `a8aa25e490ff0494ee0581c520a53577b7e33864bdf709662ebaeb6cbcd4962d` |
| `outputs/c0-readiness/20261026T153949Z-366b876a/readiness.json` | `e0cdc770b0ec5cb62d915a74e58ede3e02f60988f049ba540fd5595f6087f0fe` |
| Same directory, `mock-tests.log` | `5763cbdd5fbd9e6c9d683b8f9c26f869f6fdd16f1a15005b3bc510040c4ffcd8` |
| `outputs/c0-readiness-gitfix-20261026T233943/focused-tests.log` | `25d91060ab992e7b107f1beecc34e5f7652805d9668bb0430e7724f91a7f35cb` |

Reports retain normal Git dirty scope and `commit_only_proof=false` because the
readiness changes were not committed when tested. Git inventory preserves the
nonsecret home/config paths needed to honor global ignores; child test processes
still receive no provider or telemetry credentials. Earlier inventory reports are
superseded by these corrected reports; their saved files remain unchanged. Generate fresh inventory after publication. Compare
its `repo_head`, source hashes and effective prompt hash before any later action.
The recorded effective prompt hash is
`4d8ebd2f16b83a14c8f7278935105ab31e86b01e2b51098a7d7af0f07a17cf2e`.

Local version probes found Python 3.14.7, Codex 0.164.0, Claude Code 2.1.304,
Node 24.22.1, PowerShell 7.6.5 and Langfuse CLI 1.2.4. The CLI's bundled schema
reports API 4.35.0; inspect it with `langfuse.cmd api schema --json`. The pinned MXC
EXE/DLL, Claude hook and Codex archive match. MXC was not executed in this readiness
pass. The derived Codex hook has an observed hash but no expected pin.

Installed executables and mock transport do not establish service compatibility,
credential availability, model routing, live delivery or runtime qualification.
Every report says `paid_run_authorized=false`, `live_launch=held`,
`live_telemetry_verified=false`; configured and observed models remain unknown.

The older `Invoke-C0.ps1` preparation wrapper is historical. Its stale source pin and missing authorization-reference field make it unsuitable as a current launcher. Use the current baseline runners after fresh readiness inventory.

## Candidate run settings

The prior preparation used `claudex-001` on both harnesses. Claude requested runner
default thinking. Codex requested high for main and workers; source
`adapters/codex/prepare-profile.py` makes reviewer roles inherit worker reasoning
when no reviewer override is supplied. A future recipe must explicitly record
reviewer high, with the same model, rather than silently inherit it.

The candidate budget is 5400 seconds with the proposed 900-second advisory closeout
reserve inside that budget, one paid attempt and zero recoveries. Retain the owner's
existing native-qualification waiver with its exact reference/reason; it proves no
qualification. Do not buy a probe to replace it. These are proposed future settings,
not new launch authorization. Record desired and observed model/effort separately.
Claude default and Codex high differ; equal backend or equal effort is unproved.
The absolute process-stop cutoff, missing historical validation cache, four synthetic
judgment items and live model behavior remain open. Historical scores stay
97.46, 90.33 and 98.33. Scripted fixtures supply no ranking.

## Paste-verbatim operator prompts

These prompts are operator instructions. They do not replace
`prompts/end-to-end.md` or change contestant workflow requirements. Live prompts
require a separate explicit authorization naming that phase. Once a contestant run
is authorized, preserve its existing end-to-end workflow authorization without
asking the contestant to obtain it again.

### Offline check now

```text
On Gerald's Windows machine in PowerShell 7, workdir C:\Users\gerald.khoo\geekhoo-plugins,
read geeky-orchestration/AGENTS.md, geeky-orchestration/evals/c0-readiness.md,
geeky-orchestration/evals/lessons-learned.md, then the two readiness script files. Verify git
HEAD and status without resetting. Run C:/Python314/python.exe
geeky-orchestration/evals/scripts/check-c0-readiness.py --output outputs/c0-readiness. Use
--mock-test only if fresh local mock proof is needed. Inspect the newly emitted JSON and log;
report exact repo_head, dirty scope, prompt/source hashes, readiness state, tool/pin errors
and mock counts. This is offline only: no MXC workload, contestant/provider/judge call,
sign-in or live telemetry operation. Done means the report exists, its hashes are recorded,
and LIVE HELD remains explicit. Report within 600 words.
```

### Later telemetry diagnostic, only after explicit authorization

```text
On Gerald's Windows machine in PowerShell 7, workdir C:\Users\gerald.khoo\geekhoo-plugins,
read geeky-orchestration/AGENTS.md, geeky-orchestration/evals/c0-readiness.md,
geeky-orchestration/evals/telemetry/README.md,
geeky-orchestration/evals/telemetry/langfuse-scores.py and the authorized diagnostic scope.
Generate fresh offline readiness JSON, record its repo_head and source hashes, and compare
exact HEAD/hashes again before remote work. Stop if they changed. Require a direct owner
authorization reference for this telemetry diagnostic, its project/session, allowed payload
and write/readback scope. No contestant, provider or judge inference is authorized. Before any
write, verify that automatic judge rules and integrations cannot trigger inference for the
diagnostic session; if exclusion cannot be established, stop before writing. Read-only
existing-session queries prove read compatibility only. After exclusion is verified, use the
current CLI schema and existing publisher to preview a separately named diagnostic session's
scoped payload, then perform the authorized write and read it back. Compare exact session,
score name, numeric value, config and evaluation-input hashes; retain request/response
evidence without credentials. Never overwrite historical C0 scores or enable a judge. Done
means actual write and matching readback are evidenced, or the specific compatibility/auth
blocker is reported. Keep paid canaries HELD. Report within 600 words.
```

### Later Claude C0 canary, only after fresh explicit authorization

```text
On Gerald's Windows machine in PowerShell 7, workdir C:\Users\gerald.khoo\geekhoo-plugins,
read geeky-orchestration/AGENTS.md, geeky-orchestration/evals/c0-readiness.md,
geeky-orchestration/evals/lessons-learned.md,
geeky-orchestration/evals/mxc-litellm-runbook.md, geeky-orchestration/evals/prompts/README.md,
geeky-orchestration/evals/prompts/end-to-end.md,
geeky-orchestration/evals/cases/c0-wordstat/brief.md and
geeky-orchestration/evals/cases/c0-wordstat/contract.md, then
geeky-orchestration/evals/scripts/run-baseline.ps1 and
geeky-orchestration/evals/analyses/c0-claudex-001-preparation-20261025/README.md. Generate
fresh offline readiness JSON and pin its exact repo_head/source/prompt hashes; verify them
again immediately before launch. Require a fresh direct owner authorization naming one Claude
c0-wordstat paid canary, authorization reference, claudex-001 for main/workers/reviewers,
runner-default thinking, budget 5400, advisory reserve 900, one attempt and recovery zero.
Record the retained qualification waiver/reason and fresh distinct workspace/state paths.
Confirm credentials/model availability without printing secrets. If any required field differs
or is missing, hold before launch. Use existing runner with explicit -Case c0-wordstat -Model
claudex-001 -Litellm -TimeoutSec 5400 -CloseoutReserveSec 900 -ResumeOnRefusal 0
-AuthorizationReference and the authorized paths. Do not change the canonical prompt or re-ask
workflow permissions it already grants. Launch once only. No retry, resume, paid probe, Codex
run, judge call or score publication is included. Observe the terminal record and capture,
oracle, workflow acceptance and configured-versus-observed model/effort evidence separately.
Preserve timeout/failure evidence and report unresolved gates. Done means terminal evidence
and a report within 600 words; successful exit alone proves no acceptance. Stop after this
canary.
```

### Later Codex C0 canary, separately authorized

```text
On Gerald's Windows machine in PowerShell 7, workdir C:\Users\gerald.khoo\geekhoo-plugins,
read geeky-orchestration/AGENTS.md, geeky-orchestration/evals/c0-readiness.md,
geeky-orchestration/evals/lessons-learned.md,
geeky-orchestration/evals/mxc-litellm-runbook.md,
geeky-orchestration/evals/adapters/codex/README.md,
geeky-orchestration/evals/prompts/README.md, geeky-orchestration/evals/prompts/end-to-end.md,
geeky-orchestration/evals/cases/c0-wordstat/brief.md and
geeky-orchestration/evals/cases/c0-wordstat/contract.md, then
geeky-orchestration/evals/scripts/run-codex-baseline.ps1,
geeky-orchestration/evals/adapters/codex/prepare-profile.py and
geeky-orchestration/evals/analyses/c0-claudex-001-preparation-20261025/README.md. Generate
fresh offline readiness JSON and pin its exact repo_head/source/prompt hashes; compare them
again before launch. Require a fresh direct owner authorization naming one Codex c0-wordstat
paid canary, authorization reference, claudex-001 for main/workers/reviewers, high reasoning
explicitly for each role, budget 5400, advisory reserve 900, one attempt and recovery zero.
Record the existing qualification waiver's exact reference/reason, explicit vetted
MxcBuildSource, dedicated CodexHome and fresh distinct workspace/state paths. Verify the
generated profile's reviewer registration matches the requested model/high setting. Confirm
credentials/model availability without printing secrets. Hold if any field is missing or
changed. Use existing runner with explicit -Case c0-wordstat -Model claudex-001 -Reasoning
high -WorkerModel claudex-001 -WorkerReasoning high -ReviewerReasoning high -Litellm
-TimeoutSec 5400 -CloseoutReserveSec 900 -AuthorizationReference, the authorized paths,
-SkipNativeQualification -QualificationOverrideReason and -Launch. Do not change the canonical
prompt or re-ask its granted workflow permissions. Launch once only. No retry, resume, paid
probe, Claude run, judge call or score publication is included. Record terminal outcome,
capture/oracle/workflow evidence and desired-versus-observed role models/efforts. Backend
equivalence remains unproved. Done means terminal evidence and a report within 600 words; stop
after the canary.
```

## Documentation inventory and disposition

Reviewed active root/plugin READMEs, the only tracked AGENTS.md, eval quickstart,
runbook, prompt index, lessons and current mock follow-up entrypoints. Corrected
manifest version references, planned-skill wording, publication state and live
authorization boundaries. The relative-link audit covered 306 nonarchive,
nonbaseline, noncapture, nongenerated Markdown files and found no missing active
entrypoint target. Dated local artifact references remain historical.

Frozen contracts, canonical contestant prompt, raw captures, hash manifests,
generated projections and dated acceptance/review reports are excluded from style
rewrites. Earlier implementation prose is labelled review-time history; the
current handoff directs operators here. Existing frozen kanban/references remain
historical records, not a new readiness work queue. No planning package was added.
The single maintained lessons document is [lessons-learned.md](lessons-learned.md).


## Review and publication binding

Three GPT-6.1-Sol/medium reviewers accepted this bounded change. They ran no tests
or network operations. `/root/sol_readiness_code_review` returned PASS for the
readiness tool and focused tests. `/root/sol_readiness_docs_review` returned PASS
after historical Unicode text was restored exactly.
`/root/sol_readiness_evidence_review` returned PASS for evidence, limits and lessons.
The parent coordinator retained integration and final verification.

Code commit `26e4395` contains only the readiness tool and its tests. Tested working
bytes and committed Git blobs are identical. Tool SHA-256 is
`c409fe3071ff04a266e5121d49bfa96c1ca093ca8f744fb5bb6a417f3f62c584`;
test SHA-256 is
`58f163ad099e1b14aaa5b960a1a04aca794f25b5988588df9d7d44433e8f8e57`.
The 10 focused tests and 28 mock checks above bind these bytes at the recorded
prepublication HEAD and dirty scope. They are not fresh mock execution at a later
documentation commit. Git history identifies the subsequent documentation commit;
generate fresh default inventory at that published HEAD. No paid or live action
is included in publication.
