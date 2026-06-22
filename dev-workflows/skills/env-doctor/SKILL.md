---
name: env-doctor
description: Verify the Windows toolchain that Claude Code and its plugin hooks depend on — python3/python/py resolution, the ~/bin shim dir on PATH, and node/gh/dotnet/pwsh. Use when the user asks "is my environment OK", "why won't this run", "are my hooks alive", "check the toolchain", or when plugin hooks seem to be silently no-opping. Complements env-check (which is .venv/dependency focused); env-doctor focuses on interpreter resolution and the silent-hook-failure class. Pairs with the SessionStart canary hook shipped in this plugin.
---

# env-doctor

Toolchain health check for Windows. The security-guidance and geeky-orchestration plugin hooks shell
out to python and fail *non-blocking* (silently) when no interpreter resolves — once that degraded an
entire plugin safety layer for ~a week (1,040 invisible failures). This surfaces it on demand; the
companion canary hook surfaces it automatically at session start.

## Run

```powershell
pwsh -File scripts/env-healthcheck.ps1          # full PASS/FAIL table
pwsh -File scripts/env-healthcheck.ps1 -Quiet   # output only if something is wrong (hook mode)
```

Checks `python3` / `python` / `py` resolution, the `~/bin` shim dir on PATH, and node / gh / dotnet /
pwsh. Exit 1 when no `python3` resolves — the critical case that silently kills plugin hooks.

## The canary hook

`hooks/env-canary.sh` (wired via this plugin's `hooks/hooks.json`) runs the critical assertion at
every SessionStart and injects a loud warning into context if no python resolves. It uses **only bash
builtins** (`command -v`, `printf`), so it cannot share the failure mode it guards against. Silent when
healthy; never blocks startup. This makes the safeguard portable — it travels with the plugin across
machines instead of living in a single machine's `settings.json`.
