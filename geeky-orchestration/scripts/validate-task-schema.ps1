# validate-task-schema.ps1
# Validate that geeky-plan task files (tasks/Tx-*.md) carry the required template
# sections. Mirrors validate-task-schema.py (same checks, summary, exit codes).
#
# Required (missing => ERROR): Task Name, In scope, Dependencies,
#   Acceptance Criteria, Tests/Validation, Priority
# Recommended (missing => WARNING): Context, Module/System, Technical Notes,
#   Definition of Done, Estimate
#
# Contract: argv in, exit 0 = pass / exit 1 = fail, human summary on stdout.
#   -Json emits a machine-readable object.
#
# Usage:
#   pwsh -File validate-task-schema.ps1 -Path "C:\...\feature-folder" [-Json]
#   pwsh -File validate-task-schema.ps1 -File "C:\...\tasks\T1-foo.md"

param(
    [Parameter(Position = 0)]
    [string]$Path,
    [string]$File,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$Required = @(
    @{ name = 'Task Name';          pat = 'Task\s*Name' },
    @{ name = 'In scope';           pat = 'In\s*scope' },
    @{ name = 'Dependencies';       pat = 'Dependencies' },
    @{ name = 'Acceptance Criteria'; pat = 'Acceptance\s*Criteria' },
    @{ name = 'Tests/Validation';   pat = 'Tests\s*/\s*Validation' },
    @{ name = 'Priority';           pat = 'Priority' }
)
$Recommended = @(
    @{ name = 'Context';            pat = 'Context' },
    @{ name = 'Module/System';      pat = 'Module\s*/\s*System' },
    @{ name = 'Technical Notes';    pat = 'Technical\s*Notes' },
    @{ name = 'Definition of Done'; pat = 'Definition\s+of\s+Done' },
    @{ name = 'Estimate';           pat = 'Estimate' }
)

function Test-Label([string]$text, [string]$pattern) {
    return [regex]::IsMatch($text, "(?im)^\s*[#*\s]*$pattern\b")
}

function Test-TaskFile([System.IO.FileInfo]$f) {
    $text = Get-Content -LiteralPath $f.FullName -Raw
    $missingReq = @()
    foreach ($r in $Required)    { if (-not (Test-Label $text $r.pat)) { $missingReq += $r.name } }
    $missingRec = @()
    foreach ($r in $Recommended) { if (-not (Test-Label $text $r.pat)) { $missingRec += $r.name } }
    return [pscustomobject]@{
        file = $f.Name; ok = ($missingReq.Count -eq 0)
        missing_required = $missingReq; missing_recommended = $missingRec
    }
}

function Out-Fail([string]$msg) {
    if ($Json) { [pscustomobject]@{ ok = $false; errors = @($msg) } | ConvertTo-Json } else { Write-Output $msg }
}

$files = @()
if ($File) {
    $files = @(Get-Item -LiteralPath $File -ErrorAction SilentlyContinue)
    if (-not $files -or -not $files[0]) { Out-Fail "MISSING_FILE: $File"; exit 1 }
} else {
    if (-not $Path) {
        Write-Output "USAGE: validate-task-schema.ps1 (-Path <folder> | -File <task.md>) [-Json]"
        exit 1
    }
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { Out-Fail "MISSING_FOLDER: $Path"; exit 1 }
    $tasksDir = Join-Path $Path 'tasks'
    if (Test-Path -LiteralPath $tasksDir -PathType Container) {
        $files = @(Get-ChildItem -LiteralPath $tasksDir -Filter 'T*.md' -File |
                   Where-Object { $_.Name -notmatch '\.notes\.md$' } | Sort-Object Name)
    }
}

if (-not $files -or $files.Count -eq 0) {
    Out-Fail "NO_TASK_FILES: nothing to validate (expected tasks/Tx-*.md)"
    exit 1
}

$results = @()
foreach ($f in $files) { $results += (Test-TaskFile $f) }

$ok = -not ($results | Where-Object { -not $_.ok })
$failed = ($results | Where-Object { -not $_.ok }).Count

if ($Json) {
    [pscustomobject]@{ ok = [bool]$ok; results = $results } | ConvertTo-Json -Depth 6
} else {
    $prefix = if ($ok) { 'OK' } else { 'INVALID_TASK_SCHEMA' }
    Write-Output "${prefix}: $($results.Count) task file(s) checked, $failed failing."
    foreach ($r in $results) {
        if ($r.missing_required.Count -gt 0) {
            Write-Output "  $($r.file):"
            foreach ($m in $r.missing_required) { Write-Output "    ERROR:   missing required section: $m" }
        }
        foreach ($m in $r.missing_recommended) { Write-Output "    WARNING: $($r.file) missing recommended section: $m" }
    }
}

if ($ok) { exit 0 } else { exit 1 }
