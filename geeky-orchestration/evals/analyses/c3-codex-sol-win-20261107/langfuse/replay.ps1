# Host-side Langfuse replay of C3 run 20261107T150925Z-9e506686 from copies of its 22 rollouts.
# Uses the repo's own telemetry.ps1 (D111 identity) and codex-flush.py. Writes only to scratch and Langfuse.
param([switch]$DryRun)
$ErrorActionPreference = 'Stop'
$repo  = 'C:\Users\gerald.khoo\geekhoo-plugins\geeky-orchestration'
$run   = 'C:\Repos\c3-sol-mapfix-20261107\geeky-orchestration\evals\baselines\c3-minisql\20261107T150925Z-9e506686'
$work  = Join-Path $PSScriptRoot '..\c3replay'
$tools = 'C:\repos\.eval-tools'
$rec   = Get-Content "$run\run.json" -Raw | ConvertFrom-Json
$thread = $rec.session_id

$day = Join-Path $work 'codex-home\sessions\2026\11\06'
New-Item -ItemType Directory -Force $day | Out-Null
$main = Join-Path $day "rollout-2026-11-06T16-50-15-$thread.jsonl"
if (-not (Test-Path $main)) { Copy-Item "$run\session.jsonl" $main }
Get-ChildItem "$run\subagents\*.jsonl" | ForEach-Object {
    $dst = Join-Path $day $_.Name
    if (-not (Test-Path $dst)) { Copy-Item $_.FullName $dst }
}
"rollouts staged: $((Get-ChildItem $day -Filter *.jsonl).Count)"

# Keys set with setx after the app started live only in the User scope; lift them into this process.
foreach ($n in 'LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY','LANGFUSE_BASE_URL','LANGFUSE_CODEX_PUBLIC_KEY','LANGFUSE_CODEX_SECRET_KEY','LANGFUSE_CODEX_BASE_URL') {
    if (-not [Environment]::GetEnvironmentVariable($n)) {
        $v = [Environment]::GetEnvironmentVariable($n, 'User')
        if ($v) { [Environment]::SetEnvironmentVariable($n, $v) }
    }
}
. (Join-Path $PSScriptRoot 'lfenv.ps1')
$env:TRACE_TO_LANGFUSE = 'true'
. "$repo\evals\telemetry\telemetry.ps1"
$t = Resolve-EvalTelemetry -Harness codex -ToolsDir $tools -Case c3-minisql -Stamp 20261107T150925Z-9e506686 `
    -PluginSha $rec.plugin_sha -Model $rec.model -Reasoning $rec.reasoning -WorkerModel $rec.worker_model `
    -WorkerReasoning $rec.worker_reasoning -ReviewerReasoning $rec.reviewer_reasoning -Provider $rec.provider.name
"session: $($t.SessionId)"
"key names: $($t.KeyNames -join ', ')"
if ($DryRun) { return }

$payload = Join-Path $work 'payload.json'
@{ session_id = $thread; transcript_path = $main; hook_event_name = 'Stop' } | ConvertTo-Json -Compress | Set-Content $payload -NoNewline
$saved = Push-EvalTelemetryEnv $t
try {
    & "$tools\agent-py\Scripts\python.exe" -I "$repo\evals\telemetry\codex-flush.py" $t.Node $t.HookScript $payload *> (Join-Path $work 'langfuse-flush.log')
    "flush exit $LASTEXITCODE"
} finally { Pop-EvalTelemetryEnv $saved }
