param([string]$RunRoot,[string]$RepoRoot)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TRACE_TO_LANGFUSE='false'
$env:CLAUDE_CODE_OAUTH_TOKEN='mock-no-provider-token'
foreach($key in @('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','OPENAI_API_KEY','LITELLM_PROXY_API_KEY','LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY','LANGFUSE_BASE_URL')) { Remove-Item -LiteralPath "Env:$key" -ErrorAction SilentlyContinue }
& (Join-Path $RepoRoot 'geeky-orchestration/evals/scripts/run-codex-baseline.ps1') -Case c0-wordstat -MockAgent -MockScenario c0-full -NoTelemetry -ToolsDir 'C:\repos\.eval-tools' -WorkRoot (Join-Path $RunRoot 'codex-full') -CodexHome (Join-Path $RunRoot 'codex-full/codex-home') -CodexExe 'C:\repos\.eval-tools\codex\0.164.0\bin\codex.exe' -MxcBuildSource 'C:\repos\.eval-tools\windows-mxc\bin' -TimeoutSec 300 -CloseoutReserveSec 30 -AuthorizationReference 'user-20261026-nonchargeable-mock-c0'
exit $LASTEXITCODE