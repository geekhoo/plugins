# Shared local record/clock contract. No provider calls or recovery policy live here.
function Assert-EvalWorkflowBudgetExport([string]$SourcePlugin, [string]$ExportPlugin) {
    # The canonical prompt is an operator input, while contestant skills are
    # exported from HEAD. Reject a new prompt paired with old committed skills.
    foreach ($relative in @('scripts/workflow-budget.py', 'skills/spec-research/SKILL.md',
            'skills/geeky-plan/SKILL.md', 'skills/plan-review/SKILL.md')) {
        $source = Join-Path $SourcePlugin $relative
        $exported = Join-Path $ExportPlugin $relative
        if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or
            -not (Test-Path -LiteralPath $exported -PathType Leaf)) {
            throw "Workflow budget prerequisite absent from source/committed export: $relative. Preserve changes; commit a reviewed source revision when authorized before preparation."
        }
        # Git may check out CRLF on Windows while git archive carries LF. These
        # are text inputs: compare normalized newlines, retaining every other
        # character so a substantive dirty policy still blocks preparation.
        $sourceText = [IO.File]::ReadAllText($source).Replace("`r`n", "`n")
        $exportText = [IO.File]::ReadAllText($exported).Replace("`r`n", "`n")
        if (-not [string]::Equals($sourceText, $exportText, [StringComparison]::Ordinal)) {
            throw "Workflow budget source differs from committed export: $relative. Preserve changes; commit a reviewed source revision when authorized before preparation."
        }
    }
}

function Get-EvalMonotonicSeconds {
    return [Diagnostics.Stopwatch]::GetTimestamp() / [double][Diagnostics.Stopwatch]::Frequency
}

function Write-EvalRecord($Record, [string]$Path) {
    if ($Record.execution -and $Record.execution.process_outcome -in @('timeout', 'crash')) {
        $Record.exit_reason = $Record.execution.process_outcome
        $Record.is_error = $true
        $Record.reference_eligible = $false
    }
    $temporary = "$Path.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        [IO.File]::WriteAllText($temporary, ($Record | ConvertTo-Json -Depth 24), [Text.UTF8Encoding]::new($false))
        # Same directory/volume: a failed replacement leaves the previous valid JSON intact.
        [IO.File]::Move($temporary, $Path, $true)
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary }
    }
}

function New-EvalExecution([int]$Budget, [int]$Reserve, [int]$Recoveries, [string]$Authorization, $Waiver, $Configuration) {
    if ($Budget -le 0) { throw 'TimeoutSec must be positive' }
    if ($Reserve -lt 0 -or $Reserve -ge $Budget) { throw 'CloseoutReserveSec must be nonnegative and smaller than TimeoutSec' }
    if ($Recoveries -lt 0) { throw 'ResumeOnRefusal must be nonnegative' }
    $script:evalAttemptStart = Get-EvalMonotonicSeconds
    $Configuration['hard_wall_budget_s'] = $Budget
    $Configuration['closeout_reserve_s'] = $Reserve
    $Configuration['allowed_recoveries'] = $Recoveries
    $json = $Configuration | ConvertTo-Json -Compress -Depth 8
    return [ordered]@{
        schema = 'geeky-eval.execution/1'; state = 'prepared'
        attempt_id = [guid]::NewGuid().ToString(); segment_id = [guid]::NewGuid().ToString()
        authorization_reference = $Authorization; allowed_recoveries = $Recoveries; qualification_waiver = $Waiver
        initial_deadline_utc = [DateTime]::UtcNow.AddSeconds($Budget).ToString('o')
        hard_wall_budget_s = $Budget; closeout_reserve_s = $Reserve; closeout_policy = 'advisory-within-hard-wall'
        configuration = $Configuration
        configuration_sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($json))).ToLowerInvariant()
        invocations = @(); process_outcome = 'not-started'; capture_status = 'not-started'
        postprocessing = [ordered]@{}; active_step = 'prepared'; failure = $null
        contestant_time_s = 0.0; attempt_elapsed_s = 0.0; finalization_time_s = $null; workflow_acceptance = 'not-established'
        writer_pid = $PID; writer_host = [Environment]::MachineName; reconciliation_required = $true
        # These existing synchronous steps are outside the contestant deadline.
        step_timeouts_s = [ordered]@{ oracle = $null; claude_host_flush = $null; codex_replay = 900; sandbox_hook = 600; telemetry_poll_wait = 120; telemetry_host_process = $null; telemetry_coverage = $null; analysis = $null }
    }
}

function Get-EvalRemainingSeconds($Execution) {
    return [int][Math]::Max(0, [Math]::Floor($Execution.hard_wall_budget_s - ((Get-EvalMonotonicSeconds) - $script:evalAttemptStart)))
}

function Start-EvalInvocation($Record, [string]$Path, [string]$Kind, [ref]$HostArguments) {
    $execution = $Record.execution
    $remaining = Get-EvalRemainingSeconds $execution
    if ($remaining -lt 1) {
        $execution.state = 'deadline-exhausted'
        if ($execution.process_outcome -eq 'not-started') { $Record.exit_reason = 'deadline-exhausted' }
        Write-EvalRecord $Record $Path
        return $false
    }
    $arguments = @($HostArguments.Value)
    $arguments[[array]::IndexOf($arguments, '--timeout') + 1] = $remaining
    $HostArguments.Value = $arguments
    $execution.invocations += [ordered]@{
        invocation_id = [guid]::NewGuid().ToString(); kind = $Kind; timeout_s = $remaining
        started_utc = [DateTime]::UtcNow.ToString('o'); ended_utc = $null; exit_code = $null; outcome = 'unknown'
    }
    $script:evalInvocationStart = Get-EvalMonotonicSeconds
    # Reaching capture means the seed oracle returned and its acceptance check passed.
    if ($execution.active_step -eq 'seed-oracle' -and $execution.postprocessing['seed-oracle'] -eq 'in-progress') {
        $execution.postprocessing['seed-oracle'] = 'completed'
    }
    $execution.state = 'running'; $execution.capture_status = 'in-progress'; $execution.active_step = 'capture'
    if (-not $Record.started_utc) { $Record.started_utc = [DateTime]::UtcNow.ToString('o') }
    Write-EvalRecord $Record $Path
    return $true
}

function Complete-EvalInvocation($Record, [string]$Path, [int]$Code) {
    $execution = $Record.execution
    $invocation = $execution.invocations[-1]
    $invocation.ended_utc = [DateTime]::UtcNow.ToString('o'); $invocation.exit_code = $Code
    $invocation.outcome = if ($Code -eq 124) { 'timeout' } elseif ($Code -eq 0) { 'success' } else { 'crash' }
    $execution.process_outcome = $invocation.outcome; $execution.capture_status = 'captured'
    $execution.state = 'process-finished'; $execution.active_step = 'postprocessing'
    $execution.contestant_time_s += (Get-EvalMonotonicSeconds) - $script:evalInvocationStart
    $execution.attempt_elapsed_s = (Get-EvalMonotonicSeconds) - $script:evalAttemptStart
    $Record.ended_utc = $invocation.ended_utc; $Record.wall_time_s = $execution.contestant_time_s
    $Record.exit_code = $Code
    $Record.exit_reason = if ($Code -eq 0) { 'completed' } else { $invocation.outcome }
    $Record.is_error = $Code -ne 0
    # Persist the known child outcome before any parsing, oracle, diagnostics or telemetry.
    Write-EvalRecord $Record $Path
}

# Host-side observer of the contestant's board. It changes nothing the contestant sees, and it must never affect the run.
function Start-EvalBoardWatcher([string]$Python, [string]$Workspace, [string]$RunFolder) {
    try {
        $watcher = Join-Path $PSScriptRoot '..\telemetry\board-watcher.py'
        $stop = Join-Path $RunFolder '.board-watcher-stop'
        $arguments = @('-B', "`"$watcher`"", '--workspace', "`"$Workspace`"", '--out', "`"$(Join-Path $RunFolder 'board-snapshots.jsonl')`"", '--stop-file', "`"$stop`"", '--parent-pid', $PID)
        $process = Start-Process -FilePath $Python -ArgumentList $arguments -NoNewWindow -PassThru `
            -RedirectStandardOutput (Join-Path $RunFolder 'board-watcher-stdout.txt') -RedirectStandardError (Join-Path $RunFolder 'board-watcher-stderr.txt')
        return @{ process = $process; stop = $stop }
    } catch {
        Write-Warning "Board watcher did not start: $($_.Exception.Message)"
        return $null
    }
}

function Stop-EvalBoardWatcher($Watcher) {
    if (-not $Watcher) { return }
    try {
        Set-Content -LiteralPath $Watcher.stop -Value 'stop'
        if (-not $Watcher.process.WaitForExit(10000)) { $Watcher.process.Kill() }
        Remove-Item -LiteralPath $Watcher.stop -ErrorAction SilentlyContinue
        $folder = Split-Path -Parent $Watcher.stop
        foreach ($log in 'board-watcher-stdout.txt', 'board-watcher-stderr.txt') {
            $file = Get-Item -LiteralPath (Join-Path $folder $log) -ErrorAction SilentlyContinue
            if ($file -and $file.Length -eq 0) { Remove-Item -LiteralPath $file.FullName -ErrorAction SilentlyContinue }
        }
    } catch {
        Write-Warning "Board watcher did not stop cleanly: $($_.Exception.Message)"
    }
}

# A contestant can print its environment into a tool result, and stderr can echo headers, so stored files get
# scrubbed before they are hashed. Values come from this process's environment, never argv. These helpers never
# throw: a scrub problem marks the record and must not lose the run's evidence.
function Assert-EvalSecretTools {
    if (-not (Get-Command node -CommandType Application -ErrorAction SilentlyContinue)) { throw 'node is required on PATH to scrub secrets from the stored run.' }
    foreach ($tool in 'scrub-secrets.mjs', 'secret-scan.mjs', 'secret-rules.mjs') {
        if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $tool) -PathType Leaf)) { throw "Missing secret tool: $tool" }
    }
}

function Get-EvalSecretRecord($Record) {
    if (-not $Record.Contains('secret_scrub')) {
        $Record['secret_scrub'] = [ordered]@{ status = 'not-run'; redactions = 0; failed_files = 0; binary_files = @(); solution_history = 'not-scanned'; solution_history_hits = 0 }
    }
    return $Record['secret_scrub']
}

function Invoke-EvalSecretScrub($Record, [string]$RunFolder, [string]$ReportName) {
    $scrub = Get-EvalSecretRecord $Record
    $report = Join-Path $RunFolder $ReportName
    $code = -1
    try {
        Remove-Item -LiteralPath $report -ErrorAction SilentlyContinue
        $node = (Get-Command node -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
        & $node (Join-Path $PSScriptRoot 'scrub-secrets.mjs') $RunFolder --report $report 2>$null
        $code = $LASTEXITCODE
        $summary = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
        $scrub['redactions'] += [int]$summary.redactions
        $scrub['failed_files'] = @($summary.failed).Count
        $scrub['binary_files'] = @($summary.binary_files | ForEach-Object { [IO.Path]::GetRelativePath($RunFolder, $_).Replace('\', '/') })
    } catch { $code = if ($code -eq 0) { -1 } else { $code } }
    $scrub['status'] = if ($code -eq 0) { 'scrubbed' } else { 'failed' }
    if ($code -ne 0) {
        $Record.is_error = $true; $Record.reference_eligible = $false
        Write-Warning "Secret scrub failed (exit $code); files in $RunFolder may hold secrets. Do not commit or upload them."
    }
}

# A bundle is binary and its history cannot be rewritten without changing the evidence, so its source is only scanned.
function Invoke-EvalSolutionSecretScan($Record, [string]$Workspace, [string]$RunFolder) {
    $scrub = Get-EvalSecretRecord $Record
    $output = Join-Path $RunFolder 'secret-scan-solution.txt'
    try {
        $node = (Get-Command node -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
        & $node (Join-Path $PSScriptRoot 'secret-scan.mjs') --repo $Workspace --git --all > $output 2>$null
        $code = $LASTEXITCODE
        $scrub['solution_history'] = if ($code -eq 0) { 'clean' } elseif ($code -eq 1) { 'hits' } else { 'error' }
        $scrub['solution_history_hits'] = if ($code -eq 1) { @(Get-Content -LiteralPath $output).Count } else { 0 }
    } catch { $scrub['solution_history'] = 'error' }
    if ($scrub['solution_history'] -ne 'clean') {
        Write-Warning "Solution history scan: $($scrub['solution_history']). Review $output before committing solution.bundle."
    }
}

function Get-EvalInterventionNote($Items) {
    $listed = @($Items | Where-Object { $_ })
    return $(if ($listed.Count) { $listed -join '; ' } else { 'none' })
}

function Set-EvalStep($Record, [string]$Path, [string]$Name) {
    $prior = $Record.execution.active_step
    if ($Record.execution.postprocessing[$prior] -eq 'in-progress') { $Record.execution.postprocessing[$prior] = 'completed' }
    $Record.execution.active_step = $Name
    $Record.execution.postprocessing[$Name] = 'in-progress'
    Write-EvalRecord $Record $Path
}

function Set-EvalFailure($Record, $ErrorRecord) {
    $execution = $Record.execution
    $execution.failure = [ordered]@{ step = $execution.active_step; message = $ErrorRecord.Exception.Message }
    if ($execution.active_step -eq 'capture') {
        $execution.capture_status = 'incomplete'; $execution.process_outcome = 'unknown'; $execution.contestant_time_s = $null
    }
    else { $execution.postprocessing[$execution.active_step] = 'failed' }
    if ($execution.active_step -eq 'analysis') { $Record.analysis_status = 'failed' }
    $execution.state = 'incomplete'; $Record.is_error = $true; $Record.reference_eligible = $false
}

function Save-EvalFinalRecord($Record, [string]$Path, [string]$Workspace, [double]$FinalizationStart) {
    $execution = $Record.execution
    if ($execution.process_outcome -in @('timeout', 'crash')) { $Record.exit_reason = $execution.process_outcome }
    if (-not $execution.failure) {
        if ($execution.postprocessing[$execution.active_step] -eq 'in-progress') { $execution.postprocessing[$execution.active_step] = 'completed' }
        if ($execution.state -ne 'deadline-exhausted') { $execution.state = 'finalized' }
    }
    if ($Record.Contains('wall_time_s')) { $Record.wall_time_s = $execution.contestant_time_s }
    $execution.reconciliation_required = $execution.process_outcome -eq 'unknown'
    $execution['workspace_head'] = (& git -C $Workspace rev-parse HEAD | Out-String).Trim()
    $execution['workspace_status'] = @(& git -C $Workspace status --porcelain=v1)
    # Also covers a run that failed before the runner's own scrub, and files written after it.
    Invoke-EvalSecretScrub $Record (Split-Path $Path) 'secret-scrub.json'
    $scrub = $Record['secret_scrub']
    if ($scrub['redactions'] -gt 0 -and $Record.Contains('telemetry') -and $Record.telemetry.enabled) {
        # Spans leave from inside the sandbox during the run; a host scrub cannot reach what was already sent.
        $scrub['telemetry_exposure'] = 'possible'
        Write-Warning "Secret scrub redacted $($scrub['redactions']) value(s). Langfuse spans for this run may hold the same text."
    }
    $execution['artifact_sha256'] = [ordered]@{}
    Get-ChildItem -LiteralPath (Split-Path $Path) -File -Recurse | Where-Object { $_.FullName -ne $Path -and $_.Extension -ne '.tmp' } | ForEach-Object {
        $name = [IO.Path]::GetRelativePath((Split-Path $Path), $_.FullName).Replace('\', '/')
        $execution.artifact_sha256[$name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $execution.finalization_time_s = (Get-EvalMonotonicSeconds) - $FinalizationStart
    Write-EvalRecord $Record $Path
    # run.json is rewritten from memory above, so it gets its own last pass. It is outside artifact_sha256.
    try {
        $node = (Get-Command node -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
        & $node (Join-Path $PSScriptRoot 'scrub-secrets.mjs') $Path > $null 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Warning "Secret scrub of $Path failed (exit $LASTEXITCODE)." }
    } catch { Write-Warning "Secret scrub of $Path did not run: $($_.Exception.GetType().Name)" }
}
