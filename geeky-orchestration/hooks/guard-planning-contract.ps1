# guard-planning-contract.ps1
# PreToolUse-style guard for Edit/Write/NotebookEdit. Mirrors guard-planning-contract.py.
# Reads tool-call JSON from stdin. If file_path points at a frozen geeky-plan
# artifact, surfaces a message through a PORTABLE channel (stdout + stderr).
#
# Frozen patterns (inside a planning folder under docs/<feature>/):
#   - implementation-plan.md, feature-specification.md, draft.md, references.md
#   - tasks/Tx-*.md           (but NOT tasks/Tx-*.notes.md — those are writable)
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

$ErrorActionPreference = 'SilentlyContinue'

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }
    $payload = $raw | ConvertFrom-Json -ErrorAction Stop
} catch {
    exit 0
}

$tool = $payload.tool_name
if (-not $tool) { $tool = $payload.tool }
if (-not $tool) { exit 0 }

$filePath = $null
if ($payload.tool_input) { $filePath = $payload.tool_input.file_path }
if (-not $filePath -and $payload.input) { $filePath = $payload.input.file_path }
if (-not $filePath -and $payload.tool_input) { $filePath = $payload.tool_input.notebook_path }
if (-not $filePath) { exit 0 }

$normalized = $filePath -replace '\\', '/'
$leaf = ($normalized -split '/')[-1]

$frozenLeaves = @('implementation-plan.md', 'feature-specification.md', 'draft.md', 'references.md')

$reason = $null
if ($frozenLeaves -contains $leaf) {
    $reason = "is a frozen geeky-plan planning artifact"
} elseif ($normalized -match '/tasks/T[^/]+\.md$' -and $normalized -notmatch '\.notes\.md$') {
    $reason = "is a frozen task file (per-task notes belong in tasks/Tx-*.notes.md instead)"
}

if (-not $reason) { exit 0 }

$msg = "[geeky-orchestration] $filePath $reason. " +
       "Planning artifacts are the frozen contract between geeky-plan and geeky-implement. " +
       "If the plan is genuinely wrong, surface it via kanban Blocked + handoff.md rather than " +
       "editing the contract mid-run."

if ($Mode -eq 'block') {
    if ($ExitCode) {
        [Console]::Error.WriteLine($msg)
        exit 2
    }
    $decision = [pscustomobject]@{
        hookSpecificOutput = [pscustomobject]@{
            hookEventName = 'PreToolUse'
            permissionDecision = 'deny'
            permissionDecisionReason = $msg
        }
    }
    [Console]::Out.WriteLine(($decision | ConvertTo-Json -Compress -Depth 5))
    exit 0
}

# warn (default)
[Console]::Out.WriteLine($msg)
[Console]::Error.WriteLine($msg)
exit 0
