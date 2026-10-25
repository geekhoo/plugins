<#
.SYNOPSIS
  Run the model-free mock baseline for every harness x case (C0-C3) in MXC and report one matrix.

.DESCRIPTION
  Calls run-baseline.ps1 -MockAgent -MockScenario all,happy (Claude Code) and run-codex-baseline.ps1
  -MockAgent (Codex) for each case, one at a time, as child processes so one failure does not stop the rest. No model
  is called. A run passes when its runner exits 0, every mock check passes and, with telemetry on
  (TRACE_TO_LANGFUSE=true), Langfuse returns the session's observations.

  Each stored run folder moves out of evals/baselines into <OutDir>/<harness>-<case>/, and its
  workspace, run config and Claude session folder are deleted afterwards (-KeepWorkspaces keeps
  them). <OutDir>/matrix.json and matrix.md hold the results. Exit 1 when any run fails.

.EXAMPLE
  pwsh -File run-mock-matrix.ps1
  pwsh -File run-mock-matrix.ps1 -Harness codex -Case c2-linkvault -NoTelemetry
#>
param(
    [ValidateSet('claude-code', 'codex')][string[]]$Harness = @('claude-code', 'codex'),
    [ValidateSet('c0-wordstat', 'c1-csvledger', 'c2-linkvault', 'c3-minisql')][string[]]$Case = @('c0-wordstat', 'c1-csvledger', 'c2-linkvault', 'c3-minisql'),
    [string]$ToolsDir,
    [string]$WorkRoot,
    [string]$OutDir,
    [switch]$NoTelemetry,
    [switch]$KeepWorkspaces
)
$ErrorActionPreference = 'Stop'
$onWindows = $IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop'
if (-not $WorkRoot) { $WorkRoot = if ($onWindows) { 'C:\repos' } else { Join-Path $HOME 'repos' } }
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
if (-not $OutDir) { $OutDir = Join-Path $WorkRoot "mock-matrix-$stamp" }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$pwsh = (Get-Process -Id $PID).Path
$runners = @{ 'claude-code' = Join-Path $PSScriptRoot 'run-baseline.ps1'; 'codex' = Join-Path $PSScriptRoot 'run-codex-baseline.ps1' }
$common = @(if ($ToolsDir) { '-ToolsDir', $ToolsDir }) + @('-WorkRoot', $WorkRoot) + @(if ($NoTelemetry) { '-NoTelemetry' })
$mxcHome = if ($env:MXC_SANDBOX_HOME) { $env:MXC_SANDBOX_HOME } else { Join-Path $(if ($onWindows) { $env:USERPROFILE } else { $HOME }) '.mxc-sandbox' }

$results = foreach ($h in $Harness) {
    foreach ($c in $Case) {
        Write-Host "== $h $c" -ForegroundColor Cyan
        $log = Join-Path $OutDir "$h-$c.log"
        $started = Get-Date
        # Claude's toolchain checks (pwsh, python/pytest, git, gates, grants, MCP) live outside its workflow
        # scenario, so run both; Codex's default scenario already runs all of its checks.
        $scenario = if ($h -eq 'claude-code') { @('-MockScenario', 'all,happy') } else { @() }
        & $pwsh -NoProfile -File $runners[$h] -Case $c -MockAgent @scenario @common *>&1 | Tee-Object -FilePath $log | Out-Null
        $exitCode = $LASTEXITCODE
        $text = Get-Content $log -Raw
        $stored = if ($text -match '(?m)^(?:stored|prepared): (.+?)(?: \(analysis status.*)?$') { $Matches[1].Trim() }
        $row = [ordered]@{ harness = $h; case = $c; runner_exit = $exitCode; wall_s = [int]((Get-Date) - $started).TotalSeconds
            checks_passed = $null; checks_failed = @(); exit_reason = $null; telemetry = $null; observations = $null; folder = $null; ok = $false }
        if ($stored -and (Test-Path $stored)) {
            $run = Get-Content (Join-Path $stored 'run.json') -Raw | ConvertFrom-Json
            $mock = if (Test-Path (Join-Path $stored 'mock-summary.json')) { Get-Content (Join-Path $stored 'mock-summary.json') -Raw | ConvertFrom-Json }
            if ($mock) {
                # Claude's summary lists check names; Codex's lists checks with passed flags.
                $row.checks_failed = if ($mock.failed -is [array]) { @($mock.failed) } else { @($mock.checks | Where-Object { -not $_.passed } | ForEach-Object name) }
                $row.checks_passed = if ($mock.counts) { [int]$mock.counts.pass } else { @($mock.checks | Where-Object passed).Count }
            }
            $row.exit_reason = $run.exit_reason
            $row.telemetry = if ($run.telemetry.enabled) { $(if ($run.telemetry.delivered) { 'delivered' } else { 'missing' }) } else { 'off' }
            $row.observations = $run.telemetry.observations
            $row.ok = $exitCode -eq 0 -and $mock -and $row.checks_failed.Count -eq 0 -and $row.telemetry -ne 'missing'
            $dest = Join-Path $OutDir "$h-$c"
            Move-Item $stored $dest
            $row.folder = $dest
            if (-not $KeepWorkspaces) {
                $cfg = if ($run.config_directory) { $run.config_directory } else { Join-Path $WorkRoot ".eval-cfg-$(Split-Path $stored -Leaf)" }
                foreach ($dir in @($run.workspace, $cfg) | Where-Object { $_ -and (Test-Path $_) }) { Remove-Item $dir -Recurse -Force }
                if ($h -eq 'claude-code' -and $run.workspace) {
                    $slug = $run.workspace -replace '[^A-Za-z0-9]', '-'
                    $sessionDir = Join-Path $mxcHome "home/projects/$slug"
                    if (Test-Path $sessionDir) { Remove-Item $sessionDir -Recurse -Force }
                }
            }
        }
        Write-Host ("   {0}  exit={1} checks={2} failed=[{3}] telemetry={4} ({5} obs) {6}s" -f
            $(if ($row.ok) { 'PASS' } else { 'FAIL' }), $exitCode, $row.checks_passed, ($row.checks_failed -join ','), $row.telemetry, $row.observations, $row.wall_s)
        [pscustomobject]$row
    }
}

$report = [ordered]@{ schema = 'geeky-eval.mock-matrix/1'; stamp = $stamp; platform = [Runtime.InteropServices.RuntimeInformation]::OSDescription
    plugin_sha = (git -C $PSScriptRoot rev-parse HEAD); runs = @($results); ok = -not ($results | Where-Object { -not $_.ok }) }
$report | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $OutDir 'matrix.json')
$md = @("# Mock matrix $stamp", '', "Platform: $($report.platform). Plugin: ``$($report.plugin_sha)``. No model calls.", '',
    '| Harness | Case | Result | Runner exit | Checks passed | Failed checks | Telemetry | Observations | Wall (s) |',
    '|---|---|---|---:|---:|---|---|---:|---:|')
$md += $results | ForEach-Object { "| $($_.harness) | $($_.case) | $(if ($_.ok) { 'PASS' } else { 'FAIL' }) | $($_.runner_exit) | $($_.checks_passed) | $($_.checks_failed -join ', ') | $($_.telemetry) | $($_.observations) | $($_.wall_s) |" }
$md | Set-Content (Join-Path $OutDir 'matrix.md')
Write-Host "matrix: $(Join-Path $OutDir 'matrix.md')"
if (-not $report.ok) { exit 1 }
