---
name: test-state-machine-guards
description: This skill should be used when the user asks to "test the state machine", "cover the transition guards", "write guard tests", or fill state-machine test gaps — generate parametrized guard, transition, and cascade test suites per entity.
user-invocable: true
argument-hint: "<entity or module, e.g. Track, or src/domain/rules/...>"
---

# Test State-Machine Guards

Systematically cover state-machine transition guards with tests — a commonly under-tested area. Applies to any guarded state machine; TADM (project → track → task → delivery-point → criterion → control-item) is the running example throughout.

## 1. Map the state machine
- For the target entity, read its states, transitions, and guard conditions (in TADM: `src/domain/rules/*`). List each transition and every guard that can block it.
- Note cross-entity effects (e.g. `maybe_cascade_task_done()` auto-completing a parent track) and ordering constraints (all tasks created before any → Done, else premature cascade).

## 2. Generate parametrized tests
For each transition, cover:
- **Happy path** — all guards satisfied → transition succeeds, side effects fire once.
- **Each guard failing individually** — transition rejected with the right error.
- **Guard composition** — multiple guards failing together.
- **Edge cases** — empty/whitespace inputs, plus each domain guard failing (e.g. in TADM: missing assignee, unsatisfied BLOCKS_START dependency, active BLOCKER control item, unmet READINESS criteria).
- **Cascade/ordering** — completion cascade fires correctly and only once; health rollup is consistent; empty project ≠ GREEN.
- **Sequences** — valid multi-step paths and illegal jumps.

## 3. Async test hygiene (for async SQLAlchemy/asyncpg projects, e.g. TADM)
- Use the verified fixture pattern: sync table setup (`asyncio.run()` once per session) + a fresh `create_async_engine` per test, `AsyncSession(bind=conn, join_transaction_mode="create_savepoint")` for rollback.
- Run via the project's `.venv`; set `$env:PYTHONIOENCODING='utf-8'` first if output has Unicode.

## 4. Verify and report
- Run the suite; report coverage per transition/guard and any genuine bugs surfaced (don't paper over a real guard gap with a lenient assertion — surface it). For TADM, watch for the known double-rollup and GREEN-on-empty issues.

## Notes
This generates tests; if a guard is actually missing in the code, report it rather than writing a test that asserts the buggy behavior.
