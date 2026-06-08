---
name: api-contract-check
description: This skill should be used when the user asks to "contract-check the API", "verify the endpoints", "test every endpoint", or "do the endpoints match the spec" — inventory endpoints from source, exercise each, and report contract failures grouped by domain (FastAPI or ASP.NET).
user-invocable: true
argument-hint: "<repo or project path, + optional base URL>"
---

# API Contract Check

Use to verify that a service's real behavior matches its declared contract — inventory endpoints from source, hit each one, and collate failures. Works for FastAPI (Python) and ASP.NET (C#) projects.

## 1. Inventory endpoints from source
- **FastAPI:** scan route decorators (`@router.get/post/...`) and the app factory; capture method, path, request/response models (Pydantic/SQLModel), and auth dependencies.
- **ASP.NET:** scan controller attributes (`[HttpGet]` etc.), `Program.cs`/minimal-API maps, route prefixes. Note route matching is case-insensitive.
- Produce a table: method · path · domain · request shape · response shape · auth.

## 2. Establish a clean environment first — invoke `env-check`
Contract failures are often environment, not API, bugs. Run the `env-check` skill as the preflight (it verifies `.venv`/SDK, deps, encoding, and DB reachability/migrations). Then:
- Confirm seed data exists (a 500 on a missing row is a prereq gap, not a contract bug). For .NET + Postgres, prefer a reachable localhost DB — remote hosts have failed to resolve.
- Distinguish, in findings, **prereq/seed/migration** issues from **actual contract violations** (e.g. 500-on-missing where 404 is the contract).

## 3. Exercise each endpoint
- Drive via HTTP (curl/httpx) or the project's test client; for auth flows, obtain a token first.
- Check: status code matches contract, response shape matches the declared model, error cases return the documented status.
- Group requests by domain so partial runs are meaningful.

## 4. Report
Write a dated report grouped by domain: for each endpoint — PASS / FAIL with the observed vs expected, and the failure class (contract-violation | prereq/seed | auth | env). Summarize counts. Report first; do **not** apply fixes unless explicitly asked.

## Related skills
- `env-check` — run first as the environment preflight (Section 2).

## Notes
- Bash tool on Windows: use forward slashes, not backslashes (backslash paths get eaten).
- If the project has OpenAPI/Swagger, cross-check the live schema against the source inventory too.
