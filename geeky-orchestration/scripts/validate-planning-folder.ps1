# validate-planning-folder.ps1
# Verify that a folder produced by /geeky-plan contains all artifacts /geeky-implement needs.
# Exits 0 with a one-line OK summary if valid.
# Exits 1 with a list of missing artifacts if invalid.
#
# Usage:
#   pwsh -File validate-planning-folder.ps1 -Path "C:\path\to\docs\feature-folder"

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

# Hand-built to match Python's json.dumps exactly on the failure path. Python
# emits this one compact (no indent); ConvertTo-Json pretty-prints and escapes
# differently, which would break the declared .py/.ps1 parity.
# Mirrors ConvertTo-PyJsonString in check-dod.ps1 -- keep in sync.
function ConvertTo-PyJsonString([string]$s) {
    if ($null -eq $s) { $s = '' }
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.Append('"')
    foreach ($ch in $s.ToCharArray()) {
        $code = [int]$ch
        if ($ch -ceq '"')      { [void]$sb.Append('\"') }
        elseif ($ch -ceq '\')  { [void]$sb.Append('\\') }
        elseif ($code -eq 8)   { [void]$sb.Append('\b') }
        elseif ($code -eq 12)  { [void]$sb.Append('\f') }
        elseif ($code -eq 10)  { [void]$sb.Append('\n') }
        elseif ($code -eq 13)  { [void]$sb.Append('\r') }
        elseif ($code -eq 9)   { [void]$sb.Append('\t') }
        elseif ($code -lt 0x20 -or $code -gt 0x7E) { [void]$sb.Append(('\u{0:x4}' -f $code)) }
        else { [void]$sb.Append($ch) }
    }
    [void]$sb.Append('"')
    return $sb.ToString()
}

if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
    $msg = "MISSING_FOLDER: $Path"
    if ($Json) { Write-Output ('{"ok": false, "errors": [' + (ConvertTo-PyJsonString $msg) + ']}') } else { Write-Output $msg }
    exit 1
}

$required = @(
    'implementation-plan.md',
    'kanban.md',
    'references.md',
    'handoff.md'
)

$missing = @()
foreach ($f in $required) {
    $p = Join-Path $Path $f
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
        $missing += $f
    }
}

$tasksDir = Join-Path $Path 'tasks'
if (-not (Test-Path -LiteralPath $tasksDir -PathType Container)) {
    $missing += 'tasks/ (directory)'
} else {
    $taskFiles = Get-ChildItem -LiteralPath $tasksDir -Filter 'T*.md' -File |
                 Where-Object { $_.Name -notmatch '\.notes\.md$' }
    if ($taskFiles.Count -eq 0) {
        $missing += 'tasks/Tx-*.md (no task files found)'
    }
}

# Optional but recommended
$recommended = @('feature-specification.md', 'draft.md')
$missingRecommended = @()
foreach ($f in $recommended) {
    $p = Join-Path $Path $f
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
        $missingRecommended += $f
    }
}

$taskCount = 0
if (Test-Path -LiteralPath $tasksDir -PathType Container) {
    $taskCount = (Get-ChildItem -LiteralPath $tasksDir -Filter 'T*.md' -File |
                  Where-Object { $_.Name -notmatch '\.notes\.md$' }).Count
}
$ok = ($missing.Count -eq 0)

if ($Json) {
    $summary = if ($ok) { "planning folder valid, $taskCount task file(s)" } else { "missing $($missing.Count) required artifact(s)" }
    [pscustomobject]@{
        ok = $ok; task_count = $taskCount;
        missing_required = $missing; missing_recommended = $missingRecommended; summary = $summary
    } | ConvertTo-Json -Depth 5
    if ($ok) { exit 0 } else { exit 1 }
}

if ($missing.Count -gt 0) {
    Write-Output "INVALID_PLANNING_FOLDER: $Path"
    Write-Output "Missing required artifacts:"
    foreach ($m in $missing) { Write-Output "  - $m" }
    if ($missingRecommended.Count -gt 0) {
        Write-Output "Also missing (recommended):"
        foreach ($m in $missingRecommended) { Write-Output "  - $m" }
    }
    exit 1
}

$warningPart = ''
if ($missingRecommended.Count -gt 0) {
    $warningPart = " (warnings: missing $($missingRecommended -join ', '))"
}

Write-Output "OK: planning folder valid. $taskCount task file(s) found.$warningPart"
exit 0
