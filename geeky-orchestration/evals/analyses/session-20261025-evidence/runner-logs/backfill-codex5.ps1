$ErrorActionPreference = 'Stop'
$plugin = '/home/user/plugins/geeky-orchestration'
$stamp = '20261025T014532Z-9ecf1828'
$out = "$plugin/evals/baselines/c0-wordstat/$stamp"
$ToolsDir = "$HOME/repos/.eval-tools"; $CodexHome = "$ToolsDir/codex-home"
$cfg = "$HOME/repos/.eval-cfg-codex-$stamp"; $runTmp = "$cfg/tmp"; $mxcState = "$cfg/mxc-runner"
$python = "$ToolsDir/agent-py/bin/python"; $mxc = '/home/user/plugins/mxc-sandbox/scripts/mxc.ps1'
$run = Get-Content "$out/run.json" -Raw | ConvertFrom-Json
. "$plugin/evals/telemetry/telemetry.ps1"
$telemetry = Resolve-EvalTelemetry -Harness codex -ToolsDir $ToolsDir -Case c0-wordstat -Stamp $stamp -PluginSha $run.plugin_sha -Model ant-claude
$thread = '01a170bc-1009-7b41-876e-6db5813ff2fa'
$rollout = Get-ChildItem -LiteralPath "$CodexHome/sessions" -Recurse -Filter "rollout-*$thread.jsonl" | Select-Object -First 1
Copy-Item "$plugin/evals/telemetry/codex-flush.py" $cfg
$payloadFile = "$runTmp/codex-flush-payload.json"
@{ session_id = $thread; transcript_path = $rollout.FullName; hook_event_name = 'Stop' } | ConvertTo-Json -Compress | Set-Content -LiteralPath $payloadFile -NoNewline
$flushArgs = @('run', '--workspace', $runTmp, '--rw', $CodexHome, '--ro', $ToolsDir, '--ro', $cfg, '--timeout', 900, '--env', "PATH=$env:PATH") + @($telemetry.RoPaths | ForEach-Object { '--ro', $_ }) + $telemetry.EnvArgs
$env:MXC_CLAUDE_EXE = $python; $env:MXC_SANDBOX_HOME = $mxcState
& $mxc @flushArgs -- "$cfg/codex-flush.py" $telemetry.Node $telemetry.HookScript $payloadFile *> "$out/langfuse-flush.log"
$telemetry.Record.host_flush = "exit $LASTEXITCODE (backfilled)"
Remove-Item Env:MXC_CLAUDE_EXE
Save-EvalTelemetry -Telemetry $telemetry -SessionId $thread -OutDir $out -Python $python
$run | Add-Member -Force telemetry $telemetry.Record
$run | ConvertTo-Json -Depth 8 | Set-Content "$out/run.json"
$telemetry.Record | ConvertTo-Json -Depth 4
