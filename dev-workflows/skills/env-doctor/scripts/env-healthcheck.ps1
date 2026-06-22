#requires -Version 5
<#
.SYNOPSIS
  Verify the toolchain that Claude Code + its plugin hooks depend on, on this Windows machine.
.DESCRIPTION
  Run on demand when something seems off ("are my hooks alive?"), or quietly from the
  SessionStart canary. The critical check is `python3`/`python`/`py`: the security-guidance and
  geeky-orchestration plugin hooks shell out to Python, and when none resolves they fail
  *non-blocking* (silent) - which once went unnoticed for ~a week. See the
  feedback-windows-shell memory.
.PARAMETER Quiet
  Suppress the PASS table; only emit output if something is wrong. Intended for hook use.
.OUTPUTS
  Exit code 0 = all critical checks pass; 1 = a critical check (python interpreter) failed.
#>
[CmdletBinding()]
param([switch]$Quiet)

$ErrorActionPreference = 'SilentlyContinue'

function Resolve-Tool([string]$name) { (Get-Command $name -ErrorAction SilentlyContinue).Source }

# critical = its absence silently breaks plugin hooks; informational = nice to know
$checks = @(
    @{ Name = 'python3';  Critical = $true;  Note = 'plugin hooks (security-guidance, geeky)' }
    @{ Name = 'python';   Critical = $false; Note = 'fallback interpreter' }
    @{ Name = 'py';       Critical = $false; Note = 'Windows launcher (stable)' }
    @{ Name = 'node';     Critical = $false; Note = 'JS tooling' }
    @{ Name = 'gh';       Critical = $false; Note = 'GitHub CLI' }
    @{ Name = 'dotnet';   Critical = $false; Note = 'Markefin backend' }
    @{ Name = 'pwsh';     Critical = $false; Note = 'PowerShell 7' }
)

$rows = foreach ($c in $checks) {
    $src = Resolve-Tool $c.Name
    [PSCustomObject]@{
        Check    = $c.Name
        Status   = if ($src) { 'PASS' } elseif ($c.Critical) { 'FAIL' } else { 'missing' }
        Critical = $c.Critical
        Resolves = if ($src) { $src } else { '' }
        Note     = $c.Note
    }
}

# ~/bin (python shim dir) on PATH?
$binDir   = Join-Path $env:USERPROFILE 'bin'
$binOnPath = ($env:PATH -split ';' | ForEach-Object { $_.TrimEnd('\') }) -contains $binDir.TrimEnd('\')

$criticalFail = @($rows | Where-Object { $_.Critical -and $_.Status -eq 'FAIL' }).Count -gt 0

if (-not $Quiet) {
    "Environment health check  ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
    $rows | Format-Table Check, Status, Resolves, Note -AutoSize
    "shim dir $binDir on PATH : $binOnPath"
}

if ($criticalFail -or -not $binOnPath) {
    $msg = if ($criticalFail) {
        "ENV WARNING: no python3 interpreter resolves -> security-guidance + geeky plugin hooks will SILENTLY no-op. Fix: ensure $binDir (python/python3 shims) is on PATH, then restart the session."
    } else {
        "ENV NOTE: shim dir $binDir is not on PATH; python currently resolves via another source. If python3 ever stops resolving, hooks go silently dead - re-add $binDir to PATH."
    }
    Write-Warning $msg
    if ($criticalFail) { exit 1 }
}
exit 0
