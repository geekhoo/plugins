<#
.SYNOPSIS
  One-time host setup for Langfuse telemetry in MXC eval runs (Windows, Linux, macOS).

.DESCRIPTION
  Installs the pinned Langfuse hooks from pins.json under <ToolsDir>/langfuse, verifying each
  download's SHA-256, and builds <ToolsDir>/langfuse-py (a uv venv with the pinned langfuse
  Python SDK) for the Claude hook. The runners grant <ToolsDir> read-only to the sandbox.

    <ToolsDir>/langfuse/claude-hook/<commit>/langfuse_hook.py   Claude Code Stop/SessionEnd hook
    <ToolsDir>/langfuse/codex-tracing/<version>/dist/index.mjs  Codex Stop hook (self-contained bundle)
    <ToolsDir>/langfuse-py                                      venv with langfuse==<pin>

  Needs uv on PATH. Node.js 22+ must be on PATH at run time for the Codex hook.

.EXAMPLE
  pwsh -File install-telemetry-tools.ps1
  pwsh -File install-telemetry-tools.ps1 -ToolsDir C:\repos\.eval-tools
#>
param([string]$ToolsDir)
$ErrorActionPreference = 'Stop'
$onWindows = $IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop'
if (-not $ToolsDir) { $ToolsDir = if ($onWindows) { 'C:\repos\.eval-tools' } else { Join-Path $HOME 'repos/.eval-tools' } }
$pins = Get-Content (Join-Path $PSScriptRoot 'pins.json') -Raw | ConvertFrom-Json
$root = Join-Path $ToolsDir 'langfuse'
$tar = if ($onWindows) { Join-Path $env:SystemRoot 'System32\tar.exe' } else { 'tar' }   # never MSYS tar for a C: path

function Get-Pinned([string]$Url, [string]$Sha256, [string]$Path) {
    if ((Test-Path $Path) -and (Get-FileHash $Path -Algorithm SHA256).Hash -eq $Sha256) { return }
    New-Item -ItemType Directory -Force (Split-Path $Path) | Out-Null
    Invoke-WebRequest -Uri $Url -OutFile $Path -UseBasicParsing
    $actual = (Get-FileHash $Path -Algorithm SHA256).Hash
    if ($actual -ne $Sha256) { Remove-Item $Path; throw "SHA-256 mismatch for ${Url}: $actual" }
}

$hook = Join-Path $root "claude-hook/$($pins.claude_hook.commit)/langfuse_hook.py"
Get-Pinned $pins.claude_hook.url $pins.claude_hook.sha256 $hook

$codexDir = Join-Path $root "codex-tracing/$($pins.codex_plugin.version)"
$tgz = Join-Path $root "codex-tracing/$($pins.codex_plugin.version).tgz"
Get-Pinned $pins.codex_plugin.url $pins.codex_plugin.sha256 $tgz
if (-not (Test-Path (Join-Path $codexDir 'dist/index.mjs'))) {
    New-Item -ItemType Directory -Force $codexDir | Out-Null
    & $tar -xzf $tgz -C $codexDir --strip-components=1
    if ($LASTEXITCODE) { throw 'Codex tracing package extraction failed' }
}
# index.geeky.mjs: the same bundle with its one hard-coded trace name read from GEEKY_TRACE_NAME
# (falls back to the original names when unset). The pinned index.mjs stays untouched.
$bundle = Get-Content -LiteralPath (Join-Path $codexDir 'dist/index.mjs') -Raw
$from = 'traceName: sessionMeta.isSubagentThread ? "Codex Subagent Turn" : "Codex Turn",'
$to = 'traceName: process.env.GEEKY_TRACE_NAME ? process.env.GEEKY_TRACE_NAME + (sessionMeta.isSubagentThread ? " (subagent)" : "") : (sessionMeta.isSubagentThread ? "Codex Subagent Turn" : "Codex Turn"),'
if (([regex]::Matches($bundle, [regex]::Escape($from))).Count -ne 1) { throw "Codex tracer: expected exactly one trace-name expression to patch" }
Set-Content -LiteralPath (Join-Path $codexDir 'dist/index.geeky.mjs') -Value $bundle.Replace($from, $to) -NoNewline -Encoding utf8NoBOM

$venv = Join-Path $ToolsDir 'langfuse-py'
$venvPy = if ($onWindows) { Join-Path $venv 'Scripts\python.exe' } else { Join-Path $venv 'bin/python' }
if (-not (Test-Path $venvPy)) {
    # Linux/macOS: a system interpreter, which the sandbox can see; uv-managed ones live under the hidden home.
    $pyArgs = if ($onWindows) { @() } else { @('--python', (Get-Command python3).Source) }
    & uv venv -q @pyArgs $venv
    if ($LASTEXITCODE) { throw 'uv venv failed' }
}
$env:VIRTUAL_ENV = $venv
& uv pip install -q "langfuse==$($pins.langfuse_python)"
if ($LASTEXITCODE) { throw 'uv pip install langfuse failed' }
Remove-Item Env:VIRTUAL_ENV

$node = Get-Command node -ErrorAction SilentlyContinue
$nodeMajor = if ($node) { [int]((& $node.Source --version).TrimStart('v') -split '\.')[0] } else { 0 }
Write-Host "claude hook:   $hook"
Write-Host "codex hook:    $(Join-Path $codexDir 'dist/index.geeky.mjs') (trace name from GEEKY_TRACE_NAME)"
Write-Host "langfuse-py:   $venvPy (langfuse $($pins.langfuse_python))"
Write-Host "node:          $(if ($node) { "$($node.Source) (v$nodeMajor)" } else { 'not found' })"
if ($nodeMajor -lt [int]$pins.codex_plugin.node_major_min) { Write-Warning "Codex tracing needs Node.js $($pins.codex_plugin.node_major_min)+ on PATH at run time." }
