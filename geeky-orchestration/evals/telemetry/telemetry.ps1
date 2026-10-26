# Langfuse telemetry for MXC eval runs, shared by run-baseline.ps1 and run-codex-baseline.ps1.
# Dot-source this file. Telemetry is on when the host has TRACE_TO_LANGFUSE=true and the runner was
# not given -NoTelemetry. Secrets reach the sandbox only as bare `--env NAME` (copied by the MXC
# host, never printed); everything else is a plain NAME=VALUE.

function Get-EvalTelemetryNaming {
    param(
        [ValidateSet('claude-code', 'codex')][string]$Harness,
        [ValidateSet('win', 'linux', 'mac')][string]$Platform,
        [string]$Case,
        [string]$Stamp
    )
    if (-not $Platform) {
        $Platform = if ($IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop') { 'win' } elseif ($IsMacOS) { 'mac' } else { 'linux' }
    }
    $environment = "mxc-$Platform"
    $family = "$(if ($Harness -eq 'codex') { 'codex' } else { 'claude' })-$environment"
    $sessionId = "$family-$Case-$Stamp"
    if ($sessionId.Length -ge 200 -or $sessionId -cmatch '[^\x20-\x7e]') { throw 'Invalid telemetry session identity.' }
    [pscustomobject]@{ Platform = $Platform; Environment = $environment; Family = $family; SessionId = $sessionId }
}

function Resolve-EvalTelemetry {
    param(
        [Parameter(Mandatory)][ValidateSet('claude-code', 'codex')][string]$Harness,
        [Parameter(Mandatory)][string]$ToolsDir,
        [Parameter(Mandatory)][string]$Case,
        [Parameter(Mandatory)][string]$Stamp,
        [Parameter(Mandatory)][string]$PluginSha,
        # Read-only run config folder (the Claude hook bootstrap is copied there) and a read-write
        # folder for the Claude hook's state and log.
        [string]$ConfigDir,
        [string]$StateDir,
        [string]$Model,
        [string]$Reasoning,
        [string]$WorkerModel,
        [string]$WorkerReasoning,
        [string]$ReviewerReasoning,
        [string]$Provider,
        [switch]$Mock,
        [switch]$Disabled
    )
    if ($Disabled -or $env:TRACE_TO_LANGFUSE -ne 'true') { return $null }
    $onWindows = $IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop'
    $codex = $Harness -eq 'codex'
    $pins = Get-Content (Join-Path $PSScriptRoot 'pins.json') -Raw | ConvertFrom-Json

    # The Codex plugin prefers LANGFUSE_CODEX_* over LANGFUSE_*; the Claude hook reads LANGFUSE_*.
    $keyNames = foreach ($suffix in 'PUBLIC_KEY', 'SECRET_KEY', 'BASE_URL') {
        $candidates = @(if ($codex) { "LANGFUSE_CODEX_$suffix" }) + "LANGFUSE_$suffix"
        $found = $candidates | Where-Object { [Environment]::GetEnvironmentVariable($_) } | Select-Object -First 1
        if (-not $found) { throw "TRACE_TO_LANGFUSE=true but $($candidates -join ' / ') is not set; set it or pass -NoTelemetry." }
        $found
    }
    $baseUrl = [Environment]::GetEnvironmentVariable($keyNames[2])
    $naming = Get-EvalTelemetryNaming -Harness $Harness -Case $Case -Stamp $Stamp
    $platform = $naming.Platform
    $environment = $naming.Environment
    $family = $naming.Family
    $sessionId = $naming.SessionId
    $hostTags = [Environment]::GetEnvironmentVariable($(if ($codex) { 'LANGFUSE_CODEX_TAGS' } else { 'CC_LANGFUSE_TRACE_TAGS' }))
    $extraTags = if ($hostTags -and $hostTags.Trim().StartsWith('[')) { @($hostTags | ConvertFrom-Json) } `
        elseif ($hostTags) { @($hostTags -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) } else { @() }
    $tags = @('geeky-eval', 'identity:agent-v1', "harness:$Harness", "platform:$platform", "environment:$environment", "agent-family:$family",
        "case:$Case", "run:$Stamp", "plugin:$($PluginSha.Substring(0, 7))") +
        @(if ($Mock) { 'mock' }) + $extraTags
    $tags = @($tags | Select-Object -Unique)
    $tagsJson = ConvertTo-Json -InputObject $tags -Compress
    $traceName = "$family-orchestrator"
    # The adapter replaces this fallback with the source-bound native actor ID.
    $userId = "$family-orchestrator"
    $metadata = [ordered]@{ identity_schema = 'geeky-eval.agent-identity/1'; harness = $Harness; platform = $platform;
        environment = $environment; agent_family = $family; case = $Case; run = $Stamp; run_group_id = $sessionId;
        plugin_sha = $PluginSha; configured_model = $(if ($Model) { $Model } else { 'runner-default' });
        configured_reasoning = $(if ($Reasoning) { $Reasoning } else { 'runner-default' });
        worker_model = $(if ($WorkerModel) { $WorkerModel } elseif ($Model) { $Model } else { 'runner-default' });
        worker_reasoning = $(if ($WorkerReasoning) { $WorkerReasoning } else { 'runner-default' });
        reviewer_reasoning = $(if ($ReviewerReasoning) { $ReviewerReasoning } else { 'runner-default' });
        provider = $(if ($Mock) { 'mock' } elseif ($Provider) { $Provider } else { 'runner-default' });
        configured_provider = $(if ($Provider) { $Provider } else { 'runner-default' }); mock = $(if ($Mock) { 'true' } else { 'false' });
        claude_hook_commit = $pins.claude_hook.commit; codex_tracer_version = $pins.codex_plugin.version }
    $metadataJson = ConvertTo-Json $metadata -Compress

    # Both SDKs cap each OTLP export at LANGFUSE_TIMEOUT seconds (default 5); a full eval session's batch
    # takes longer, and the hook then fails open with nothing delivered (C1 Codex run 3 replay).
    $envArgs = @('--env', 'TRACE_TO_LANGFUSE=true', '--env', "LANGFUSE_TRACING_ENVIRONMENT=$environment", '--env', 'LANGFUSE_TIMEOUT=300',
        '--env', "GEEKY_TRACE_NAME=$traceName", '--env', "GEEKY_AGENT_FAMILY=$family", '--env', "GEEKY_SESSION_ID=$sessionId",
        '--env', "GEEKY_RUN_METADATA=$metadataJson", '--env', "GEEKY_RUN_TAGS=$tagsJson",
        '--env', "OTEL_SERVICE_NAME=$family", '--env', "OTEL_RESOURCE_ATTRIBUTES=service.namespace=geeky-eval,deployment.environment.name=$environment")
    foreach ($name in $keyNames) { $envArgs += @('--env', $name) }
    # A host that trusts a private CA (a TLS-inspecting proxy) must hand it to the hooks too, or
    # their HTTPS uploads fail certificate verification inside the sandbox.
    $roPaths = @()
    $caNames = @('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'NODE_EXTRA_CA_CERTS') |
        Where-Object { $v = [Environment]::GetEnvironmentVariable($_); $v -and (Test-Path -LiteralPath $v -PathType Leaf) }
    foreach ($name in $caNames) {
        $envArgs += @('--env', $name)
        $roPaths += Split-Path ([Environment]::GetEnvironmentVariable($name))
    }
    $record = [ordered]@{
        enabled = $true; backend = 'langfuse'; base_url = $baseUrl; environment = $environment; trace_name = $traceName; tags = $tags
        user_id = $userId; user_id_policy = 'source-bound-agent'; agent_family = $family; metadata = $metadata;
        full_content = $true; ca_passthrough = @($caNames); session_id = $sessionId; native_session_id = $null; summary = $null
        delivered = $null; observations = $null; coverage_complete = $null; coverage_missed = $null
        user_ids = @(); agent_roles = @(); trace_count = $null
    }
    $result = [ordered]@{ Harness = $Harness; KeyNames = $keyNames; BaseUrl = $baseUrl; Tags = $tags; Record = $record
        RoPaths = @($roPaths | Select-Object -Unique) }

    if ($codex) {
        $index = Join-Path $ToolsDir "langfuse/codex-tracing/$($pins.codex_plugin.version)/dist/index.geeky.mjs"
        if (-not (Test-Path $index)) { throw "Missing $index; run evals/telemetry/install-telemetry-tools.ps1." }
        $node = (Get-Command node -ErrorAction SilentlyContinue).Source
        $major = if ($node) { [int]((& $node --version).TrimStart('v') -split '\.')[0] } else { 0 }
        if ($major -lt [int]$pins.codex_plugin.node_major_min) { throw "Codex tracing needs Node.js $($pins.codex_plugin.node_major_min)+ on PATH (found: $(if ($node) { "v$major at $node" } else { 'none' }))." }
        # LANGFUSE_CODEX_USER_ID set explicitly keeps the plugin from reading CODEX_HOME/auth.json.
        $envArgs += @('--env', "LANGFUSE_CODEX_USER_ID=$userId", '--env', "LANGFUSE_CODEX_TAGS=$tagsJson",
            '--env', "LANGFUSE_CODEX_METADATA=$metadataJson", '--env', "LANGFUSE_CODEX_ENVIRONMENT=$environment", '--env', 'LANGFUSE_CODEX_SKILL_TAGS=true')
        $record.hook = [ordered]@{ kind = 'codex-stop'; package = "$($pins.codex_plugin.package)@$($pins.codex_plugin.version)"; node = $node; script = $index }
        $result.Node = $node
        $result.HookScript = $index
    } else {
        $hook = Join-Path $ToolsDir "langfuse/claude-hook/$($pins.claude_hook.commit)/langfuse_hook.py"
        if (-not (Test-Path $hook) -or (Get-FileHash $hook -Algorithm SHA256).Hash -ne $pins.claude_hook.sha256) {
            throw "Missing or modified $hook; run evals/telemetry/install-telemetry-tools.ps1."
        }
        $venv = Join-Path $ToolsDir 'langfuse-py'
        $venvPy = if ($onWindows) { Join-Path $venv 'Scripts\python.exe' } else { Join-Path $venv 'bin/python' }
        if (-not (Test-Path $venvPy)) { throw "Missing $venvPy; run evals/telemetry/install-telemetry-tools.ps1." }
        $sitePackages = (& $venvPy -c "import sysconfig; print(sysconfig.get_paths()['purelib'])").Trim()
        # Windows: the venv launcher cannot start inside MXC, so run its base interpreter (as for geeky_mcp).
        $python = if ($onWindows) {
            $home_ = ((Get-Content (Join-Path $venv 'pyvenv.cfg')) -match '^home\s*=' -replace '^home\s*=\s*', '').Trim()
            Join-Path $home_ 'python.exe'
        } else { $venvPy }
        $boot = Join-Path $ConfigDir 'claude-hook-boot.py'
        Copy-Item (Join-Path $PSScriptRoot 'claude-hook-boot.py') $boot
        foreach ($helper in 'agent_identity.py', 'claude_identity.py') {
            Copy-Item (Join-Path $PSScriptRoot $helper) (Join-Path $ConfigDir $helper)
        }
        New-Item -ItemType Directory -Force $StateDir | Out-Null
        $hookArgs = @($python, $boot, $sitePackages, $hook)
        # Windows hooks must not use Git Bash, which cannot start in MXC (microsoft/mxc#1061).
        $entry = if ($onWindows) {
            [ordered]@{ type = 'command'; shell = 'powershell'; timeout = 600
                command = '& ' + (($hookArgs | ForEach-Object { "'" + ($_ -replace "'", "''") + "'" }) -join ' ') }
        } else {
            [ordered]@{ type = 'command'; timeout = 600
                command = ($hookArgs | ForEach-Object { "'" + ($_ -replace "'", "'\''") + "'" }) -join ' ' }
        }
        $result.SettingsHooks = [ordered]@{ Stop = @(@{ hooks = @($entry) }); SessionEnd = @(@{ hooks = @($entry) }) }
        $result.HookCommand = $hookArgs
        $envArgs += @('--env', 'CC_LANGFUSE_MAX_CHARS=2147483647', '--env', 'CC_LANGFUSE_CAPTURE_SKILL_CONTENT=true',
            '--env', "CC_LANGFUSE_TRACE_TAGS=$tagsJson", '--env', "CC_LANGFUSE_STATE_DIR=$StateDir", '--env', "LANGFUSE_USER_ID=$userId")
        $record.hook = [ordered]@{ kind = 'claude-stop-sessionend'; commit = $pins.claude_hook.commit; sha256 = $pins.claude_hook.sha256
            langfuse_python = $pins.langfuse_python; state_dir = $StateDir }
        $result.StateDir = $StateDir
    }
    $result.EnvArgs = $envArgs
    return [pscustomobject]$result
}

# Set the run's NAME=VALUE telemetry variables in this process for a host-side upload; returns what to restore.
function Push-EvalTelemetryEnv([Parameter(Mandatory)]$Telemetry) {
    $saved = @{}
    for ($i = 0; $i -lt $Telemetry.EnvArgs.Count; $i += 2) {
        $spec = $Telemetry.EnvArgs[$i + 1]
        if ($spec -notmatch '^([^=]+)=(.*)$') { continue }   # bare names are already host variables
        $saved[$Matches[1]] = [Environment]::GetEnvironmentVariable($Matches[1])
        [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2])
    }
    return $saved
}
function Pop-EvalTelemetryEnv([hashtable]$Saved) {
    foreach ($name in $Saved.Keys) { [Environment]::SetEnvironmentVariable($name, $Saved[$name]) }
}

# After a Claude run: upload the captured transcript from the host. The hook only fires when a turn ends,
# and `claude -p` is one turn, so a run that times out or is killed would otherwise leave Langfuse empty.
# The shared state folder keeps turns the in-sandbox hook already sent from being sent twice.
function Invoke-ClaudeTelemetryFlush {
    param([Parameter(Mandatory)]$Telemetry, [Parameter(Mandatory)][string]$SessionId, [Parameter(Mandatory)][string]$TranscriptPath)
    $saved = Push-EvalTelemetryEnv $Telemetry
    try {
        $payload = @{ session_id = $SessionId; transcript_path = $TranscriptPath; hook_event_name = 'SessionEnd' } | ConvertTo-Json -Compress
        $hook = $Telemetry.HookCommand
        $payload | & $hook[0] @($hook | Select-Object -Skip 1)
        $Telemetry.Record.host_flush = "exit $LASTEXITCODE"
    } finally { Pop-EvalTelemetryEnv $saved }
}

# After the run: confirm the session reached Langfuse and store a summary (never fatal; ingestion is async).
function Save-EvalTelemetry {
    param([Parameter(Mandatory)]$Telemetry, [string]$SessionId, [Parameter(Mandatory)][string]$OutDir,
          [Parameter(Mandatory)][string]$Python, [int]$WaitSec = 120)
    # Presence, required harness coverage and score readback are independent claims.
    # Reset stale presence/coverage when a later recovery cannot read the service.
    $Telemetry.Record.delivered = $false # compatibility alias: observations > 0 only
    $Telemetry.Record.observations_present = $false
    $Telemetry.Record.observations = $null
    $Telemetry.Record.trace_count = $null
    $Telemetry.Record.observations_status = 'pending'
    $Telemetry.Record.coverage_complete = $null
    $Telemetry.Record.coverage_status = 'unknown'
    $Telemetry.Record.scores_verified = $false # published/read back separately by langfuse-scores.py
    $Telemetry.Record.scores_status = 'pending'
    $Telemetry.Record.session_id = $SessionId
    $Telemetry.Record.native_session_id = $SessionId
    if ($SessionId -and $Telemetry.Record.agent_family) {
        $nativeSlug = ($SessionId.ToLowerInvariant() -replace '[^a-z0-9]+', '-').Trim('-')
        $Telemetry.Record.user_id = "$($Telemetry.Record.agent_family)-orchestrator-$nativeSlug"
    }
    if ($Telemetry.Record.metadata.run_group_id) { $Telemetry.Record.session_id = $Telemetry.Record.metadata.run_group_id }
    $SessionId = $Telemetry.Record.session_id
    if ($Telemetry.StateDir -and (Test-Path (Join-Path $Telemetry.StateDir 'langfuse_hook.log'))) {
        Copy-Item (Join-Path $Telemetry.StateDir 'langfuse_hook.log') (Join-Path $OutDir 'langfuse-hook.log')
    }
    if (-not $SessionId) { $Telemetry.Record.summary = 'no-session-id'; return }
    $summary = Join-Path $OutDir 'langfuse.json'
    & $Python (Join-Path $PSScriptRoot 'langfuse-run.py') --session-id $SessionId --wait $WaitSec --output $summary `
        --public-key-env $Telemetry.KeyNames[0] --secret-key-env $Telemetry.KeyNames[1] --base-url-env $Telemetry.KeyNames[2]
    $Telemetry.Record.summary = if ($LASTEXITCODE -eq 0) { 'langfuse.json' } else { "langfuse-run exit $LASTEXITCODE" }
    if ($LASTEXITCODE -eq 0 -and (Test-Path $summary)) {
        $sessionSummary = Get-Content $summary -Raw | ConvertFrom-Json
        $observations = [int]$sessionSummary.observations
        $Telemetry.Record.observations = $observations
        $Telemetry.Record.delivered = $observations -gt 0
        $Telemetry.Record.observations_present = $observations -gt 0
        $Telemetry.Record.observations_status = if ($observations -gt 0) { 'present' } else { 'pending' }
        $Telemetry.Record.user_ids = @($sessionSummary.user_ids)
        $Telemetry.Record.agent_roles = @($sessionSummary.agent_roles)
        $Telemetry.Record.trace_count = $sessionSummary.traces
    }
    if ($Telemetry.Record.delivered) {
        # Which harness points the session reached (cases/c0-wordstat/spec.md); informational, never fatal.
        $coverage = Join-Path $OutDir 'langfuse-coverage.json'
        & $Python (Join-Path $PSScriptRoot 'langfuse-coverage.py') --session-id $SessionId --output $coverage `
            --public-key-env $Telemetry.KeyNames[0] --secret-key-env $Telemetry.KeyNames[1] --base-url-env $Telemetry.KeyNames[2] | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path $coverage)) {
            $report = Get-Content $coverage -Raw | ConvertFrom-Json
            $Telemetry.Record.coverage_complete = [bool]$report.complete
            $Telemetry.Record.coverage_status = if ($report.complete) { 'met' } else { 'missing' }
            $Telemetry.Record.coverage_missed = @($report.missed)
        }
    }
}
