param([string]$RunRoot,[string]$RepoRoot)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TRACE_TO_LANGFUSE='false'
$env:CLAUDE_CODE_OAUTH_TOKEN='mock-no-provider-token'
foreach($key in @('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','OPENAI_API_KEY','LITELLM_PROXY_API_KEY','LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY','LANGFUSE_BASE_URL')) { Remove-Item -LiteralPath "Env:$key" -ErrorAction SilentlyContinue }
$env:MXC_SANDBOX_HOME=Join-Path $RunRoot 'claude-timeout-oracle-fault-verified-mxc'
$watcher=Start-Job -ScriptBlock {
    param($BaselineRoot,$Match,$Report)
    $ErrorActionPreference='Stop'
    $until=[DateTime]::UtcNow.AddSeconds(50)
    while([DateTime]::UtcNow -lt $until){
        $folders=@(Get-ChildItem $BaselineRoot -Directory|Sort-Object Name -Descending|Select-Object -First 4)
        foreach($folder in $folders){
            $recordPath=Join-Path $folder.FullName 'run.json'
            if(-not(Test-Path $recordPath)){continue}
            try{$record=Get-Content $recordPath -Raw|ConvertFrom-Json}catch{continue}
            if($record.workspace -like "*$Match*" -and $record.execution.state -eq 'running'){
                $faultPath=Join-Path $folder.FullName 'oracle-output.txt'
                if(Test-Path -LiteralPath $faultPath){throw 'Refuse to replace existing oracle evidence'}
                [IO.Directory]::CreateDirectory($faultPath)|Out-Null
                if(-not(Test-Path -LiteralPath $faultPath -PathType Container)){throw 'Fault not verified'}
                @{applied=$true;record=$recordPath;fault_path=$faultPath;injected_utc=[DateTime]::UtcNow.ToString('o');observed_state='running';original_bytes_removed=$false}|ConvertTo-Json|Set-Content $Report
                return
            }
        }
        Start-Sleep -Milliseconds 100
    }
    throw 'Fault injection watcher expired without a running record'
} -ArgumentList (Join-Path $RepoRoot 'geeky-orchestration/evals/baselines/c0-wordstat'),'claude-timeout-oracle-fault-verified',(Join-Path $RepoRoot 'outputs/c0-remediation-mock-20261026/claude-timeout-oracle-fault-verified-injection.json')
& (Join-Path $RepoRoot 'geeky-orchestration/evals/scripts/run-baseline.ps1') -Case c0-wordstat -MockAgent -MockScenario slow -NoTelemetry -ToolsDir 'C:\repos\.eval-tools' -WorkRoot (Join-Path $RunRoot 'claude-timeout-oracle-fault-verified') -TimeoutSec 30 -CloseoutReserveSec 3 -ResumeOnRefusal 0 -AuthorizationReference 'user-20261026-nonchargeable-mock-c0'
$code=$LASTEXITCODE
Wait-Job $watcher | Out-Null
Receive-Job $watcher -ErrorAction Continue
exit $code