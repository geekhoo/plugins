---
name: dx-saas-ux-pattern-translation
description: Translate proven SaaS UX patterns from products such as Salesforce, Microsoft 365, Google Workspace, and monday.com into DevExtreme jQuery capability maps and implementation plans without cloning vendor layouts.
---

# DevExtreme SaaS UX Pattern Translation

Use this skill when a user asks for SaaS-style UX, enterprise workflow design, capability-map expansion, or component selection inspired by mature SaaS apps.

Keep the boundary: pure HTML, JavaScript, CSS, jQuery, and DevExtreme jQuery widgets. Do not emit Angular, React, Vue, JSX, TSX, generated wrapper usage, or ThemeBuilder output.

## Workflow

1. Identify the user's operational goal: act on records, switch views, manage context, monitor status, filter dashboards, or complete a workflow.
2. Load the smallest relevant SaaS reference:
   - `references/saas-ux/source-inventory.json` for source provenance.
   - `references/saas-ux/pattern-taxonomy.json` for cross-product pattern categories.
   - `references/saas-ux/vendor-observations.json` for product-specific observations.
3. Load the matching capability map under `references/capability-map/saas-patterns/`.
4. Translate the pattern into DevExtreme jQuery primitives using `references/capability-map/index.json` and component maps.
5. Preserve the user's design direction; use the SaaS pattern as a capability model, not as a visual template.

## Translation Rules

- Start from the user's work object: record, task, file, message, event, item, board row, or dashboard signal.
- Prefer "same data, different lens" designs when users need to analyze one object model in multiple ways.
- Put actions near the selected item, row, or current view before adding global controls.
- Keep secondary context in drawers, split panes, side panels, popups, or popovers so users avoid tab switching.
- Use semantic tokens for status, people, tags, files, events, and ownership when they help scanning or filtering.
- Design dashboards as filterable compositions with drill-through, not static card collections.
- Always map back to concrete DevExtreme widgets and option paths before implementation.

## Anti-Patterns

- Do not copy Salesforce, monday.com, Microsoft, Google, Fluent, or Material layouts verbatim.
- Do not add recipe-style full layouts when a capability map is enough.
- Do not choose dashboards when users need direct row-level editing.
- Do not choose side panels for destructive or validation-heavy workflows that need modal focus.
- Do not hide primary actions in overflow menus on desktop unless the surface is genuinely constrained.
