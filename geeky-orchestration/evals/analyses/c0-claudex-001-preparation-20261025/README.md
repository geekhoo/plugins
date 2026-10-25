# C0 / claudex-001 preparation. 2026-10-25

Both Windows MXC harness configurations are prepared for LiteLLM alias
`claudex-001`. No contestant, mock, oracle or judge ran in the preparation step.
The owner subsequently waived qualification and authorized one Codex run, now
[completed and scored](../c0-claudex-001-win-20261026/codex/report.md). Claude has
since completed a router-fixed, same-folder retry that timed out during final
review, at parity 90.33. See [the current comparison](../c0-claudex-001-win-20261026/README.md)
and [Claude retry report](../c0-claudex-001-win-20261026/claude-code/router-fixed/report.md).
The original qualification hold below is historical and superseded.

Base Git revision: `c83d4b941341b4094b6e7d2f4ac125e5c1b74154`.
Existing Windows setup and telemetry identity changes remain uncommitted.

## Prepared environment

The machine-local files are under `C:\repos\.eval-tools\c0-claudex-001`:

- `environment.ps1` loads the existing private environment file and selects
  LiteLLM `claudex-001` for Claude aliases/subagents and generic API defaults.
  Credentials are assigned from environment variables and are not stored here.
- `readiness.json` contains the exact prepared paths, checks, named-file hashes
  and the unresolved Codex launch blocker.
- `Invoke-C0.ps1` displays status by default. It cannot start an evaluation
  without an explicit `-Launch`; the owner-authorized qualification override is recorded.
- `codex-preparation/` retains the generated static run/profile record outside
  the real baseline-results directory.

Loading the environment or inspecting readiness does not start either harness:

```powershell
. C:\repos\.eval-tools\c0-claudex-001\environment.ps1
& C:\repos\.eval-tools\c0-claudex-001\Invoke-C0.ps1
```

No launch command was executed or authorized in this preparation task.

## Checked configuration

| Concern | Claude Code | Codex |
|---|---|---|
| Case | `c0-wordstat` | `c0-wordstat` |
| Model | `claudex-001` | `claudex-001` |
| Child/default models | Opus/Sonnet/Haiku aliases and `CLAUDE_CODE_SUBAGENT_MODEL` pinned | All seven registered roles and worker/default model pinned |
| Provider wire | Anthropic Messages | OpenAI Responses |
| Authentication | `ANTHROPIC_API_KEY` from LiteLLM; bearer/OAuth cleared | `model_providers.litellm`, `env_key=LITELLM_PROXY_API_KEY`, no OpenAI auth required |
| Reasoning | Runner default | `high` for main and workers; no separate reviewer override |
| Wall ceiling | 5400 seconds | 5400 seconds |
| Langfuse | `mxc-win`, `claude-mxc-win` family | `mxc-win`, `codex-mxc-win` family |
| Preparation | `-PrepareOnly`, no oracle or MXC workload | No `-Launch` or `-MockAgent`, static profile passes |
| State at preparation | Prepared; not run | Prepared; not run |

The model alias is present in authenticated LiteLLM `/models`. Read-only
`/model/info` identifies its configured upstream as
`auto_router/complexity_router`. Same alias does not guarantee the same backend
for differently shaped harness requests. No Messages or Responses inference was
used to test the route. Claude/default and Codex/high are also distinct reasoning
configurations; no equal-effort claim is made.

MXC reports supported Windows ProcessContainer/BaseContainer. Current source,
EXE and DLL match the stored Windows build pin. Confirmed tools: PowerShell
7.6.8, Claude Code 2.1.304, Codex 0.164.0 with Code Mode host, Node 24.22.1,
Python 3.13.15 / pytest 9.0.3, MCP 2.3.0 and Langfuse SDK 4.18.0.
Both Langfuse credential sets authenticated with read-only CLI requests;
no telemetry fixture or new trace was exported during this preparation.

## Former qualification hold. waived by owner

The LiteLLM catalog deliberately uses classic JSON functions. The current
Windows native fixture scripts Code Mode `apply_patch` and `functions.exec`,
which this profile does not expose. The previous failed LiteLLM qualification
is preserved in the Windows setup record. The standard passing proof uses
`gpt-6.1-sol/high`; it cannot satisfy the exact `claudex-001` model-matrix gate.

The owner explicitly instructed: ignore qualification; this model already works
on both Claude and Codex in MXC. The runner now supports the explicit
`-SkipNativeQualification -QualificationOverrideReason <reason>` path, recording
the waiver without claiming new proof. Default proof requirements remain for
non-overridden launches. The preparation did not run a native fixture, and the
subsequent authorized Codex run succeeded without one.

## Preparation records and source changes

Claude's new `-PrepareOnly` path creates the seed workspace, committed plugin
export, MCP/settings/telemetry config and `prepared-launch.json`, then returns
before oracle or MXC execution. Its export manifest is name-bound and has a
verified SHA-256. The older `-DryRun` still runs the seed oracle and was not used.
Local seed commits are workspace initialization, not repository commits.

Codex's existing preparation path creates its isolated catalog, role layers,
profile and `run.json` with `exit_reason=prepared` and no start time. At preparation, both
workspaces had only the seed commit and no contestant stream.

See [readiness.json](readiness.json), [kanban.md](kanban.md),
[handoff.md](handoff.md), and [references.md](references.md). Named-file hashes
cover the listed files only; credentials are loaded at use time. Nothing was
committed or pushed.
