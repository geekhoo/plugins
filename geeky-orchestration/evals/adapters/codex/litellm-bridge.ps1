# Host-side lifecycle only. Starting the listener performs no provider request.
function Start-CodexLitellmBridge {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Python,
        [Parameter(Mandatory)][string]$AdapterDirectory,
        [Parameter(Mandatory)][string]$StateDirectory,
        [Parameter(Mandatory)][string]$UpstreamBaseUrl
    )
    $ErrorActionPreference = 'Stop'
    if (-not $env:LITELLM_PROXY_API_KEY) { throw 'LiteLLM bridge requires the process API key.' }
    if (Test-Path -LiteralPath $StateDirectory) { throw 'LiteLLM bridge state already exists; refusing reuse.' }
    # Windows venv python.exe can be a redirector whose PID differs from the
    # actual interpreter. The bridge is stdlib-only: launch its native base
    # interpreter directly so readiness must still match the owned process.
    $probeStart = [Diagnostics.ProcessStartInfo]::new()
    $probeStart.FileName = $Python
    $probeStart.UseShellExecute = $false
    $probeStart.CreateNoWindow = $true
    $probeStart.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
    $probeStart.RedirectStandardOutput = $true
    $probeStart.RedirectStandardError = $true
    foreach ($argument in @('-I','-S','-c','import json,os,sys; print(json.dumps(os.path.realpath(getattr(sys,"_base_executable",None) or sys.executable)))')) {
        $probeStart.ArgumentList.Add($argument)
    }
    $probe = [Diagnostics.Process]::new()
    $probe.StartInfo = $probeStart
    $probeStarted = $false
    try {
        if (-not $probe.Start()) { throw 'LiteLLM bridge Python resolution did not start.' }
        $probeStarted = $true
        $probeOutput = $probe.StandardOutput.ReadToEndAsync()
        $probeError = $probe.StandardError.ReadToEndAsync()
        if (-not $probe.WaitForExit(10000)) { throw 'LiteLLM bridge Python resolution timed out.' }
        if ($probe.ExitCode -ne 0) { throw 'LiteLLM bridge Python resolution failed.' }
        $nativePython = $probeOutput.GetAwaiter().GetResult() | ConvertFrom-Json -ErrorAction Stop
        if ($nativePython -isnot [string] -or -not [IO.Path]::IsPathFullyQualified($nativePython) -or
            -not (Test-Path -LiteralPath $nativePython -PathType Leaf)) {
            throw 'Invalid LiteLLM bridge native Python executable.'
        }
    } finally {
        if ($probeStarted -and -not $probe.HasExited) { $probe.Kill($true); $null = $probe.WaitForExit(5000) }
        $probe.Dispose()
    }
    New-Item -ItemType Directory -Path $StateDirectory | Out-Null
    $ready = Join-Path $StateDirectory 'ready.json'
    $base = $UpstreamBaseUrl.TrimEnd('/')
    if (-not $base.EndsWith('/v1') -and -not $base.EndsWith('/responses')) { $base += '/v1' }
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $nativePython
    $start.WorkingDirectory = $AdapterDirectory
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in @('-m','litellm_bridge','serve','--port','0','--ready-file',$ready)) {
        $start.ArgumentList.Add($argument)
    }
    $start.Environment['LITELLM_PROXY_API_BASE'] = $base
    $start.Environment['PYTHONDONTWRITEBYTECODE'] = '1'
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    $started = $false
    try {
        if (-not $process.Start()) { throw 'LiteLLM bridge process did not start.' }
        $started = $true
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $deadline = [DateTime]::UtcNow.AddSeconds(15)
        $metadata = $null
        while ([DateTime]::UtcNow -lt $deadline -and -not $process.HasExited) {
            if (Test-Path -LiteralPath $ready) {
                try { $metadata = Get-Content -LiteralPath $ready -Raw | ConvertFrom-Json -ErrorAction Stop; break } catch { }
            }
            Start-Sleep -Milliseconds 50
        }
        if (-not $metadata) { throw 'LiteLLM bridge did not become ready; no contestant launched.' }
        $uri = [Uri]$metadata.base_url
        if ($metadata.pid -ne $process.Id -or $uri.Scheme -ne 'http' -or $uri.Host -ne '127.0.0.1' -or
            $uri.Port -le 0 -or $uri.AbsolutePath -ne '/v1' -or $uri.UserInfo -or $uri.Query -or $uri.Fragment) {
            throw 'Invalid LiteLLM bridge readiness record.'
        }
        $hashes = [ordered]@{}
        foreach ($name in '__init__.py','__main__.py','mapper.py','server.py') {
            $path = Join-Path (Join-Path $AdapterDirectory 'litellm_bridge') $name
            $hashes[$name] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        return [pscustomobject]@{
            Process = $process; Stdout = $stdout; Stderr = $stderr; StateDirectory = $StateDirectory
            Record = [ordered]@{ enabled = $true; protocol = 'codex-v2-to-responses-v1-wire';
                base_url = [string]$metadata.base_url; pid = $process.Id; source_sha256 = $hashes;
                state_directory = $StateDirectory;
                known_plaintext_policy = 'process-local-provenance-only'; provider_requests_on_start = 0 }
        }
    } catch {
        if ($started -and -not $process.HasExited) { $process.Kill($true); $null = $process.WaitForExit(5000) }
        if (Test-Path -LiteralPath $ready) { Remove-Item -LiteralPath $ready }
        $process.Dispose()
        throw
    }
}

function Stop-CodexLitellmBridge {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Bridge)
    try {
        if (-not $Bridge.Process.HasExited) { $Bridge.Process.Kill($true) }
        if (-not $Bridge.Process.WaitForExit(5000)) { throw 'LiteLLM bridge did not stop.' }
        [IO.File]::WriteAllText((Join-Path $Bridge.StateDirectory 'stdout.log'), $Bridge.Stdout.GetAwaiter().GetResult())
        [IO.File]::WriteAllText((Join-Path $Bridge.StateDirectory 'stderr.log'), $Bridge.Stderr.GetAwaiter().GetResult())
        @{pid=$Bridge.Process.Id;stopped_utc=[DateTime]::UtcNow.ToString('o');exited=$Bridge.Process.HasExited} |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Bridge.StateDirectory 'stopped.json') -Encoding utf8NoBOM
        $ready = Join-Path $Bridge.StateDirectory 'ready.json'
        if (Test-Path -LiteralPath $ready) { Remove-Item -LiteralPath $ready }
    } finally { $Bridge.Process.Dispose() }
}
