---
name: mxc-setup
description: This skill should be used when the user asks to "set up MXC", "enable the MXC sandbox", "check if this machine can run claude in MXC", "probe MXC", "build the mxc-sandbox host", "rebuild the MXC host", or wants to know whether Microsoft MXC containment (ProcessContainer / BaseContainer / IsolationSession) works on this Windows host before running Claude Code inside it. Not for Docker, devcontainers, or Claude Code's built-in /sandbox.
argument-hint: "[--workspace <dir>] [--isolated] [--allow-win32k]"
allowed-tools: PowerShell, Read, Edit
---

# MXC sandbox setup and host probe

Prepare a Windows host to run the Claude Code CLI inside a Microsoft MXC sandbox and report exactly
what the sandbox will grant. Setup is a build of the bundled .NET host plus a probe; there is no
installer and no admin step on a BaseContainer-capable host.

## Resolve the wrapper

```powershell
# <base> = the "Base directory for this skill" path shown when this skill loads
$mxc = (Resolve-Path (Join-Path '<base>' '..\..\scripts\mxc.ps1')).Path
# Fallback when no base path is shown:
# $mxc = (Get-ChildItem "$env:USERPROFILE\.claude\plugins" -Recurse -Filter mxc.ps1 |
#     Where-Object FullName -match 'mxc-sandbox\\.*scripts\\mxc\.ps1$' |
#     Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
```

The wrapper copies the host source to `%USERPROFILE%\.mxc-sandbox\src`, builds it into
`%USERPROFILE%\.mxc-sandbox\bin` whenever the source hash changes (including on first use), then
forwards all arguments. It never writes into the plugin directory. To force a build, pass
`-Rebuild` as the **first** argument: `& $mxc -Rebuild probe`.

## Procedure

1. **Check prerequisites** (stop and report if any fail):
   - Windows 11 x64/ARM64.
   - .NET SDK matching the host's target (`net10.0`): `dotnet --list-sdks`. The wrapper checks this
     and names the project file to edit when only SDK 8/9 is present. Such an edit lives in the
     plugin directory and is lost on plugin update.
   - Claude CLI at `%USERPROFILE%\.local\bin\claude.exe` (native install), or `$env:MXC_CLAUDE_EXE`
     set to its path.
2. **Probe** with the options the user intends to run with and an explicit workspace. Without
   `--workspace`, the current directory is granted read-write, which skews the report.

   ```powershell
   & $mxc probe --workspace C:\repos\<project>
   & $mxc probe --workspace C:\repos\<project> --allow-win32k
   & $mxc probe --workspace C:\repos\<project> --isolated
   ```

3. **Interpret the probe** with the table below. Report the tier, the containment class, every
   `grant read-only` / `grant read-write` line, the pinned env, the config mode, and the Win32k state.

| Probe line | Good value | Action if not |
|---|---|---|
| `platform supported` | `True` | Stop; MXC cannot run here |
| `processContainer tier` | `BaseContainer` | An `AppContainer` tier needs `wxc-host-prep prepare-system-drive` once and `prepare-null-device` after every boot, both elevated. The user must run them; do not elevate on their behalf |
| `isolationSession` | `True` | `tui` mode is unavailable; headless `run` still works |
| `enumeratePaths` | `True` | Without it, `--allow-win32k` cannot fix node's `EPERM lstat 'C:\'` |
| `containment` | `Process`, or `ProcessContainer` with `--allow-win32k` | `ProcessContainer` appears only when `--allow-win32k` is set and `enumeratePaths` is `True` |
| `claude exe ... exists` | `True` | Install the native CLI or set `MXC_CLAUDE_EXE` |
| `env token passthrough` | any | Matters only for `--isolated` and `tui` |

4. **Smoke test** a real prompt. Shared config uses the existing login:

   ```powershell
   & $mxc run --workspace C:\repos\<project> --timeout 180 -- -p "Reply with exactly: PONG"
   ```

   Expect `PONG` and exit 0. An `[mcp-sdk] SEP-2352` warning line is harmless.

## Modes at a glance

| Mode | Backend | Use for |
|---|---|---|
| `probe` | n/a | Capability and grant report for a `run` with the same options |
| `run` | ProcessContainer | Headless `claude -p` / subcommands with filesystem and network policy (`mxc-run`) |
| `tui` | IsolationSession | Interactive claude as a separate local account, no fs/net policy (`mxc-interactive`) |

## State locations

| Path | Purpose |
|---|---|
| `%USERPROFILE%\.mxc-sandbox\bin` | Built host |
| `%USERPROFILE%\.mxc-sandbox\home` | `--isolated` config dir |
| `%USERPROFILE%\.mxc-sandbox\cache\{npm,uv}`, `\tmp` | Sandbox-private caches and temp |
| `%ProgramData%\mxc-sandbox\bin\claude.exe` | CLI copy staged for `tui` (machine-wide) |

`MXC_SANDBOX_HOME` overrides the root. Never point it under `%LOCALAPPDATA%`: the container
redirects that tree, so read-write grants there cannot be written.

## Additional resources

- **`mxc-troubleshooting`** skill: verified failure signatures and fixes.
- **`mxc-run`** skill: headless runs with the right options.
