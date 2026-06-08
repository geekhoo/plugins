---
name: test-and-seed
description: This skill should be used when the user asks to "test the UI and seed data", "smoke test the frontend then populate it", or "set up demo data" — exercise the app UI then load coherent data, composing env-check, browser-qa, and db-seed.
user-invocable: true
argument-hint: "<app URL or repo, + what to seed, e.g. '2-3 projects of varying complexity'>"
---

# Test and Seed

Orchestrates a UI smoke test plus realistic seeding. It is a thin workflow — it **delegates** to existing skills rather than re-implementing them:
- environment preflight → `env-check`
- driving/verifying the UI → `browser-qa` (or `browser-probe` for scripted/repeatable checks)
- populating data → `db-seed`

## 1. Clarify before starting
- **Which UI flows** to smoke (e.g. create-project, create-task)?
- **Seed shape/volume** and timeline?
- **Append or reset** existing data? (Never reset without an explicit yes.)
- Are backend + frontend running, and on which ports (e.g. FastAPI 8000, SPA 3000)?

## 2. Preflight — run `env-check`
Confirm `.venv`, deps, DB reachable/migrated, encoding. Start backend/frontend if needed (via the venv interpreter, forward-slash paths in the Bash tool). Don't proceed until green.

## 3. UI smoke — invoke `browser-qa` (or `browser-probe`)
Drive the real UI to validate the create flow end-to-end before bulk seeding. That skill already handles the Playwright MCP gotchas this machine has — re-snapshot after each DOM change and use role/aria-label locators (not numeric `ref=eNNN`); `datetime-local` inputs take `YYYY-MM-DDTHH:MM` (no `Z`/seconds); `file://` is blocked, serve generated HTML over `http.server` on 127.0.0.1. Watch the console for `Failed to fetch`/CORS/404 — isolate with a direct API POST. Screenshot the result.

**Gate:** the create-one-entity UI flow passes before any seeding starts.

## 4. Seed — invoke `db-seed`
Hand `db-seed` the data model + volume/shape/timeline + append-vs-reset decision. It enforces the domain invariants (create-all-before-Done ordering, enum values not names, MILESTONE vs CHECKPOINT, no fabricated unset fields) and verifies counts/orphans afterward.

## 5. Re-verify
Re-run the UI smoke to confirm the seeded data renders correctly (and that unset status/trigger/event fields render no misleading tags/colors).

## Verification gates / acceptance criteria
- env-check green before any UI/DB action.
- UI create-flow passes pre-seed.
- db-seed acceptance met (counts match, invariants hold, no orphans/dupes).
- Post-seed UI render confirmed; console errors triaged.

## Expected outcome
A verified UI + a coherently seeded DB + screenshots + a summary of flows passed and data created. No data reset without approval.
