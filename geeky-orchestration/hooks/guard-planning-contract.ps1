# guard-planning-contract.ps1
# PreToolUse hook for Edit/Write/NotebookEdit.
# Reads tool input JSON from stdin. If file_path points at a frozen geeky-plan
# artifact, emits a warning to stderr but does NOT block the tool call.
#
# Frozen patterns (inside a planning folder under docs/<feature>/):
#   - implementation-plan.md
#   - feature-specification.md
#   - draft.md
#   - references.md
#   - tasks/Tx-*.md           (but NOT tasks/Tx-*.notes.md — those are writable)
#
# Exit codes:
#   0  -> allow (with or without warning printed to stderr)
#   1  -> non-blocking error from hook itself (still allows tool call)
#   2  -> block (we never use this — guard is warn-only by design)

$ErrorActionPreference = 'SilentlyContinue'

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }

    $payload = $raw | ConvertFrom-Json -ErrorAction Stop
} catch {
    # Malformed input — don't block, just exit clean.
    exit 0
}

# Possible shapes:
#   { tool_name: "Edit", tool_input: { file_path: "..." } }
#   { tool: "Edit", input: { file_path: "..." } }
$tool = $payload.tool_name
if (-not $tool) { $tool = $payload.tool }
if (-not $tool) { exit 0 }

$filePath = $null
if ($payload.tool_input) { $filePath = $payload.tool_input.file_path }
if (-not $filePath -and $payload.input) { $filePath = $payload.input.file_path }
if (-not $filePath -and $payload.tool_input) { $filePath = $payload.tool_input.notebook_path }
if (-not $filePath) { exit 0 }

# Normalize path separators
$normalized = $filePath -replace '\\', '/'
$leaf = ($normalized -split '/')[-1]

$frozenLeaves = @(
    'implementation-plan.md',
    'feature-specification.md',
    'draft.md',
    'references.md'
)

$isFrozen = $false
$reason = ''

if ($frozenLeaves -contains $leaf) {
    $isFrozen = $true
    $reason = "is a frozen geeky-plan planning artifact"
}

# tasks/Tx-*.md (but not tasks/Tx-*.notes.md)
if (-not $isFrozen) {
    if ($normalized -match '/tasks/T[^/]+\.md$' -and $normalized -notmatch '\.notes\.md$') {
        $isFrozen = $true
        $reason = "is a frozen task file (per-task notes belong in tasks/Tx-*.notes.md instead)"
    }
}

if ($isFrozen) {
    [Console]::Error.WriteLine("")
    [Console]::Error.WriteLine("[geeky-orchestration] WARNING: $filePath $reason.")
    [Console]::Error.WriteLine("[geeky-orchestration] Planning artifacts are the contract between /geeky-plan and /geeky-implement.")
    [Console]::Error.WriteLine("[geeky-orchestration] If the plan is genuinely wrong, surface the issue via kanban Blocked + handoff.md")
    [Console]::Error.WriteLine("[geeky-orchestration] rather than editing the contract mid-run. Tool call WILL proceed (warn-only).")
    [Console]::Error.WriteLine("")
}

exit 0
