# check-dod.ps1
# Definition-of-Done checker for a single geeky-implement task. Mirrors check-dod.py
# (same checks, summary, exit codes). Embodies "verify, don't trust".
#
# Checks for task <ID> in <folder>:
#   ERROR   - no per-task notes file tasks/<ID>-*.notes.md
#   ERROR   - <ID> not in the Done lane of kanban.md
#   WARNING - handoff.md does not mention <ID>
#   WARNING - <ID> also appears in a non-Done lane
# Also prints the task's Tests/Validation block for the caller to re-run.
#
# Contract: argv in, exit 0 = pass / exit 1 = fail, human summary on stdout.
#   -Json emits a machine-readable object.
#
# Usage:
#   pwsh -File check-dod.ps1 -Path "C:\...\feature" -Task T3 [-Json]

param(
    [Parameter(Position = 0)]
    [string]$Path,
    [Parameter(Position = 1)]
    [string]$Task,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

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

function Get-LanesForTask([string[]]$lines, [string]$taskId) {
    $found = @()
    $current = $null
    $pat = "\b$([regex]::Escape($taskId))\b"
    foreach ($line in $lines) {
        if ($line -match '^\s{0,3}#{1,6}\s+(.*\S)\s*$') {
            $current = Get-LaneForHeading $Matches[1]
            continue
        }
        if ($current -and ([regex]::IsMatch($line, $pat, 'IgnoreCase')) -and ($found -notcontains $current)) {
            $found += $current
        }
    }
    return $found
}

function Get-ValidationBlock([string]$text) {
    $lines = $text -split "`r?`n"
    $start = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ([regex]::IsMatch($lines[$i], 'Tests\s*/\s*Validation', 'IgnoreCase')) { $start = $i + 1; break }
    }
    if ($start -lt 0) { return '' }
    $out = @()
    for ($i = $start; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ([regex]::IsMatch($line, '^\s*[#*\s]*(Estimate|Priority)\b', 'IgnoreCase')) { break }
        if ($line -match '^\s{0,3}#{1,6}\s+\S') { break }
        $out += $line
    }
    return ($out -join "`n").Trim()
}

function Out-Fail([string]$msg) {
    if ($Json) { [pscustomobject]@{ ok = $false; errors = @($msg) } | ConvertTo-Json } else { Write-Output $msg }
}

if (-not $Path -or -not $Task) {
    Write-Output "USAGE: check-dod.ps1 -Path <folder> -Task <ID> [-Json]"
    exit 1
}
$taskId = $Task.ToUpper()

if (-not (Test-Path -LiteralPath $Path -PathType Container)) { Out-Fail "MISSING_FOLDER: $Path"; exit 1 }

$errors = @()
$warnings = @()

# 1. notes file
$tasksDir = Join-Path $Path 'tasks'
$notes = @()
if (Test-Path -LiteralPath $tasksDir -PathType Container) {
    $notes = @(Get-ChildItem -LiteralPath $tasksDir -File |
               Where-Object { $_.Name -match "^$([regex]::Escape($taskId))\b" -and $_.Name -match '\.notes\.md$' })
}
if ($notes.Count -eq 0) { $errors += "no per-task notes file tasks/$taskId-*.notes.md" }

# 2/4. kanban placement
$kanban = Join-Path $Path 'kanban.md'
$lanes = @()
if (-not (Test-Path -LiteralPath $kanban -PathType Leaf)) {
    $errors += "kanban.md not found"
} else {
    $lanes = @(Get-LanesForTask (Get-Content -LiteralPath $kanban) $taskId)
    if ($lanes -notcontains 'Done') {
        $where = if ($lanes.Count) { $lanes -join ', ' } else { 'no lane' }
        $errors += "$taskId is not in the Done lane (found in: $where)"
    }
    $nonDone = @($lanes | Where-Object { $_ -ne 'Done' })
    if ($nonDone.Count -gt 0) { $warnings += "$taskId also appears in: $($nonDone -join ', ')" }
}

# 3. handoff mention
$handoff = Join-Path $Path 'handoff.md'
if (-not (Test-Path -LiteralPath $handoff -PathType Leaf)) {
    $warnings += "handoff.md not found"
} elseif (-not [regex]::IsMatch((Get-Content -LiteralPath $handoff -Raw), "\b$([regex]::Escape($taskId))\b", 'IgnoreCase')) {
    $warnings += "handoff.md does not mention $taskId"
}

# validation block (informational)
$validation = ''
if (Test-Path -LiteralPath $tasksDir -PathType Container) {
    $taskFile = Get-ChildItem -LiteralPath $tasksDir -Filter 'T*.md' -File |
                Where-Object { $_.Name -match "^$([regex]::Escape($taskId))\b" -and $_.Name -notmatch '\.notes\.md$' } |
                Select-Object -First 1
    if ($taskFile) { $validation = Get-ValidationBlock (Get-Content -LiteralPath $taskFile.FullName -Raw) }
}

$ok = ($errors.Count -eq 0)
$summary = if ($ok) { "DOD_OK: $taskId" } else { "DOD_INCOMPLETE: $taskId" }

if ($Json) {
    [pscustomobject]@{
        ok = $ok; task = $taskId; errors = $errors; warnings = $warnings;
        lanes = $lanes; validation_block = $validation
    } | ConvertTo-Json -Depth 6
} else {
    Write-Output $summary
    foreach ($e in $errors)   { Write-Output "  ERROR:   $e" }
    foreach ($w in $warnings) { Write-Output "  WARNING: $w" }
    if ($validation) {
        Write-Output "  Re-run this task's validation block (verify, don't trust):"
        foreach ($line in ($validation -split "`n")) { Write-Output "    | $line" }
    }
}

if ($ok) { exit 0 } else { exit 1 }
