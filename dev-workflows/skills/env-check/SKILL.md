---
name: env-check
description: This skill should be used when the user asks to "check the Python environment", "preflight the repo", "why won't this run", or "use the .venv" — verify .venv, dependencies, encoding, and database state before running code or tests, surfacing fixes for Windows quirks.
user-invocable: true
argument-hint: "<repo path, default: current project>"
---

# Env Check

Run before executing Python/tests in a repo to catch environment problems early. Targets the recurring Windows friction on this machine.

## Checks

### 1. Virtual environment
- Confirm `<repo>/.venv` exists and find the interpreter: `<repo>/.venv/Scripts/python.exe` (Windows).
- Always invoke that interpreter by absolute path with forward slashes in the Bash tool. Avoid `.\.venv\...` relative paths in PowerShell — they resolve unreliably and can error with "not recognized".
- Report Python version (`python --version`).

### 2. Dependencies
- Diff installed packages against `requirements*.txt` / `pyproject.toml`: `pip check` and `pip list`.
- Flag version conflicts (notably pydantic / pydantic-core mismatches) and missing test deps (jsonschema, pytest). Propose adding missing test deps to requirements rather than ad-hoc installs.

### 3. Encoding
- Note that Python `print()` of Unicode crashes on the Windows console (cp1252). For any script that emits non-ASCII, recommend `$env:PYTHONIOENCODING='utf-8'` or writing utf-8 to a file.

### 4. Environment variables & .env
- Check for a `.env` and list the keys it sets. Warn when test runs would inherit production values (e.g. `AGENT_MODE=pydantic` overriding a test's expected default) — tests should use isolated env, not load production `.env` at import.

### 5. Database (if applicable)
- For async SQLAlchemy/asyncpg test setups, confirm `conftest.py` uses sync table setup + a fresh engine per test (event-loop scope mismatch otherwise).
- Confirm migrations are applied and the target DB is reachable; prefer a localhost DB (remote hosts may be unreachable from the dev machine).

## Output
A short checklist: ✅/⚠️/❌ per check with the exact remediation command. Don't change anything without asking — this is a preflight, not a fixer. If everything's green, say so and give the ready-to-run command using the venv interpreter.

## Related skills
- `dotnet-env-check` — the .NET/ASP.NET equivalent (SDK, restore, EF migrations, DB reachability).
- `env-doctor` — machine-level toolchain resolution when interpreters/SDKs don't resolve at all.
