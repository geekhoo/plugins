<#
.SYNOPSIS
  Give every system python3.X on PATH pytest inside the sandbox (Linux/macOS).

.DESCRIPTION
  <ToolsDir>/agent-py (one interpreter with pytest) is first on the sandbox PATH, so `python` has
  pytest but `python3.11` resolves to the bare system interpreter. A contestant that checks the
  contract's minimum Python then finds no pytest (Codex C0 attempt 5). For each other python3.X on
  PATH this builds <ToolsDir>/agent-py-3.X with the same pytest version and links
  agent-py/bin/python3.X to it. Needs uv. Windows uses the py launcher and is not covered.

.EXAMPLE
  pwsh -File install-agent-pythons.ps1
#>
param([string]$ToolsDir = (Join-Path $HOME 'repos/.eval-tools'))
$ErrorActionPreference = 'Stop'
if ($IsWindows) { throw 'Linux/macOS only' }
$agentBin = Join-Path $ToolsDir 'agent-py/bin'
$pytest = (& (Join-Path $agentBin 'python') -c 'import pytest; print(pytest.__version__)').Trim()
if ($LASTEXITCODE) { throw "agent-py has no pytest" }
$own = (& (Join-Path $agentBin 'python') -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")').Trim()

$versions = $env:PATH -split ':' | Where-Object { $_ -and $_ -ne $agentBin -and (Test-Path $_) } |
    ForEach-Object { Get-ChildItem $_ -Filter 'python3.*' -ErrorAction SilentlyContinue } |
    Where-Object { $_.Name -match '^python(3\.\d+)$' } | ForEach-Object { $Matches[1] } | Sort-Object -Unique
foreach ($v in $versions | Where-Object { $_ -ne $own }) {
    $exe = (Get-Command "python$v").Source
    $venv = Join-Path $ToolsDir "agent-py-$v"
    $py = Join-Path $venv 'bin/python'
    if (-not (Test-Path $py)) { & uv venv -q --python $exe $venv; if ($LASTEXITCODE) { throw "uv venv $v failed" } }
    $env:VIRTUAL_ENV = $venv
    & uv pip install -q "pytest==$pytest"
    if ($LASTEXITCODE) { throw "pytest install for $v failed" }
    Remove-Item Env:VIRTUAL_ENV
    # A wrapper, not a symlink: Python finds its venv from the pyvenv.cfg beside the path it was started
    # by, so a link in agent-py/bin would pick up agent-py's own (other-version) venv.
    $link = Join-Path $agentBin "python$v"
    if (Test-Path $link) { Remove-Item $link }
    Set-Content -LiteralPath $link -Value "#!/bin/sh`nexec '$py' `"`$@`"" -NoNewline
    & chmod 755 $link
    Write-Host "python$v -> $py (pytest $(& $link -m pytest --version 2>&1))"
}
