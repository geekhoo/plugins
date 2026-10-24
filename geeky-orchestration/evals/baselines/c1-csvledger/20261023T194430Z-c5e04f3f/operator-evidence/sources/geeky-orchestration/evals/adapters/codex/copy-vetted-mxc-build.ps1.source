# Copy a pinned build into fresh private state without compiling or executing it.
function Copy-VettedMxcBuild {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$BuildSource,
        [Parameter(Mandatory)][string]$StateRoot,
        [Parameter(Mandatory)][string]$SourceDirectory,
        [Parameter(Mandatory)][string]$PinPath,
        [Parameter(Mandatory)][string]$ReportPath
    )
    $ErrorActionPreference = 'Stop'
    $source = (Resolve-Path -LiteralPath $BuildSource).Path
    $destination = [IO.Path]::GetFullPath((Join-Path $StateRoot 'bin'))
    if (Test-Path -LiteralPath $StateRoot) { throw 'MXC private state already exists; refusing overwrite.' }
    if (Test-Path -LiteralPath $ReportPath) { throw 'MXC provenance report already exists; refusing overwrite.' }
    $pin = Get-Content -LiteralPath $PinPath -Raw | ConvertFrom-Json
    $sourceHash = (Get-ChildItem -LiteralPath $SourceDirectory -File |
        Where-Object Extension -in '.cs', '.csproj' | Sort-Object Name |
        ForEach-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }) -join ''
    if ($sourceHash -cne $pin.source_hash) { throw 'MXC current source hash does not match pin.' }
    $entries = @(Get-Item -LiteralPath $source) + @(Get-ChildItem -LiteralPath $source -Force -Recurse)
    $rootFiles = @('.source-hash', 'Microsoft.Mxc.Sdk.dll', 'MxcClaude.dll', 'MxcClaude.exe',
        'MxcClaude.deps.json', 'MxcClaude.runtimeconfig.json', 'MxcClaude.pdb')
    foreach ($entry in $entries) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'MXC build contains a reparse point.' }
        if ($entry.FullName -eq $source) { continue }
        $relative = [IO.Path]::GetRelativePath($source, $entry.FullName).Replace('\', '/')
        if ($entry.PSIsContainer) {
            if ($relative -ne 'runtimes' -and -not $relative.StartsWith('runtimes/')) {
                throw "Unexpected directory in MXC build: $relative"
            }
        } elseif ($relative -notin $rootFiles -and
            -not ($relative.StartsWith('runtimes/') -and $entry.Extension -in '.dll', '.exe', '.so', '.dylib', '.pdb')) {
            throw "Unexpected file in MXC build: $relative"
        }
    }
    foreach ($required in ($rootFiles | Where-Object { $_ -ne 'MxcClaude.pdb' })) {
        if (-not (Test-Path -LiteralPath (Join-Path $source $required) -PathType Leaf)) {
            throw "Incomplete MXC build: $required"
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $source 'runtimes') -PathType Container)) {
        throw 'Incomplete MXC build: runtimes'
    }
    $stamp = (Get-Content -LiteralPath (Join-Path $source '.source-hash') -Raw).Trim()
    if ($stamp -cne $pin.source_hash) { throw 'MXC build source stamp does not match pin.' }
    foreach ($pair in @(@('MxcClaude.exe', 'exe_sha256'), @('MxcClaude.dll', 'dll_sha256'))) {
        if ((Get-FileHash -LiteralPath (Join-Path $source $pair[0]) -Algorithm SHA256).Hash -cne $pin.($pair[1])) {
            throw "MXC pinned binary hash mismatch: $($pair[0])"
        }
    }
    function Get-BuildManifest([string]$Root) {
        @(Get-ChildItem -LiteralPath $Root -Force -Recurse -File | Sort-Object FullName | ForEach-Object {
            [ordered]@{ path = [IO.Path]::GetRelativePath($Root, $_.FullName).Replace('\', '/');
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
        })
    }
    $sourceManifest = @(Get-BuildManifest $source)
    New-Item -ItemType Directory -Path $StateRoot | Out-Null
    New-Item -ItemType Directory -Path $destination | Out-Null
    Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $destination -Recurse
    $destinationManifest = @(Get-BuildManifest $destination)
    $sourceAfter = @(Get-BuildManifest $source)
    $serializedSource = ConvertTo-Json -InputObject $sourceManifest -Compress -Depth 5
    if ($serializedSource -cne (ConvertTo-Json -InputObject $destinationManifest -Compress -Depth 5) -or
        $serializedSource -cne (ConvertTo-Json -InputObject $sourceAfter -Compress -Depth 5)) {
        throw 'MXC build manifest changed during copy or does not match destination.'
    }
    $report = [ordered]@{ schema = 'geeky-eval.mxc-build-copy/1'; verified = $true;
        source_directory = $source; destination_directory = $destination;
        pin_path = (Resolve-Path -LiteralPath $PinPath).Path; source_hash = $sourceHash;
        exe_sha256 = $pin.exe_sha256; dll_sha256 = $pin.dll_sha256;
        source_manifest = $sourceManifest; destination_manifest = $destinationManifest }
    $json = ConvertTo-Json -InputObject $report -Depth 8
    $json | Set-Content -LiteralPath (Join-Path $StateRoot 'mxc-build-provenance.json') -Encoding utf8
    $json | Set-Content -LiteralPath $ReportPath -Encoding utf8
    return $report
}
