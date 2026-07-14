---
name: podman-containers
description: Run, build, and test containers on this Windows machine with Podman — Docker Desktop is NOT installed; Podman is the container engine and it already forwards the Docker API. Use this skill whenever a task touches containers in any way - docker or podman commands, Dockerfiles/Containerfiles, docker-compose stacks, container images or registries, Testcontainers-based test suites, or reproducing container-based CI/CD pipeline steps locally - even when the user (or the repo's scripts) say "docker" and never mention Podman.
allowed-tools: PowerShell(podman:*) PowerShell(docker-compose:*)
---

# Containers on this machine: Podman with Docker compatibility

Docker Desktop is not installed here and must not be assumed. Podman provides the
container engine, and the goal is always: **make Docker-flavored assets (Dockerfiles,
compose files, CI scripts) work unchanged** — never port them to Podman-specific syntax,
because they must stay runnable on Docker-based CI runners and teammates' machines.

## Environment (verified 2026-07-02 — re-verify with preflight if things look off)

- `podman.exe` 5.8.3 at `C:\Program Files\RedHat\Podman\podman.exe` — a **remote client**; all containers actually run in a WSL2 VM
- Machine `podman-machine-default`: WSL2, **rootful**, 4 CPU / 2 GiB RAM / 100 GiB disk. It is also the default WSL distro
- `docker-compose` v2.39.3 (genuine Compose v2) on PATH
- `docker` CLI: **not installed**
- While the machine runs, Podman forwards the Docker API on `\\.\pipe\docker_engine` — Docker SDK clients (Testcontainers, docker-py, VS, compose) connect with **zero configuration**

## Preflight — run before any container work

```powershell
# run scripts/preflight.ps1, resolving the path from this skill's own directory
# (do NOT rely on $PSScriptRoot — it is empty when the command is pasted into a shell)
& "<path-to-this-skill>/scripts/preflight.ps1"
```

Or manually: `podman machine ls` — if the machine is not "Currently running", run
`podman machine start`. This matters because podman.exe is only a client: when the WSL VM
is down (it does NOT autostart after reboot), every command fails with connection-refused
style errors that look like a broken install but aren't.

## Rule 1: keep project scripts Docker-compatible

Never rewrite a repo's build scripts, compose files, or CI YAML from `docker …` to
`podman …`. Instead, make the `docker` invocation work:

| Situation | Solution |
|---|---|
| You are typing commands yourself | Just use `podman` — verbs and flags are identical to docker (`build`, `run`, `ps`, `logs`, `exec`, `pull`, `push`, `volume`, `network`, …) |
| A script calls `docker` and runs in your pwsh session | `Set-Alias docker podman` (session-scoped; harmless) |
| A child process needs a literal `docker.exe` (npm scripts, Makefiles, CI runners) | Write a shim `docker.cmd` containing `@podman %*` into the scratchpad dir and prepend that dir to `$env:PATH` for the process |
| Docker SDK / API clients (Testcontainers, docker-py, compose) | Nothing — they hit `docker_engine` pipe which Podman forwards. Fallback if that pipe is unavailable: `$env:DOCKER_HOST = 'npipe:////./pipe/podman-machine-default'` |

## Compose

Compose files need no edits. Two equivalent invocations:

```powershell
podman compose up -d      # thin wrapper; delegates to the installed real docker-compose v2
docker-compose up -d      # direct; connects via the forwarded docker_engine pipe
```

Because the delegate is genuine Compose v2 (not python podman-compose), the full Compose
spec is supported. If compose behaves oddly, first check `$env:DOCKER_HOST` isn't set to
something stale — an explicit DOCKER_HOST overrides the default pipe.

## Builds

`podman build -t <name> .` consumes Dockerfiles unchanged (Buildah under the hood; a
"Containerfile" is just the alternate default filename). Notes:

- If a downstream tool rejects OCI-format images, rebuild with `--format docker`
- Common BuildKit features (`RUN --mount`, heredoc syntax) work; if an exotic BuildKit
  frontend feature fails, that's the first suspect — check before debugging the Dockerfile
- Always fully qualify base images (`docker.io/library/node:22`) — short names can hit
  Podman's registry-resolution prompt, which hangs non-interactive runs

## Reproducing CI/CD pipeline steps locally

Run the pipeline's docker commands **verbatim** through the compatibility layer above —
translating them defeats the purpose of local verification. Before doing CI-reproduction
work, load `references/ci-and-troubleshooting.md` for the rootful-vs-rootless, network-name,
host.docker.internal, and Testcontainers/Ryuk divergences vs Linux CI runners.

## Env-specific gotchas

- **2 GiB VM memory** — large builds/stacks can OOM inside the VM. Fix:
  `podman machine stop; podman machine set --memory 4096; podman machine start`
- Volume mounts accept `C:\Users\...`, `/c/Users/...`, or WSL-internal paths
- Never `wsl --unregister podman-machine-default` — it is the default WSL distro; remove
  machines only with `podman machine rm`
- Only one machine provider at a time: WSL and Hyper-V machines cannot coexist
- **Space-interleaved output** (`p o d m a n   m a c h i n e   s t a r t …`) is UTF-16 read as
  8-bit — cosmetic but it breaks any gate that greps the output. Fix for that call:
  pipe through `| Out-String`, or set `[Console]::OutputEncoding = [Text.Encoding]::UTF8`
  before invoking `podman`/`wsl`.

## Troubleshooting

On any container failure (connection refused, API clients can't connect, short-name
resolution prompt, compose targeting the wrong engine, exit 137), consult the
symptom→fix table in `references/ci-and-troubleshooting.md` before debugging.
