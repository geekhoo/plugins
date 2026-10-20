---
name: mxc-troubleshooting
description: This skill should be used when a Microsoft MXC sandbox run fails, an MCP server shows "Failed to connect" inside MXC, or the user asks to "debug the MXC sandbox" or "write a custom MXC request with Microsoft.Mxc.Sdk". Signature errors include 0xC0000142 / -1073741502, "EPERM lstat 'C:\\'", hook exit 66, "path could not be vetted", and "Not logged in" inside MXC.
allowed-tools: PowerShell, Read, Grep, Write
---

# MXC sandbox troubleshooting and policy reference

Diagnose failures of Claude Code (or any workload) running under Microsoft MXC on Windows, using
failure signatures verified on a Windows 11 26H2 BaseContainer host. Fix the cause; do not retry
blindly.

## Triage order

1. Resolve the wrapper and re-run `probe` with the same options and an explicit `--workspace`.
   Confirm the tier, containment class, and every grant line before theorising.

   ```powershell
   # <base> = the "Base directory for this skill" path shown when this skill loads
   $mxc = (Resolve-Path (Join-Path '<base>' '..\..\scripts\mxc.ps1')).Path
   & $mxc probe --workspace C:\repos\<project> <same options as the failing run>
   ```

   If no base path is shown, use the fallback lookup in `mxc-setup`.
2. Match the exact error text against the table below.
3. To separate policy problems from tool problems, reproduce with `cmd.exe` as the workload
   (`$env:MXC_CLAUDE_EXE = 'C:\Windows\System32\cmd.exe'`). The same grants apply, except the
   read-only grant for the executable's folder moves to the replacement executable's folder.
4. Change one option at a time and re-probe. Host options must be spelled exactly; the first
   unrecognised argument starts claude's arguments.

## Signature table

| Symptom | Cause | Fix |
|---|---|---|
| Exit `-1073741502` / `0xC0000142` from node, npx, uv, pwsh | Default `UiPolicy.Disable=true` blocks Win32k syscalls; `user32.dll` cannot initialise. python and claude do not load it | `--allow-win32k` (opt-in, weakens isolation) |
| node: `EPERM: operation not permitted, lstat 'C:\'` | realpath stats the drive root, which is not granted | `--allow-win32k` also adds enumerate-only access to `C:\` (needs `enumeratePaths: True` in probe). Never `--ro C:\` |
| Every hook `exit=66`; stderr `bash.exe: *** fatal error - NtCreateDirectoryObject(\BaseNamedObjects\msys-...): 0xC0000022` | Claude Code runs all hooks through Git Bash; msys cannot create named objects in the container | Hard limit. Disable hooks with `--settings <file {"disableAllHooks": true}>`; test hook scripts directly (see `mxc-run` recipes) |
| `uv run ...` MCP server `CONNECTION_CLOSED`; `Failed to update Windows PE resources ... \AC\Temp\...uv-trampoline-*.exe: Access is denied` | uv builds a trampoline in the AppContainer temp dir (Windows returns the package temp path, ignoring TEMP/TMP) | Hard limit for `uv run` servers. Pre-built Python venv entry points, or node-based servers, work instead |
| Writes denied in a folder under `%LOCALAPPDATA%` despite a read-write grant | The container redirects `%LOCALAPPDATA%` | Keep writable state elsewhere (default `%USERPROFILE%\.mxc-sandbox`) |
| uv: `Failed to persist temporary file ... Access is denied` in a shared host cache | Container cannot replace files the host wrote | Host pins private caches (`npm_config_cache`, `UV_CACHE_DIR` under `.mxc-sandbox\cache`) |
| claude: `Settings file could not be read: Refusing to read a file whose path could not be vetted` | Workspace path is deep (e.g. `%TEMP%` 8.3 path); upward traversal blocked | Use a shallow workspace such as `C:\repos\<name>` |
| `~/.claude.json` unreadable in the sandbox | BaseContainer denies single-file grants; claude also saves it via a temp file in the profile root | Shared mode sets `CLAUDE_CONFIG_DIR=~/.claude` and mirrors `~/.claude.json` one-way into it |
| `Not logged in · Please run /login` | `--isolated` (or `tui`) without a host token | User sets `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`) or `ANTHROPIC_API_KEY`; or drop `--isolated` |
| `tui` prints only `Access is denied.` | IsolationSession agent account cannot read the host profile (CLI or workspace) | CLI is auto-staged to `%ProgramData%\mxc-sandbox\bin`; move the workspace out of `C:\Users\<user>` |
| `[mcp-sdk] SEP-2352: stored OAuth credential has no 'issuer' stamp` | Harmless MCP SDK warning | Filter it from output |
| `MXC error [...]` before launch | Request rejected by validation (unsupported combination) | Read the message; check `references/sdk-and-policy.md` for backend support |
| Probe tier `AppContainer` (not BaseContainer) | Host lacks the BaseContainer feature | User runs `wxc-host-prep prepare-system-drive` once and `prepare-null-device` after every boot, both elevated. Do not elevate on the user's behalf |
| Host exit `2` with a usage message | Bad host options, or `tui` started without a real console | Fix the options; launch `tui` in a terminal (see `mxc-interactive`) |

## Security pitfalls (verified)

- A read-only grant on a drive root (`C:\`) exposes **every** child folder's contents on
  BaseContainer, contrary to MXC docs. Never grant drive roots.
- `enumeratePaths` on `C:\` lets every folder's names be listed recursively; contents stay denied.
- Shared mode exposes all of `~/.claude` read-write, including credentials and session history.

## Additional resources

- **`references/sdk-and-policy.md`**: .NET SDK API (`ContainerRequest`, `Containment`,
  `FilesystemPolicy`, `NetworkPolicy`, `UiPolicy`, `SpawnAsync`, `SpawnWithPty`, `Probe`), backend
  capability matrix, network CIDR rules, env semantics, and where to read MXC source for anything
  not covered.
