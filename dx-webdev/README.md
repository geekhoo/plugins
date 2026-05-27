# dx-webdev

Personal Codex plugin for generating and reviewing high-quality DevExtreme jQuery UI in pure HTML, JavaScript, and CSS apps.

This plugin targets DevExtreme jQuery widgets only. Generated output should be ordinary `index.html`, `styles.css`, and `app.js` files that load jQuery and DevExtreme directly. It intentionally avoids framework wrappers, JSX/TSX, generated wrapper code, and ThemeBuilder output. Start from an official DevExtreme theme CSS file, then apply local app styling with CSS variables and wrapper-scoped selectors.

## Skills

- `dx-jquery-app-generation`: create or modify pure HTML/JS/CSS pages with DevExtreme jQuery widgets.
- `dx-component-selection`: map UX intent to the right DevExtreme widget composition.
- `dx-capability-map-usage`: map UX intent to DevExtreme widget capabilities, option paths, dependencies, and constraints.
- `dx-saas-ux-pattern-translation`: translate mature SaaS UX patterns into DevExtreme jQuery capability choices without cloning vendor layouts.
- `dx-options-recipes`: use optional starter option examples only when recipes or samples are explicitly requested.
- `dx-styling-without-themebuilder`: style widgets with app CSS variables and stable scoped selectors.
- `dx-design-system-translation`: translate design tokens and UX phrases into concrete DevExtreme choices.
- `dx-ux-review`: review generated pages for widget fit, load order, styling scope, states, accessibility, and validation.

For substantial UI work, first produce a short `ux-intent.json` or `component-plan.md`, check `references/capability-map/` for relevant widget capabilities, then generate the page and run static validation.

## Capability Maps

Capability maps are queryable references for what DevExtreme jQuery widgets can do. They are intentionally not recipes or layouts. Use them to answer questions like "which option enables fixed columns?", "what dependencies does popup toolbar placement have?", or "should this be a drawer, splitter, popup, toolbar, or CSS layout wrapper?"

Current maps live under `references/capability-map/`:

- `index.json`: inventory and phrase index.
- `components/dxDataGrid.json`
- `components/dxDrawer.json`
- `components/dxSplitter.json`
- `components/dxPopup.json`
- `components/dxToolbar.json`
- `components/dxForm.json`
- `components/tabbed-navigation.json`
- `components/list-tree-navigation.json`
- `components/dropdown-editors.json`
- `components/dxMenu.json`
- `components/layout-widgets.json`
- `components/card-and-board-views.json`
- `components/scheduling-and-planning.json`
- `components/analytics-and-filtering.json`
- `components/action-controls.json`
- `components/feedback-and-overlays.json`
- `components/validation-and-forms-support.json`
- `components/hierarchical-workbench.json`
- `components/file-and-content-workflows.json`
- `components/collaboration-and-context.json`
- `saas-patterns/work-object-model.json`
- `saas-patterns/multi-view-data.json`
- `saas-patterns/contextual-actions.json`
- `saas-patterns/side-context-surfaces.json`
- `saas-patterns/semantic-status-and-entities.json`
- `saas-patterns/dashboard-composition.json`
- `saas-patterns/workflow-feedback.json`
- `html-css-layout.json`

Recipes and templates remain available as examples, but capability maps should be the primary context for targeted reconfiguration and UX enhancement.

## SaaS UX References

`references/saas-ux/` contains source-backed observations from Salesforce, monday.com, Microsoft 365/Fluent, Google Workspace, and Material Design:

- `source-inventory.json`: URLs, evidence snippets, and pattern tags.
- `pattern-taxonomy.json`: reusable SaaS workflow pattern definitions.
- `vendor-observations.json`: vendor-specific observations translated into DevExtreme targets.

Use these references to reason about operational patterns such as record workbenches, side-context panels, contextual actions, semantic chips, filterable dashboards, and workflow feedback. Do not use them to copy a vendor's visual layout.

## Script Usage

The scripts are expected to run with Node.js and no external npm dependencies:

```bash
node scripts/generate-dx-page.js --spec references/example-page-spec.json --out tmp/generated-basic
node scripts/validate-dx-html-js.js --dir tmp/generated-basic
node scripts/audit-dx-output.js --dir tmp/generated-basic
node scripts/extract-design-tokens.js --tokens path/to/tokens.json --out tmp/tokens.css
```

Syntax checks:

```bash
node --check scripts/generate-dx-page.js
node --check scripts/validate-dx-html-js.js
node --check scripts/extract-design-tokens.js
node --check scripts/audit-dx-output.js
```

## Example Page Spec

`references/example-page-spec.json` is a basic-page spec for an orders workbench. It defines a page title, base theme CSS, widget containers, DevExtreme jQuery widgets, sample data, local design tokens, and expected output files.

Minimal shape:

```json
{
  "title": "Orders Workbench",
  "template": "basic-page",
  "themeCss": "https://cdn3.devexpress.com/jslib/25.2.3/css/dx.light.css",
  "devextremeVersion": "25.2.3",
  "containers": [
    { "id": "ordersToolbar", "className": "app-toolbar" },
    { "id": "ordersList", "className": "app-list" }
  ],
  "widgets": [
    { "containerId": "ordersToolbar", "type": "dxToolbar" },
    { "containerId": "ordersList", "type": "dxList", "dataKey": "orders" }
  ],
  "sampleData": {
    "orders": [
      { "id": 1001, "customer": "Northwind Traders", "status": "Ready" }
    ]
  },
  "tokens": {
    "color": { "brand": "#1F6FEB" },
    "spacing": { "md": "16px" }
  },
  "outputFiles": ["index.html", "styles.css", "app.js"]
}
```

## Example Token Input

`extract-design-tokens.js` expects a simple JSON object and emits CSS variables:

```json
{
  "color": {
    "surface": "#FFFFFF",
    "text": "#1F2937",
    "brand": "#1F6FEB"
  },
  "spacing": {
    "sm": "8px",
    "md": "16px",
    "lg": "24px"
  },
  "radius": {
    "sm": "4px"
  },
  "typography": {
    "fontFamily": "Arial, sans-serif"
  },
  "elevation": {
    "panel": "0 1px 3px rgba(0, 0, 0, 0.12)"
  }
}
```

## Review Expectations

Generated pages should validate that DevExtreme CSS and JavaScript are loaded, jQuery appears before DevExtreme JavaScript, widget container IDs exist, jQuery widget initialization is present, local styling is scoped, and no excluded framework or ThemeBuilder artifacts are emitted.
