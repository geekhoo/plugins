---
name: db-seed
description: This skill should be used when the user asks to "seed the database", "create demo or sample data", "populate N projects", or "load realistic test data" — seed coherent multi-entity data that respects state-machine ordering, enum-value casing, and encoding.
user-invocable: true
argument-hint: "<repo + what to seed, e.g. '3 projects of varying complexity, Q2-Q3 timeline'>"
---

# DB Seed

A focused primitive for populating a database with believable data without corrupting domain state. Built for state-machine apps like TADM where naive inserts break invariants. Other skills (e.g. `test-and-seed`) call this.

## 1. Clarify before writing
Ask up front (don't assume):
- **Volume & shape:** how many of each entity, what complexity mix, what timeline?
- **Coherence:** what real-world scenario should the data tell (e.g. one ongoing core build + one feature project + one marketing track)?
- **Append or reset:** append to existing data, or reset first? **Never reset/clear without an explicit yes** (destructive — see the destructive-op rule).

## 2. Preflight
- Run `env-check` first (or confirm): correct `.venv` interpreter, DB reachable + migrated, encoding set (`$env:PYTHONIOENCODING='utf-8'` before the command on Windows; forward-slash paths in the Bash tool).
- **Prefer the repo's existing seed script** (`scripts/seed_*.py`) over ad-hoc inserts. Read it to learn the data model and any helper functions.

## 3. Respect domain invariants (where they apply)
- **Creation order / cascades:** create all children before advancing any to a terminal state. In TADM specifically, create *all* tasks before marking any task Done, or the completion cascade closes the parent track prematurely; a project must be Planned before its tracks transition.
- **Enum values, not names:** persist the spec value (`'Active'`), not the Python name (`'ACTIVE'`).
- **Type constraints:** honor model rules (e.g. TADM `MILESTONE` delivery points are project-level with no `track_id`; `CHECKPOINT` may nest under a track).
- **Unset fields:** leave genuinely-unset status/trigger/event null (don't fabricate placeholder values that surface misleading UI).

## 4. Verification gates / acceptance criteria
- Post-seed query confirms **counts match the request**.
- **No orphans or duplicates** (spot-check FKs and unique keys).
- **State-machine invariants hold** (no prematurely-completed parents; health/status sane).
- If a seed run fails partway, report what landed; don't leave half-seeded state silently.
Acceptance = counts match AND invariants hold AND no orphans/dupes.

## 5. Expected outcome
A coherently populated database plus a short manifest: one line per entity group (what was created, counts, timeline) and any cleanup notes. Reports what changed; performs no resets without approval.
