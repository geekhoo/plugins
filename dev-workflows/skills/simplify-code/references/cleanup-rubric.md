# Cleanup Rubric

Use this reference as a checklist after scope is known. Report rule names only when they help the user understand the change; do not turn the final answer into a rubric dump.

## Comments

- Delete comments that narrate the diff, restate obvious code, mention temporary AI scaffolding, preserve TODOs without an owner or issue, or explain why a mechanical implementation was chosen.
- Keep comments that explain domain constraints, surprising behavior, protocol requirements, security assumptions, migration compatibility, or test intent — including host quirks (`::deep` DevExtreme scoping, `py -3` PATH stability, PowerShell quoting).
- Tighten long comments into the smallest rationale that would help a future maintainer.

## Structure

- Prefer existing local helpers, services, adapters, fixtures, and test utilities over new near-duplicates — `window.Markefin` namespaces on the frontend, existing MediatR handlers and domain services in `mf-dotnet`.
- Inline pass-through functions, single-use helpers, and wrappers that do not name a meaningful concept.
- Remove dead branches, speculative extension points, fallback code that cannot be reached, and unused abstractions after proving call sites.
- Avoid turning one clear function into a network of tiny helpers unless the split mirrors existing local style.

## Duplication

- Collapse repeated literals, conditionals, mapping tables, test setup, and argument-shaping code when it improves readability.
- Keep duplication when branches are intentionally separate domain concepts, when abstraction would hide policy, or when shared code would create awkward coupling.
- Keep apparent CSS/JS duplication in the ProgramsV2 grid unless the full column/band interdependency set is verified — partial "deduplication" there breaks the grid.

## Typing And APIs

- Use established project types, aliases, enums, result shapes, and framework APIs.
- Remove redundant casts, broad `any`/`object` escapes, needless nullability churn, and reimplemented standard-library behavior.
- Do not change public contracts unless the user asked for that level of refactor.

## Complexity

- Prefer straight-line code, guard clauses, simple loops, and data tables over nested conditionals and clever control flow.
- Split large functions only where there is a stable concept boundary and local style supports it.
- Flag broad module decomposition as a follow-up unless the current task explicitly authorizes it.

## Defensive Code

- Remove swallowed exceptions, catch-and-ignore blocks, retry loops, and fallback defaults only when existing callers/tests prove they are not required.
- Keep validation at trust boundaries, user input boundaries, serialization boundaries, external service boundaries, and concurrency boundaries.
- Treat async, cancellation, transactions, disposal, and idempotency as behavior-sensitive — especially EF Core DbContext lifetime and MediatR pipeline behavior in `mf-dotnet`.

## Tests

- Simplify duplicated setup and over-specified assertions when intent remains clear.
- Keep tests that document regressions, boundary cases, and domain policy even if implementation now looks simpler.
- Run or update the smallest relevant test set after changing production behavior-adjacent code.
