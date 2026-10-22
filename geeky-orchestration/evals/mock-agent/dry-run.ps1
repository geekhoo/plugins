<#
.SYNOPSIS
  Dry-run the eval toolchain with the mock agent: no model calls, no token.

.DESCRIPTION
  Runs mock_claude.py with the same claude arguments, environment, and (with -InMxc) the same MXC
  grants and --env flags as run-baseline.ps1, then prints one PASS/FAIL line per check and writes
  stream.jsonl, stderr.txt, session.jsonl and mock-summary.json to -OutDir.

  Without -Workspace a scratch git workspace is created under -WorkRoot (seeded with the case's
  brief.md and contract.md when -Case is given). Without -PluginDir the plugin is exported at the
  committed HEAD, without evals/, like the runner does. Created workspace and config folders are
  deleted at the end unless -Keep.

  Checks (comma-separated): env-probe, grants, pwsh, python, git, gates, mcp, network, happy,
  gate-fail, crash, slow, bg-wait, all (= env-probe,grants,pwsh,python,git,gates,mcp).

.EXAMPLE
  pwsh -File dry-run.ps1 -InMxc
  pwsh -File dry-run.ps1 -Checks env-probe,mcp -InMxc
  pwsh -File dry-run.ps1 -Case c2-linkvault -Checks happy -InMxc -Keep
  pwsh -File dry-run.ps1 -Workspace C:\repos\some-repo -Checks grants,git
#>
param(
    [string]$Workspace,
    [string]$Case,
    [string]$Checks = 'all',
    [switch]$InMxc,
    [string]$PluginDir,
    [ValidateSet('rw', 'ro')][string]$PluginGrant = 'rw',
    [int]$TimeoutSec = 900,
    [string]$ToolsDir = 'C:\repos\.eval-tools',
    [string]$WorkRoot = 'C:\repos',
    [string]$OutDir,
    [switch]$Keep
)
$ErrorActionPreference = 'Stop'

$plugin = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path          # geeky-orchestration
$repoRoot = (Resolve-Path (Join-Path $plugin '..')).Path
$mxc = Join-Path $repoRoot 'mxc-sandbox\scripts\mxc.ps1'
$agentPy = Join-Path $ToolsDir 'agent-py'
$agentPython = Join-Path $agentPy 'Scripts\python.exe'
if (-not (Test-Path $agentPython)) { throw "missing $agentPython (uv venv + uv pip install --offline pytest)" }
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
if (-not $OutDir) { $OutDir = Join-Path ([IO.Path]::GetTempPath()) "geeky-dryrun-$stamp" }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$created = @()

# Config folder, outside the workspace (read-only in MXC)
$cfg = Join-Path $WorkRoot ".eval-cfg-dryrun-$stamp"
New-Item -ItemType Directory -Force $cfg | Out-Null
$created += $cfg
if ($PluginDir) {
    $pluginRun = (Resolve-Path $PluginDir).Path
} else {
    $export = Join-Path $cfg 'plugin'
    New-Item -ItemType Directory -Force $export | Out-Null
    git -C $repoRoot archive --format=tar HEAD geeky-orchestration ':(exclude)geeky-orchestration/evals' | & (Join-Path $env:SystemRoot 'System32\tar.exe') -x -C $export   # not MSYS tar: it reads C: as a host
    $pluginRun = Join-Path $export 'geeky-orchestration'
}
$mcpCfgArgs = @()
$mcpVenv = Join-Path $ToolsDir 'geeky-mcp\pyvenv.cfg'
if (Test-Path $mcpVenv) {
    $venvHome = ((Get-Content $mcpVenv) -match '^home\s*=' -replace '^home\s*=\s*', '').Trim()
    $boot = "import site,runpy,sys; site.addsitedir(r'$ToolsDir\geeky-mcp\Lib\site-packages'); sys.path.insert(0, r'$pluginRun\mcp'); sys.argv=[r'$pluginRun\mcp\server.py']; runpy.run_path(sys.argv[0], run_name='__main__')"
    @{ mcpServers = @{ geeky = @{ command = (Join-Path $venvHome 'python.exe'); args = @('-u', '-c', $boot) } } } |
        ConvertTo-Json -Depth 6 | Set-Content (Join-Path $cfg 'mcp.json')
    $mcpCfgArgs = @('--strict-mcp-config', '--mcp-config', (Join-Path $cfg 'mcp.json'))
} else { Write-Warning "no $mcpVenv; the mcp check falls back to the plugin's .mcp.json" }
'{"env": {"MCP_TIMEOUT": "120000"}}' | Set-Content (Join-Path $cfg 'settings.json')
$mockDir = Join-Path $cfg 'mock-agent'
New-Item -ItemType Directory -Force $mockDir | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'mock_claude.py') $mockDir

# Workspace
if ($Workspace) {
    $ws = (Resolve-Path $Workspace).Path
} else {
    $ws = Join-Path $WorkRoot "eval-dryrun-$stamp"
    New-Item -ItemType Directory -Force $ws | Out-Null
    $created += $ws
    if ($Case) {
        $caseDir = Join-Path $plugin "evals\cases\$Case"
        if (-not (Test-Path $caseDir)) { throw "unknown case $Case" }
        Copy-Item (Join-Path $caseDir 'brief.md'), (Join-Path $caseDir 'contract.md') $ws
    }
    Set-Content (Join-Path $ws '.gitignore') "__pycache__/`n"
    git -C $ws init -q
    git -C $ws -c user.name=eval-seed -c user.email=eval-seed@local add -A
    git -C $ws -c user.name=eval-seed -c user.email=eval-seed@local commit -q -m 'seed: dry run'
}

$prompt = (Get-Content (Join-Path $plugin 'evals\prompts\end-to-end.md') -Raw) -replace '\{\{PLANNING_FOLDER\}\}', 'docs/spec-001-feature/'
$sid = [guid]::NewGuid().ToString()
$mockArgs = @((Join-Path $mockDir 'mock_claude.py'), '-p', $prompt, '--session-id', $sid, '--plugin-dir', $pluginRun,
    '--settings', (Join-Path $cfg 'settings.json')) + $mcpCfgArgs + @('--permission-mode', 'bypassPermissions',
    '--output-format', 'stream-json', '--verbose', '--disallowedTools', 'Bash', '--mock-scenario', $Checks)
if ($Case) { $mockArgs += @('--mock-case', $Case) }

# The runner's sandbox environment, verbatim
$envPairs = [ordered]@{
    GIT_CONFIG_COUNT = '1'; GIT_CONFIG_KEY_0 = 'safe.directory'; GIT_CONFIG_VALUE_0 = ($ws -replace '\\', '/')
    XDG_CONFIG_HOME = $cfg; CLAUDE_CODE_DISABLE_WINDOWS_SHELL_LAUNCHER = '1'; CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS = '0'
    PATH = "$agentPy\Scripts;$env:PATH"; VIRTUAL_ENV = $agentPy
    GIT_AUTHOR_NAME = 'geeky-eval-agent'; GIT_AUTHOR_EMAIL = 'agent@geeky-eval.local'
    GIT_COMMITTER_NAME = 'geeky-eval-agent'; GIT_COMMITTER_EMAIL = 'agent@geeky-eval.local'
}
# Per-run writable temp: MXC forces TEMP/TMP to the AppContainer AC\Temp; TMPDIR wins for Python/pytest/git.
$runTmp = Join-Path $cfg 'tmp'
New-Item -ItemType Directory -Force $runTmp | Out-Null
if ($InMxc) { $envPairs['TMPDIR'] = $runTmp }
$stream = Join-Path $OutDir 'stream.jsonl'
$stderr = Join-Path $OutDir 'stderr.txt'
if ($InMxc) {
    $grantArgs = if ($PluginDir) { @("--$PluginGrant", $pluginRun) } else { @("--$PluginGrant", (Split-Path $pluginRun)) }
    $hostArgs = @('run', '--workspace', $ws, '--isolated', '--allow-win32k', '--host-loopback') + $grantArgs +
        @('--ro', $cfg, '--rw', $runTmp, '--ro', $ToolsDir, '--timeout', $TimeoutSec)
    foreach ($k in $envPairs.Keys) { $hostArgs += @('--env', "$k=$($envPairs[$k])") }
    $sessionRoot = Join-Path $env:USERPROFILE '.mxc-sandbox\home\projects'
    $saved = $env:MXC_CLAUDE_EXE
    $env:MXC_CLAUDE_EXE = $agentPython
    try { & $mxc @hostArgs -- @mockArgs > $stream 2> $stderr; $exitCode = $LASTEXITCODE }
    finally { $env:MXC_CLAUDE_EXE = $saved }
} else {
    $home2 = Join-Path $cfg 'home'
    $envPairs['CLAUDE_CONFIG_DIR'] = $home2
    $sessionRoot = Join-Path $home2 'projects'
    $saved = @{}
    foreach ($k in $envPairs.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, $envPairs[$k]) }
    Push-Location $ws
    try { & $agentPython @mockArgs > $stream 2> $stderr; $exitCode = $LASTEXITCODE }
    finally { Pop-Location; foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) } }
}

$session = Get-ChildItem $sessionRoot -Recurse -Filter "$sid.jsonl" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($session) {
    Copy-Item $session.FullName (Join-Path $OutDir 'session.jsonl')
    if ($InMxc) { Remove-Item $session.FullName; Remove-Item $session.Directory.FullName -ErrorAction SilentlyContinue }
}
$lines = Get-Content $stream | Where-Object { $_ -match '^\{' }
$summaryLine = $lines | Where-Object { $_ -match '"subtype":"mock_summary"' } | Select-Object -Last 1
$summary = if ($summaryLine) { $summaryLine | ConvertFrom-Json } else { $null }
if ($summary) { $summary | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $OutDir 'mock-summary.json') }

foreach ($c in ($lines | Where-Object { $_ -match '"subtype":"mock_check"' } | ForEach-Object { $_ | ConvertFrom-Json })) {
    $color = @{ pass = 'Green'; fail = 'Red'; warn = 'Yellow'; info = 'DarkGray' }[$c.status]
    $detail = ("$($c.detail)" -split "`r?`n")[0]
    if ($detail.Length -gt 160) { $detail = $detail.Substring(0, 160) + '...' }
    Write-Host ("{0,-4} {1,-50} {2}" -f $c.status.ToUpper(), $c.name, $detail) -ForegroundColor $color
}
$hasResult = [bool]($lines | Where-Object { $_ -match '"type":"result"' })
$reason = if ($exitCode -eq 124) { 'timeout' } elseif (-not $hasResult) { 'crash' } elseif ($summary -and $summary.ok) { 'completed' } else { 'checks-failed' }
Write-Host "workload exit $exitCode, $reason; session file $(if ($session) { 'found' } else { 'MISSING' }); output in $OutDir"

if (-not $Keep) { foreach ($d in $created) { Remove-Item $d -Recurse -Force -ErrorAction SilentlyContinue } }
elseif ($created) { Write-Host "kept: $($created -join ', ')" }
exit $(if ($reason -eq 'completed') { 0 } else { 1 })
