# C1 run 2: operator guide

Historical preparation guide, 2026-10-24, Asia/Singapore. Target: Windows 11 / PowerShell 7, `C:\Users\gerald.khoo\geekhoo-plugins`. Run 2 subsequently completed as `20261023T194430Z-c5e04f3f`, with owner-overridden **Sol/medium for main and every descendant**, superseding the Luna settings below. Its corrected composite is 98.0. Read [checkpoint 5 closeout](codex-c1-checkpoint5.md) for current state. Do not reuse these historical launch commands as authorization for another run.

## Fast path: avoid setup and discovery turns

The preparation is already complete. The operator's job is to use it, not rediscover the harness. Use this guide and the short preparation result first; open detailed history only for an encountered issue.

- Use the exact pinned executable, complete package, existing signed-in home, vetted build and explicit model arguments below. Do not reinstall, sign in, rebuild, enumerate every tool/agent, or repeat provider/skill/hook catalogue discovery when the recorded fingerprints match. The runner performs its own required install/trust/preflight steps.
- Reuse the passing mock/native proof if sources, profile and environment are unchanged. Rerun only affected checks after a change. No paid smoke tests or repeated dry runs to reconfirm the same state.
- Keep the canonical prompt. Use existing role registrations, MCP bootstrap and generated plugin catalogue/paths. Do not resolve skills by repeatedly searching alternative caches, read all skill bodies in advance, or change shell/tool conventions mid-run. Load the active stage and its required references when needed. Do not add extra administration-agent reviews merely to repeat a completed check.
- Batch independent read-only checks into one shell call; show compact status and exact failure evidence. Use known output paths. During execution monitor at bounded intervals (about 60 seconds), not continuous raw-trace dumps or rapid polls. Investigate new failures once, at their actual source.
- Preserve full coder/test/reviewer evidence and required task/phase gates. Save turns by avoiding duplicate work, not by omitting acceptance evidence. Reuse valid own-commit test evidence; rerun for changed code or an unresolved claim.
- Launch one authorized attempt, then audit and score once. Read the known diagnostic policy before reacting to ERROR text. Keep unsupported fields explicit; defer nonessential parser work instead of growing the cycle.

## 1. Read and verify the starting state

Read in order:

1. `geeky-orchestration/AGENTS.md` and this guide.
2. [Preparation results and source snapshots](adapters/codex/evidence/20261023T1926Z-run2-preparation/README.md).
3. Relevant sections of [parent/child issues and resolutions](codex-c1-run1-retrospective.md) only if troubleshooting is needed.
4. [Run 1 score limitations](baselines/c1-csvledger/20261023T182024Z-5fa13924/scoring-status.json), then the runner and adapter README when executing.

Run from the repository root:

```powershell
Set-Location C:\Users\gerald.khoo\geekhoo-plugins
git status --short
git log -1 --oneline
git merge-base --is-ancestor bee7b14c3b17b00a6ce0b5643015226a1d7ef963 HEAD
if ($LASTEXITCODE -ne 0) { throw 'Unexpected plugin ancestry; stop.' }
$env:PYTHONUTF8 = '1'
```

Preparation was verified at HEAD `bee7b14`. Other sessions share this checkout. Before every edit repeat status/log; preserve existing tracked and untracked work. Do not stage, commit, push or clean up without authorization. Fixture/contestant commits in disposable repositories are allowed. The runner exports **committed HEAD excluding evals**; uncommitted canonical skill changes are not included. Record the actual plugin SHA and exact administration-harness snapshot separately.

Run 1 remains frozen: completed replacement `20261023T182024Z-5fa13924`, provisional 81.7, oracle 118/118 stable three times. Its initial stopped attempt is separate. Do not overwrite either run, score or manifest.

## 2. Keep the tested tools and model settings

| Component | Required setting |
|---|---|
| Administration session | `gpt-6.1-sol/high` |
| Contestant orchestrator | `gpt-6.1-sol/medium` |
| All contestant descendants, including nested/default workers | `gpt-6-luna/max` |
| CLI | Complete pinned 0.164.0 package; `C:\repos\.eval-tools\codex\0.164.0\bin\codex.exe` |
| Existing signed-in home | `C:\repos\.eval-tools\codex-home`; never inspect/copy auth contents |
| Python / pytest | `C:\repos\.eval-tools\agent-py\Scripts\python.exe` |
| Vetted MXC build source | `C:\repos\.eval-cfg-codex-20261023T162259Z-60b450bc\mxc-native-probe\bin` |

Use explicit main/worker parameters; the runner defaults alone do not select this matrix. Do not substitute models, rebuild the MXC host and loosen pins, change the canonical prompt, tune skills or expose eval/oracle content to the contestant. Keep private MXC state, scoped Git settings, the dedicated-home lock and all isolation checks.

## 3. Use the passing model-free checks

These checks were completed during preparation. Repeat when the harness, CLI, pinned build, profile or environment changes; do not repeat unchanged checks unnecessarily.

```powershell
$c1VettedBuild = 'C:\repos\.eval-cfg-codex-20261023T162259Z-60b450bc\mxc-native-probe\bin'
pwsh -NoProfile -File geeky-orchestration/evals/scripts/run-codex-baseline.ps1 `
  -Case c1-csvledger -Model gpt-6.1-sol -Reasoning medium `
  -WorkerModel gpt-6-luna -WorkerReasoning max `
  -MockAgent -MockScenario happy -MxcBuildSource $c1VettedBuild
```

Use the new folder printed as `prepared:`/`stored:` for the native check; do not guess a timestamp:

```powershell
$c1PreparedRun = '<absolute stored mock/preparation folder>'
pwsh -NoProfile -File geeky-orchestration/evals/adapters/codex/run-native-probe.ps1 `
  -RunFolder $c1PreparedRun -MxcBuildSource $c1VettedBuild
```

Acceptance: mock 7/7 groups, native 21/21 checks, pinned build verified, zero unexpected errors, external egress denied in the native fixture, exact main/child/grandchild/default model settings. Raw native logs may contain the owner-approved exact CLI0.164.0 user-skill-root denial. Install/catalogue counts must be zero; exec requires at least one exact-signature occurrence, all retained with independent denial/skill/parity proofs. No generic ERROR exemption applies.

Latest passing preparation:

- Mock folder: `C:\Users\gerald.khoo\geekhoo-plugins\geeky-orchestration\evals\baselines\c1-csvledger\20261023T192610Z-e3ec171a`.
- Native proof: that folder's `native-attempts\native-probe-a3cbfdc5`.
- Offline integration: **285 tests + 32 subtests passed**, no skips.
- All six Claude scores reproduce exactly, including raw dimensions: **77.2, 77.0, 86.7, 97.9, 93.8, 98.3**.

Mock oracle setup failures and incomplete lightweight mock scoring analysis are expected: the mock exercises infrastructure and does not implement C1. Use `mock-summary.json`, `native-summary.json`, raw stderr and build proof to assess the checks. Do not report a mock as a successful contestant run.

## 4. Launch exactly once, only after owner authorization

The command below is a later launch template, not an instruction to launch now. Immediately before use, verify the owner has authorized one paid run, the paths still exist, the evidence matches current source/profile pins, and no other process holds the dedicated-home lock.

```powershell
$c1NativeProof = 'C:\Users\gerald.khoo\geekhoo-plugins\geeky-orchestration\evals\baselines\c1-csvledger\20261023T192610Z-e3ec171a\native-attempts\native-probe-a3cbfdc5'
$c1VettedBuild = 'C:\repos\.eval-cfg-codex-20261023T162259Z-60b450bc\mxc-native-probe\bin'
pwsh -NoProfile -File geeky-orchestration/evals/scripts/run-codex-baseline.ps1 `
  -Case c1-csvledger -Model gpt-6.1-sol -Reasoning medium `
  -WorkerModel gpt-6-luna -WorkerReasoning max `
  -MxcBuildSource $c1VettedBuild -NativeProofFolder $c1NativeProof -Launch
```

Record the exact printed workspace/config/output paths. Let the contestant work independently; do not help solve the case. Monitor its stored progress, completion and diagnostics using bounded read-only checks. Preserve failures; do not automatically retry, resume, start a judge or launch a second paid probe. The existing 12M token ceiling remains informational for Codex calibration; do not silently change it.

## 5. Close out from evidence

1. Read `run.json` and raw diagnostics. Require completed execution, unchanged plugin export, complete main/descendant rollouts and the exact model matrix. Preserve `stream.jsonl`, `session.jsonl`, `subagents/`, stderr, Git bundle, oracle output and source hashes. Keep API latency/cost unknown if unavailable.
2. Distinguish exact approved root denials from recovered candidate tool failures. The audit may accept a patch failure only with one-to-one physical request/output/path/hash/ordinal/timestamp correlation. Keep original rejection records if readjudicating. Unmatched infrastructure errors or incomplete evidence prevent acceptance.
3. Verify oracle stability, each task's validation at its **own commit**, final claimed tests/help, and physical same-thread reviewer reports. New parsing accepts explicit plain bullets/fences and refuses empty Codex validation instead of treating 0/0 as success. Ownership requires unambiguous own task-body read plus notes/product writes.
4. Review active stage transitions. Bulk skill prereads are not stage starts. Supply `stage-evidence.json` only from exact main plaintext source records using the documented schema in `scripts/codex-trace.py`; SHA/ordinal/timestamp/text validation is mandatory. Do not copy run 1's artifact into run 2. Preserve the original derivation separately.
5. Write evidence-backed manual verdicts, then analyze/score the **new run folder** with the shared rubric. Commands write derived files; never point them at frozen run 1:

```powershell
$c1Run2Folder = '<absolute new completed run-2 folder>'
& C:\repos\.eval-tools\agent-py\Scripts\python.exe -B `
  geeky-orchestration/evals/scripts/analyze-run.py $c1Run2Folder --harness codex
& C:\repos\.eval-tools\agent-py\Scripts\python.exe -B `
  geeky-orchestration/evals/scripts/score-run.py $c1Run2Folder --harness codex `
  --manual (Join-Path $c1Run2Folder 'manual-verdicts.json')
```

Some native lane-helper/Done attribution, critical-finding recognition and reused-worker duration precision remain limited. Inspect failures before calling them contestant violations; qualify the score instead of inventing evidence or tuning verdicts. Run 2 remains calibration evidence until those limits are resolved. Keep different plugin/model configurations separate from Claude means.

Done means one authorized attempt preserved, a completed score or precise blocker, remaining limitations stated, and a concise result. Stop there. No repository commit/push, extra paid run or child-chat contact is included.
