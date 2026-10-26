$ErrorActionPreference = 'Stop'
$plugin = (Resolve-Path (Join-Path $PSScriptRoot '../../../../../..')).Path
$repo = Split-Path $plugin
$results = @()
foreach ($runner in @('run-baseline.ps1', 'run-codex-baseline.ps1')) {
    $runnerPath = Join-Path $plugin "evals/scripts/$runner"
    $tokens = $null
    $parseErrors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile($runnerPath, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count) { throw "Runner parse failed: $runner" }
    # Execute only the runner's existing render/hash assignments, never its entry point.
    foreach ($variable in @('prompt', 'promptSha')) {
        $assignments = @($ast.FindAll({ param($node)
            $node -is [Management.Automation.Language.AssignmentStatementAst] -and
            $node.Left -is [Management.Automation.Language.VariableExpressionAst] -and
            $node.Left.VariablePath.UserPath -eq $variable
        }, $true))
        if ($assignments.Count -ne 1) { throw "Expected one $variable assignment in $runner" }
        . ([scriptblock]::Create($assignments[0].Extent.Text))
    }
    $results += [pscustomobject]@{ runner = $runner; prompt_sha256 = $promptSha; prompt = $prompt }
}
if ($results[0].prompt -cne $results[1].prompt -or $results[0].prompt_sha256 -ne $results[1].prompt_sha256) {
    throw 'Equivalent harness renders/hashes differ'
}
$historical = Get-Content (Join-Path $PSScriptRoot 'historical-prompt.md') -Raw
$historicalRender = $historical.Replace('{{PLANNING_FOLDER}}', 'docs/spec-001-feature/')
$historicalSha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($historicalRender))).ToLowerInvariant()
if ($historicalSha -eq $results[0].prompt_sha256) { throw 'Changed prompt did not change hash' }
$c0Record = Get-Content (Join-Path $plugin 'evals/baselines/c0-wordstat/20261025T154802Z-c140d9e7/run.json') -Raw | ConvertFrom-Json
if ($historicalSha -ne $c0Record.prompt_sha256) { throw 'Historical prompt replay differs from frozen C0 record' }
$results | Select-Object runner, prompt_sha256 | ConvertTo-Json | Write-Output
Write-Output "historical_render_sha256=$historicalSha; matches frozen C0 prompt_sha256"
Write-Output 'PASS: executed only actual render/hash assignment ASTs; no runner/model/telemetry launch'
