---
name: mxc-interactive
description: This skill should be used when the user asks to "open an interactive claude in MXC", "start a sandboxed claude TUI", "run the claude TUI inside MXC", "interactive PTY claude in an MXC IsolationSession", or "chat with claude inside the MXC sandbox" on Windows, i.e. a full-terminal Claude Code session under Microsoft MXC IsolationSession. Not for headless runs (mxc-run) or non-MXC sandboxes.
argument-hint: "--workspace <dir> [--timeout <sec>] [-- <claude args>]"
allowed-tools: PowerShell, Read
---

# Interactive Claude Code in an MXC IsolationSession

Start an interactive Claude Code session (full PTY) inside Microsoft MXC. On Windows, MXC provides a
PTY only through **IsolationSession**, which runs the workload as a separate, ephemeral local agent
account (for example `<host>\q5-h8` with profile `C:\Users\Q5-H8`).

## Isolation model: tell the user

| Property | IsolationSession (`tui`) |
|---|---|
| Identity | Separate local account with its own profile; cannot read the host user's profile |
| Filesystem policy | None from MXC; access follows that account's normal Windows ACLs |
| Network policy | None (MXC requires unrestricted networking to be declared) |
| Host `~/.claude` (login, settings, plugins, memory) | Not visible |
| Persistence | Ephemeral account; a `/login` made inside does not persist |

`--isolated`, `--deny-net`, `--allow-win32k`, `--ro`, and `--rw` have no effect in `tui`. For
filesystem and network policy, use `mxc-run` (headless). On Windows, interactive use and
fine-grained policy are mutually exclusive.

## Procedure

1. Confirm the host is built and the probe shows `isolationSession: True` (`mxc-setup`).
2. Resolve the wrapper path:

   ```powershell
   # <base> = the "Base directory for this skill" path shown when this skill loads
   $mxc = (Resolve-Path (Join-Path '<base>' '..\..\scripts\mxc.ps1')).Path
   ```

   If no base path is shown, use the fallback lookup in `mxc-setup`.
3. Pick a workspace the agent account can read. Folders under `C:\repos` are readable by local
   Users; anything under `C:\Users\<host user>` is not.
4. Auth: a host `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` is passed in. Otherwise the user
   runs `/login` inside every session.
5. Launch in a real console. `tui` refuses redirected I/O (`tui needs an interactive terminal`,
   exit 2), so never run it through a captured shell tool call:
   - If a tool exists that opens a terminal tab for the user (e.g. a desktop app's
     `run_in_terminal`), run the command there:
     `pwsh -NoProfile -File '<resolved $mxc>' tui --workspace C:\repos\<project>`
   - Otherwise print that exact command, with the resolved path filled in, for the user to paste
     into their own terminal.

   Claude arguments go after the host options (for example `... tui --workspace <ws> -- --model sonnet`).
6. For a quick check that the mode works, launch the same way with `-- --version`. Expect the CLI
   version and exit 0.

## Behaviour details

- The first launch copies `claude.exe` (about 280 MB) to `%ProgramData%\mxc-sandbox\bin`, because
  the agent account cannot read `%USERPROFILE%\.local\bin`. It re-copies when the source changes.
- `Access is denied.` with no other output means the agent account cannot reach the CLI or the
  workspace. Move the workspace out of the host user's profile.
- `--timeout <sec>` applies. Window size is taken from the launching console at start; resizes
  during the session are not forwarded.
- `/exit` or Ctrl-D ends the session; the wrapper returns claude's exit code.

## Additional resources

- **`mxc-troubleshooting`**: failure signatures for both modes.
- **`mxc-run`**: headless runs with real filesystem and network policy.
