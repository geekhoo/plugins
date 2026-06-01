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

if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
    if ($Json) { [pscustomobject]@{ ok = $false; errors = @("MISSING_FOLDER: $Path") } | ConvertTo-Json } else { Write-Output "MISSING_FOLDER: $Path" }
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
