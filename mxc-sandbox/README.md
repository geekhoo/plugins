# mxc-sandbox

Run the Claude Code CLI inside a [Microsoft MXC](https://github.com/microsoft/mxc) sandbox on
Windows, for isolated testing of prompts, plugins, skills, hooks, and untrusted repositories.

The plugin bundles a small .NET host (`Microsoft.Mxc.Sdk` 1.0.1) and four skills that drive it.

## Requirements

- Windows 11 (verified on 26H2, build 26300); BaseContainer tier needs no admin step
- .NET 10 SDK (host targets `net10.0`; for SDK 8/9 edit `scripts/host/MxcClaude/MxcClaude.csproj`; the
  wrapper checks the SDK against the project's target)
- Native Claude CLI at `%USERPROFILE%\.local\bin\claude.exe` (or set `MXC_CLAUDE_EXE`)

## Skills

| Skill | Use it for |
|---|---|
| `mxc-setup` | Check prerequisites, build the host, probe tier and grants, smoke test |
| `mxc-run` | Headless `claude -p` / subcommands in a ProcessContainer with filesystem and network policy |
| `mxc-interactive` | Interactive claude (PTY) in an IsolationSession as a separate local account |
| `mxc-troubleshooting` | Failure signatures and fixes, plus the .NET SDK and policy reference |

## Host usage

```powershell
$mxc = '<plugin-root>\scripts\mxc.ps1'      # builds on first use into %USERPROFILE%\.mxc-sandbox\bin

& $mxc probe --workspace C:\repos\app
& $mxc run   --workspace C:\repos\app -- -p "summarise this repo"
& $mxc run   --workspace C:\repos\app --allow-win32k -- mcp list
& $mxc run   --workspace C:\repos\app --isolated -- -p "review for malware"
& $mxc tui   --workspace C:\repos\app
```

| Option | Modes | Effect |
|---|---|---|
| `--workspace <dir>` | all | Read-write project folder (default: current directory). Keep it shallow |
| `--isolated` | run, probe | Private config dir; auth only from host `CLAUDE_CODE_OAUTH_TOKEN` / `ANTHROPIC_API_KEY` |
| `--allow-win32k` | run, probe | Let node/npx/uv/pwsh start; adds enumerate-only access to `C:\` (folder names listable, contents denied) |
| `--deny-net` | run, probe | Block all egress; claude retries the API until `--timeout`, so set a short one |
| `--ro <dir>` / `--rw <dir>` | run, probe | Extra grants (repeatable) |
| `--timeout <sec>` | run, tui | Kill after N seconds (exit 124) |
| `-Rebuild` | wrapper | Force a host rebuild; must be the first argument |

`probe` reports the grants a `run` with the same options would apply. `tui` ignores the
filesystem, network, and config options (IsolationSession supports none of them).

The first argument that is not a host option starts claude's arguments. `--` is optional: the
PowerShell `&` operator drops it, while `pwsh -File` passes it through, and the host handles both.
A misspelled host option is therefore passed to claude, which rejects it as an unknown option.

Exit codes: claude's own code, `124` on timeout, `2` for bad host usage, `1` for an `MXC error`.

## Isolation summary (verified)

| | `run` default | `run --allow-win32k` | `tui` |
|---|---|---|---|
| Other repos, `~/.ssh`, `Documents` | denied | names only | Windows ACLs of agent account |
| Writes outside workspace/config/cache | denied | denied | agent account ACLs |
| Host `~/.claude` | read-write (shared) or none (`--isolated`) | same | none |
| Network | egress allowed, inbound denied (`--deny-net` blocks egress) | same | unrestricted |
| node/npx stdio MCP servers | fail | work | n/a |
| `uv run` MCP servers, all hooks | fail | fail | n/a |

Hooks fail because Claude Code runs every hook through Git Bash, which cannot start in
BaseContainer. Disable them with `--settings` pointing at `{"disableAllHooks": true}`.

## State

All state lives under `%USERPROFILE%\.mxc-sandbox` (`MXC_SANDBOX_HOME` overrides):
`src\`, `bin\`, `home\` (isolated config), `cache\npm`, `cache\uv`, `tmp\`. `tui` copies
`claude.exe` (about 280 MB) machine-wide to `%ProgramData%\mxc-sandbox\bin`, readable by all local
users. Avoid `%LOCALAPPDATA%` for any override: the container cannot write there.
