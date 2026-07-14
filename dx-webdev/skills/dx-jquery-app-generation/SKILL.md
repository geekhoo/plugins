---
name: dx-jquery-app-generation
description: Use when generating a new pure HTML/CSS/JS app or page with DevExtreme jQuery widgets — scaffolding, asset load order, jQuery widget initialization. For reconfiguring existing widgets, use dx-capability-map-usage.
---

# DevExtreme jQuery App Generation

Use this skill when generating or changing a pure HTML/JS/CSS page that uses DevExtreme jQuery widgets.

Before substantial UI work, write a short `ux-intent` plan covering surface, audience, workflow, density, widget composition, required states, and validation approach.

Generate or update exactly the app files the task needs, usually:

- `index.html`
- `styles.css`
- `app.js`

Load assets in this order:

1. DevExtreme theme CSS.
2. jQuery.
3. DevExtreme JavaScript.
4. Local `app.js`.

Initialize widgets with jQuery syntax, for example:

```javascript
$('#ordersGrid').dxDataGrid({
    dataSource: orders,
    searchPanel: { visible: true },
    columnAutoWidth: true
});
```

Prefer DevExtreme widgets over hand-built controls when an appropriate widget exists. Include loading, empty, error, disabled, validation, and responsive states when they are relevant to the workflow. Use browser or static validation when possible.

Before reporting a generated page as working, run the **render gate** in `dx-ux-review` (serve over local HTTP, verify in a real browser via browser-verify/browser-qa, zero console errors, widgets instantiated).

Do not generate framework wrapper code, JSX, TSX, generated wrapper package usage, or ThemeBuilder output. Keep output as pure HTML, JavaScript, and CSS.
