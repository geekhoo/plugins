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
Runs on Windows (ProcessContainer) and Linux/macOS (Bubblewrap/Seatbelt); see run-baseline.ps1.
With TRACE_TO_LANGFUSE=true on the host, the pinned Langfuse Codex Stop hook uploads each turn,
child thread, tool call and reasoning summary untruncated (evals/telemetry/README.md).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('c0-wordstat', 'c1-csvledger', 'c2-linkvault', 'c3-minisql')][string]$Case,
    [string]$Model = 'gpt-6.1-sol',
    [ValidateSet('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')][string]$Reasoning = 'high',
    [string]$WorkerModel,
    [ValidateSet('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')][string]$WorkerReasoning,
    [ValidateSet('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')][string]$ReviewerReasoning,
    [int]$TimeoutSec,
    [int]$CloseoutReserveSec = 0,
    [string]$AuthorizationReference,
    [string]$ToolsDir,
    [string]$WorkRoot,
    [string]$CodexHome,
    [string]$CodexExe,
    [string]$MxcBuildSource,
    [string]$NativeProofFolder,
    [string]$ReviewerProofFolder,
    # Explicit owner override; does not claim native qualification or relax MXC isolation.
    [switch]$SkipNativeQualification,
    [string]$QualificationOverrideReason,
    [switch]$MockAgent,
    [ValidateSet('happy', 'all', 'fail')][string]$MockScenario = 'happy',
    [switch]$Launch,
    [switch]$NoTelemetry,
    # Route every model through LiteLLM's Responses API (LITELLM_PROXY_URL, LITELLM_PROXY_API_KEY);
    # models are given run-scoped catalog entries (classic JSON tools, multi-agent v2).
    [switch]$Litellm,
    [int]$ContextWindow = 200000,
    # Debugging: a RUST_LOG filter for the contestant Codex process; its log lands in stderr.txt.
    [string]$CodexRustLog
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'run-lifecycle.ps1')
$PSNativeCommandUseErrorActionPreference = $false
if ($MockAgent -and $Launch) { throw 'Choose -MockAgent or -Launch, not both.' }
if ($SkipNativeQualification -and -not $QualificationOverrideReason) {
    throw '-SkipNativeQualification requires an explicit -QualificationOverrideReason.'
}
if ($SkipNativeQualification -and ($NativeProofFolder -or $ReviewerProofFolder)) {
    throw 'Choose native proof or the owner override, not both.'
}
# The vetted host build and the native proof are Windows ProcessContainer artifacts. Elsewhere the host is
# built from source and a launch without native proof is recorded as such (never reference-eligible).
$windowsHost = $IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop'
if ($Launch -and $windowsHost -and -not $MxcBuildSource) { throw '-Launch requires an explicit -MxcBuildSource containing the vetted pinned build.' }
if ($Launch -and -not $SkipNativeQualification -and $windowsHost -and -not $NativeProofFolder) { throw '-Launch requires an explicit -NativeProofFolder containing passing model-free native proof.' }
if ($Launch -and -not $SkipNativeQualification -and $ReviewerReasoning -and -not $ReviewerProofFolder) { throw 'Reviewer settings require an explicit -ReviewerProofFolder proving the architect reviewer role.' }
if (-not $WorkerModel) { $WorkerModel = $Model }
if (-not $WorkerReasoning) { $WorkerReasoning = $Reasoning }

$onWindows = $IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop'
if (-not $ToolsDir) { $ToolsDir = if ($onWindows) { 'C:\repos\.eval-tools' } else { Join-Path $HOME 'repos/.eval-tools' } }
if (-not $WorkRoot) { $WorkRoot = if ($onWindows) { 'C:\repos' } else { Join-Path $HOME 'repos' } }
$plugin = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$repoRoot = (Resolve-Path (Join-Path $plugin '..')).Path
$caseDir = Join-Path $plugin "evals/cases/$Case"
$adapter = Join-Path $plugin 'evals/adapters/codex'
$forbiddenSkillRoot = Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)) '.agents/skills'
$agentPyBin = Join-Path $ToolsDir $(if ($onWindows) { 'agent-py\Scripts' } else { 'agent-py/bin' })
$python = Join-Path $agentPyBin $(if ($onWindows) { 'python.exe' } else { 'python' })
if (-not $CodexHome) { $CodexHome = Join-Path $ToolsDir 'codex-home' }
$CodexHome = [IO.Path]::GetFullPath($CodexHome)
if (-not $CodexExe) { $CodexExe = Join-Path $ToolsDir "codex/0.164.0/bin/$(if ($onWindows) { 'codex.exe' } else { 'codex' })" }
$codexExe = (Resolve-Path -LiteralPath $CodexExe).Path
$tarExe = if ($onWindows) { Join-Path $env:SystemRoot 'System32\tar.exe' } else { 'tar' } # Never select MSYS tar for a C: path.
$mxc = Join-Path $repoRoot 'mxc-sandbox/scripts/mxc.ps1'
$mxcHostSource = Join-Path $repoRoot 'mxc-sandbox/scripts/host/MxcClaude'
$mxcPin = Join-Path $adapter 'profile/mxc-pin.json'
foreach ($required in @($python, $CodexHome, $mxc) + @(if ($onWindows) { $tarExe }) + @( (Join-Path $adapter 'prepare-profile.py'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing prerequisite: $required" }
}
& $python -c 'import pytest'
if ($LASTEXITCODE) { throw 'agent-py must have pytest installed' }
$caseCfg = Get-Content (Join-Path $caseDir 'case.json') -Raw | ConvertFrom-Json
if (-not $PSBoundParameters.ContainsKey('TimeoutSec')) { $TimeoutSec = [int]$caseCfg.wall_time_ceiling_s }
if ($TimeoutSec -le 0) { throw 'TimeoutSec must be positive' }
if ($CloseoutReserveSec -lt 0 -or $CloseoutReserveSec -ge $TimeoutSec) { throw 'CloseoutReserveSec must be nonnegative and smaller than TimeoutSec' }

function Invoke-Git {
    $result = & git @args
    if ($LASTEXITCODE) { throw "git failed: $($args[0])" }
    return $result
}
function Get-TreeHash([string]$Directory) {
    # Include relative names: renamed files must count as tampering too.
    $entries = Get-ChildItem -LiteralPath $Directory -Recurse -File |
        Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' } | Sort-Object FullName |
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
$out = Join-Path $plugin "evals/baselines/$Case/$stamp"
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
$recordPath = Join-Path $out 'run.json'
$waiver = [ordered]@{
    status = $(if ($SkipNativeQualification) { 'waived-by-owner' } else { 'required-for-windows-launch' })
    override_reason = $(if ($SkipNativeQualification) { $QualificationOverrideReason } else { $null })
}
$execution = New-EvalExecution $TimeoutSec $CloseoutReserveSec 0 $AuthorizationReference $waiver `
    ([ordered]@{ model = $Model; reasoning = $Reasoning; worker_model = $WorkerModel; worker_reasoning = $WorkerReasoning
        reviewer_reasoning = $ReviewerReasoning; mock = [bool]$MockAgent; provider = $(if ($Litellm) { 'litellm' } else { 'openai' }) })
$record = [ordered]@{ schema = 'geeky-eval.baseline/1'; case = $Case; harness = 'codex'; model = $Model
    workspace = $ws; config_directory = $cfg; seed_sha = $baseSha; plugin_sha = $pluginSha
    started_utc = $null; ended_utc = $null; exit_code = $null; exit_reason = 'prepared'
    is_error = $false; reference_eligible = $false; analysis_status = 'not-started'; execution = $execution }
Write-EvalRecord $record $recordPath
$lock = $null
$finalizationStart = Get-EvalMonotonicSeconds
try {
$archive = Join-Path $cfg 'plugin.tar'
Invoke-Git @('-C', $repoRoot, 'archive', '--format=tar', "--output=$archive", $pluginSha, 'geeky-orchestration', ':(exclude)geeky-orchestration/evals') | Out-Null
& $tarExe -xf $archive -C $export
if ($LASTEXITCODE) { throw 'Plugin export extraction failed' }
$pluginRun = Join-Path $export 'geeky-orchestration'
if (Test-Path (Join-Path $pluginRun 'evals')) { throw 'Export contains forbidden evals directory' }
$exportHash = Get-TreeHash $pluginRun

# Only the established placeholder substitution changes the canonical prompt.
$prompt = (Get-Content (Join-Path $plugin 'evals/prompts/end-to-end.md') -Raw).Replace('{{PLANNING_FOLDER}}', 'docs/spec-001-feature/')
$promptSha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($prompt))).ToLowerInvariant()
$profileResult = Join-Path $cfg 'codex-profile.json'
$reviewerArgs = if ($ReviewerReasoning) { @('--reviewer-reasoning', $ReviewerReasoning) } else { @() }
. (Join-Path $plugin 'evals/telemetry/telemetry.ps1')
$telemetry = Resolve-EvalTelemetry -Harness codex -ToolsDir $ToolsDir -Case $Case -Stamp $stamp -PluginSha $pluginSha `
    -Model $Model -Reasoning $Reasoning -WorkerModel $WorkerModel -WorkerReasoning $WorkerReasoning -ReviewerReasoning $ReviewerReasoning `
    -Provider $(if ($Litellm) { 'litellm' } else { 'openai' }) -Mock:$MockAgent -Disabled:$NoTelemetry
$telemetryArgs = if ($telemetry) { @('--telemetry-node', $telemetry.Node, '--telemetry-hook', $telemetry.HookScript) } else { @() }
$providerArgs = @()
if ($Litellm) {
    $litellmUrl = if ($env:LITELLM_PROXY_URL) { $env:LITELLM_PROXY_URL } else { throw '-Litellm needs LITELLM_PROXY_URL' }
    if (-not $env:LITELLM_PROXY_API_KEY) { throw '-Litellm needs LITELLM_PROXY_API_KEY' }
    # Catalog entries derive from this pinned binary's own catalog; an empty CODEX_HOME keeps auth out of it.
    $catalogBase = Join-Path $cfg 'codex-models.json'
    $catalogHome = Join-Path $cfg 'catalog-home'
    New-Item -ItemType Directory -Path $catalogHome | Out-Null
    $savedHome = $env:CODEX_HOME; $env:CODEX_HOME = $catalogHome
    try { $null | & $codexExe debug models | Set-Content -LiteralPath $catalogBase -Encoding utf8 } finally { $env:CODEX_HOME = $savedHome }
    if ($LASTEXITCODE) { throw 'codex debug models failed' }
    $providerArgs = @('--provider-base-url', ($litellmUrl.TrimEnd('/') + '/v1'), '--provider-env-key', 'LITELLM_PROXY_API_KEY',
        '--catalog-base', $catalogBase, '--context-window', $ContextWindow)
}
& $python (Join-Path $adapter 'prepare-profile.py') --plugin $pluginRun --home $runHome --codex-home $CodexHome --tools-dir $ToolsDir --profile (Join-Path $adapter 'profile') --output $profileResult --model $Model --reasoning $Reasoning --worker-model $WorkerModel --worker-reasoning $WorkerReasoning @reviewerArgs @telemetryArgs @providerArgs
$preflightCode = $LASTEXITCODE
if (Test-Path -LiteralPath $profileResult) { Copy-Item -LiteralPath $profileResult -Destination (Join-Path $out 'parity-preflight.json') }
if ($preflightCode -ne 0 -or -not (Test-Path -LiteralPath $profileResult)) {
    throw "Codex parity preflight failed; inspect $(Join-Path $out 'parity-preflight.json'). No contestant launched."
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
        '--mock-forbidden-path', (Join-Path $plugin 'agents/geeky-coder.md'))
} elseif ($Launch) {
    $trustedExec = Join-Path $cfg 'trusted-exec.py'
    Copy-Item (Join-Path $plugin 'evals/telemetry/codex-flush.py') $cfg   # post-run Langfuse replay
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
    '--env', "PATH=$agentPyBin$([IO.Path]::PathSeparator)$env:PATH", '--env', "VIRTUAL_ENV=$(Join-Path $ToolsDir 'agent-py')",
    '--env', 'GIT_AUTHOR_NAME=geeky-eval-agent', '--env', 'GIT_AUTHOR_EMAIL=agent@geeky-eval.local',
    '--env', 'GIT_COMMITTER_NAME=geeky-eval-agent', '--env', 'GIT_COMMITTER_EMAIL=agent@geeky-eval.local')
if ($telemetry) { $hostArgs += @($telemetry.RoPaths | ForEach-Object { '--ro', $_ }) + $telemetry.EnvArgs }
if ($Litellm) { $hostArgs += @('--env', 'LITELLM_PROXY_API_KEY') }   # bare name: the MXC host copies the value
if ($CodexRustLog) { $hostArgs += @('--env', "RUST_LOG=$CodexRustLog") }

$record = [ordered]@{
    schema = 'geeky-eval.baseline/1'; case = $Case; harness = 'codex'; harness_version = (& $codexExe --version | Out-String).Trim()
    model = $Model; reasoning = $Reasoning; approach = $(if ($MockAgent) { "mock-agent:$MockScenario" } else { 'canonical-prompt' }); plugin_sha = $pluginSha
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
    native_proof_folder = $(if ($Launch -and $NativeProofFolder) { [IO.Path]::GetFullPath($NativeProofFolder) } else { $null })
    native_qualification = [ordered]@{
        status = $(if ($SkipNativeQualification) { 'waived-by-owner' } else { 'required-for-windows-launch' })
        override_reason = $(if ($SkipNativeQualification) { $QualificationOverrideReason } else { $null })
    }
    provider = $(if ($Litellm) { [ordered]@{ name = 'litellm'; base_url = $litellmUrl; context_window = $ContextWindow } } else { $null })
    telemetry = $(if ($telemetry) { $telemetry.Record } else { [ordered]@{ enabled = $false } })
}
if ($ReviewerReasoning) { $record['reviewer_reasoning'] = $ReviewerReasoning }
if ($ReviewerProofFolder) { $record['reviewer_proof_folder'] = [IO.Path]::GetFullPath($ReviewerProofFolder) }
$record['execution'] = $execution
$hostArgs += @('--env', "GEEKY_DEADLINE_UTC=$($record.execution.initial_deadline_utc)", '--env', "GEEKY_CLOSEOUT_RESERVE_S=$CloseoutReserveSec")
Write-EvalRecord $record $recordPath
Write-Host "workspace: $ws (seed $baseSha)"
Write-Host "prepared: $out"
if (-not $Launch -and -not $MockAgent) { Write-Host 'Preparation only; no MXC workload or model call launched.'; return }
Set-EvalStep $record $recordPath 'launch-preparation'
$mxcState = Join-Path $cfg 'mxc-runner'
if ($MxcBuildSource) {
    . (Join-Path $adapter 'copy-vetted-mxc-build.ps1')
    Copy-VettedMxcBuild -BuildSource $MxcBuildSource -StateRoot $mxcState `
        -SourceDirectory $mxcHostSource `
        -PinPath $mxcPin `
        -ReportPath (Join-Path $out 'mxc-build-provenance.json') | Out-Null
}
if ($Launch -and -not $SkipNativeQualification -and $NativeProofFolder) {
    $reviewerProofArgs = if ($ReviewerProofFolder) { @('--reviewer-proof-folder', $ReviewerProofFolder) } else { @() }
    & $python (Join-Path $adapter 'paid-diagnostic-audit.py') --run-folder $out `
        --native-proof-folder $NativeProofFolder --pin $mxcPin `
        --forbidden-skill-root $forbiddenSkillRoot `
        --source-directory $mxcHostSource @reviewerProofArgs
    if ($LASTEXITCODE -ne 0) { throw "Paid launch native proof failed; inspect $(Join-Path $out 'native-proof-validation.json'). No contestant launched." }
}

# Serialize this dedicated auth/session store, without touching its auth files.
$lock = [IO.File]::Open((Join-Path $ToolsDir '.codex-baseline.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    Set-EvalStep $record $recordPath 'seed-oracle'
    $empty = Invoke-Oracle $ws (Join-Path $out 'oracle-seed-output.txt')
    if ($empty.passed -gt 0 -or $empty.exit_code -ne 1 -or ($empty.failed + $empty.errors) -eq 0) { throw 'Seed oracle did not establish expected test failures' }
    $started = (Get-Date).ToUniversalTime()
    $savedExe = $env:MXC_CLAUDE_EXE
    $savedMxcHome = $env:MXC_SANDBOX_HOME
    $env:MXC_CLAUDE_EXE = $python
    $env:MXC_SANDBOX_HOME = $mxcState
    try {
        if (-not (Start-EvalInvocation $record $recordPath 'initial' ([ref]$hostArgs))) { throw 'Attempt deadline exhausted before launch' }
        & $mxc @hostArgs -- @codexArgs > (Join-Path $out 'stream.jsonl') 2> (Join-Path $out 'stderr.txt')
        $exitCode = $LASTEXITCODE
        Complete-EvalInvocation $record $recordPath $exitCode
    } finally { $env:MXC_CLAUDE_EXE = $savedExe; $env:MXC_SANDBOX_HOME = $savedMxcHome }
    $ended = (Get-Date).ToUniversalTime()
    $record.started_utc = $started.ToString('o'); $record.ended_utc = $ended.ToString('o')
    $record.wall_time_s = [int]($ended - $started).TotalSeconds; $record.exit_code = $exitCode
    $record.exit_reason = if ($exitCode -eq 124) { 'timeout' } elseif ($exitCode -eq 0) { 'completed' } else { 'crash' }
    $record.is_error = $exitCode -ne 0
    $finalizationStart = Get-EvalMonotonicSeconds
    Set-EvalStep $record $recordPath 'parsing'
    $events = @(Get-Content (Join-Path $out 'stream.jsonl') | ForEach-Object { try { $_ | ConvertFrom-Json -ErrorAction Stop } catch { } })
    if ($MockAgent) {
        $summary = $events | Where-Object type -eq 'mock_summary' | Select-Object -Last 1
        if ($summary) {
            $summary | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $out 'mock-summary.json')
            $record.runtime_toolchain_verified = $summary.ok -eq $true
        }
        if (-not $summary -or $summary.ok -ne $true) {
            $record.is_error = $true; $record.exit_reason = 'mock-checks-failed'
            $record.execution.postprocessing['parsing'] = 'incomplete'
        }
    }
    if (@($events | Where-Object { $_.type -in @('turn.failed', 'error') }).Count -gt 0) {
        $record.is_error = $true; $record.exit_reason = 'turn-failed'
        $record.execution.postprocessing['parsing'] = 'incomplete'
    } elseif (-not ($events | Where-Object type -eq 'turn.completed')) {
        $record.is_error = $true
        $record.execution.postprocessing['parsing'] = 'incomplete'
        if ($exitCode -eq 0) { $record.exit_reason = 'missing-turn-completed' }
    }
    $thread = $events | Where-Object type -eq 'thread.started' | Select-Object -First 1
    if ($thread) {
        Set-EvalStep $record $recordPath 'native-capture'
        $record.session_id = $thread.thread_id
        $sessions = Join-Path $CodexHome 'sessions'
        # Only rollout transcripts are enumerated, never the home or auth files.
        & $python (Join-Path $adapter 'capture-rollouts.py') --sessions $sessions --thread-id $thread.thread_id --output $out
        if ($LASTEXITCODE -ne 0) {
            $record.is_error = $true; $record.exit_reason = 'missing-or-ambiguous-rollout'
            $record.execution.postprocessing['native-capture'] = 'incomplete'
        }
        # The Stop hook only fires when a turn ends; a run that times out or is killed mid-turn would leave
        # Langfuse empty. Replay the main rollout (children are found beside it) through the tracer in a short
        # network-enabled MXC workload: its exporter ignores proxies, so it needs the sandbox's direct egress.
        $rollout = Get-ChildItem -LiteralPath $sessions -Recurse -Filter "rollout-*$($thread.thread_id).jsonl" | Select-Object -First 1
        if ($telemetry -and $Launch -and $rollout) {
            Set-EvalStep $record $recordPath 'telemetry-replay'
            $payloadFile = Join-Path $runTmp 'codex-flush-payload.json'
            @{ session_id = $thread.thread_id; transcript_path = $rollout.FullName; hook_event_name = 'Stop' } | ConvertTo-Json -Compress |
                Set-Content -LiteralPath $payloadFile -NoNewline
            $flushArgs = @('run', '--workspace', $runTmp, '--allow-win32k', '--rw', $CodexHome, '--ro', $ToolsDir, '--ro', $cfg, '--timeout', 900,
                '--env', "PATH=$env:PATH") + @($telemetry.RoPaths | ForEach-Object { '--ro', $_ }) + $telemetry.EnvArgs
            $env:MXC_CLAUDE_EXE = $python; $env:MXC_SANDBOX_HOME = $mxcState
            try {
                & $mxc @flushArgs -- (Join-Path $cfg 'codex-flush.py') $telemetry.Node $telemetry.HookScript $payloadFile *> (Join-Path $out 'langfuse-flush.log')
                $telemetry.Record.host_flush = "exit $LASTEXITCODE"
                if ($LASTEXITCODE -ne 0) { $record.execution.postprocessing['telemetry-replay'] = 'incomplete' }
            } finally { $env:MXC_CLAUDE_EXE = $savedExe; $env:MXC_SANDBOX_HOME = $savedMxcHome }
        }
    } else {
        $record.is_error = $true; $record.exit_reason = 'missing-thread-id'
        $record.execution.postprocessing['parsing'] = 'incomplete'
        $record.execution.postprocessing['native-capture'] = 'not-available'
    }
    $record.plugin_modified_during_run = (Get-TreeHash $pluginRun) -ne $exportHash
    Set-EvalStep $record $recordPath 'oracle'
    $runs = @(1..3 | ForEach-Object { Invoke-Oracle $ws (Join-Path $out 'oracle-output.txt') })
    $first = $runs[0]
    $record.oracle = [ordered]@{ collected = $first.passed + $first.failed + $first.errors + $first.skipped; passed = $first.passed; failed = $first.failed; errors = $first.errors; skipped = $first.skipped
        stable_over_3 = @($runs | ForEach-Object { "$(ConvertTo-Json $_ -Compress)" } | Select-Object -Unique).Count -eq 1 }
    Invoke-Git @('-C', $ws, 'bundle', 'create', (Join-Path $out 'solution.bundle'), '--all') | Out-Null
    $record.commits = [int](Invoke-Git @('-C', $ws, 'rev-list', '--count', "$baseSha..HEAD"))
    $record.raw_sha256 = [ordered]@{ stream = Get-Sha (Join-Path $out 'stream.jsonl'); session = Get-Sha (Join-Path $out 'session.jsonl') }
    Set-EvalStep $record $recordPath 'telemetry'
    if ($telemetry) { Save-EvalTelemetry -Telemetry $telemetry -SessionId $record.session_id -OutDir $out -Python $python }
    if ($telemetry -and -not $telemetry.Record.delivered) { $record.execution.postprocessing['telemetry'] = 'pending-or-incomplete' }
    if ($Launch -and (Test-Path (Join-Path $runTmp 'native-hook-trust'))) {
        # Launch evidence (codex-exit.json, hook catalogue, denial proof) travels with the run.
        Copy-Item (Join-Path $runTmp 'native-hook-trust') (Join-Path $out 'launch-evidence') -Recurse -Exclude 'hook-catalog-home'
    }
    if ($Launch -and ($SkipNativeQualification -or -not $NativeProofFolder)) {
        # No qualification claim when explicitly waived or when no native proof exists.
        $record.diagnostics_passed = $null
        $record.runtime_parity_verified = $false
    } elseif ($Launch) {
        # Preserve oracle/bundle/rollouts first; diagnostics must pass before automatic analysis.
        Set-EvalStep $record $recordPath 'diagnostics'
        & $python (Join-Path $adapter 'paid-diagnostic-audit.py') --run-folder $out `
            --runtime-evidence (Join-Path $runTmp 'native-hook-trust') --forbidden-skill-root $forbiddenSkillRoot `
            --pin $mxcPin `
            --source-directory $mxcHostSource
        $record.diagnostics_passed = $LASTEXITCODE -eq 0
        $record.runtime_parity_verified = $record.diagnostics_passed
        $record.runtime_toolchain_verified = $record.diagnostics_passed
        if (-not $record.diagnostics_passed) {
            $record.execution.postprocessing['diagnostics'] = 'failed'
            $record.is_error = $true; $record.exit_reason = 'diagnostics-failed'
            $record.analysis_status = 'diagnostics-failed'
        }
    }
if (-not $record.is_error) {
    Set-EvalStep $record $recordPath 'analysis'
    $record.analysis_status = 'in-progress'
    $analysisOut = Join-Path $out 'derived'
    & $python (Join-Path $PSScriptRoot 'analyze-run.py') $out --token-ceiling $caseCfg.token_ceiling --out $analysisOut
    if ($LASTEXITCODE -ne 0) { throw "Codex trace analysis failed: $out" }
    $analyzed = Get-Content -LiteralPath (Join-Path $analysisOut 'run.json') -Raw | ConvertFrom-Json -AsHashtable
    foreach ($key in $analyzed.Keys) { if ($key -ne 'execution') { $record[$key] = $analyzed[$key] } }
    Copy-Item -LiteralPath (Join-Path $analysisOut 'analysis.json') -Destination (Join-Path $out 'analysis.json')
} else { $record.analysis_status = 'skipped-process-or-capture-error' }
} catch {
    if ($record.execution.active_step -eq 'capture' -or $record.execution.process_outcome -eq 'not-started') { $finalizationStart = Get-EvalMonotonicSeconds }
    Set-EvalFailure $record $_
    throw
} finally {
    try {
        if ($record.execution.state -eq 'prepared') { Write-EvalRecord $record $recordPath }
        else { Save-EvalFinalRecord $record $recordPath $ws $finalizationStart }
    }
    finally { if ($lock) { $lock.Dispose() } }
}
Write-Host "stored: $out (analysis status: $($record.analysis_status); score-run.py requires reviewed manual verdicts)"
if ($MockAgent -and $record.is_error) { throw "Codex mock failed: $out" }
if ($Launch -and $record.is_error) { throw "Codex paid run failed ($($record.exit_reason)); evidence preserved: $out" }
