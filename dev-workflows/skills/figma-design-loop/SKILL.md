---
name: figma-design-loop
description: Use for a traceable Figma design→code→VALIDATION loop — fetch design context, implement scoped UI, then validate the RENDERED output against the Figma evidence. Delegates Figma API work to figma-use and rendered checks to browser-qa / ui-parity-validator; its own value is the evidence→scope→rendered-validation gates. Triggers "validate UI against Figma", "implement this Figma design and check it renders", "Figma-backed UI loop". For plain Figma authoring/reading (FigJam, Slides, variables) use the figma plugin skills directly.
---

# Figma Design Loop

## Overview

Use Figma evidence as the source of truth for scoped design, implementation, and UI validation work. Keep the loop traceable: target, evidence, mapping, scoped execution, rendered validation, and limitations. This skill is the **loop orchestrator** — it proxies the actual Figma fetch/write to `figma-use` (or the figma plugin skills) and the rendered checks to `browser-qa` / `ui-parity-validator`; its differential is the verification-gated loop, not re-implementing the Figma API.

## Prerequisites And Clarification

- Use the required Figma prerequisite skill or Figma tooling before fetching design context when the task, URL, or plugin instructions require it. When available, `figma-use` is the expected Figma prerequisite route.
- Ask for the Figma file, node, URL, or current selection only when no target is available.
- Ask when account, plan, permissions, or unavailable tool capabilities block the requested Figma operation.
- Do not rely on remembered or stale Figma tool names. Inspect currently available Figma capabilities when tool availability is uncertain; use `capability-inventory` if needed.
- Use `browser-qa` for ordinary rendered route and interaction checks; use `ui-parity-validator` when the user needs strict visual matching against a Figma reference.

## Workflow

1. Identify the Figma target and the allowed implementation or design scope.
2. Fetch current design context and screenshots from the Figma target.
3. Extract the important components, layout, spacing, typography, tokens, states, responsive behavior, and constraints.
4. Map the Figma evidence to existing code patterns, design-system components, or artifact requirements before editing.
5. Implement only the scoped UI or produce only the requested Figma-backed design artifact.
6. Validate the rendered output, generated artifact, or design-to-code result against the captured Figma evidence.
7. Report the evidence used, validation performed, limitations, and unresolved deltas.

## Verification Gates

- G0: Figma target is known, including file, node, URL, or active selection.
- G1: Design context and screenshot evidence are captured from the current Figma source.
- G2: Implementation or artifact plan maps Figma evidence to existing code patterns or output requirements.
- G3: Work is performed within the requested UI, design, or artifact scope.
- G4: Browser rendering, screenshot comparison, or artifact inspection validates the output against the Figma evidence.
- G5: Final report includes Figma limitations, unavailable capabilities, permission issues, and accepted visual deltas when any exist.

## Acceptance Criteria

- The implementation or artifact is traceable to specific Figma evidence.
- Account, permission, plan, and tool limitations are surfaced instead of hidden.
- The rendered result matches the important design constraints: layout, hierarchy, components, typography, spacing, colors, states, and responsive behavior relevant to the request.
- Changes stay inside the user-approved scope and use existing repo patterns where implementation is required.

## Expected Outcome

A Figma-backed implementation or design artifact with captured evidence, scoped changes, visible validation, and a clear final report.

## Common Mistakes

- Starting implementation from memory, labels, or screenshots the user mentioned without fetching current Figma context.
- Treating compile success as validation when the task requires browser-visible or screenshot-backed comparison.
- Expanding scope into unrelated UI cleanup or design-system refactors.
- Hiding Figma account, permission, or plan limits instead of reporting them.
- Using obsolete Figma tool names when current capability discovery is needed.
