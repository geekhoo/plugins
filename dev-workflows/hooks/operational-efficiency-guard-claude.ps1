param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('PreToolUse', 'UserPromptSubmit')]
  [string]$Event
)

# Claude Code companion to operational-efficiency-guard.ps1 (which is Codex/OMX-wired via the
# native shim and MUST stay untouched). Same operational checks, but adapted to the Claude Code
# hook contract: reads the hook JSON from STDIN, and emits warnings as hookSpecificOutput.
# additionalContext on STDOUT so they SURFACE to the model — rather than the Codex script's
# stderr, which Claude Code's non-blocking hooks would swallow silently. Warning-only; always
# exits 0; emits nothing when clean (no noise).

$ErrorActionPreference = 'SilentlyContinue'
$raw = [Console]::In.ReadToEnd()
$payload = $null
try { $payload = $raw | ConvertFrom-Json -Depth 80 } catch { $payload = $null }
$flat = ($raw).ToLowerInvariant()

$warnings = New-Object System.Collections.Generic.List[string]
function Add-Warning([string]$m) { if (-not $warnings.Contains($m)) { $warnings.Add($m) | Out-Null } }

if ($Event -eq 'PreToolUse') {
  $cmd = ''
  if ($payload) {
    $ti = $payload.tool_input; if (-not $ti) { $ti = $payload.toolInput }
    if ($ti) {
      if ($ti -is [string]) { $cmd = $ti }
      elseif ($ti.PSObject.Properties.Name -contains 'command') { $cmd = [string]$ti.command }
      else { $cmd = ($ti | ConvertTo-Json -Compress -Depth 20) }
    }
  }
  $c = $cmd.ToLowerInvariant()
  if ($c -match '(^|[;&|\s])(sed|nl)(\.exe)?\s') { Add-Warning 'Operational guard: POSIX inspection command (sed/nl) on Windows. Prefer Get-Content/Select-String, or use the Bash tool explicitly.' }
  if ($c -match '<<\s*[''"A-Za-z_]') { Add-Warning 'Operational guard: bash heredoc in a command. Prefer a PowerShell here-string or a temp file.' }
  if ($c -match 'foreach\s*\(' -and $c -match '\}\s*\|') { Add-Warning 'Operational guard: PowerShell foreach block piped directly. Collect into an array before piping.' }
  if ($c -match 'rg\s+' -and $c -match '[A-Za-z0-9_\-]+\*\.[A-Za-z0-9]+') { Add-Warning 'Operational guard: rg positional glob can fail on Windows. Prefer rg --files -g or explicit file lists.' }
  if ($c -match 'sessions|archived_sessions|rollout' -and $c -match 'rg\s+' -and $c -notmatch 'max|head|select-object|totalcount|response_length') { Add-Warning 'Operational guard: broad session scan detected. Cap output and shard by folder first.' }
  if ($c -match '<[a-z0-9_\-]+>') { Add-Warning 'Operational guard: unresolved <PLACEHOLDER> in a command. Resolve placeholders before dispatching.' }
}

if ($Event -eq 'UserPromptSubmit') {
  $p = ''
  if ($payload -and ($payload.PSObject.Properties.Name -contains 'prompt')) { $p = [string]$payload.prompt }
  if (-not $p) { $p = $flat }
  $p = $p.ToLowerInvariant()
  if ($p -match 'parallel subagents|spawn.*subagent|use.*subagents') { Add-Warning 'Operational guard: subagent request. Make lanes concrete, bounded, and placeholder-free before dispatching.' }
  if ($p -match 'browser|playwright|chrome|screenshot|ui validation|localhost') { Add-Warning 'Operational guard: browser/UI proof request. Gather real browser evidence before any runtime/"it works" claim.' }
  if ($p -match 'geeky-plan|plan-review|geeky-implement|packet|kanban|handoff') { Add-Warning 'Operational guard: packet/planning workflow. Keep plan/tasks/kanban/handoff consistent and persist artifacts.' }
  if ($p -match 'figma|visual parity|baseline|devextreme|widget') { Add-Warning 'Operational guard: Figma/UI parity request. Lock scope and capture before/after evidence (figma-batch-analyzer / devextreme-grid-updater).' }
  if ($p -match 'stabili[sz]e|repeatable workflow|future work together|wasted rounds|skills to use|fix hooks|optimi[sz]e') { Add-Warning 'Operational guard: workflow-stabilization request. Prefer durable skill/memory/hook/tool changes, validated — and check geekhoo-plugins for an existing twin first.' }
}

if ($warnings.Count -gt 0) {
  $out = @{ hookSpecificOutput = @{ hookEventName = $Event; additionalContext = ($warnings -join ' | ') } }
  $out | ConvertTo-Json -Compress -Depth 5
}
exit 0
