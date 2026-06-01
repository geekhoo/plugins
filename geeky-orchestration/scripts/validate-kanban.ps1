# validate-kanban.ps1
# Deterministic integrity check for a geeky-plan kanban.md against the tasks/ folder.
# Mirrors validate-kanban.py exactly (same checks, summary, and exit codes).
#
# Checks (errors fail the run; warnings do not):
#   ERROR   - a task file in tasks/ is not placed in any lane (untracked)
#   ERROR   - a task id appears in more than one lane (ambiguous placement)
#   WARNING - a task id referenced in the kanban has no matching task file (dangling)
#   WARNING - In Progress count exceeds the WIP cap (default 3)
#   WARNING - a known lane heading is entirely missing
#
# Contract: argv in, exit 0 = pass / exit 1 = fail, human summary on stdout.
#   -Json emits a machine-readable object instead of the human summary.
#
# Usage:
#   pwsh -File validate-kanban.ps1 -Path "C:\path\to\docs\feature-folder" [-Wip 3] [-Json]

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path,
    [int]$Wip = 3,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

# Ordered so more specific "In ..." lanes are tested before short names.
$KnownLanes = @('Backlog', 'Ready', 'In Progress', 'In Review', 'Blocked', 'Done')

function Get-LaneForHeading([string]$heading) {
    $norm = $heading.Trim().ToLower()
    if ($norm -match 'validation') { return $null }
    foreach ($lane in $KnownLanes) {
        $l = $lane.ToLower()
        if ($norm -eq $l -or $norm.StartsWith($l)) { return $lane }
    }
    return $null
}

function Write-Result($report) {
    if ($Json) {
        $report | ConvertTo-Json -Depth 6
    } else {
        Write-Output $report.summary
        foreach ($e in $report.errors)   { Write-Output "  ERROR:   $e" }
        foreach ($w in $report.warnings) { Write-Output "  WARNING: $w" }
    }
}

if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
    $msg = "MISSING_FOLDER: $Path"
    if ($Json) { [pscustomobject]@{ ok = $false; errors = @($msg) } | ConvertTo-Json } else { Write-Output $msg }
    exit 1
}

$kanban = Join-Path $Path 'kanban.md'
if (-not (Test-Path -LiteralPath $kanban -PathType Leaf)) {
    $report = [pscustomobject]@{
        ok = $false; errors = @("MISSING: $kanban"); warnings = @();
        lane_counts = @{}; summary = "INVALID_KANBAN: $kanban not found."
    }
    Write-Result $report
    exit 1
}

# Task ids from files: leading T<digits> of each tasks/T*.md (excluding *.notes.md).
$fileIds = New-Object System.Collections.Generic.HashSet[string]
$tasksDir = Join-Path $Path 'tasks'
if (Test-Path -LiteralPath $tasksDir -PathType Container) {
    Get-ChildItem -LiteralPath $tasksDir -Filter 'T*.md' -File |
        Where-Object { $_.Name -notmatch '\.notes\.md$' } |
        ForEach-Object {
            if ($_.Name -match '^(T\d+)') { [void]$fileIds.Add($Matches[1].ToUpper()) }
        }
}

# Parse kanban: lane -> set of task ids; track present lanes.
$placements = @{}
foreach ($lane in $KnownLanes) { $placements[$lane] = New-Object System.Collections.Generic.HashSet[string] }
$present = New-Object System.Collections.Generic.HashSet[string]
$current = $null
foreach ($line in (Get-Content -LiteralPath $kanban)) {
    if ($line -match '^\s{0,3}#{1,6}\s+(.*\S)\s*$') {
        $current = Get-LaneForHeading $Matches[1]
        if ($current) { [void]$present.Add($current) }
        continue
    }
    if ($null -eq $current) { continue }
    foreach ($m in [regex]::Matches($line, '\bT\d+\b', 'IgnoreCase')) {
        [void]$placements[$current].Add($m.Value.ToUpper())
    }
}

# id -> lanes
$idLanes = @{}
foreach ($lane in $KnownLanes) {
    foreach ($tid in $placements[$lane]) {
        if (-not $idLanes.ContainsKey($tid)) { $idLanes[$tid] = @() }
        $idLanes[$tid] += $lane
    }
}

$errors = @()
$warnings = @()

foreach ($tid in ($fileIds | Sort-Object)) {
    if (-not $idLanes.ContainsKey($tid)) {
        $errors += "$tid has a task file but is not placed in any kanban lane"
    }
}
foreach ($tid in ($idLanes.Keys | Sort-Object)) {
    if ($idLanes[$tid].Count -gt 1) {
        $errors += "$tid appears in multiple lanes: $(($idLanes[$tid] | Sort-Object) -join ', ')"
    }
}
foreach ($tid in ($idLanes.Keys | Sort-Object)) {
    if ($fileIds.Count -gt 0 -and -not $fileIds.Contains($tid)) {
        $warnings += "$tid is referenced in the kanban but has no tasks/$tid-*.md file"
    }
}
foreach ($lane in $KnownLanes) {
    if (-not $present.Contains($lane)) {
        $warnings += "lane `"$lane`" heading not found in kanban.md"
    }
}
$inProgress = $placements['In Progress'].Count
if ($inProgress -gt $Wip) {
    $warnings += "In Progress has $inProgress tasks (WIP cap $Wip)"
}

$laneCounts = [ordered]@{}
foreach ($lane in $KnownLanes) { $laneCounts[$lane] = $placements[$lane].Count }
$tracked = ($idLanes.Keys | Sort-Object -Unique).Count
$ok = ($errors.Count -eq 0)
$countStr = (($KnownLanes | ForEach-Object { "$_=$($laneCounts[$_])" }) -join ', ')
$prefix = if ($ok) { 'OK' } else { 'INVALID_KANBAN' }
$summary = "${prefix}: $tracked task(s) tracked, $($fileIds.Count) task file(s). $countStr"

$report = [pscustomobject]@{
    ok = $ok; errors = $errors; warnings = $warnings;
    lane_counts = $laneCounts; summary = $summary
}
Write-Result $report
if ($ok) { exit 0 } else { exit 1 }
