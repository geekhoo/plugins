---
name: dotnet-env-check
description: Use when the user asks to "check the .NET environment", "preflight the dotnet repo", "why won't dotnet build/run", "check EF migrations", or before running an ASP.NET service or its tests — verify SDK, restore, EF Core migration state per DbContext, and database reachability. For Python repos use env-check; for machine-level toolchain resolution use env-doctor.
user-invocable: true
argument-hint: "<repo path, default: current project>"
---

# .NET Env Check

Run before building, running, or testing a .NET/ASP.NET repo to catch environment problems early. The .NET sibling of `env-check` — same contract: a preflight, not a fixer.

## Checks

### 1. SDK resolution
- `dotnet --version` from the repo root — if a `global.json` exists, confirm the pinned SDK is installed (`dotnet --list-sdks`); a missing pinned version fails with a misleading "SDK not found" at build time.
- If `dotnet` itself doesn't resolve, that's a machine-level problem — route to `env-doctor`.

### 2. Restore
- `dotnet restore` (or confirm `obj/project.assets.json` is newer than the `.csproj`/`Directory.Packages.props`). Flag NuGet feed/auth errors distinctly from package-version conflicts.
- If the repo has a `.config/dotnet-tools.json`, run `dotnet tool restore` too — `dotnet ef` usually lives there, and the EF checks below silently fail without it.

### 3. EF Core migrations — per DbContext
- Multi-context repos must pass `--context` explicitly or every `ef` call errors with "More than one DbContext was found" (mf-api-v2 has two: `ApplicationDbContext` business + `ApplicationIdentityDbContext` identity). Enumerate contexts first: `dotnet ef dbcontext list`.
- For **each** context: `dotnet ef migrations list --context <Ctx>` and report pending (un-applied) migrations. A service whose startup doesn't auto-migrate (mf-api-v2's `CoordinateMigrationsAsync` is never invoked) will 500 on first query — pending migrations are a prereq gap, not an app bug.

### 4. Database reachability
- Read the connection string from `appsettings.Development.json` / user-secrets / env vars — report which source won.
- Probe the host:port (e.g. `Test-NetConnection <host> -Port 5432`). Prefer a localhost database — remote Postgres hosts have failed to resolve from this dev machine. If the target is remote and unreachable, recommend pointing at localhost rather than retrying.

### 5. Seed data & the destructive-endpoint guardrail
- Check whether required seed data exists (a 500 on a missing row is a prereq gap). If seeding is manual (e.g. a `DataSeederController`), name the seed endpoint as the remediation.
- **Never call `/api/DataSeeder/clear` or any other destructive/reset endpoint as part of this preflight, and never propose it without explicit user approval.** Preflight is read-only against the database.

## Output
A short checklist: ✅/⚠️/❌ per check with the exact remediation command (including the `--context` flag where relevant). Don't change anything without asking. If everything's green, say so and give the ready-to-run command.

## Related skills
- `env-check` — the Python/.venv equivalent of this preflight.
- `env-doctor` — machine-level toolchain resolution (dotnet/python/node on PATH) when the SDK itself doesn't resolve.
- `api-contract-check` — invokes this skill as its §2 preflight for .NET repos.
