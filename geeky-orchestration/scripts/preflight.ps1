<#
.SYNOPSIS
preflight.ps1 — Windows entry point for the geeky-orchestration tooling preflight.

.DESCRIPTION
Cross-env fallback wrapper (N1): resolves a Python interpreter via the chain
`py -3` -> `python3` -> `python` and delegates to preflight.py (the canonical
implementation — stdlib-only, so it cannot itself hit the missing-dependency
class it guards against). If NO Python resolves, falls back to verifying that
the native .ps1 validator set is present and parseable, and reports that the
Python validator chain is unavailable (warning, not failure, since the .ps1
ports can carry a Windows-only run).

Contract: exit 0 = pass, exit 1 = fail. Same flags as preflight.py.

.EXAMPLE
pwsh -NoProfile -ExecutionPolicy Bypass -File preflight.ps1 -Path "docs/pkg"
#>
[CmdletBinding()]
param(
    [string]$Path,
    [double]$StaleHours = 24,
    [switch]$Json
)
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = $null

foreach ($candidate in @(@('py', '-3'), @('python3'), @('python'))) {
    $exe = $candidate[0]
    if (Get-Command $exe -ErrorAction SilentlyContinue) {
        # Verify it actually runs (a broken shim resolves but fails to execute)
        & $exe @($candidate[1..($candidate.Count-1)] | Where-Object { $_ }) --version *> $null
        if ($LASTEXITCODE -eq 0) { $py = $candidate; break }
    }
}

if ($py) {
    $args_ = @($py[1..($py.Count-1)] | Where-Object { $_ }) + @("$here\preflight.py")
    if ($Path)      { $args_ += @('--path', $Path) }
    if ($StaleHours -ne 24) { $args_ += @('--stale-hours', $StaleHours) }
    if ($Json)      { $args_ += '--json' }
    & $py[0] @args_
    exit $LASTEXITCODE
}

# --- No Python anywhere: reduced native check -------------------------------
Write-Output "[WARN] no Python interpreter found (tried: py -3, python3, python) — .py validator chain unavailable on this host"
$fail = $false
$required = @('validate-planning-folder.ps1', 'validate-task-schema.ps1', 'validate-kanban.ps1', 'check-dod.ps1', 'check-commit.ps1')
foreach ($f in $required) {
    $full = Join-Path $here $f
    if (-not (Test-Path $full)) {
        Write-Output "[FAIL] missing native validator: $f"
        $fail = $true
        continue
    }
    $tokens = $null; $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($full, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors -and $errors.Count -gt 0) {
        Write-Output "[FAIL] parse error in ${f}: $($errors[0].Message)"
        $fail = $true
    } else {
        Write-Output "[PASS] parse: $f"
    }
}
if ($Path) {
    $kanban = Join-Path $Path 'kanban.md'
    $handoff = Join-Path $Path 'handoff.md'
    if (-not (Test-Path $kanban)) { Write-Output "[FAIL] freshness: kanban.md missing in $Path"; $fail = $true }
    elseif ((Test-Path $handoff) -and (((Get-Item $kanban).LastWriteTime - (Get-Item $handoff).LastWriteTime).TotalHours -gt $StaleHours)) {
        Write-Output "[WARN] handoff.md older than kanban.md by > $StaleHours h — reconcile before running"
    }
}
Write-Output "[REMINDER] If this run may exceed ~1 hour: re-auth NOW (/login) before starting — OAuth expiry mid-run has no in-session recovery."
if ($fail) { Write-Output 'PREFLIGHT FAILED'; exit 1 } else { Write-Output 'PREFLIGHT OK (native-only mode)'; exit 0 }
