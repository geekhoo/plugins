<#
.SYNOPSIS
Prepare a Codex baseline beside the Claude runner; launch only with -Launch.
.DESCRIPTION
Preparation exports committed plugin HEAD without evals, seeds a workspace, and
runs the fail-closed Codex parity preflight. It never signs in or handles auth
contents. The dedicated, already signed-in CODEX_HOME is used only as the auth
and session store; user config/rules are ignored, and HOME is isolated per run.
Mock and MXC smoke validation belong to checkpoint 2. Paid launch requires the
owner's later authorization. Codex analysis/scoring are deliberately not called.
-Gateway litellm (default, D101) routes every thread through LITELLM_PROXY_URL with
LITELLM_PROXY_API_KEY (copied into the workload by name, excluded from the agent's shell);
-Gateway direct uses the signed-in CODEX_HOME. With TRACE_TO_LANGFUSE=true a completed
run is uploaded to Langfuse afterwards by langfuse-upload.py on the host.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('c1-csvledger', 'c2-linkvault', 'c3-minisql')][string]$Case,
    # Default: zen/gpt-6.1-sol through LiteLLM, gpt-6.1-sol direct.
    [string]$Model,
    [ValidateSet('litellm', 'direct')][string]$Gateway = 'litellm',
    [ValidateSet('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')][string]$Reasoning = 'high',
    [string]$WorkerModel,
    [ValidateSet('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')][string]$WorkerReasoning,
    [ValidateSet('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')][string]$ReviewerReasoning,
    [int]$TimeoutSec,
    [string]$ToolsDir = 'C:\repos\.eval-tools',
    [string]$WorkRoot = 'C:\repos',
    [string]$CodexHome,
    [string]$CodexExe,
    [string]$MxcBuildSource,
    [string]$NativeProofFolder,
    [string]$ReviewerProofFolder,
    [switch]$MockAgent,
    [ValidateSet('happy', 'all', 'fail')][string]$MockScenario = 'happy',
    [switch]$Launch
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
if ($MockAgent -and $Launch) { throw 'Choose -MockAgent or -Launch, not both.' }
if ($Launch -and -not $MxcBuildSource) { throw '-Launch requires an explicit -MxcBuildSource containing the vetted pinned build.' }
if ($Launch -and -not $NativeProofFolder) { throw '-Launch requires an explicit -NativeProofFolder containing passing model-free native proof.' }
if ($Launch -and $ReviewerReasoning -and -not $ReviewerProofFolder) { throw 'Reviewer settings require an explicit -ReviewerProofFolder proving the architect reviewer role.' }
foreach ($name in @('LITELLM_PROXY_URL', 'LITELLM_PROXY_API_KEY', 'TRACE_TO_LANGFUSE',
        'LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY', 'LANGFUSE_BASE_URL', 'LANGFUSE_TRACING_ENVIRONMENT')) {
    if (-not [Environment]::GetEnvironmentVariable($name)) {
        [Environment]::SetEnvironmentVariable($name, [Environment]::GetEnvironmentVariable($name, 'User'))
    }
}
$gatewayArgs = @()
if ($Gateway -eq 'litellm') {
    if (-not ($env:LITELLM_PROXY_URL -and $env:LITELLM_PROXY_API_KEY)) {
        if (-not $MockAgent) { throw 'LITELLM_PROXY_URL and LITELLM_PROXY_API_KEY must be set for -Gateway litellm.' }
        $Gateway = 'direct'   # the mock makes no model calls
    } else { $gatewayArgs = @('--litellm-base-url', ($env:LITELLM_PROXY_URL.TrimEnd('/') + '/v1')) }
    if (-not $Model) { $Model = 'zen/gpt-6.1-sol' }
} elseif (-not $Model) { $Model = 'gpt-6.1-sol' }
if (-not $WorkerModel) { $WorkerModel = $Model }
if (-not $WorkerReasoning) { $WorkerReasoning = $Reasoning }

$plugin = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$repoRoot = (Resolve-Path (Join-Path $plugin '..')).Path
$caseDir = Join-Path $plugin "evals\cases\$Case"
$adapter = Join-Path $plugin 'evals\adapters\codex'
$forbiddenSkillRoot = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)) '.agents\skills'
$python = Join-Path $ToolsDir 'agent-py\Scripts\python.exe'
if (-not $CodexHome) { $CodexHome = Join-Path $ToolsDir 'codex-home' }
$CodexHome = [IO.Path]::GetFullPath($CodexHome)
if (-not $CodexExe) { $CodexExe = Join-Path $ToolsDir 'codex\0.164.0\bin\codex.exe' }
$codexExe = (Resolve-Path -LiteralPath $CodexExe).Path
$tarExe = Join-Path $env:SystemRoot 'System32\tar.exe' # Never select MSYS tar for a C: path.
$mxc = Join-Path $repoRoot 'mxc-sandbox\scripts\mxc.ps1'
foreach ($required in @($python, $CodexHome, $tarExe, $mxc, (Join-Path $adapter 'prepare-profile.py'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing prerequisite: $required" }
}
& $python -c 'import pytest'
if ($LASTEXITCODE) { throw 'agent-py must have pytest installed' }
$caseCfg = Get-Content (Join-Path $caseDir 'case.json') -Raw | ConvertFrom-Json
if (-not $TimeoutSec) { $TimeoutSec = [int]$caseCfg.wall_time_ceiling_s }
if ($TimeoutSec -le 0) { throw 'TimeoutSec must be positive' }

function Invoke-Git {
    $result = & git @args
    if ($LASTEXITCODE) { throw "git failed: $($args[0])" }
    return $result
}
function Get-TreeHash([string]$Directory) {
    # Include relative names: renamed files must count as tampering too.
    $entries = Get-ChildItem -LiteralPath $Directory -Recurse -File |
        Where-Object { $_.FullName -notmatch '\\__pycache__\\' } | Sort-Object FullName |
        ForEach-Object { $_.FullName.Substring($Directory.Length) + ':' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes(($entries -join "`n")))).ToLowerInvariant()
}
function Get-Sha([string]$Path) {
    if (Test-Path -LiteralPath $Path -PathType Leaf) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
    return $null
}
function Invoke-Oracle([string]$Target, [string]$OutputPath) {
    $priorTarget = $env:ORACLE_TARGET
    $env:ORACLE_TARGET = $Target
    Push-Location (Join-Path $caseDir 'oracle')
    try {
        $output = & $python -m pytest -q -rA -p no:cacheprovider 2>&1 | Out-String
        $code = $LASTEXITCODE
    } finally { Pop-Location; $env:ORACLE_TARGET = $priorTarget }
    if ($OutputPath) { Add-Content -LiteralPath $OutputPath -Value $output }
    $summary = $output -split "`r?`n" | Where-Object { $_ -match '\d+ (passed|failed|error)' } | Select-Object -Last 1
    $counts = [ordered]@{ passed = 0; failed = 0; errors = 0; skipped = 0; exit_code = $code }
    foreach ($pair in @(@('passed','passed'), @('failed','failed'), @('errors','error'), @('skipped','skipped'))) {
        if ($summary -match "(\d+) $($pair[1])") { $counts[$pair[0]] = [int]$Matches[1] }
    }
    return $counts
}

# A GUID suffix avoids colliding with another session's timestamp or resources.
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$ws = Join-Path $WorkRoot "eval-$Case-codex-$stamp"
$cfg = Join-Path $WorkRoot ".eval-cfg-codex-$stamp"
$out = Join-Path $plugin "evals\baselines\$Case\$stamp"
$runHome = Join-Path $cfg 'home'
$runTmp = Join-Path $cfg 'tmp'
$export = Join-Path $cfg 'plugin'
foreach ($directory in @($ws, $cfg, $out, $runTmp, $export)) {
    New-Item -ItemType Directory -Path $directory | Out-Null
}
Copy-Item (Join-Path $caseDir 'brief.md'), (Join-Path $caseDir 'contract.md') $ws
Set-Content (Join-Path $ws '.gitignore') "__pycache__/`n"
Invoke-Git @('-C', $ws, 'init', '-q') | Out-Null
Invoke-Git @('-C', $ws, 'add', '-A') | Out-Null
Invoke-Git @('-C', $ws, '-c', 'user.name=eval-seed', '-c', 'user.email=eval-seed@local', 'commit', '-q', '-m', 'seed: brief and contract') | Out-Null
$baseSha = Invoke-Git @('-C', $ws, 'rev-parse', 'HEAD')
$pluginSha = Invoke-Git @('-C', $repoRoot, 'rev-parse', 'HEAD')
$archive = Join-Path $cfg 'plugin.tar'
Invoke-Git @('-C', $repoRoot, 'archive', '--format=tar', "--output=$archive", $pluginSha, 'geeky-orchestration', ':(exclude)geeky-orchestration/evals') | Out-Null
& $tarExe -xf $archive -C $export
if ($LASTEXITCODE) { throw 'Plugin export extraction failed' }
$pluginRun = Join-Path $export 'geeky-orchestration'
if (Test-Path (Join-Path $pluginRun 'evals')) { throw 'Export contains forbidden evals directory' }
$exportHash = Get-TreeHash $pluginRun

# Only the established placeholder substitution changes the canonical prompt.
$prompt = (Get-Content (Join-Path $plugin 'evals\prompts\end-to-end.md') -Raw).Replace('{{PLANNING_FOLDER}}', 'docs/spec-001-feature/')
$promptSha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($prompt))).ToLowerInvariant()
$profileResult = Join-Path $cfg 'codex-profile.json'
$reviewerArgs = if ($ReviewerReasoning) { @('--reviewer-reasoning', $ReviewerReasoning) } else { @() }
& $python (Join-Path $adapter 'prepare-profile.py') --plugin $pluginRun --home $runHome --codex-home $CodexHome --tools-dir $ToolsDir --profile (Join-Path $adapter 'profile') --output $profileResult --model $Model --reasoning $Reasoning --worker-model $WorkerModel --worker-reasoning $WorkerReasoning @reviewerArgs @gatewayArgs
$preflightCode = $LASTEXITCODE
if (Test-Path -LiteralPath $profileResult) { Copy-Item -LiteralPath $profileResult -Destination (Join-Path $out 'parity-preflight.json') }
if ($preflightCode -ne 0 -or -not (Test-Path -LiteralPath $profileResult)) {
    throw "Codex parity preflight failed; inspect $out\parity-preflight.json. No contestant launched."
}
$profile = Get-Content -LiteralPath $profileResult -Raw | ConvertFrom-Json
if ($profile.ok -ne $true) { throw "Codex parity preflight did not pass: $profileResult" }
$codexArgs = @('--no-daemon', 'exec', '--json', '--sandbox', 'danger-full-access', '--ignore-user-config', '--ignore-rules', '--strict-config', '--cd', $ws, '--model', $Model)
foreach ($override in $profile.codex_config_overrides) { $codexArgs += @('-c', [string]$override) }
if ($profile.PSObject.Properties.Name -contains 'extra_args') { $codexArgs += @($profile.extra_args) }
$codexArgs += $prompt
if ($MockAgent) {
    $mockPath = Join-Path $cfg 'mock_codex.py'
    Copy-Item -LiteralPath (Join-Path $adapter 'mock_codex.py') -Destination $mockPath
    $codexArgs = @($mockPath) + $codexArgs + @('--mock-scenario', $MockScenario,
        '--mock-forbidden-path', (Join-Path $caseDir 'spec.md'),
        '--mock-forbidden-path', (Join-Path $plugin 'agents\geeky-coder.md'))
} elseif ($Launch) {
    $trustedExec = Join-Path $cfg 'trusted-exec.py'
    Copy-Item (Join-Path $adapter 'trusted-exec.py'), (Join-Path $adapter 'native-probe.py'), (Join-Path $adapter 'diagnostics.py') $cfg
    $promptFile = Join-Path $cfg 'canonical-prompt.txt'
    Set-Content -LiteralPath $promptFile -Value $prompt -NoNewline -Encoding utf8
    $codexArgs = @($trustedExec, '--codex', $codexExe, '--profile', $profileResult,
        '--workspace', $ws, '--output', (Join-Path $runTmp 'native-hook-trust'), '--prompt-file', $promptFile,
        '--forbidden-skill-root', $forbiddenSkillRoot)
}
$hostArgs = @('run', '--workspace', $ws, '--isolated', '--allow-win32k', '--no-enumerate-root', '--host-loopback',
    '--rw', $export, '--ro', $cfg, '--rw', $runHome, '--rw', $runTmp, '--ro', $ToolsDir, '--rw', $CodexHome,
    '--timeout', $TimeoutSec, '--env', "CODEX_HOME=$CodexHome", '--env', "HOME=$runHome", '--env', "USERPROFILE=$runHome",
    '--env', "CLAUDE_PLUGIN_ROOT=$pluginRun", '--env', "PLUGIN_ROOT=$pluginRun",
    '--env', "TMPDIR=$runTmp", '--env', 'PYTHONDONTWRITEBYTECODE=1', '--env', "XDG_CONFIG_HOME=$runHome",
    '--env', 'GIT_CONFIG_COUNT=1', '--env', 'GIT_CONFIG_KEY_0=safe.directory', '--env', "GIT_CONFIG_VALUE_0=$($ws.Replace('\','/'))",
    '--env', "PATH=$ToolsDir\agent-py\Scripts;$env:PATH", '--env', "VIRTUAL_ENV=$ToolsDir\agent-py",
    '--env', 'GIT_AUTHOR_NAME=geeky-eval-agent', '--env', 'GIT_AUTHOR_EMAIL=agent@geeky-eval.local',
    '--env', 'GIT_COMMITTER_NAME=geeky-eval-agent', '--env', 'GIT_COMMITTER_EMAIL=agent@geeky-eval.local')
if ($Gateway -eq 'litellm') { $hostArgs += @('--env', 'LITELLM_PROXY_API_KEY') }

$record = [ordered]@{
    schema = 'geeky-eval.baseline/1'; case = $Case; harness = 'codex'; harness_version = (& $codexExe --version | Out-String).Trim()
    model = $Model; reasoning = $Reasoning; gateway = $Gateway
    gateway_url = $(if ($Gateway -eq 'litellm') { $env:LITELLM_PROXY_URL } else { $null }); approach = $(if ($MockAgent) { "mock-agent:$MockScenario" } else { 'canonical-prompt' }); plugin_sha = $pluginSha
    worker_model = $profile.worker_model; worker_reasoning = $profile.worker_reasoning; model_matrix = $profile.model_matrix
    plugin_modified_during_run = $false; prompt_sha256 = $promptSha; workspace = $ws; config_directory = $cfg; seed_sha = $baseSha
    session_id = $null; started_utc = $null; ended_utc = $null; wall_time_s = $null
    tokens = $null; model_calls = $null; latency_median_ms = $null; max_idle_gap_s = $null
    stages = $null; tasks = $null; impl_review_rounds = $null; oracle = $null; loc = $null; commits = 0
    exit_code = $null; exit_reason = 'prepared'; is_error = $false; raw_sha256 = $null; interventions = 0
    token_ceiling = $caseCfg.token_ceiling; token_ceiling_policy = 'informational-until-codex-baseline'
    reference_eligible = $false; analysis_status = 'awaiting-rollout'; parity_passed = $true
    runtime_parity_verified = ($profile.runtime_verified -eq $true); profile_sha256 = $profile.profile_sha256
    mock_agent = [bool]$MockAgent; runtime_toolchain_verified = $false
    diagnostics_passed = $false
    native_proof_folder = $(if ($Launch) { [IO.Path]::GetFullPath($NativeProofFolder) } else { $null })
}
if ($ReviewerReasoning) { $record['reviewer_reasoning'] = $ReviewerReasoning }
if ($ReviewerProofFolder) { $record['reviewer_proof_folder'] = [IO.Path]::GetFullPath($ReviewerProofFolder) }
$record | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'run.json')
Write-Host "workspace: $ws (seed $baseSha)"
Write-Host "prepared: $out"
if (-not $Launch -and -not $MockAgent) { Write-Host 'Preparation only; no MXC workload or model call launched.'; return }
$mxcState = Join-Path $cfg 'mxc-runner'
if ($MxcBuildSource) {
    . (Join-Path $adapter 'copy-vetted-mxc-build.ps1')
    Copy-VettedMxcBuild -BuildSource $MxcBuildSource -StateRoot $mxcState `
        -SourceDirectory (Join-Path $repoRoot 'mxc-sandbox\scripts\host\MxcClaude') `
        -PinPath (Join-Path $adapter 'profile\mxc-pin.json') `
        -ReportPath (Join-Path $out 'mxc-build-provenance.json') | Out-Null
}
if ($Launch) {
    $reviewerProofArgs = if ($ReviewerProofFolder) { @('--reviewer-proof-folder', $ReviewerProofFolder) } else { @() }
    & $python (Join-Path $adapter 'paid-diagnostic-audit.py') --run-folder $out `
        --native-proof-folder $NativeProofFolder --pin (Join-Path $adapter 'profile\mxc-pin.json') `
        --forbidden-skill-root $forbiddenSkillRoot `
        --source-directory (Join-Path $repoRoot 'mxc-sandbox\scripts\host\MxcClaude') @reviewerProofArgs
    if ($LASTEXITCODE -ne 0) { throw "Paid launch native proof failed; inspect $out\native-proof-validation.json. No contestant launched." }
}

# Serialize this dedicated auth/session store, without touching its auth files.
$lock = [IO.File]::Open((Join-Path $ToolsDir '.codex-baseline.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
try {
    $empty = Invoke-Oracle $ws (Join-Path $out 'oracle-seed-output.txt')
    if ($empty.passed -gt 0 -or $empty.exit_code -ne 1 -or ($empty.failed + $empty.errors) -eq 0) { throw 'Seed oracle did not establish expected test failures' }
    $started = (Get-Date).ToUniversalTime()
    $savedExe = $env:MXC_CLAUDE_EXE
    $savedMxcHome = $env:MXC_SANDBOX_HOME
    $env:MXC_CLAUDE_EXE = $python
    $env:MXC_SANDBOX_HOME = $mxcState
    try {
        & $mxc @hostArgs -- @codexArgs > (Join-Path $out 'stream.jsonl') 2> (Join-Path $out 'stderr.txt')
        $exitCode = $LASTEXITCODE
    } finally { $env:MXC_CLAUDE_EXE = $savedExe; $env:MXC_SANDBOX_HOME = $savedMxcHome }
    $ended = (Get-Date).ToUniversalTime()
    $record.started_utc = $started.ToString('o'); $record.ended_utc = $ended.ToString('o')
    $record.wall_time_s = [int]($ended - $started).TotalSeconds; $record.exit_code = $exitCode
    $record.exit_reason = if ($exitCode -eq 124) { 'timeout' } elseif ($exitCode -eq 0) { 'completed' } else { 'crash' }
    $record.is_error = $exitCode -ne 0
    $events = @(Get-Content (Join-Path $out 'stream.jsonl') | ForEach-Object { try { $_ | ConvertFrom-Json -ErrorAction Stop } catch { } })
    if ($MockAgent) {
        $summary = $events | Where-Object type -eq 'mock_summary' | Select-Object -Last 1
        if ($summary) {
            $summary | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $out 'mock-summary.json')
            $record.runtime_toolchain_verified = $summary.ok -eq $true
        }
        if (-not $summary -or $summary.ok -ne $true) {
            $record.is_error = $true; $record.exit_reason = 'mock-checks-failed'
        }
    }
    if (@($events | Where-Object { $_.type -in @('turn.failed', 'error') }).Count -gt 0) {
        $record.is_error = $true; $record.exit_reason = 'turn-failed'
    } elseif (-not ($events | Where-Object type -eq 'turn.completed')) {
        $record.is_error = $true
        if ($exitCode -eq 0) { $record.exit_reason = 'missing-turn-completed' }
    }
    $thread = $events | Where-Object type -eq 'thread.started' | Select-Object -First 1
    if ($thread) {
        $record.session_id = $thread.thread_id
        $sessions = Join-Path $CodexHome 'sessions'
        # Only rollout transcripts are enumerated, never the home or auth files.
        & $python (Join-Path $adapter 'capture-rollouts.py') --sessions $sessions --thread-id $thread.thread_id --output $out
        if ($LASTEXITCODE -ne 0) { $record.is_error = $true; $record.exit_reason = 'missing-or-ambiguous-rollout' }
    } else { $record.is_error = $true; $record.exit_reason = 'missing-thread-id' }
    $record.plugin_modified_during_run = (Get-TreeHash $pluginRun) -ne $exportHash
    $runs = @(1..3 | ForEach-Object { Invoke-Oracle $ws (Join-Path $out 'oracle-output.txt') })
    $first = $runs[0]
    $record.oracle = [ordered]@{ collected = $first.passed + $first.failed + $first.errors + $first.skipped; passed = $first.passed; failed = $first.failed; errors = $first.errors; skipped = $first.skipped
        stable_over_3 = @($runs | ForEach-Object { "$(ConvertTo-Json $_ -Compress)" } | Select-Object -Unique).Count -eq 1 }
    Invoke-Git @('-C', $ws, 'bundle', 'create', (Join-Path $out 'solution.bundle'), '--all') | Out-Null
    $record.commits = [int](Invoke-Git @('-C', $ws, 'rev-list', '--count', "$baseSha..HEAD"))
    $record.raw_sha256 = [ordered]@{ stream = Get-Sha (Join-Path $out 'stream.jsonl'); session = Get-Sha (Join-Path $out 'session.jsonl') }
    if ($Launch) {
        # Preserve oracle/bundle/rollouts first; diagnostics must pass before automatic analysis.
        $record | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'run.json')
        & $python (Join-Path $adapter 'paid-diagnostic-audit.py') --run-folder $out `
            --runtime-evidence (Join-Path $runTmp 'native-hook-trust') --forbidden-skill-root $forbiddenSkillRoot `
            --pin (Join-Path $adapter 'profile\mxc-pin.json') `
            --source-directory (Join-Path $repoRoot 'mxc-sandbox\scripts\host\MxcClaude')
        $record.diagnostics_passed = $LASTEXITCODE -eq 0
        $record.runtime_parity_verified = $record.diagnostics_passed
        $record.runtime_toolchain_verified = $record.diagnostics_passed
        if (-not $record.diagnostics_passed) {
            $record.is_error = $true; $record.exit_reason = 'diagnostics-failed'
            $record.analysis_status = 'diagnostics-failed'
        }
    }
} finally {
    $record | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'run.json')
    $lock.Dispose()
}
if (-not $record.is_error) {
    & $python (Join-Path $PSScriptRoot 'analyze-run.py') $out --token-ceiling $caseCfg.token_ceiling
    if ($LASTEXITCODE -ne 0) { throw "Codex trace analysis failed: $out" }
}
# Host-side Langfuse upload of the captured rollouts; fails open (result in langfuse.json).
if ($env:TRACE_TO_LANGFUSE -eq 'true' -and -not $MockAgent -and $record.session_id) {
    & $python (Join-Path $PSScriptRoot 'langfuse-upload.py') $out --tools-dir (Join-Path $ToolsDir 'langfuse')
}
Write-Host "stored: $out (analysis status: $($record.analysis_status); score-run.py requires reviewed manual verdicts)"
if ($MockAgent -and $record.is_error) { throw "Codex mock failed: $out" }
if ($Launch -and $record.is_error) { throw "Codex paid run failed ($($record.exit_reason)); evidence preserved: $out" }
