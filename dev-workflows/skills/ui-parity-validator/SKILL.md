---
name: ui-parity-validator
description: Use when the user asks to "match a reference page or image", "verify UI parity", "compare before and after", "check a visual diff", or "preserve layout or responsive behavior" by validating a target UI against a reference.
---

# UI Parity Validator

## Overview

Validate visible UI behavior against a known reference. Treat parity as matching the important user-visible result, not pixel perfection, unless the user explicitly asks for pixel-level comparison.

Use `browser-qa` when the task expands beyond source-target parity into broad rendered route/flow QA, console/network health, or frontend completion.

## Prerequisites And Clarification

- Identify the reference source: URL, screenshot, Figma node, existing route, component, or before-state capture.
- Identify the target: route, local app, file, component, branch, implementation, or screenshot.
- Ask only when the reference, target, tolerance, priority dimensions, required viewports, or required states are unclear.
- When comparing before/after behavior, capture the baseline before editing.
- If implementation is not in scope, validate and report only.

## Workflow

1. Define parity criteria: layout, typography, spacing, color, content, responsive behavior, interactions, loading/error states, accessibility-relevant affordances, and explicit non-goals.
2. Capture reference evidence with screenshots or source-backed design evidence. Use `browser-probe` for scripted screenshots when available; use `figma-design-loop` when the reference is Figma-specific.
3. Capture target evidence across the required viewports and states. Include console, network, DOM, or interaction evidence when visual output depends on runtime behavior.
4. Compare source and target. Record each delta with location, expected behavior, actual behavior, severity, and whether it must be fixed or can be accepted.
5. Iterate only if implementation is in scope: make the smallest UI changes needed, recapture target evidence, and recheck the affected criteria.
6. Report final parity status with evidence paths, viewport/state coverage, pass/fail deltas, fixed or accepted differences, assumptions, and limitations.

## Verification Gates

- G0 Scope: reference and target are known.
- G1 Evidence: baseline or reference evidence is captured before comparison.
- G2 Criteria: parity dimensions, tolerance, viewports, and states are explicit.
- G3 Execution: captures, comparisons, and any edits stay within the allowed scope.
- G4 Validation: comparison is performed across required viewports and states.
- G5 Reporting: final output lists pass/fail deltas and unresolved risks.

## Acceptance Criteria

- Important visible behavior is compared, not just source code or static markup.
- Deltas are explained and either fixed, accepted, or called out as unresolved.
- Responsive states are covered when relevant.
- Before/after evidence is provided when validating a change.
- Final status is clear enough for another agent or reviewer to reproduce the check.

## Expected Outcome

Produce a UI parity report or a fixed implementation with before/after evidence, viewport coverage, and an explicit list of remaining visual deltas.

## Common Mistakes

- Treating a passing build or unit test as UI parity evidence.
- Skipping baseline capture before editing a before/after target.
- Comparing only one desktop viewport when the requested surface is responsive.
- Ignoring interactions, loading states, or error states that define the visible behavior.
- Claiming parity while leaving unexplained visual differences.
