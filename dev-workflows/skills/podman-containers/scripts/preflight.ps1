# Ensures the Podman machine is running and reports Docker-compatibility status.
$ErrorActionPreference = 'Stop'

# Note: the Default flag can be False even for the sole machine, so fall back to the first one
$machines = @(podman machine ls --format json | ConvertFrom-Json)
if ($machines.Count -eq 0) { throw "No podman machine exists. Run: podman machine init" }
$default = ($machines | Where-Object { $_.Default } | Select-Object -First 1) ?? $machines[0]

if (-not $default.Running) {
    Write-Host "Machine '$($default.Name)' is stopped - starting it..."
    podman machine start $default.Name
}

"machine            : $($default.Name) (running, rootful=$(podman machine inspect $default.Name --format '{{.Rootful}}'))"
"docker_engine pipe : $(Test-Path '\\.\pipe\docker_engine')"
"podman pipe        : $(Test-Path "\\.\pipe\$($default.Name)")"
if ($env:DOCKER_HOST) {
    "WARNING: DOCKER_HOST is set to '$env:DOCKER_HOST' - this overrides the default docker_engine pipe for Docker API clients."
}
podman version --format 'client / server   : {{.Client.Version}} / {{.Server.Version}}'
