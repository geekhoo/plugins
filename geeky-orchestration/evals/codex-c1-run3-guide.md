# C1 run 3: completed run and preparation record

Run3 completed as `20261023T230041Z-2c3b5489`. [Final report](baselines/c1-csvledger/20261023T230041Z-2c3b5489/report.md) records reviewed QACT99.6, oracle118/118 stable3, exact requested matrix and final110tests. Its single launch authorization was consumed. Do not reuse the historical launch template for another attempt.

## Historical preparation record

Prepared 2026-10-24, Asia/Singapore. Target: Windows, PowerShell 7.6.5. Workdir: `C:\Users\gerald.khoo\geekhoo-plugins`. **The C1 contestant is unstarted. No paid model calls, scorer/oracle runs, repository staging/commits or pushes.** Two model-free native fixtures used scripted loopback responses to verify the requested settings and real sandbox tooling.

Read this guide and the [readiness evidence](adapters/codex/evidence/20261023T223555Z-run3-readiness/README.md). Pinned plugin HEAD is `bee7b14c3b17b00a6ce0b5643015226a1d7ef963`, branch `main`. Verify it through Git before launch and preserve all shared dirty work. The runner exports committed HEAD excluding `evals`; the administration harness is separately fingerprinted in the evidence manifest.

| Assignment | Model | Effort |
|---|---|---|
| Main | gpt-6.1-sol | high |
| geeky-coder, ordinary/nested task workers, unspecified workers | gpt-6.1-sol | medium |
| Plan semantic, task/phase and final domain reviewers | gpt-6.1-sol | xhigh |
| Architect doing sequencing review | gpt-6.1-sol | xhigh |

The medium catch-all is configured in every role's nested defaults. `code-reviewer` has an xhigh role layer. A generated `code-architect-reviewer` alias retains the canonical architect body with xhigh; ordinary `code-architect` production stays medium. Generated per-run developer instructions route review assignments to those two roles. Canonical skill/agent bodies and the canonical prompt are unchanged.

## Verified preparation

- Full Codex 0.164.0 package: **45/45** archive members match installed files. Existing dedicated home `C:\repos\.eval-tools\codex-home` retained; auth contents never read.
- Python **3.13.15**, pytest **9.0.3**; evaluation and MCP environments passed `uv pip check` (**6** and **29** packages). These uv environments have no pip module; no installation was necessary. Required .NET 10 runtimes are present.
- Fresh static profile: **12/12**, with eight complete skills, seven registered roles and the MCP bootstrap. [Prepared record](baselines/c1-csvledger/20261023T224720Z-e569fde0/run.json).
- Fresh private MXC build copy: all **18** manifest entries match the pinned original; MXC source/binaries were not rebuilt or changed.
- Fresh native fixtures: **21/21 each**, zero paid model calls, external egress denied. Requests observed main high, `geeky-coder` and default worker medium, and each selected reviewer xhigh. Native proof measures configuration/tooling, not model capability.
- Combined launch-proof validation: **30/30**, retaining both reviewer proofs. Matching matrix labels, task-only proof or missing second reviewer proof cannot satisfy the new gate.
- Offline verification: **126 tests + 39 subtests** passed; after tightening reviewer coverage, the **106 affected native/audit tests** passed again. Shell scripts parse; the shell helper runs without starting a workload. The proof-coverage finding was independently re-reviewed and closed.

Preparation workspace: `C:\repos\eval-c1-csvledger-codex-20261023T224720Z-e569fde0`. Private home/config/temp/export: `C:\repos\.eval-cfg-codex-20261023T224720Z-e569fde0`. The workspace contains disposable native-fixture markers; a future paid launch creates a new workspace and output folder. The initial all-medium preparation is retained and superseded; its proof does not qualify for this matrix.

## Operator shell, without launch

```powershell
Set-Location C:\Users\gerald.khoo\geekhoo-plugins
. .\geeky-orchestration\evals\adapters\codex\evidence\20261023T223555Z-run3-readiness\prepare-shell.ps1
```

The helper sets process-only UTF-8 variables, PATH and `c1` operator variables, using exact PowerShell/Python/CLI/build/proof paths. It does not change machine/user profiles or authentication files. Reuse the matching proof; no reinstall, sign-in, MXC rebuild or repeated catalogue discovery is needed.

## Later launch template: requires a new direct owner instruction

**Do not execute under the preparation-only request.** First verify HEAD, current source fingerprints, paths and the free dedicated-home lock. If runtime/profile inputs drift, repeat the affected checks. Keep the requested matrix explicit.

```powershell
& $c1Pwsh -NoLogo -NoProfile -File geeky-orchestration/evals/scripts/run-codex-baseline.ps1 `
  -Case c1-csvledger -Model $c1Model -Reasoning $c1Reasoning `
  -WorkerModel $c1WorkerModel -WorkerReasoning $c1WorkerReasoning `
  -ReviewerReasoning $c1ReviewerReasoning `
  -ToolsDir $c1Tools -CodexHome $c1CodexHome -CodexExe $c1CodexExe `
  -MxcBuildSource $c1VettedBuild -NativeProofFolder $c1NativeProof `
  -ReviewerProofFolder $c1ReviewerProof -Launch
```

Primary proof: `C:\Users\gerald.khoo\geekhoo-plugins\geeky-orchestration\evals\baselines\c1-csvledger\20261023T224720Z-e569fde0\native-attempts\native-probe-0fd25848`. Architect reviewer proof: `C:\Users\gerald.khoo\geekhoo-plugins\geeky-orchestration\evals\baselines\c1-csvledger\20261023T224720Z-e569fde0\native-attempts\native-probe-275eb041`. The runner requires both for this reviewer matrix and revalidates retained hashes. Only the approved CLI 0.164.0 denied-root signature has recurrence accounting: install/catalogue zero, exec minimum one, with independent proofs; unknown errors fail closed. Preserve stopped attempts, with no automatic retry, judge or resume.

Case limits remain 5,400 seconds / 12M informational tokens; reference eligibility remains false pending calibration. Scoring source hashes still match the final-pair verification; no scorer code changed here. Actual paid-session automatic hook invocation remains unverified, the documented shell-write bypass remains, and live auth/provider access was not exercised. The fixtures cannot guarantee a future unseen trace shape.

Current records supersede older run-2 launch/model examples and the former records-only handoff. Historical guides/checkpoints and the initial preparation remain preserved. Updated plugin/adapter READMEs, kanban, handoff and references point here. All changes are unstaged and uncommitted.
