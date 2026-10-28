# C0 operator readiness and verification

Latest [Luna/high preparation](analyses/c0-luna-preparation-20261028/README.md),
2026-10-28: runner/workflow fixes are committed and the owner explicitly waived
qualification for this Windows MXC C0 pair using `vercel/gpt-6-luna` at high for
main, workers and reviewers. The new [waiver](analyses/c0-luna-preparation-20261028/qualification-waiver.json)
does not establish qualification or grant launch authority. Fresh official
preparation and private build copies are recorded under local
`outputs/c0-luna-final-preparation-20261028/`; old draft commands are superseded.
Both evaluations remain stopped. Preparation configures Langfuse hooks but performs
no provider call, MXC workload, live telemetry operation or judge call.

Current state, 2026-10-26: local inventory and mock verification pass. **LIVE HELD.**
This record grants no paid run, provider or judge call, sign-in, live telemetry
write, or schedule. The canonical contestant prompt remains unchanged.

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
