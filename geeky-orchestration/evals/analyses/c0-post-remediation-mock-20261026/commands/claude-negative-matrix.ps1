param([string]$RunRoot,[string]$RepoRoot,[string]$EvidenceRoot)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TRACE_TO_LANGFUSE='false'
$env:CLAUDE_CODE_OAUTH_TOKEN='mock-no-provider-token'
foreach($key in @('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','OPENAI_API_KEY','LITELLM_PROXY_API_KEY','LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY','LANGFUSE_BASE_URL')) { Remove-Item -LiteralPath "Env:$key" -ErrorAction SilentlyContinue }
. (Join-Path $RepoRoot 'geeky-orchestration/evals/adapters/codex/copy-vetted-mxc-build.ps1')
$cases=@(@{label='claude-crash';scenario='crash';budget=45;recoveries=0},@{label='claude-timeout';scenario='slow';budget=15;recoveries=0},@{label='claude-refusal-zero';scenario='refusal';budget=45;recoveries=0},@{label='claude-refusal-one';scenario='refusal';budget=45;recoveries=1})
$rows=@()
$baselineRoot=Join-Path $RepoRoot 'geeky-orchestration/evals/baselines/c0-wordstat'
foreach($case in $cases){
    $stateRoot=Join-Path $RunRoot ($case.label+'-mxc')
    Copy-VettedMxcBuild -BuildSource 'C:\repos\.eval-tools\windows-mxc\bin' -StateRoot $stateRoot -SourceDirectory (Join-Path $RepoRoot 'mxc-sandbox/scripts/host/MxcClaude') -PinPath (Join-Path $RepoRoot 'geeky-orchestration/evals/adapters/codex/profile/mxc-pin.json') -ReportPath (Join-Path $EvidenceRoot ($case.label+'-mxc-build.json')) | Out-Null
    $env:MXC_SANDBOX_HOME=$stateRoot
    $prior=@(Get-ChildItem $baselineRoot -Directory | ForEach-Object FullName)
    $log=Join-Path $EvidenceRoot ($case.label+'.log')
    & (Get-Command pwsh).Source -NoProfile -File (Join-Path $RepoRoot 'geeky-orchestration/evals/scripts/run-baseline.ps1') -Case c0-wordstat -MockAgent -MockScenario $case.scenario -NoTelemetry -ToolsDir 'C:\repos\.eval-tools' -WorkRoot (Join-Path $RunRoot $case.label) -TimeoutSec $case.budget -CloseoutReserveSec 2 -ResumeOnRefusal $case.recoveries -AuthorizationReference 'user-20261026-nonchargeable-mock-c0' *> $log
    $controllerExit=$LASTEXITCODE
    $new=@(Get-ChildItem $baselineRoot -Directory | Where-Object FullName -notin $prior)
    if($new.Count -ne 1){throw "Expected one evidence directory for $($case.label)"}
    $recordPath=Join-Path $new[0].FullName 'run.json'
    $record=Get-Content $recordPath -Raw|ConvertFrom-Json
    $row=[ordered]@{label=$case.label;scenario=$case.scenario;controller_exit=$controllerExit;record=$recordPath;child_exit=$record.exit_code;reason=$record.exit_reason;execution=$record.execution;oracle=$record.oracle;telemetry=$record.telemetry}
    $rows+=$row
    $rows|ConvertTo-Json -Depth 16|Set-Content (Join-Path $EvidenceRoot 'claude-negative-matrix.json')
    [PSCustomObject]@{label=$case.label;controller_exit=$controllerExit;child_exit=$record.exit_code;reason=$record.exit_reason;state=$record.execution.state;invocations=@($record.execution.invocations).Count}|ConvertTo-Json -Compress|Write-Output
}