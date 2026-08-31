# guard-planning-contract.ps1
# PreToolUse-style guard for Edit/Write/NotebookEdit. Mirrors guard-planning-contract.py
# byte-for-byte on stdout and exit code (declared parity contract in geeky.manifest.json).
# Reads tool-call JSON from stdin. If file_path points at a frozen geeky-plan
# artifact AND the planning package is past its freeze point, surfaces a message
# through a PORTABLE channel (stdout + stderr).
#
# Frozen patterns (inside a planning folder under docs/<feature>/):
#   - implementation-plan.md, feature-specification.md, draft.md, references.md
#   - tasks/Tx-*.md           (but NOT tasks/Tx-*.notes.md -- those are writable)
#
# Path handling: file_path is normalized lexically (separators collapsed to "/",
# "./" segments dropped, duplicate/trailing separators removed) before matching, so
# relative POSIX, absolute POSIX, Windows backslash, mixed, UNC and Git-Bash/MSYS
# (/c/Users/...) forms all match identically. The filesystem is never consulted for
# matching -- the target may not exist yet.
#
# Stage awareness: the freeze starts when the first task leaves the Backlog lane.
# The guard infers the planning folder from the edited path, reads kanban.md, and
# stays SILENT for a pre-freeze package. If kanban.md cannot be located the package
# cannot be proven pre-freeze, so the guard defaults to protective behavior and says
# so. Override the pre-freeze lane set with $env:GEEKY_PREFREEZE_LANES (comma
# separated, default 'Backlog').
#
# Fail-closed: a payload the guard cannot interpret (unreadable/empty stdin, invalid
# JSON, no tool_name, or no file_path on a guarded tool) is NOT treated as "fine".
# In block mode it denies; in warn mode it emits a visible warning. A payload that is
# simply not a protected operation still exits 0 silently.
#
# Modes (default warn) via -Mode or $env:GEEKY_GUARD_MODE:
#   warn   -> advisory. Writes the message to stdout (context channel) and stderr; exit 0.
#   block  -> emits Claude/Codex-style deny JSON on stdout; exit 0 (host parses & blocks).
#             Pass -ExitCode to return exit 2 instead (for exit-code-only frameworks).
#
# Exit codes:
#   0 -> normal (warn, or block-via-JSON)
#   2 -> hard block via exit code (only with -ExitCode in block mode)

param(
    [ValidateSet('warn', 'block')]
    [string]$Mode = $(if ($env:GEEKY_GUARD_MODE) { $env:GEEKY_GUARD_MODE } else { 'warn' }),
    [switch]$ExitCode
)

$ErrorActionPreference = 'Stop'

$FrozenLeaves = @('implementation-plan.md', 'feature-specification.md', 'draft.md', 'references.md')

# Tools whose payloads are expected to carry a file_path. Any other tool is not a
# protected operation and exits 0 silently.
$GuardedTools = @('edit', 'write', 'multiedit', 'notebookedit', 'notebook_edit')

# Lane vocabulary duplicated from scripts/check-dod.ps1 (KnownLanes /
# Get-LaneForHeading). Deliberately duplicated rather than dot-sourced: this hook
# must run standalone from any cwd and stay byte-identical to its Python twin.
# Keep the two in sync.
$KnownLanes = @('Backlog', 'Ready', 'In Progress', 'In Review', 'Blocked', 'Done')

$Tail = 'Planning artifacts are the frozen contract between geeky-plan and ' +
        'geeky-implement. If the plan is genuinely wrong, surface it via kanban ' +
        'Blocked + handoff.md rather than editing the contract mid-run.'

function Get-MalformedMessage([string]$detail) {
    return "[geeky-orchestration] guard could not interpret the hook payload " +
           "($detail). Failing closed: the guard cannot prove this edit is safe, " +
           "so it is treated as an edit to a frozen planning artifact. " + $Tail
}

# Matches Python json.dumps() escaping exactly (ensure_ascii=True).
function ConvertTo-JsonStringLiteral([string]$s) {
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

function Invoke-Emit([string]$msg) {
    if ($Mode -eq 'block') {
        if ($ExitCode) {
            [Console]::Error.WriteLine($msg)
            exit 2
        }
        $reason = ConvertTo-JsonStringLiteral $msg
        $json = '{"hookSpecificOutput": {"hookEventName": "PreToolUse", ' +
                '"permissionDecision": "deny", "permissionDecisionReason": ' + $reason + '}}'
        [Console]::Out.WriteLine($json)
        exit 0
    }
    [Console]::Out.WriteLine($msg)
    [Console]::Error.WriteLine($msg)
    exit 0
}

function Get-NormalizedPath([string]$path) {
    $s = $path.Trim().Trim('"').Trim("'") -replace '\\', '/'
    $s = $s -replace '/+', '/'
    $s = [regex]::Replace($s, '(?:^|(?<=/))\./', '')
    if ($s.Length -gt 1) { $s = $s.TrimEnd('/') }
    return $s
}

function Get-FrozenReason([string]$normalized) {
    $leaf = ($normalized -split '/')[-1].ToLower()
    if ($FrozenLeaves -contains $leaf) {
        return 'is a frozen geeky-plan planning artifact'
    }
    if ($normalized -match '(^|/)tasks/T[^/]+\.md$' -and $normalized -notmatch '\.notes\.md$') {
        return 'is a frozen task file (per-task notes belong in tasks/Tx-*.notes.md instead)'
    }
    return $null
}

function Get-PlanningFolder([string]$normalized) {
    $m = [regex]::Match($normalized, '(^|/)tasks/[^/]+$', 'IgnoreCase')
    if ($m.Success) {
        $head = if ($m.Index -gt 0) { $normalized.Substring(0, $m.Index) } else { '' }
        if ($head) { return $head } else { return '.' }
    }
    if ($normalized.Contains('/')) {
        $head = $normalized.Substring(0, $normalized.LastIndexOf('/'))
        if ($head) { return $head } else { return '/' }
    }
    return '.'
}

function Get-FsPath([string]$candidate, [string]$base) {
    $s = $candidate -replace '\\', '/'
    $onWindows = if ($null -ne $IsWindows) { $IsWindows } else { $true }
    if ($onWindows) {
        $m = [regex]::Match($s, '^/([A-Za-z])(/.*)?$')
        if ($m.Success) {
            $rest = if ($m.Groups[2].Success) { $m.Groups[2].Value } else { '/' }
            $s = $m.Groups[1].Value.ToUpper() + ':' + $rest
        }
    }
    if ([System.IO.Path]::IsPathRooted($s)) { return $s }
    return (Join-Path $base $s)
}

function Find-Kanban([string]$folder) {
    $cur = $folder
    for ($i = 0; $i -lt 2; $i++) {
        $k = Join-Path $cur 'kanban.md'
        try {
            if (Test-Path -LiteralPath $k -PathType Leaf) { return (Get-Item -LiteralPath $k).FullName }
        } catch { return $null }
        $parent = [System.IO.Path]::GetDirectoryName($cur)
        if (-not $parent -or $parent -eq $cur) { break }
        $cur = $parent
    }
    return $null
}

function Get-PrefreezeLanes() {
    $raw = if ($env:GEEKY_PREFREEZE_LANES) { $env:GEEKY_PREFREEZE_LANES } else { 'Backlog' }
    $out = @()
    foreach ($p in ($raw -split ',')) {
        $t = $p.Trim().ToLower()
        if ($t) { $out += $t }
    }
    return $out
}

function Get-LaneForHeading([string]$heading) {
    # Mirrors scripts/check-dod.ps1::Get-LaneForHeading -- keep in sync.
    $norm = $heading.Trim().ToLower()
    if ($norm -match 'validation') { return $null }
    foreach ($lane in $KnownLanes) {
        $l = $lane.ToLower()
        if ($norm -eq $l -or $norm.StartsWith($l)) { return $lane }
    }
    return $null
}

function Test-PackageFrozen([string]$kanbanText) {
    $pre = Get-PrefreezeLanes
    $current = $null
    # Lane placement (keep in sync with scripts/validate-kanban.* and check-dod.*):
    # only a markdown list item whose LEADING token is a task id counts as a
    # promotion. Comments are stripped so a note like
    # "<!-- none yet; T1 will go here first -->" cannot falsely freeze a package.
    $stripped = [regex]::Replace($kanbanText, '<!--.*?-->', '', 'Singleline')
    $placementPattern = '^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s*)?[*_`~]*\s*(T\d+)\b'
    foreach ($line in ($stripped -split "`r?`n")) {
        if ($line -match '^\s{0,3}#{1,6}\s+(.*\S)\s*$') {
            $current = Get-LaneForHeading $Matches[1]
            continue
        }
        if ($current -and ($pre -notcontains $current.ToLower()) -and
            ([regex]::IsMatch($line, $placementPattern, 'IgnoreCase'))) {
            return $true
        }
    }
    return $false
}

function Get-StageNote([string]$normalized, [string]$base) {
    # Returns $null when the package is pre-freeze (stay silent).
    # The note names the inferred planning folder in its NORMALIZED (lexical, '/')
    # form rather than a resolved filesystem path, so the message is identical to
    # the Python twin regardless of platform path canonicalization.
    $folderRel = Get-PlanningFolder $normalized
    $kanban = Find-Kanban (Get-FsPath $folderRel $base)
    if (-not $kanban) {
        return "No kanban.md was found for $folderRel, so this package " +
               'cannot be proven pre-freeze and is treated as frozen.'
    }
    try {
        $text = Get-Content -LiteralPath $kanban -Raw -Encoding UTF8
    } catch {
        return "kanban.md for $folderRel could not be read, so this package " +
               'cannot be proven pre-freeze and is treated as frozen.'
    }
    if ($null -eq $text) { $text = '' }
    if (Test-PackageFrozen $text) {
        return "kanban.md for $folderRel shows at least one task past the " +
               'Backlog lane, so this package is frozen.'
    }
    return $null
}

# ---------------------------------------------------------------- main

$raw = $null
try {
    $raw = [Console]::In.ReadToEnd()
} catch {
    Invoke-Emit (Get-MalformedMessage 'stdin could not be read')
}
if (-not $raw -or -not $raw.Trim()) {
    Invoke-Emit (Get-MalformedMessage 'stdin was empty')
}

$payload = $null
try {
    $payload = $raw | ConvertFrom-Json -ErrorAction Stop
} catch {
    Invoke-Emit (Get-MalformedMessage 'stdin was not valid JSON')
}
if ($null -eq $payload -or $payload -isnot [System.Management.Automation.PSCustomObject]) {
    Invoke-Emit (Get-MalformedMessage 'payload was not a JSON object')
}

$tool = $payload.tool_name
if (-not $tool) { $tool = $payload.tool }
if (-not $tool -or $tool -isnot [string]) {
    Invoke-Emit (Get-MalformedMessage 'payload carried no tool_name')
}

if ($GuardedTools -notcontains $tool.Trim().ToLower()) { exit 0 }

$toolInput = $payload.tool_input
if (-not $toolInput) { $toolInput = $payload.input }

$filePath = $null
if ($toolInput) {
    $filePath = $toolInput.file_path
    if (-not $filePath) { $filePath = $toolInput.notebook_path }
}
if (-not $filePath -or $filePath -isnot [string]) {
    Invoke-Emit (Get-MalformedMessage "$tool payload carried no file_path")
}

$normalized = Get-NormalizedPath $filePath
$reason = Get-FrozenReason $normalized
if (-not $reason) { exit 0 }

$base = $payload.cwd
if (-not $base) { $base = $payload.workspace }
if (-not $base -or $base -isnot [string]) { $base = (Get-Location).Path }

$note = Get-StageNote $normalized $base
if (-not $note) { exit 0 }

Invoke-Emit "[geeky-orchestration] $filePath $reason. $note $Tail"
