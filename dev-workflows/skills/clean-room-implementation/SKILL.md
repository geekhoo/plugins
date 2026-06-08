---
name: clean-room-implementation
description: Use when the user asks for clean room work, to recreate behavior without copying, match a reference from specs only, avoid source reuse, or reimplement behavior from observable or public specs without copying source.
---

# Clean Room Implementation

## Overview

Use this skill to preserve clean-room boundaries while implementing behavior from allowed evidence. The core rule is simple: do not inspect, reuse, paraphrase, or derive implementation details from forbidden source material.

## Prerequisites And Clarification

- Identify allowed references before starting: public docs, user-provided specs, observed behavior, tests, screenshots, API responses, fixtures, or generated black-box outputs.
- Identify forbidden inputs before starting: proprietary source, protected repositories, copied code, private implementation notes, leaked snippets, or any material the user excludes.
- Treat allowed evidence as behavior-defining, not copy permission: do not copy protected text, code, assets, layouts, names, constants, or expressive content unless the license or user explicitly permits reuse; record license and source terms when public material is used.
- Ask before proceeding if allowed and forbidden materials overlap, legal/IP boundaries are unclear, or acceptable similarity is not defined.
- Avoid reading forbidden source entirely. If forbidden material was already visible in the session, treat it as contaminated context and ask how the user wants to proceed.
- Confirm the validation target: behavioral tests, reference outputs, UI parity criteria, API contracts, or user acceptance examples.

## Route Boundaries

- Use `evidence-review` for review-only or source-backed critique work.
- Use `repo-validation-runner` when validation scope expands beyond the allowed clean-room criteria.
- Use `minimal-change-patch` when the user asks for a surgical fix rather than independent implementation.
- Use `ui-parity-validator` for visual behavior matching against an allowed reference.

## Workflow

1. Record the clean-room boundary:
   - Allowed evidence and where it came from.
   - Forbidden source materials and paths.
   - Similarity constraints or uncertainty.
   - Validation criteria.
2. Extract a behavior spec only from allowed evidence:
   - Inputs, outputs, states, edge cases, errors, visual behavior, timing, accessibility, and compatibility requirements.
   - Ambiguities that require clarification or conservative assumptions.
3. Plan an independent implementation:
   - Use existing local architecture and public APIs when permitted.
   - Avoid copying names, structure, comments, algorithms, constants, layouts, or data from forbidden material.
   - Prefer simple, idiomatic implementation choices justified by the behavior spec.
4. Implement inside the allowed edit scope.
5. Validate against allowed criteria:
   - Run allowed tests, compare allowed reference outputs, inspect rendered behavior, or exercise black-box examples.
   - If validation exposes missing behavior, update the behavior spec from allowed evidence before changing code.
6. Report the clean-room constraints followed, validation performed, and any residual similarity or evidence gaps.

## Verification Gates

- G0: Allowed and forbidden sources are known before implementation.
- G1: Behavior spec is derived from allowed evidence only.
- G2: Implementation approach is independent and scoped.
- G3: No forbidden inputs are inspected or reused during implementation.
- G4: Behavior validation passes against allowed tests, reference outputs, or acceptance examples.
- G5: Final report states clean-room constraints, validation, assumptions, and unresolved similarity risk.

## Acceptance Criteria

- No forbidden source material was read, copied, paraphrased, or structurally reused.
- The delivered behavior matches the allowed reference criteria.
- Implementation choices can be explained from allowed evidence, public knowledge, or local project conventions.
- Similarity concerns and ambiguous boundaries are documented instead of hidden.
- Validation evidence is concrete enough for another agent or reviewer to reproduce.

## Expected Outcome

An independently produced implementation that matches allowed behavior evidence, preserves clean-room constraints, and includes a clear record of what was used, what was avoided, and how the result was validated.

## Common Mistakes

- Reading forbidden source "just to understand behavior."
- Treating copied tests, names, constants, or comments as harmless when they reveal implementation.
- Using memory of forbidden material as an implementation guide.
- Expanding the allowed reference set without asking.
- Claiming behavioral parity without running allowed tests or checking reference outputs.
- Reporting only what was built, not the clean-room boundary that was preserved.
