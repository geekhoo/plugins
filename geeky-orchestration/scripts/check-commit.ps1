# check-commit.ps1
# Validate a commit message against the geeky-implement format. Mirrors check-commit.py.
#
# Rules (violations => ERROR, exit 1):
#   - subject matches  type(scope)!: summary  (Conventional Commits)
#     type in feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert
#   - subject length <= 72 chars
#   - a task reference exists: "Tasks: T<n>" line (error if none; warn if only a bare T<n>)
#     unless a docs commit has a case-insensitive "Tasks: none" line
#   - a "Tasks: none" line is an error for every type other than docs
#
# Message source (first provided): positional FILE (git commit-msg), -Message, or stdin.
#
# Contract: exit 0 = pass / exit 1 = fail, human summary on stdout. -Json optional.
#
# Usage:
#   pwsh -File check-commit.ps1 .git/COMMIT_EDITMSG
#   pwsh -File check-commit.ps1 -Message "feat(plan): add linter`n`nTasks: T3"
#   $msg | pwsh -File check-commit.ps1 -Json

param(
    [Parameter(Position = 0)]
    [string]$File,
    [string]$Message,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$Types = 'feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert'
$SubjectPattern = "^(?<type>$Types)(?:\([^)]+\))?!?: .+"
$MaxSubject = 72

function Out-Fail([string]$msg) {
    if ($Json) { [pscustomobject]@{ ok = $false; errors = @($msg) } | ConvertTo-Json } else { Write-Output $msg }
}

# Resolve message source.
$msgText = $null
if ($PSBoundParameters.ContainsKey('Message')) {
    $msgText = $Message
} elseif ($File) {
    if (-not (Test-Path -LiteralPath $File -PathType Leaf)) { Out-Fail "NO_MESSAGE: file not found: $File"; exit 1 }
    $msgText = Get-Content -LiteralPath $File -Raw
} else {
    $msgText = [Console]::In.ReadToEnd()
}

if ([string]::IsNullOrEmpty($msgText)) {
    Out-Fail "NO_MESSAGE: provide a file path, -Message, or pipe via stdin"
    exit 1
}

$lines = @($msgText -split "`r?`n" | Where-Object { -not ($_.TrimStart().StartsWith('#')) })
$subject = ($lines | Where-Object { $_.Trim() } | Select-Object -First 1)
if ($null -eq $subject) { $subject = '' }
$body = ($lines -join "`n")

$errors = @()
$warnings = @()

$subjectMatch = [regex]::Match($subject, $SubjectPattern)
if (-not $subjectMatch.Success) {
    $errors += "subject is not Conventional Commits `"type(scope): summary`": '$subject'"
}
if ($subject.Length -gt $MaxSubject) {
    $errors += "subject exceeds $MaxSubject chars ($($subject.Length))"
}

if ([regex]::IsMatch($body, '^\s*Tasks:\s*none\b', 'IgnoreCase,Multiline')) {
    if (-not $subjectMatch.Success -or $subjectMatch.Groups['type'].Value -ne 'docs') {
        $errors += 'Tasks: none is allowed only for docs commits'
    }
} elseif ([regex]::IsMatch($body, '^\s*Tasks:\s*.*\bT\d+\b', 'IgnoreCase,Multiline')) {
    # ok
} elseif ([regex]::IsMatch($body, '\bT\d+\b')) {
    $warnings += 'task referenced but no "Tasks: T<n>" line (recommended)'
} else {
    $errors += "no task reference (expected a Tasks: line with T<n>)"
}

$ok = ($errors.Count -eq 0)

if ($Json) {
    [pscustomobject]@{ ok = $ok; subject = $subject; errors = $errors; warnings = $warnings } | ConvertTo-Json -Depth 5
} else {
    if ($ok) { Write-Output "OK: commit message valid." } else { Write-Output "INVALID_COMMIT_MESSAGE:" }
    foreach ($e in $errors)   { Write-Output "  ERROR:   $e" }
    foreach ($w in $warnings) { Write-Output "  WARNING: $w" }
}

if ($ok) { exit 0 } else { exit 1 }
