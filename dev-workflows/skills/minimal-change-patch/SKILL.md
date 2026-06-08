---
name: minimal-change-patch
description: Use when the user asks for a small targeted fix, minimal change, small patch, just fix, comment-based implementation, surgical edit, or speed/no-overexploration for a known small patch.
---

# Minimal Change Patch

## Overview

Make the smallest behavior-focused patch that satisfies the request. Preserve nearby code shape, avoid broad refactors, and validate in proportion to the risk of the change.

## Prerequisites

- Identify the exact file, function, failing behavior, or requested comment target before editing.
- Ask only when the patch target is ambiguous or the risk is high.
- Inspect enough surrounding code to avoid breaking contracts, imports, call sites, or tests.
- Use a broader workflow instead when the request needs feature design, cross-cutting refactors, or a full validation campaign.

## Complexity Split

- Use `scope-guard` when protected paths, user-owned changes, or allowed edit boundaries are unclear.
- Use `repo-validation-runner` when validation scope grows beyond a narrow targeted check.
- Use `git-hygiene` for staging, commit, branch, push, dirty-tree, release, or archive operations.

## Workflow

1. Confirm the minimal target from the user request and current repo evidence.
2. Read the smallest necessary context around that target.
3. Apply a focused patch that changes only what is needed for the requested behavior.
4. Remove only unused code introduced by the patch.
5. Run targeted validation: the narrow test, build check, lint check, or browser/API check most likely to catch regressions.
6. Report the narrow scope, validation result, and any broader issue intentionally left untouched.

## Verification Gates

| Gate | Pass condition |
| --- | --- |
| G0 | Target file, function, bug, or comment is known. |
| G1 | Local context was inspected before editing. |
| G3 | Patch is limited to the target behavior and avoids unrelated refactors. |
| G4 | Targeted validation ran, or the reason it could not run is explicit. |
| G5 | Final report names intentionally unaddressed broader issues when relevant. |

## Acceptance Criteria

- Patch is minimal and behavior-focused.
- No unrelated formatting, abstraction, cleanup, or architecture changes.
- Validation is proportional to risk and tied to the changed behavior.
- User-owned changes outside the target are preserved.

## Expected Outcome

A small, validated fix with a clear explanation of exactly what changed and what was deliberately left alone.

## Common Mistakes

- Expanding a bug fix into a refactor because adjacent code looks messy.
- Reading the whole repository when a local function and its call sites are enough.
- Skipping validation because the patch is small.
- Deleting pre-existing unused code or unrelated files.
- Hiding broader issues instead of reporting that they were outside the minimal patch scope.
