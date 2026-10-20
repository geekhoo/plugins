# mxc-run recipes

All commands assume `$mxc` resolves to `<plugin-root>\scripts\mxc.ps1` and a shallow workspace
such as `C:\repos\scratch` (create it first).

## 1. Prompt and parse the result

```powershell
$lines = & $mxc run --workspace C:\repos\scratch --timeout 300 -- `
    -p "List the files in this folder" --output-format stream-json --verbose 2>&1
$result = ($lines | Where-Object { $_ -match '"type":"result"' } | ConvertFrom-Json)
$result.result          # final text
$result.is_error        # true on failure
$result.total_cost_usd
```

Filter out `[mcp-sdk] SEP-2352` lines when showing raw output; they are a harmless warning about
stored MCP OAuth credentials.

## 2. Tool calls made inside the sandbox

```powershell
$lines | Where-Object { $_ -match '"type":"assistant"' } | ForEach-Object {
    ($_ | ConvertFrom-Json).message.content | Where-Object type -eq 'tool_use' |
        ForEach-Object { "{0} {1}" -f $_.name, ($_.input | ConvertTo-Json -Compress) }
}
```

## 3. Hook events

```powershell
$lines | Where-Object { $_ -match '"subtype":"hook_response"' } | ForEach-Object {
    $j = $_ | ConvertFrom-Json; "{0} exit={1} {2}" -f $j.hook_name, $j.exit_code, ([string]$j.stderr).Trim()
}
```

Inside BaseContainer every hook exits 66 (Git Bash cannot start). To test hook *logic*, run the
hook script directly as the workload, e.g. for a node hook:

```powershell
$env:MXC_CLAUDE_EXE = 'C:\Program Files\nodejs\node.exe'
& $mxc run --workspace C:\repos\scratch --allow-win32k --ro <hook dir> -- <hook dir>\hook.js
Remove-Item env:MXC_CLAUDE_EXE
```

`MXC_CLAUDE_EXE` swaps the workload executable. The same grants apply, except the read-only grant
for the executable's folder moves to the replacement's folder. Stdin is closed, so a hook
that reads event JSON from stdin sees empty input: this verifies the script starts and its
dependencies resolve inside the sandbox, not its event handling.

## 4. Containment check with an arbitrary workload

```powershell
$env:MXC_CLAUDE_EXE = 'C:\Windows\System32\cmd.exe'
& $mxc run --workspace C:\repos\scratch -- /d /c "type %USERPROFILE%\.ssh\config >nul 2>&1 && echo LEAK || echo DENIED"
Remove-Item env:MXC_CLAUDE_EXE
```

## 5. Diff the workspace after a run

```powershell
git -C C:\repos\scratch init -q; git -C C:\repos\scratch add -A; git -C C:\repos\scratch commit -qm baseline
& $mxc run --workspace C:\repos\scratch -- -p "<task>" --permission-mode acceptEdits
git -C C:\repos\scratch status --short
git -C C:\repos\scratch diff
```

## 6. Plugin under development

```powershell
$plugin = 'C:\repos\geekhoo-plugins\<plugin>'
'{ "disableAllHooks": true }' | Set-Content C:\repos\scratch\no-hooks.json
& $mxc run --workspace C:\repos\scratch --ro $plugin --timeout 300 -- `
    --plugin-dir $plugin --settings C:\repos\scratch\no-hooks.json -p "<phrase that should trigger the skill>"
```

Add `--allow-win32k` when the plugin ships a node/npx stdio MCP server. `uv run` servers do not
start in the sandbox.

## 7. Isolated run with a token

```powershell
# One-time, by the user: claude setup-token, then store it in their User environment.
& $mxc run --isolated --workspace C:\repos\untrusted --timeout 600 -- `
    -p "Review this repo for malware" --allowedTools "Read,Grep,Glob"
```

The sandbox cannot read `~/.claude` in isolated mode; credentials come only from the token.
