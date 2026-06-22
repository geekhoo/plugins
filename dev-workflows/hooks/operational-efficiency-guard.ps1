param(
  [Parameter(Mandatory=$true)]
  [string]$InputJson
)

$ErrorActionPreference = 'SilentlyContinue'
$warnings = New-Object System.Collections.Generic.List[string]
$payload = $null
try { $payload = $InputJson | ConvertFrom-Json -Depth 80 } catch { $payload = $null }
$flat = $InputJson.ToLowerInvariant()

function Add-Warning([string]$message) {
  if (-not $warnings.Contains($message)) { $warnings.Add($message) | Out-Null }
}

$toolName = ''
$cmd = ''
if ($payload) {
  foreach ($name in @('tool_name','toolName','name')) {
    if ($payload.PSObject.Properties.Name -contains $name) { $toolName = [string]$payload.$name }
  }
  $candidate = $payload.tool_input
  if (-not $candidate) { $candidate = $payload.toolInput }
  if (-not $candidate) { $candidate = $payload.arguments }
  if ($candidate) {
    if ($candidate -is [string]) { $cmd = $candidate }
    elseif ($candidate.PSObject.Properties.Name -contains 'cmd') { $cmd = [string]$candidate.cmd }
    else { $cmd = ($candidate | ConvertTo-Json -Compress -Depth 20) }
  }
}
$cmdLower = $cmd.ToLowerInvariant()

if ($flat -match 'pretooluse|pre_tool_use' -or $toolName) {
  if ($cmdLower -match '(^|[;&|\s])(sed|nl)(\.exe)?\s') {
    Add-Warning 'Operational guard: POSIX inspection command detected on Windows. Prefer Get-Content/Select-String or explicitly use Bash.'
  }
  if ($cmdLower -match '<<\s*[''"A-Za-z_]') {
    Add-Warning 'Operational guard: Bash heredoc-like syntax detected in a Windows shell command. Prefer PowerShell here-strings or a temp file.'
  }
  if ($cmdLower -match 'foreach\s*\(' -and $cmdLower -match '\}\s*\|') {
    Add-Warning 'Operational guard: PowerShell foreach block piped directly. Collect into an array before piping.'
  }
  if ($cmdLower -match 'rg\s+' -and $cmdLower -match '[A-Za-z0-9_\-]+\*\.[A-Za-z0-9]+') {
    Add-Warning 'Operational guard: rg positional glob on Windows can fail. Prefer rg --files -g or explicit file lists.'
  }
  if ($cmdLower -match 'sessions|archived_sessions|rollout' -and $cmdLower -match 'rg\s+' -and $cmdLower -notmatch 'max|head|select-object|totalcount|response_length') {
    Add-Warning 'Operational guard: broad session scan detected. Cap output and shard by folder before launching.'
  }
  if ($cmdLower -match '<[A-Z0-9_\-]+>') {
    Add-Warning 'Operational guard: unresolved template placeholder detected. Resolve placeholders before dispatching commands or subagents.'
  }
}

if ($flat -match 'userpromptsubmit|user_prompt_submit') {
  if ($flat -match 'parallel subagents|spawn.*subagent|use.*subagents') {
    Add-Warning 'Operational guard: subagent request detected. Use subagent-orchestration-hygiene; make lanes concrete, bounded, and placeholder-free.'
  }
  if ($flat -match 'browser|playwright|chrome|screenshot|ui validation|localhost') {
    Add-Warning 'Operational guard: browser/UI proof request detected. Use browser-ui-validation-gates before runtime claims.'
  }
  if ($flat -match 'geeky-plan|plan-review|geeky-implement|packet|kanban|handoff') {
    Add-Warning 'Operational guard: packet workflow request detected. Use packet-workflow-integrity and persist artifacts.'
  }
  if ($flat -match 'figma|visual parity|baseline|devextreme|widget') {
    Add-Warning 'Operational guard: Figma/UI parity request detected. Use figma-ui-scope-parity to lock scope and evidence.'
  }
  if ($flat -match 'stabili[sz]e|repeatable workflow|future work together|wasted rounds|skills to use|fix hooks|optimise|optimize') {
    Add-Warning 'Operational guard: workflow-stabilization request detected. Use codex-operational-stabilizer; prefer skill, memory, hook, and tool updates with validation.'
  }
}

foreach ($warning in $warnings) {
  [Console]::Error.WriteLine($warning)
}
