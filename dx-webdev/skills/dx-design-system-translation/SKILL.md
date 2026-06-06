---
name: dx-design-system-translation
description: Use when converting design tokens into DevExtreme jQuery implementation decisions.
---

# Design System Translation

Use this skill when converting design-system intent into a DevExtreme jQuery page.

For substantial pages, produce an intermediate `ux-intent.json` or `component-plan.md` before writing code. Include color roles, spacing, density, typography hierarchy, target workflows, selected widgets, and required states.

Translate:

- Color roles into CSS variables such as `--app-surface`, `--app-text`, `--app-primary`, and `--app-danger`.
- Spacing and density into page layout, grid density, form column count, toolbar grouping, and content rhythm.
- Typography into app shell headings, section titles, labels, grid cell treatment, and status text.
- UX phrases into concrete widget options and layout decisions.

Mappings:

- Quiet enterprise UI: compact layout, restrained borders, low shadow, dense grid.
- Primary action should dominate: one `dxButton` with `type: 'default'`; secondary actions use outlined or text styling.
- Financial grid: right-aligned numeric columns, explicit formatting, summaries, and clear grouping.
- Operational dashboard: filters first, status indicators, scannable grid/detail views.
- Error-prone form: validation group, inline validation, required markers, disabled submit until valid.
- Read-only workflow: disabled editing, clear status labels, review mode styling.

Keep generated output pure HTML, JavaScript, and CSS with DevExtreme jQuery widgets.
