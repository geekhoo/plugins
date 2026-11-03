---
name: mxc-run
description: This skill should be used when the user asks to "run claude in MXC", "run claude inside the MXC sandbox", "test this plugin in the MXC sandbox", "try this skill/prompt in an MXC-sandboxed claude", "run claude headless against an untrusted repo in MXC", or "claude mcp list inside MXC" on Windows, i.e. a non-interactive Claude Code CLI invocation inside a Microsoft MXC ProcessContainer with filesystem and network policy. Not for interactive sessions (mxc-interactive), diagnosing failures (mxc-troubleshooting), Docker/devcontainer sandboxes, or Claude Code's built-in /sandbox.
argument-hint: "--workspace <dir> [--isolated] [--allow-win32k] [--host-loopback] [--deny-net] [--ro <dir>] [--rw <dir>] [--env NAME[=VALUE]] [--timeout <sec>] -- <claude args>"
allowed-tools: PowerShell, Read, Write
---

# Run headless Claude Code inside an MXC ProcessContainer

Execute a non-interactive Claude Code CLI command inside a Microsoft MXC ProcessContainer
(BaseContainer tier on Windows 11). The sandboxed process sees only what is granted. There is no
TTY, so only `-p` prompts and subcommands work; for an interactive session use `mxc-interactive`.

## Resolve the wrapper and run

```powershell
# <base> = the "Base directory for this skill" path shown when this skill loads
$mxc = (Resolve-Path (Join-Path '<base>' '..\..\scripts\mxc.ps1')).Path
& $mxc run --workspace C:\repos\<project> --timeout 300 -- -p "<prompt>"
```

If no base path is shown, use the fallback lookup in the `mxc-setup` skill. The wrapper builds the
host on first use; run `mxc-setup` first only to verify the tier and grants.

Host options come first. The first argument that is not a host option starts claude's arguments.
`--` is optional (PowerShell's `&` drops it), so spell host options exactly; a misspelled one is
passed to claude, which rejects it as an unknown option.

Exit codes: claude's own, `124` timeout, `2` bad host usage, `1` `MXC error` before launch.

## Choose options deliberately

| Need | Options | Effect |
|---|---|---|
| Existing login, settings, plugins, HTTP MCP servers | *(default: shared)* | `CLAUDE_CONFIG_DIR=%USERPROFILE%\.claude` granted read-write; `~/.claude.json` copied one-way to `~/.claude/.claude.json` before each run |
| Private Claude config | `--isolated` | Uses persistent `%USERPROFILE%\.mxc-sandbox\home` instead of granting the host Claude config. The workload can still receive credentials and other inherited or explicitly passed environment values. |
| stdio MCP servers, node/npx/pwsh tools | `--allow-win32k` | Allows Win32k syscalls and, when supported and not suppressed by `--no-enumerate-root`, enumerate-only access to the system drive. Folder names become listable; file contents outside grants stay denied. Check the probe. |
| Containment test without network | `--deny-net --timeout 60` | Blocks all egress. claude retries the API until the timeout (exit 124) rather than failing fast, so always pair it with a short `--timeout` |
| Load a local plugin under test | `--ro <plugin dir>` and `--plugin-dir <plugin dir>` for claude | Extra read-only grant |
| Extra writable folder | `--rw <dir>` | Extra read-write grant |
| Python stdio MCP servers built on the `mcp` library | `--allow-win32k --host-loopback` | asyncio's loopback socketpair hangs under the default loopback deny ([microsoft/mxc#1505](https://github.com/microsoft/mxc/issues/1505)). This opens every host loopback port to the workload. Launch the server with a prebuilt interpreter, not `uv run`, which still fails. |
| Set a variable for the workload | `--env NAME=VALUE` (or `--env NAME` to copy the host's value) | Repeatable, and applied last. The request inherits the backend default environment; the host explicitly adds two auth variables and pinned values. Use this option to set or override values such as `MCP_TIMEOUT` or another CLI's `CODEX_HOME`. Pass secrets as a bare `NAME`, never as a literal value. |
| Disable hooks for a test | claude `--settings <file containing {"disableAllHooks": true}>` | Suppresses hook execution; do not use when testing hooks |

Keep the workspace shallow (`C:\repos\<name>`). A deep path such as a `%TEMP%` 8.3 path makes
claude refuse to read `<workspace>\.claude\settings*.json`, because upward traversal is blocked.

## What the sandbox can and cannot do (verified)

| Capability | Default | `--allow-win32k` |
|---|---|---|
| Read/write workspace and config dir | yes | yes |
| Read other repos, `~/.ssh`, `Documents`, `%APPDATA%` | no | names listable, contents no |
| Write outside grants (`C:\`, profile root) | no | no |
| `claude -p`, `claude mcp list`, HTTP MCP servers | yes | yes |
| `node`, `npx`, `pwsh`, `uv` start | no (`0xC0000142`) | yes |
| stdio MCP servers via `node`/`npx` (e.g. playwright, pdf-viewer) | no | yes; the first `npx` run fills a private cache and may need a retry |
| stdio MCP servers via `uv run` | no | no: uv builds a trampoline `.exe` in the AppContainer temp dir, which is denied |
| Settings and plugin hooks | Git Bash hooks failed in the 2026-10-20 BaseContainer observations | Git Bash hooks failed; a hook explicitly declaring `"shell": "powershell"` was observed working with `--allow-win32k`. Verify the particular hook and grants. |
| Inbound connections | denied | denied |
| Host loopback (Windows) | denied by default; `--host-loopback` allows it | denied by default; `--host-loopback` allows it |

When a limit affects the requested test, report it instead of retrying.

## Recipes

- **Smoke test:** `& $mxc run --workspace <ws> -- -p "Reply with exactly: PONG"`.
- **Inspect tool and hook events:** add claude `--output-format stream-json --verbose`, then filter
  lines containing `"type":"result"` or `"subtype":"hook_response"`.
- **Test a plugin in development:** write `{"disableAllHooks": true}` to `<ws>\no-hooks.json`, then
  `& $mxc run --workspace <ws> --ro <plugin> -- --plugin-dir <plugin> --settings <ws>\no-hooks.json -p "<trigger phrase>"`.
- **Untrusted repo:** `--isolated` avoids granting the host Claude config directory. The workload receives the host token, and the private config directory is persistent; treat its contents and any explicit grants as accessible to the workload. Add claude `--allowedTools` / `--permission-mode` to limit actions.

Full command lines, result parsing, tool-call extraction, hook-script checks, and workspace
diffing are in **`references/recipes.md`**.

## Security notes

- Shared mode grants read-write access to all of `~/.claude`, including `.credentials.json`,
  memory, and session transcripts. Use `--isolated` for untrusted code.
- Never pass `--ro C:\` (or any drive root): on BaseContainer it exposes every child folder.
- Outbound network is all-or-nothing (no hostname allow-lists); only `--deny-net` restricts it.
