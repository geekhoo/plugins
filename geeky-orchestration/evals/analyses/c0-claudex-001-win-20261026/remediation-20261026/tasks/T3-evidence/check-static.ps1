$ErrorActionPreference = 'Stop'
$problems=$null
[Management.Automation.Language.Parser]::ParseFile((Resolve-Path 'evals/telemetry/telemetry.ps1'),[ref]$null,[ref]$problems) | Out-Null
if ($problems) { $problems; exit 1 }
Write-Output 'PASS: telemetry.ps1 PowerShell syntax'
& C:/Python314/python.exe -c "import ast,pathlib; files=['evals/scripts/evaluation_scope.py','evals/scripts/parity-eval.py','evals/scripts/test_parity_eval.py','evals/telemetry/langfuse-scores.py','evals/telemetry/test_langfuse_scores.py']; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'),filename=p) for p in files]; print('PASS: five Python AST parses')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git diff --check -- evals/scripts/parity-eval.py evals/scripts/evaluation_scope.py evals/scripts/test_parity_eval.py evals/telemetry/langfuse-scores.py evals/telemetry/test_langfuse_scores.py evals/telemetry/telemetry.ps1 evals/telemetry/README.md evals/mxc-litellm-runbook.md
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output 'PASS: touched-file whitespace check'
