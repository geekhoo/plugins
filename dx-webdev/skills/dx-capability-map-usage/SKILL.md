---
name: dx-capability-map-usage
description: Use when reconfiguring, enhancing, or planning a DevExtreme jQuery UI and you must check which widgets, option paths, or composition primitives exist — search the capability maps before emitting code.
---

# DevExtreme Capability Map Usage

Use this skill when a task asks to reconfigure, enhance, or plan a DevExtreme jQuery UI and the answer depends on which widgets, options, or composition primitives are available.

Keep the plugin boundary: pure HTML, JavaScript, CSS, jQuery, and DevExtreme jQuery widgets. Do not switch to Angular, React, Vue, JSX, TSX, generated wrappers, or ThemeBuilder output.

## Workflow

1. Interpret the requested UX outcome in plain terms.
2. Search the capability maps by component, option path, user phrase, and constraint.
3. Select the smallest set of DevExtreme widgets and plain HTML/CSS needed.
4. Prefer reconfiguring existing widgets before replacing them.
5. Prefer DevExtreme options before CSS overrides.
6. Use CSS for layout, spacing, responsive behavior, visual treatment, and template content.
7. Validate option paths, enum values, and dependencies before emitting code.

## Reference Files

These live at the **plugin root** (the `dx-webdev` plugin directory, NOT this skill's directory) — resolve `<plugin-root>` before reading or searching:

- `<plugin-root>/references/capability-map/index.json`: map inventory and phrase index.
- `<plugin-root>/references/capability-map/components/*.json`: component capability maps.
- `<plugin-root>/references/capability-map/saas-patterns/*.json`: cross-product SaaS workflow maps that translate operational patterns into DevExtreme primitives.
- `<plugin-root>/references/capability-map/html-css-layout.json`: plain HTML/CSS layout primitives that complement widgets.
- `<plugin-root>/references/saas-ux/*.json`: source-backed SaaS observations and taxonomy. Load only when the task asks for SaaS-style pattern translation or research provenance.

Load only the files that match the current user intent. The maps answer what primitives are available; they are not layout recipes and should not decide the final visual design for you.

Useful searches:

```bash
# run from <plugin-root>, or prefix the paths with it
rg -n "fixed column|columnFixing|drawer|splitter|toolbar|popup" references/capability-map
rg -n "\"path\": \"columns\\[\\]\\.fixed\"" references/capability-map
rg -n "record workbench|side panel|smart chip|dashboard widgets|command bar" references/capability-map references/saas-ux
```

## Behavior Rules

- Preserve creative layout decisions unless a DevExtreme constraint requires a specific structure.
- Keep recipes and templates optional; use them only when the user explicitly asks for examples or a starter page.
- If a requested option path is absent from the map, verify it against local DevExtreme declarations or source before using it.
- When a dependency exists, include the dependency with the option. Example: `columns[].fixedPosition` requires `columns[].fixed = true`.
- When a widget is already present, patch its options in place where possible instead of rebuilding the page.
