<#
.SYNOPSIS
Load this machine's evaluation environment, or run the model-free Windows MXC preflight.
.EXAMPLE
. C:\repos\.eval-tools\windows-eval.ps1
.EXAMPLE
& C:\repos\.eval-tools\windows-eval.ps1 -Preflight
#>
[CmdletBinding()]
param(
    [string]$EnvironmentFile = 'C:\Users\gerald.khoo\env.cloud.claude',
    [string]$Repository = 'C:\Users\gerald.khoo\geekhoo-plugins',
    [ValidateSet('c0-wordstat','c1-csvledger','c2-linkvault','c3-minisql')]
    [string[]]$Case = @('c0-wordstat'),
    [ValidateSet('claude-code','codex')]
    [string[]]$Harness = @('claude-code','codex'),
    [switch]$Preflight
)
$ErrorActionPreference = 'Stop'
if (-not $IsWindows) { throw 'This launcher requires PowerShell 7 on Windows.' }
$loadedNames = @()
foreach ($entryLine in [IO.File]::ReadAllLines($EnvironmentFile)) {
    $entryText = $entryLine.Trim()
    if (-not $entryText -or $entryText.StartsWith('#')) { continue }
    if ($entryText -notmatch '^(?:export\s+|\$env:)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        throw 'Unsupported environment-file syntax. Values were not displayed.'
    }
    $entryName = $Matches[1]
    $entryValue = $Matches[2].Trim().TrimEnd(';').Trim()
    if ($entryValue.Length -ge 2 -and
        (($entryValue.StartsWith('"') -and $entryValue.EndsWith('"')) -or
         ($entryValue.StartsWith("'") -and $entryValue.EndsWith("'")))) {
        $entryValue = $entryValue.Substring(1, $entryValue.Length - 2)
    }
    [Environment]::SetEnvironmentVariable($entryName, $entryValue, 'Process')
    $loadedNames += $entryName
}
# The runner owns authentication, trace identity and tags; avoid host overrides.
foreach ($overrideName in @('ANTHROPIC_AUTH_TOKEN','CLAUDE_CODE_OAUTH_TOKEN',
    'LANGFUSE_CODEX_TAGS','LANGFUSE_CODEX_USER_ID')) {
    [Environment]::SetEnvironmentVariable($overrideName, $null, 'Process')
}
$env:TRACE_TO_LANGFUSE = 'true'
$env:GEEKY_EVAL_LANGFUSE_ENVIRONMENT = 'mxc'
$env:LANGFUSE_TRACING_ENVIRONMENT = 'mxc'
$env:MXC_SANDBOX_HOME = 'C:\repos\.eval-tools\windows-mxc'
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = 'C:\Program Files\PowerShell\7;' + $env:PATH
foreach ($requiredName in @('LITELLM_PROXY_URL','LITELLM_PROXY_API_KEY',
    'LANGFUSE_BASE_URL','LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY')) {
    if (-not [Environment]::GetEnvironmentVariable($requiredName)) {
        throw "Missing required variable: $requiredName"
    }
}
Write-Host "Loaded $($loadedNames.Count) environment entries for Windows MXC; no credential values displayed."
if ($Preflight) {
    $preflightStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
    $preflightOutput = "C:\repos\.eval-tools\windows-setup\preflight-$preflightStamp"
    # Preserve workspaces: no cleanup or recursive deletion is performed by the matrix.
    Push-Location (Join-Path $Repository 'geeky-orchestration')
    try {
        & (Join-Path $Repository 'geeky-orchestration\evals\scripts\run-mock-matrix.ps1') `
            -Case $Case -Harness $Harness -ToolsDir 'C:\repos\.eval-tools' `
            -WorkRoot 'C:\repos' -OutDir $preflightOutput -KeepWorkspaces
    } finally { Pop-Location }
}
