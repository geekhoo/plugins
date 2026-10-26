param([string]$RunRoot,[string]$RepoRoot)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TRACE_TO_LANGFUSE='false'
$env:CLAUDE_CODE_OAUTH_TOKEN='mock-no-provider-token'
foreach($key in @('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','OPENAI_API_KEY','LITELLM_PROXY_API_KEY','LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY','LANGFUSE_BASE_URL')) { Remove-Item -LiteralPath "Env:$key" -ErrorAction SilentlyContinue }
$env:MXC_SANDBOX_HOME=Join-Path $RunRoot 'claude-timeout-postprocess-fault-mxc'
& (Join-Path $RepoRoot 'geeky-orchestration/evals/scripts/run-baseline.ps1') -Case c0-wordstat -MockAgent -MockScenario slow -NoTelemetry -ToolsDir 'C:\repos\.eval-tools' -WorkRoot (Join-Path $RunRoot 'claude-timeout-postprocess-fault') -TimeoutSec 30 -CloseoutReserveSec 3 -ResumeOnRefusal 0 -AuthorizationReference 'user-20261026-nonchargeable-mock-c0'
exit $LASTEXITCODE