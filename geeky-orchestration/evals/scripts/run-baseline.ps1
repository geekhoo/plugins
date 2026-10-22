<#
.SYNOPSIS
  Run one O14 baseline: Claude Code in an isolated MXC sandbox, driven by the canonical
  end-to-end prompt, then oracle checks and a stored baseline record.

.DESCRIPTION
  Implements evals/baseline-runs.md:
    1. fresh seed workspace (git init, brief.md, contract.md, seed commit, no remote)
    2. oracle against the empty workspace (every test must fail)
    3. headless claude in MXC (--isolated --allow-win32k --host-loopback), stream captured
    4. oracle 3x against the result (flake check)
    5. stores solution.bundle, stream/session/stderr, oracle output and run.json under
       evals/baselines/<case>/<UTC stamp>/
  Fields that need the ATIF ingest tool (latency, idle gaps, stages, tasks) are left null.

  Requires: CLAUDE_CODE_OAUTH_TOKEN (process or User env), the mxc-sandbox plugin, Python with
  pytest on PATH, and C:\repos\.eval-tools\geeky-mcp (prebuilt venv for geeky_mcp, see D75).

.EXAMPLE
  pwsh -File run-baseline.ps1 -Case c1-csvledger -DryRun
  pwsh -File run-baseline.ps1 -Case c1-csvledger
  pwsh -File run-baseline.ps1 -Case c3-minisql -Model claude-opus-5-5
#>
param(
    [Parameter(Mandatory)][ValidateSet('c1-csvledger', 'c2-linkvault', 'c3-minisql')][string]$Case,
    [string]$Model,
    [int]$TimeoutSec,
    [string]$ToolsDir = 'C:\repos\.eval-tools',
    [string]$WorkRoot = 'C:\repos',
    [switch]$DryRun,
    # Run evals/mock-agent/mock_claude.py as the MXC workload instead of claude: no model calls,
    # no token needed. Scenarios are comma-separated (see mock_claude.py); default happy.
    [switch]$MockAgent,
    [string]$MockScenario = 'happy'
)
$ErrorActionPreference = 'Stop'

$plugin = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path          # geeky-orchestration
$repoRoot = (Resolve-Path (Join-Path $plugin '..')).Path
$caseDir = Join-Path $plugin "evals\cases\$Case"
$mxc = Join-Path $repoRoot 'mxc-sandbox\scripts\mxc.ps1'
# Oracle needs a Python with pytest; geeky_mcp must run on the venv's own base interpreter (D75).
$python = @((Get-Command python -All -ErrorAction SilentlyContinue).Source; 'C:\Python314\python.exe') |
    Where-Object { $_ -and (Test-Path $_) } | Where-Object { & $_ -c 'import pytest' 2>$null; -not $LASTEXITCODE } | Select-Object -First 1
if (-not $python) { throw 'no Python with pytest found' }
$venvHome = ((Get-Content (Join-Path $ToolsDir 'geeky-mcp\pyvenv.cfg')) -match '^home\s*=' -replace '^home\s*=\s*', '').Trim()
$mcpPython = Join-Path $venvHome 'python.exe'
$agentPy = Join-Path $ToolsDir 'agent-py'   # venv with pytest, first on the sandbox PATH
if (-not (Test-Path (Join-Path $agentPy 'Scripts\python.exe'))) { throw "missing $agentPy (uv venv + uv pip install --offline pytest)" }
$caseCfg = Get-Content (Join-Path $caseDir 'case.json') -Raw | ConvertFrom-Json   # D66 limits
if (-not $TimeoutSec) { $TimeoutSec = [int]$caseCfg.wall_time_ceiling_s }
# The slow scenario exists to hit the timeout; keep it short unless one was given.
if ($MockAgent -and $MockScenario -match '\bslow\b' -and -not $PSBoundParameters.ContainsKey('TimeoutSec')) { $TimeoutSec = 30 }

if (-not $env:CLAUDE_CODE_OAUTH_TOKEN) {
    $env:CLAUDE_CODE_OAUTH_TOKEN = [Environment]::GetEnvironmentVariable('CLAUDE_CODE_OAUTH_TOKEN', 'User')
}
if (-not $MockAgent -and -not $env:CLAUDE_CODE_OAUTH_TOKEN) { throw 'CLAUDE_CODE_OAUTH_TOKEN is not set (run claude setup-token).' }

function Invoke-Oracle([string]$target, [string]$outFile) {
    $env:ORACLE_TARGET = $target
    Push-Location (Join-Path $caseDir 'oracle')
    try { $out = & $python -m pytest -q -rA -p no:cacheprovider 2>&1 | Out-String } finally { Pop-Location }
    if ($outFile) { Add-Content -Path $outFile -Value $out }
    $last = ($out -split "`r?`n" | Where-Object { $_ -match '\d+ (passed|failed|error)' } | Select-Object -Last 1)
    $n = { param($k) if ($last -match "(\d+) $k") { [int]$Matches[1] } else { 0 } }
    [ordered]@{ passed = & $n 'passed'; failed = & $n 'failed'; errors = & $n 'error'; skipped = & $n 'skipped' }
}

# 1. Seed workspace
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$ws = Join-Path $WorkRoot "eval-$Case-$stamp"
New-Item -ItemType Directory -Force $ws | Out-Null
Copy-Item (Join-Path $caseDir 'brief.md'), (Join-Path $caseDir 'contract.md') $ws
Set-Content (Join-Path $ws '.gitignore') "__pycache__/`n"
git -C $ws init -q
git -C $ws -c user.name=eval-seed -c user.email=eval-seed@local add -A
git -C $ws -c user.name=eval-seed -c user.email=eval-seed@local commit -q -m 'seed: brief and contract'
$baseSha = git -C $ws rev-parse HEAD
Write-Host "workspace: $ws (seed $baseSha)"

# 2. Oracle must fail entirely on the seed
$empty = Invoke-Oracle $ws $null
if ($empty.passed -gt 0) { throw "oracle passed $($empty.passed) tests against the empty workspace" }
Write-Host "empty-workspace oracle: passed=0 failed=$($empty.failed) errors=$($empty.errors) (ok)"

# 3. Harness config, outside the workspace
$cfg = Join-Path $WorkRoot ".eval-cfg-$stamp"
New-Item -ItemType Directory -Force $cfg | Out-Null
# Plugin export at the committed HEAD without evals/ (D50: the contestant never sees oracles or specs).
# Granted read-write: under a read-only MXC grant Claude's directory scan of skills/agents/commands
# fails with EPERM and no plugin components load. The export is per run; its hash is checked after.
$pluginSha = git -C $repoRoot rev-parse HEAD
$export = Join-Path $cfg 'plugin'
New-Item -ItemType Directory -Force $export | Out-Null
git -C $repoRoot archive --format=tar $pluginSha geeky-orchestration ':(exclude)geeky-orchestration/evals' | tar -x -C $export
$pluginRun = Join-Path $export 'geeky-orchestration'
$hashTree = { param($dir) (Get-ChildItem $dir -Recurse -File | Sort-Object FullName | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash }) -join '' }
$exportHash = & $hashTree $pluginRun
$boot = "import site,runpy,sys; site.addsitedir(r'$ToolsDir\geeky-mcp\Lib\site-packages'); sys.path.insert(0, r'$pluginRun\mcp'); sys.argv=[r'$pluginRun\mcp\server.py']; runpy.run_path(sys.argv[0], run_name='__main__')"
@{ mcpServers = @{ geeky = @{ command = $mcpPython; args = @('-u', '-c', $boot) } } } | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $cfg 'mcp.json')
'{"env": {"MCP_TIMEOUT": "120000"}}' | Set-Content (Join-Path $cfg 'settings.json')

$prompt = (Get-Content (Join-Path $plugin 'evals\prompts\end-to-end.md') -Raw) -replace '\{\{PLANNING_FOLDER\}\}', 'docs/spec-001-feature/'
$promptSha = [BitConverter]::ToString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($prompt))).Replace('-', '').ToLower()
$sid = [guid]::NewGuid().ToString()
$claudeArgs = @('-p', $prompt, '--session-id', $sid, '--plugin-dir', $pluginRun,
    '--settings', (Join-Path $cfg 'settings.json'), '--strict-mcp-config', '--mcp-config', (Join-Path $cfg 'mcp.json'),
    '--permission-mode', 'bypassPermissions', '--output-format', 'stream-json', '--verbose')
if ($Model) { $claudeArgs += @('--model', $Model) }
if ($MockAgent) {
    # MXC_CLAUDE_EXE must be an .exe: the agent-py python runs the mock, copied under the read-only
    # config grant so the sandbox can read it (the repo itself is not granted).
    $mockDir = Join-Path $cfg 'mock-agent'
    New-Item -ItemType Directory -Force $mockDir | Out-Null
    Copy-Item (Join-Path $plugin 'evals\mock-agent\mock_claude.py') $mockDir
    $claudeArgs = @((Join-Path $mockDir 'mock_claude.py')) + $claudeArgs + @('--mock-scenario', $MockScenario, '--mock-case', $Case)
}
# Git sees the workspace as owned by another identity inside the container ("dubious ownership").
# Trust only this workspace via env-scoped config; the global git config is untouched.
# MXC forces TEMP/TMP to the AppContainer's AC\Temp, where mkdtemp()-style folders (pytest tmp_path,
# git temp repos) are not writable. TMPDIR takes precedence for Python, pytest and git and MXC leaves
# it alone, so point it at a per-run writable folder.
$runTmp = Join-Path $cfg 'tmp'
New-Item -ItemType Directory -Force $runTmp | Out-Null
$hostArgs = @('run', '--workspace', $ws, '--isolated', '--allow-win32k', '--host-loopback',
    '--rw', $export, '--ro', $cfg, '--rw', $runTmp, '--ro', $ToolsDir, '--timeout', $TimeoutSec,
    '--env', "TMPDIR=$runTmp",
    '--env', 'GIT_CONFIG_COUNT=1', '--env', 'GIT_CONFIG_KEY_0=safe.directory', '--env', "GIT_CONFIG_VALUE_0=$($ws -replace '\\','/')",
    '--env', "XDG_CONFIG_HOME=$cfg",   # host ~/.config/git is unreadable in the container; avoid per-command warnings
    # Claude's Windows shell launcher makes every PowerShell tool call report "Exit code 5" inside MXC
    # even on success; without it the tool returns the command's real exit code.
    '--env', 'CLAUDE_CODE_DISABLE_WINDOWS_SHELL_LAUNCHER=1',
    # claude -p stops background subagents still running 10 min after the main agent's last turn; the
    # main agent is resumed when they finish, so wait indefinitely (the MXC --timeout still bounds the run).
    '--env', 'CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0',
    # pytest for the agents' own tests: the sandbox Python has none and pip cannot install inside MXC.
    '--env', "PATH=$agentPy\Scripts;$env:PATH", '--env', "VIRTUAL_ENV=$agentPy",
    # Neutral commit identity (the seed repo has none); set via env so no repo or global config changes.
    '--env', 'GIT_AUTHOR_NAME=geeky-eval-agent', '--env', 'GIT_AUTHOR_EMAIL=agent@geeky-eval.local',
    '--env', 'GIT_COMMITTER_NAME=geeky-eval-agent', '--env', 'GIT_COMMITTER_EMAIL=agent@geeky-eval.local')

if ($DryRun) {
    Write-Host "DRY RUN. Would launch (timeout ${TimeoutSec}s):`n  $mxc $($hostArgs -join ' ') -- <claude args: session $sid, plugin $pluginRun>"
    Write-Host "Workspace $ws and config $cfg were created; delete them when done."
    exit 0
}

# Run
$out = Join-Path $plugin "evals\baselines\$Case\$stamp"
New-Item -ItemType Directory -Force $out | Out-Null
$started = (Get-Date).ToUniversalTime()
if ($MockAgent) { $savedExe = $env:MXC_CLAUDE_EXE; $env:MXC_CLAUDE_EXE = Join-Path $agentPy 'Scripts\python.exe' }
try {
    & $mxc @hostArgs -- @claudeArgs > (Join-Path $out 'stream.jsonl') 2> (Join-Path $out 'stderr.txt')
    $exitCode = $LASTEXITCODE
} finally { if ($MockAgent) { $env:MXC_CLAUDE_EXE = $savedExe } }
$ended = (Get-Date).ToUniversalTime()
if ($MockAgent) {
    $mockSummary = Get-Content (Join-Path $out 'stream.jsonl') | Where-Object { $_ -match '"subtype":"mock_summary"' } | Select-Object -Last 1
    if ($mockSummary) { $mockSummary | ConvertFrom-Json | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'mock-summary.json') }
}

$pluginTampered = (& $hashTree $pluginRun) -ne $exportHash
$session = Get-ChildItem (Join-Path $env:USERPROFILE '.mxc-sandbox\home\projects') -Recurse -Filter "$sid.jsonl" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($session) { Copy-Item $session.FullName (Join-Path $out 'session.jsonl') }

# 4. Oracle 3x
$oracleFile = Join-Path $out 'oracle-output.txt'
$runs = 1..3 | ForEach-Object { Invoke-Oracle $ws $oracleFile }
$stable = ($runs | ForEach-Object { "$($_.passed)/$($_.failed)/$($_.errors)/$($_.skipped)" } | Select-Object -Unique).Count -eq 1

# 5. Store
git -C $ws bundle create (Join-Path $out 'solution.bundle') --all 2>$null
$lines = Get-Content (Join-Path $out 'stream.jsonl') | Where-Object { $_ -match '^\{' }
$init = $lines | Where-Object { $_ -match '"subtype":"init"' } | Select-Object -First 1 | ConvertFrom-Json
$result = $lines | Where-Object { $_ -match '"type":"result"' } | Select-Object -Last 1 | ConvertFrom-Json
$u = $result.usage
$inputTotal = [long]$u.input_tokens + [long]$u.cache_creation_input_tokens + [long]$u.cache_read_input_tokens
$pkg = $Case.Substring(3)
$py = Get-ChildItem $ws -Recurse -Filter *.py -File | Where-Object { $_.FullName -notmatch '\\\.git\\' }
$isTest = { param($f) $f.Name -like 'test_*' -or $f.Name -like '*_test.py' -or $f.FullName -match '\\tests?\\' }
$srcLoc = ($py | Where-Object { $_.FullName -like "$ws\$pkg\*" -and -not (& $isTest $_) } | Get-Content | Measure-Object -Line).Lines
$testLoc = ($py | Where-Object { & $isTest $_ } | Get-Content | Measure-Object -Line).Lines
$bgKilled = Select-String -Path (Join-Path $out 'stderr.txt') -Pattern 'Background tasks still running .* stopping them' -Quiet
$exitReason = if ($exitCode -eq 124) { 'timeout' } elseif ($bgKilled) { 'bg_killed' } elseif ($result -and -not $result.is_error) { 'completed' } elseif (-not $result) { 'crash' } else { 'aborted' }
$o = $runs[0]
$clean = $stable -and $o.failed -eq 0 -and $o.errors -eq 0 -and $o.passed -gt 0
$sha = { param($p) if (Test-Path $p) { (Get-FileHash $p -Algorithm SHA256).Hash.ToLower() } }

[ordered]@{
    schema = 'geeky-eval.baseline/1'; case = $Case
    harness = 'claude-code'; harness_version = $init.claude_code_version; model = $init.model; reasoning = 'default'
    approach = $(if ($MockAgent) { "mock-agent:$MockScenario" } else { 'canonical-prompt' }); plugin_sha = $pluginSha; plugin_modified_during_run = $pluginTampered; prompt_sha256 = $promptSha
    geeky_skills_loaded = @($init.skills | Where-Object { "$_" -like 'geeky-orchestration:*' }).Count
    workspace = $ws; seed_sha = $baseSha; session_id = $sid
    started_utc = $started.ToString('o'); ended_utc = $ended.ToString('o'); wall_time_s = [int]($ended - $started).TotalSeconds
    tokens = [ordered]@{ input = $inputTotal; cached_input = [long]$u.cache_read_input_tokens; output = [long]$u.output_tokens
        reasoning = [long]$u.output_tokens_details.thinking_tokens; total = $inputTotal + [long]$u.output_tokens }
    model_calls = $result.num_turns; latency_median_ms = $null; max_idle_gap_s = $null
    stages = $null; tasks = $null; impl_review_rounds = $null
    oracle = [ordered]@{ collected = $o.passed + $o.failed + $o.errors + $o.skipped; passed = $o.passed; failed = $o.failed
        errors = $o.errors; skipped = $o.skipped; stable_over_3 = $stable }
    loc = [ordered]@{ source_non_test = $srcLoc; test = $testLoc
        files_changed = @(git -C $ws diff --name-only $baseSha HEAD).Count }
    commits = [int](git -C $ws rev-list --count "$baseSha..HEAD")
    exit_code = $exitCode; exit_reason = $exitReason; is_error = $result.is_error
    raw_sha256 = [ordered]@{ stream = & $sha (Join-Path $out 'stream.jsonl'); session = & $sha (Join-Path $out 'session.jsonl') }
    interventions = 0
    reference_eligible = (-not $MockAgent -and $clean -and $exitReason -eq 'completed' -and -not $pluginTampered -and @($init.skills | Where-Object { "$_" -like 'geeky-orchestration:*' }).Count -gt 0)
} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $out 'run.json')

Set-Content (Join-Path $out 'notes.md') "# Baseline $Case $stamp`n`nApproach: canonical prompt, Claude Code isolated in MXC.`nInterventions: none.`nOracle verdicts: (fill in for any failure)`n"
# Derived measures (tokens summed over all models, stages, latency, idle gap) -> run.json + analysis.json
& $python (Join-Path $PSScriptRoot 'analyze-run.py') $out --token-ceiling $caseCfg.token_ceiling
Write-Host "stored: $out"
