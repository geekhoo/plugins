# check-dod.ps1
# Definition-of-Done checker for a single geeky-implement task. Mirrors check-dod.py
# (same checks, summary, exit codes). Embodies "verify, don't trust".
#
# Lifecycle: move the task to In Review -> run validation + this gate -> move to Done
# only on success. Both 'In Review' and 'Done' are accepted placements: 'In Review' is
# the normal pre-Done state this gate runs from, and 'Done' stays acceptable so
# re-running the gate after the move is not an error.
#
# Checks for task <ID> in <folder>:
#   ERROR   - no per-task notes file tasks/<ID>-*.notes.md
#   ERROR   - <ID> not in the In Review or Done lane of kanban.md
#   WARNING - handoff.md does not mention <ID>
#   WARNING - <ID> also appears in another lane
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
# Lanes from which the DoD gate may legitimately pass. 'In Review' is the state the
# gate is run from; 'Done' keeps a post-move re-run from failing.
$AcceptedLanes = @('In Review', 'Done')

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
    # Lane placement (keep in sync with validate-kanban.* and the guard): only a
    # markdown list item whose LEADING token is the id places the task. A trailing
    # cross-reference ("- T1 (unblocks T4)") or an HTML comment merely mentions it.
    $found = @()
    $current = $null
    $want = $taskId.ToUpper()
    $placementPattern = '^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s*)?[*_`~]*\s*(T\d+)\b'
    $stripped = [regex]::Replace(($lines -join "`n"), '<!--.*?-->', '', 'Singleline')
    foreach ($line in ($stripped -split "`r?`n")) {
        if ($line -match '^\s{0,3}#{1,6}\s+(.*\S)\s*$') {
            $current = Get-LaneForHeading $Matches[1]
            continue
        }
        if (-not $current) { continue }
        $pm = [regex]::Match($line, $placementPattern, 'IgnoreCase')
        if ($pm.Success -and ($pm.Groups[1].Value.ToUpper() -eq $want) -and ($found -notcontains $current)) {
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

# --- JSON emitters -------------------------------------------------------
# Hand-built to match Python's json.dumps() byte-for-byte (ensure_ascii=True,
# separators ', ' / ': ', indent=2 for the report). ConvertTo-Json differs in
# whitespace and escaping, which would break the declared .py/.ps1 parity.
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

function ConvertTo-PyJsonArray($items) {
    $arr = @($items)
    if ($arr.Count -eq 0) { return '[]' }
    $parts = @()
    foreach ($i in $arr) { $parts += ('    ' + (ConvertTo-PyJsonString ([string]$i))) }
    return "[`n" + ($parts -join ",`n") + "`n  ]"
}

function Out-Fail([string]$msg) {
    if ($Json) {
        Write-Output ('{"ok": false, "errors": [' + (ConvertTo-PyJsonString $msg) + ']}')
    } else {
        Write-Output $msg
    }
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
    $accepted = @($lanes | Where-Object { $AcceptedLanes -contains $_ })
    if ($accepted.Count -eq 0) {
        $where = if ($lanes.Count) { $lanes -join ', ' } else { 'no lane' }
        $errors += "$taskId is not in the In Review or Done lane (found in: $where)"
    }
    $extra = @($lanes | Where-Object { $AcceptedLanes -notcontains $_ })
    if ($extra.Count -gt 0) { $warnings += "$taskId also appears in: $($extra -join ', ')" }
    if (($lanes -contains 'In Review') -and ($lanes -contains 'Done')) {
        $warnings += "$taskId appears in both In Review and Done"
    }
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
    $okLit = if ($ok) { 'true' } else { 'false' }
    # NOTE: every element is parenthesized. PowerShell's comma operator binds
    # tighter than '+', so an unparenthesized "'a' + $x + ','," inside @(...)
    # builds nested arrays instead of one concatenated string.
    $lines = @(
        '{'
        ('  "ok": ' + $okLit + ',')
        ('  "task": ' + (ConvertTo-PyJsonString $taskId) + ',')
        ('  "errors": ' + (ConvertTo-PyJsonArray $errors) + ',')
        ('  "warnings": ' + (ConvertTo-PyJsonArray $warnings) + ',')
        ('  "lanes": ' + (ConvertTo-PyJsonArray $lanes) + ',')
        ('  "validation_block": ' + (ConvertTo-PyJsonString $validation) + ',')
        ('  "accepted_lanes": ' + (ConvertTo-PyJsonArray $AcceptedLanes))
        '}'
    )
    # Python writes "\n" and the runtime translates it to the platform newline;
    # PowerShell does not translate, so do it explicitly to keep stdout identical.
    Write-Output (($lines -join "`n").Replace("`n", [Environment]::NewLine))
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
