# Codex baseline adapter

Latest Windows C0 result, 2026-10-26: Codex completed at parity 97.46 with
oracle 13/13 stable over three repetitions and 93 public tests passed.
[The comparison](../../analyses/c0-claudex-001-win-20261026/README.md) includes
Claude's router-fixed timeout at parity 90.33. The owner explicitly waived
native qualification for those attempts. The fixture limits below still apply.

Windows host setup (2026-10-25): [current setup and qualification record](../../analyses/windows-mxc-setup-20261025/README.md).
The current MXC build passes the standard 21-check native fixture. LiteLLM's
classic-tool profile remains incompatible with that fixture; its failed attempt
is retained and does not establish paid Windows LiteLLM qualification.

Current (2026-10-25): Linux MXC launches through LiteLLM (`-Litellm -Model <name> -Launch`) are documented in [the MXC + LiteLLM runbook](../../mxc-litellm-runbook.md); cross-harness scoring uses `scripts/parity-eval.py` (D103). The "no further paid run" notes below belong to the C1 closeout.

Historical C1 run 3 result (2026-10-24): [completed report](../../baselines/c1-csvledger/20261023T230041Z-2c3b5489/report.md), [operator evidence](evidence/20261023T230039Z-run3-operator/README.md). Runner 0, 1410s,oracle 118/118 stable over 3 repetitions,final 110 tests; reviewed QACT 99.5628555, complete/no unresolved judgments. Actual16 threads/19 contexts verify main Sol/high, task/default Sol/medium and reviewers Sol/xhigh. Automatic process extraction is unsupported for this general-orchestrator shape; reviewed annotations and dp12 correction are disclosed. Historical preparation below is superseded. At that checkpoint, no further paid run, repository commit, or push was authorized.

Current final-pair closeout: [automatic normalization and guard evidence](../../analyses/c1-final-parity-20261024/README.md). Run 2 process extraction and strict failure contract are Done for supported shapes; 68 parser tests and 64 guard/profile/trust tests pass (2 optional parser fixture skips). No guard code change; shared shell bypass and unverified paid invocation remain explicit. No new run, commit or push authorized.

Current scoring result: [consistent four-run saved-trace rescore](../../analyses/c1-consistent-rescore-20261024/README.md). Source-bound process attribution, exact task-commit validation replay and a strict completeness gate repair the historical parser-limited Codex scores. New composites are Codex 1=96.3, Codex 2=98.0; selected Claude scores remain 98.3/97.9. Original artifacts are unchanged; no paid run was started.

Start with [checkpoint 5 closeout](../../codex-c1-checkpoint5.md), then the [four-run derivation](../../analyses/c1-consistent-rescore-20261024/README.md) and [frozen six-Claude verification](../../analyses/c1-checkpoint5-20261024/README.md). Both Codex runs completed; run 2 used Sol/medium throughout. Historical preparation/launch sections below remain provenance. Full paid-runtime hook parity is unverified; static/native proof is not retroactive contestant proof.

`../../scripts/run-codex-baseline.ps1` prepares a sibling to the Claude runner.
It exports committed plugin HEAD without `evals/`, seeds a case workspace, and
calls `prepare-profile.py` to generate a run profile and a parity report. The
canonical prompt receives only the existing planning-folder substitution.

The runner defaults to preparation only. For a later authorized preparation:

```powershell
pwsh -NoProfile -File geeky-orchestration/evals/scripts/run-codex-baseline.ps1 -Case c1-csvledger
```

The default executable is pinned to
`C:\repos\.eval-tools\codex\0.164.0\bin\codex.exe` (complete official Windows
release, SHA-256 `6f267830b029ee25d9339864aa867cd45de9f8fd4c5ea007d2e63c13a0c66d36`).
The complete package SHA-256 is `700116be3143576d006467af8576f7f4c9dada1feddfdb7f69743bfde0997018`;
its Code Mode host and resource/path directories are required. A flat main executable
alone was insufficient for native tool execution.
Override with `-CodexExe` when deliberately changing the contestant version.
The desktop app's bundled executable is a separate installation. The original CP1-3 profile used `gpt-6.1-sol/high` for all threads. Checkpoint4
uses independent `-Model`/`-Reasoning` and `-WorkerModel`/`-WorkerReasoning`; the
paid attempt used main `gpt-6.1-sol/medium` and all descendants `gpt-6-luna/max`.
`--no-daemon` keeps the eval independent of the desktop app's shared server.

Preparation creates resources; it does not launch MXC or call a model. A failed
preflight preserves `parity-preflight.json` when available and stops. Static
configuration parity is distinct from runtime evidence: checkpoint 2 must test
discovery, the hook, MCP, Python/pytest, PowerShell and Git inside MXC before a
paid baseline is authorized.

Model-free checks (disposable fixture Git commits only):

```powershell
pwsh -NoProfile -File geeky-orchestration/evals/scripts/run-codex-baseline.ps1 -Case c1-csvledger -MockAgent
pwsh -NoProfile -File geeky-orchestration/evals/adapters/codex/run-native-probe.ps1 -RunFolder '<stored mock/preparation folder>'
```

The mock performs real file/grant, skill/role readability, guard, pwsh, pytest,
scratch Git and MCP initialize/list/call checks. Native discovery is a separate
test: the real Codex CLI uses a loopback-only scripted Responses provider inside
MXC with external egress denied. No provider performs inference. It exercises
real patches, guard context, shell, MCP and subagent dispatch. Native attempts
are stored separately, so failed attempts cannot display stale success reports.

The owner signs in separately to the dedicated
`C:\repos\.eval-tools\codex-home`. The adapter never reads, copies or prints its
auth file. Codex uses that home for auth and session persistence with
`--ignore-user-config --ignore-rules`; the generated run `HOME` and `USERPROFILE`
contain only the exported skills, agent projections and adapter configuration.
The preflight rejects discovery contamination in the dedicated Codex home.
Its generated `.system` skills and plugin caches are permitted but explicitly
disabled through `skills.bundled.enabled=false` and `plugins._default.enabled=false`.
The ignored `config.toml` is left untouched; unrelated skills, agents, hooks,
memory and instruction files still fail the preflight.
Generated config overrides register the agents, MCP server and guard bridge.
On Windows, native Known Folder skill discovery ignores HOME/USERPROFILE. The
adapter therefore creates a run-home local marketplace with a complete pinned
export plus a minimal Codex manifest. Model-free `codex plugin add` materializes
that export in the dedicated Codex cache; only that plugin is enabled. Its
manifest suppresses automatic MCP/hook loading so the explicit bootstrap and
warn bridge are authoritative. The source plugin files remain unchanged.

Native `hooks/list` supplies the exact declaration key/hash. The invocation
sets `hooks.state` for that vetted declaration; it does not bypass hook trust.
`trusted-exec.py` applies the same installation and trust steps to a later
authorized run, preserving the canonical prompt. The initial paid attempt stopped; a separately authorized replacement completed. See the current status below.

`profile/config.toml` supplies static defaults. `profile/mcp-bootstrap.py` uses
the MCP venv's base Python with `site.addsitedir`, avoiding its inaccessible
launcher inside MXC. Runtime paths and registrations are generated by the helper.
The exported plugin's shipped skills, agents and guard sources are untouched.

The later `-Launch` switch runs `codex exec --json --sandbox danger-full-access`
inside MXC with Win32k, loopback, no recursive drive-root enumeration, scoped Git identity/trust, writable temporary
storage and agent-py first on PATH. It serializes this runner's use of the shared
dedicated auth/session store with a file lock. It stores `stream.jsonl`, the
matching rollout as `session.jsonl`, `stderr.txt`, oracle results,
`solution.bundle` and `run.json` in the existing case baseline layout. Resources
are preserved for inspection and never automatically deleted.
Each runner uses its own MXC build/cache state rather than rebuilding another
session's host. `--no-enumerate-root` is opt-in; the Claude path's default is unchanged.

The runner calls the shared analyzer with explicit Codex routing after capturing
the main rollout and its proven descendants. Reference eligibility remains false,
and the existing token ceiling is informational until Codex calibration. Later
launch authorization and checkpoint 2 evidence are procedural requirements;
the presence of `-Launch` does not grant them.

See [kanban](kanban.md), [handoff](handoff.md), and [references](references.md).

Checkpoint 3 commands (saved evidence only; no contestant or judge model calls):

```powershell
& C:\repos\.eval-tools\agent-py\Scripts\python.exe geeky-orchestration/evals/scripts/analyze-run.py '<run-folder>' --harness codex
& C:\repos\.eval-tools\agent-py\Scripts\python.exe geeky-orchestration/evals/scripts/score-run.py '<run-folder>' --harness codex --manual '<reviewed-manual-verdicts.json>'
& C:\repos\.eval-tools\agent-py\Scripts\python.exe geeky-orchestration/evals/adapters/codex/verify-claude-regression.py
```

Codex events are normalized into the existing scorer's tool, gate, review and
task evidence interface; the QACT weights, checks and caps are shared. Native
command execution, file changes, MCP and delegation messages use rollout
timestamps. Successful explicit SKILL.md reads identify stage entry, not workflow
completion. Child histories inherited from parents are excluded. Final cumulative
token counters are counted once per thread; cached input and reasoning output
remain subsets. Missing or malformed traces, missing workers and failed evidence
produce incomplete analysis and the scorer refuses them. Unknown API latency
and cost remain null; the existing task-time formula uses raw duration when
latency is unavailable. No price or latency is invented.

`capture-rollouts.py` copies the selected main thread and recursive descendants
identified by session metadata. The analyzer reads only these run-local files,
never the signed-in home. `--analysis-only` leaves run.json untouched. Scoring
still lists judgement checks as needs_judge until reviewed manual verdicts exist.
The regression verifier uses scratch copies and cloned committed Git bundles;
original baseline files are hashed before/after and never rescored in place.
Four historical bundles omit an untracked `.heartbeat` used by the recorded
scores. The verifier copies the actual retained file for runs 2, 4, 5 and 6,
checks that the original workspace HEAD matches the bundle, and records the
file's source and SHA-256 before/after. Those supplementary runtime files are
required for exact reproduction; their status or timestamp is never invented.
The lightweight CP2 mock does not supply a complete scoring trace. It remains
infrastructure evidence; native captured rollouts exercise the scoring path.

Final checkpoint 3 proof: **139 tests plus 10 subtests passed**. The frozen-source
six-run regression exits 0, reproducing all raw Q/A/C/T and composite dimensions
to tolerance 1e-9: **77.2, 77.0, 86.7, 97.9, 93.8, 98.3**. Original fixtures and
supplementary files are unchanged. See [checkpoint 3 evidence](evidence/20261023T1722Z-checkpoint3/README.md).
At checkpoint3 no paid run, staging, repository commit or push had occurred.
Checkpoint4 current status is recorded below.
Older Codex workspace-write and no-hooks examples in `baseline-runs.md` and the
decision record are historical; this adapter follows the kickoff's MXC-contained
danger-full-access recipe. Updating the full procedure is checkpoint 5 work.

Checkpoint 1 verification on 2026-10-23: 14 offline tests plus 10 subtests passed,
syntax checks passed, and the preparation-only integration produced a passing
static report in run `20261023T154525Z-2f68b6f5`. No MXC workload ran.

Checkpoint 2 status (2026-10-24 Singapore): mock checks pass, and native functional
checks pass with all eight exact skill catalogue paths, complete skill read,
MCP gate result, warn context and one child request proven. The owner explicitly
approved only the following denied-root diagnostic:
native Codex logs `failed to walk skills root file:///C:/Users/gerald.khoo/.agents/skills:
Access is denied. (os error 5)`. Raw logs are retained. Native source always adds
that Known Folder root and logs inaccessible roots as errors. Disabling skills
is applied after discovery; the installed MXC SDK has no path-redirection API.
No log suppression, user-directory change or weaker read grant is applied.
The classifier retains every raw line and requires version 0.164.0, all native
functional checks, independent PermissionError/winerror 5 proof for that root,
and successful native skill invocation. Checkpoint 2 used exact required per-process counts
are plugin-install 0, hook-catalogue 0, exec 1. Missing/new process roles, different
paths/codes, extra/missing matches, stream errors and other ERROR/FATAL/Traceback
lines fail. The wrapper also verifies the MXC source and binary fingerprints in
`profile/mxc-pin.json`; drift requires revalidation. This exception does not
authorize paid runs or checkpoint 3.

Passing native evidence: `20261023T162259Z-60b450bc/native-attempts/native-probe-8b83bc99`.
All 13 checks passed, with zero unexpected errors and zero stream error events;
the one approved exec diagnostic remains in the raw log. Latest Codex mock:
`20261023T163202Z-2a0a12c1`, all seven check groups passed, zero model calls.

Final validation after fixing bounded hook-catalogue stderr draining:
native attempt `native-probe-ead06d6b` passes all 13 checks. The full offline
suite passes 77 tests plus 10 subtests. Claude regression dry-run passes 69
checks; runner mock `20261023T164824Z` passes 22 checks with a matching transcript.
Both Claude wrappers now locate transcripts under `MXC_SANDBOX_HOME` when set,
preserving the existing default otherwise. Neither analyzer nor scorer changed.
See [final checkpoint evidence](evidence/20261023T1651Z-checkpoint2/README.md).

## Historical checkpoint 4 outcome (superseded by checkpoint 5)

The separately authorized replacement [20261023T182024Z-5fa13924](../../baselines/c1-csvledger/20261023T182024Z-5fa13924/notes.md) completed in 1, 349 seconds with zero interventions and seven contestant commits. Oracle 118/118 passed in all three checks. Independent bundle-clone validation passed T1's 23 tests at a8a5f34, T2's 72 tests and help at 20ed68b, and the final 76 tests and help at d05528f. All 14 own-history thread contexts verify main gpt-6.1-sol/medium and all 13 descendants gpt-6-luna/max. Usage: 17, 729, 214 tokens (cached input is a subset); API latency and cost remain null. Reference eligibility remains false pending Codex calibration.

The initial attempt [20261023T175251Z-2941f32c](../../baselines/c1-csvledger/20261023T175251Z-2941f32c/score.md) remains separately preserved and unscorable. It stopped after 82 seconds because two denied-root recurrences exceeded the then-approved exact-one count. Human authorization then approved one replacement and exact-signature recurrence accounting: install/catalogue remain exact zero; exec requires at least one; every raw recurrence and all independent version/root/skill/parity proofs remain required. Six model-free fork comparisons all had one recurrence, so forkall causation is unverified. No paid authorization remains.

Replacement native preflight passed 21/21 checks with the original pinned complete MXC build copied into fresh private state. Post-run diagnostic review retains two approved denied-root recurrences and two separately classified candidate_tool_failure records. Each rejected apply_patch has an exact same-thread request/response, source ordinal/hash, workspace path and 0-100ms timestamp correlation. Unmatched errors fail closed. automatic-run.json and automatic-diagnostic-report.json preserve the original conservative diagnostic rejection; raw captures are byte-identical. No generic router-error exception or isolation change was made.

The raw prefetch-based analysis is preserved as analysis-prefetch-original.json and prefetch-original/. Its stage attribution is invalid because early bulk reads were mistaken for active stages. Any reviewed stage attribution must cite immutable plaintext main-session commencement records. Product/test/reviewer claims have independent evidence; the shared parser's code-span-only validation extraction misses this contestant's plain-bullet commands, so independent-validation.json records exact-command, own-commit reruns. Read run-local scoring-status.json and score.md for the accepted derivation and limitations.

See [checkpoint4 evidence](evidence/20261023T1738Z-checkpoint4/README.md), [handoff](handoff.md), [kanban](kanban.md) and [references](references.md). Adapter records supersede their stale stopped-only wording. Historical kickoff, baseline-runs, lessons-learned and full decision records remain stale and deferred to checkpoint5. Canonical skills, agents and prompt are unchanged. No repository staging, commit, push or cleanup occurred.

Final closeout: provisional shared QACT **81.7** (Q95.9/A81.5/C78.2/T40.0), no needs_judge; reviewed stages applied. See run-local scoring-status.json and learnings.md for parser limits. No further execution planned.
