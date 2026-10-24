# Dot-source for the C1 run 3 operator shell. This file never starts a run.
$c1Repo = 'C:\Users\gerald.khoo\geekhoo-plugins'
$c1Pwsh = 'C:\Users\gerald.khoo\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$c1Tools = 'C:\repos\.eval-tools'
$c1Evidence = Join-Path $c1Repo 'geeky-orchestration\evals\adapters\codex\evidence\20261023T223555Z-run3-readiness'
$c1Python = Join-Path $c1Tools 'agent-py\Scripts\python.exe'
$c1CodexExe = Join-Path $c1Tools 'codex\0.164.0\bin\codex.exe'
$c1CodexHome = Join-Path $c1Tools 'codex-home'
$c1VettedBuild = 'C:\repos\.eval-cfg-codex-20261023T162259Z-60b450bc\mxc-native-probe\bin'
$c1NativeProof = (Get-Content -LiteralPath (Join-Path $c1Evidence 'native-reviewer-attempt.json') -Raw | ConvertFrom-Json).attempt
$c1ReviewerProof = (Get-Content -LiteralPath (Join-Path $c1Evidence 'native-architect-reviewer-attempt.json') -Raw | ConvertFrom-Json).attempt
$c1PreparedRun = (Get-Content -LiteralPath (Join-Path $c1Evidence 'preparation.json') -Raw | ConvertFrom-Json).prepared_run
$c1Model = 'gpt-6.1-sol'
$c1Reasoning = 'high'
$c1WorkerModel = 'gpt-6.1-sol'
$c1WorkerReasoning = 'medium'
$c1ReviewerReasoning = 'xhigh'
foreach ($c1Required in @($c1Repo, $c1Pwsh, $c1Python, $c1CodexExe, $c1CodexHome, $c1VettedBuild, $c1NativeProof, $c1ReviewerProof, $c1PreparedRun)) {
    if (-not (Test-Path -LiteralPath $c1Required)) { throw "Missing prepared prerequisite: $c1Required" }
}
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$c1PinnedPath = @((Split-Path -Parent $c1Pwsh), (Split-Path -Parent $c1Python))
$env:PATH = (($c1PinnedPath + ($env:PATH -split ';')) | Select-Object -Unique) -join ';'
Write-Host 'C1 run 3 shell prepared: Sol/high main, Sol/medium workers and fallback, Sol/xhigh reviewers. No workload or model call started.'
