# Windows MXC setup. 2026-10-25

This dated record covers host setup. Later paid C0 attempts are documented in the
[current comparison](../c0-claudex-001-win-20261026/README.md). The owner's
[publication instruction](../c0-claudex-001-win-20261026/alignment-report-2026-10-26.md)
supersedes the original no-commit checkpoint. No further paid run is authorized here.

Windows toolchain setup and C0 model-free validation are complete on Gerald's
machine. Paid evaluations were not run. Base revision: `c83d4b941341b4094b6e7d2f4ac125e5c1b74154`;
the Windows fixes and records in this folder are uncommitted changes.

## Use on this machine

Open PowerShell 7 and run the free C0 preflight:

```powershell
& C:\repos\.eval-tools\windows-eval.ps1 -Preflight
```

To load the environment into an evaluation shell without starting anything:

```powershell
. C:\repos\.eval-tools\windows-eval.ps1
Set-Location C:\Users\gerald.khoo\geekhoo-plugins\geeky-orchestration
```

The installed launcher is reproduced in [windows-eval.ps1](windows-eval.ps1).
It reads `C:\Users\gerald.khoo\env.cloud.claude` as assignments, without executing
the file or printing values. Credentials are loaded into the current process
only; no credential values are copied into this repository. It clears
`ANTHROPIC_AUTH_TOKEN`, the OAuth token, and host Codex tag/user overrides, and
originally set the runner's Langfuse environment to `mxc`. Current runners select
`mxc-win`; see the [identity contract](../../telemetry/README.md#agent-and-run-identities).
Use a dedicated evaluation shell.

The launcher supports `-Harness codex` or `-Harness claude-code` and `-Case`
selection. It retains disposable workspaces and stores preflight evidence under
`C:\repos\.eval-tools\windows-setup`. It does not launch a paid evaluation.

## Installed and verified

| Component | Location / version |
|---|---|
| Windows backend | ProcessContainer / BaseContainer, Windows build 26300 |
| PowerShell | `C:\Program Files\PowerShell\7\pwsh.exe`, 7.6.8 |
| .NET SDK used | 10.0.402 |
| Node | `C:\Program Files\nodejs\node.exe`, 24.22.1 |
| Claude Code | `C:\Users\gerald.khoo\.local\bin\claude.exe`, 2.1.304 |
| Codex | `C:\repos\.eval-tools\codex\0.164.0\bin\codex.exe`, 0.164.0; Code Mode host present |
| Agent Python | `C:\repos\.eval-tools\agent-py`, Python 3.13.15 / pytest 9.0.3 |
| MCP Python | `C:\repos\.eval-tools\geeky-mcp`, Python 3.13.15 / mcp 2.3.0 |
| Telemetry Python | `C:\repos\.eval-tools\langfuse-py`, langfuse 4.18.0 |
| Telemetry hooks | Installed from `telemetry/pins.json`, downloads SHA-256 verified |
| Current MXC build | `C:\repos\.eval-tools\windows-mxc\bin` |

LiteLLM authenticated successfully for the read-only `/models` request. No model
inference was requested. C0 checks exercised real sandbox processes and Langfuse
uploads tagged `mock`; any mock transcript token/cost figures are synthetic.

## Validation and fixes

- Claude C0: 73 checks passed, zero failed; 196 Langfuse observations and complete
  coverage. Source: `preflight-20261025T135531Z/claude-code-c0-wordstat` under the
  local evidence root. This initial matrix's Codex row failed and is preserved.
- Codex C0 after fixes: nine checks passed, zero failed; 10 Langfuse observations.
  Source: `preflight-20261025T140919Z/codex-c0-wordstat`. Mock coverage is not a
  full real contestant lifecycle proof.
- Standard native Codex fixture: 21/21 checks, zero unexpected diagnostics, zero
  paid model calls. See [native-default/native-summary.json](native-default/native-summary.json).
  The denied user-skills root remains denied; root enumeration was not enabled.
- Final regression suite: [85 tests passed](regression-tests.log) across mock,
  tracer wrapper, profile, build-copy and paid diagnostic audit tests.

Three Windows issues were reproduced and corrected:

1. Python version discovery skips inaccessible PATH directories instead of
   failing on the host's PowerToys directory.
2. The mock invokes the generated Windows Stop-hook command directly, avoiding
   an ungranted `cmd.exe` process. POSIX retains shell execution.
3. The Windows Node wrapper uses `--preserve-symlinks-main --preserve-symlinks`
   so its entry-point resolution does not enumerate `C:\`. The pinned tracer
   bundle and sandbox grants are unchanged.

The canonical MXC build pin now identifies the current host source and the
retained Windows build that passed native qualification. Historical pins and
results remain available through Git history.

## Qualification boundary

The passing native fixture uses standard Codex tools, `gpt-6.1-sol/high` for the
main thread and workers, and no separate reviewer-effort override. It qualifies
that exact configuration and build. It does not qualify arbitrary model matrices.

The separate `zen/gpt-6.1-sol` LiteLLM native attempt failed: the existing fixture
issues Code Mode `apply_patch` and `functions.exec` calls, but the LiteLLM profile
deliberately exposes classic JSON tools. Its native patch, guard and MCP checks
therefore cannot pass. See [native-litellm-attempt/native-summary.json](native-litellm-attempt/native-summary.json).
Do not use the standard proof to claim LiteLLM native parity or bypass the paid
runner's `-MxcBuildSource` / `-NativeProofFolder` checks. Full Windows LiteLLM paid
qualification needs a compatible native fixture and model-matched evidence.

The Linux-only `install-agent-pythons.ps1` was not run. The actual Windows Python,
pytest and MCP paths were checked through MXC instead. C1–C3 and paid execution
were not validated by this setup. Nothing was committed or pushed.

See [kanban.md](kanban.md), [handoff.md](handoff.md),
[references.md](references.md), and [setup-validation.json](setup-validation.json).
