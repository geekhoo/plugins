---
name: dx-ui-pattern
description: Use when the user asks for "DevExtreme", "DX WebDev", "jQuery SaaS UI", "dxDataGrid", "drawer or action-sheet", or "mfdx legacy frontend" work that needs DevExtreme/jQuery UI patterns, vendor-local assets, and viewport contracts.
---

# DX UI Pattern

## Overview

Implement or validate DevExtreme jQuery UI patterns from current repo evidence. Preserve vendor asset boundaries and prove the result through rendered viewport and interaction checks.

## Prerequisites And Clarification

- Identify the target framework, DevExtreme version, local asset paths, and excluded vendor directories before editing.
- Inspect existing layout, theme, data-shape, and widget conventions before choosing components.
- Ask for the target screen, reference UI, widget set, or required viewport contract only when it is not inferable from the request or repo.
- Use `ui-parity-validator` when the work is primarily reference matching.
- Use `browser-qa` when the work is primarily general rendered validation.

## Workflow

1. Define the UI goal: target screen, data shape, primary workflows, required widgets, viewports, and interaction states.
2. Inventory existing assets and boundaries: DevExtreme bundles, local vendor paths, CSS conventions, app initialization, routing, and directories that must remain untouched.
3. Map the data shape to DevExtreme widgets and options. Prefer established local patterns for grids, forms, filters, drawers, dialogs, action sheets, toolbars, and responsive containers.
4. Implement the smallest scoped change in allowed source files. Keep vendor-local assets referenced, not rewritten, unless the user explicitly asks to change them.
5. Validate browser-visible behavior: route loads, widgets render, data appears, drawer or action-sheet interactions work, no obvious overflow occurs, and required desktop/mobile viewports satisfy the contract.
6. Compare against a reference only when one exists or was requested. Capture screenshots where they clarify parity, layout risk, or interaction state.
7. Report the implemented pattern, validation evidence, skipped checks, and remaining UI risks.

## Verification Gates

| Gate | Requirement |
|---|---|
| G0 Scope | Target UI, framework/version, dependencies, allowed files, and protected vendor paths are known. |
| G1 Evidence | Existing DevExtreme assets, layout conventions, widget patterns, and data shape have been inspected. |
| G2 Plan | Widget selection, responsive behavior, and interaction states are explicit before implementation. |
| G3 Implementation | Changes are complete inside the allowed source boundary and preserve vendor-local assets. |
| G4 Browser Validation | Rendered checks cover required viewports and key interactions such as grids, drawers, dialogs, action sheets, filters, or toolbars. |
| G5 Reporting | Final output includes validation commands or browser evidence, UI risks, screenshots where useful, and any skipped checks. |

## Acceptance Criteria

- UI uses appropriate DevExtreme widgets and options for the actual data shape and workflow.
- Layout works across required viewports without incoherent overlap, clipping, or unusable controls.
- Drawer, action-sheet, toolbar, grid, form, filter, and dialog behavior works when in scope.
- Local vendor asset boundaries and excluded directories remain preserved.
- Completion is based on rendered validation, not source inspection alone.

## Expected Outcome

Produce a working DevExtreme UI pattern or implementation with clear source boundaries, responsive layout behavior, validated interactions, and rendered evidence sufficient to judge the UI.

## Common Mistakes

- Inventing DevExtreme versions, asset paths, routes, demo behavior, or startup commands.
- Rewriting vendor-local assets or editing excluded directories to make a quick fix.
- Choosing widgets from labels alone instead of mapping the actual data shape and workflow.
- Treating a successful build as proof that the UI renders correctly.
- Checking only desktop when a viewport contract or responsive layout is in scope.
- Omitting skipped interactions, screenshot evidence, or residual UI risks from the final report.
