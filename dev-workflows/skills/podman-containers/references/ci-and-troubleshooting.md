# Reproducing CI/CD steps locally & troubleshooting quick reference

Supporting reference for `podman-containers`.

## Reproducing CI/CD pipeline steps locally

When verifying or implementing a container-based CI step (GitHub Actions `docker build`
/ `docker run` steps, Jenkins agents, etc.), run the pipeline's docker commands
**verbatim** through the compatibility layer in SKILL.md — translating them defeats the purpose
of local verification. Differences vs a Linux CI runner that can produce divergent results:

- CI runners are usually rootless or user-namespaced; this machine's engine is **rootful**
  (containers run as root, low ports < 1024 bind fine here but may fail in CI)
- Default network here is named `podman`, not `bridge` — scripts hardcoding
  `--network bridge` need that network created, not the script edited
- `host.docker.internal` and `host.containers.internal` both resolve inside containers
  (Podman 5 adds them automatically)
- Testcontainers: works out of the box via the pipe; if the Ryuk reaper container flakes,
  set `TESTCONTAINERS_RYUK_DISABLED=true` for the test run

## Troubleshooting quick reference

| Symptom | Cause → fix |
|---|---|
| `connection refused` / `cannot connect to Podman` | Machine not running → `podman machine start` |
| Docker API clients can't connect | `docker_engine` pipe missing → restart machine; or set `DOCKER_HOST` to the podman pipe |
| `short-name "x" did not resolve` or a registry prompt | Unqualified image name → use `docker.io/library/x` |
| Compose targets wrong/absent engine | Stale `$env:DOCKER_HOST` → clear it or point at `npipe:////./pipe/podman-machine-default` |
| Build killed / exit 137 | VM out of memory → raise machine memory (see SKILL.md gotchas) |
