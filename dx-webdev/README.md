# dx-webdev

Personal Codex plugin for pure HTML, JavaScript, and CSS apps that use DevExtreme jQuery widgets.

## Scope

- Use jQuery plus DevExtreme jQuery widgets.
- Generate ordinary `index.html`, `styles.css`, and `app.js` files.
- Start from an official DevExtreme theme CSS file, then add local app CSS variables and wrapper-scoped selectors.
- Do not emit Angular, React, Vue, JSX, TSX, generated wrappers, or ThemeBuilder output.

## Skills

- `dx-jquery-app-generation`: create or modify pure HTML/JS/CSS DevExtreme jQuery pages.
- `dx-component-selection`: choose widgets from UX intent and data shape.
- `dx-capability-map-usage`: find widget options, dependencies, constraints, and capability-map references.
- `dx-styling-without-themebuilder`: style widgets with local CSS variables and scoped selectors.
- `dx-design-system-translation`: translate tokens and UX language into DevExtreme implementation choices.
- `dx-ux-review`: review widget fit, load order, styling scope, states, accessibility, and validation.
- `dx-options-recipes`: explicit-only recipe and starter option examples.
- `dx-saas-ux-pattern-translation`: explicit-only SaaS workflow pattern translation.

For substantial UI work, produce a short `ux-intent.json` or `component-plan.md`, consult the smallest relevant file under `references/capability-map/`, implement, then run validation.

## References

Use `references/capability-map/index.json` as the router, then open the smallest matching component or SaaS-pattern map. Capability maps are not layouts or recipes; use templates and recipes only when examples are explicitly requested.

## Spec contract

`references/dx-page-spec-schema.json` is the authoritative input contract for `scripts/generate-dx-page.js`. It is versioned (`schemaVersion` `1.0.0`), and the generator validates every spec against it *before* generating anything. A violation exits non-zero with path-qualified errors and writes no files:

```
ERROR: Spec validation failed for tests/fixtures/invalid/notify-as-widget.json (1 error):
  /widgets/0/type  is "DevExpress.ui.notify", which must be one of: "dxDataGrid", ...
Contract: references/dx-page-spec-schema.json
```

Required top-level keys: `schemaVersion`, `title`, `template`, `widgets`. Everything else is optional. The schema is closed (`additionalProperties: false`), so an unrecognised key is an error rather than silently ignored.

**Widget types are a closed discriminated union.** `widgets[].type` must be one of the 57 supported `dx*` types, discriminated on `type`. `DevExpress.ui.notify` is a callable, not a component, so it is not expressible as a widget — reach it through a `notify` handler instead.

**Event handlers are typed objects, never JavaScript strings.** The generator emits the call site itself, so no spec value is ever interpolated as executable code. Function bodies in a spec are rejected. Two kinds:

```json
{ "kind": "named-reference", "name": "handleSubmit" }
{ "kind": "notify", "message": "Saved", "notifyType": "success", "displayTime": 1600 }
```

`named-reference` requires `name` (a plain JS identifier) and resolves against `window.dxPageHandlers` at call time; a page whose handler is not registered degrades to a warning toast rather than throwing. `notify` requires `message`; `notifyType` (`info`/`warning`/`error`/`success`) and `displayTime` are optional.

**`containers`** groups widgets into page sections, each with its own class list and heading. Omit it and every widget gets its own section, which is the historical layout.

**`outputFiles`** is an object map — `{ "html": ..., "css": ..., "js": ... }` — that renames the emitted files. The generated HTML links whatever names are declared. Defaults are `index.html`, `styles.css`, `app.js`.

## Scripts

Scripts use Node.js and no external npm dependencies:

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

Test suite — golden-output tests for every template and supported widget type, plus negative fixtures asserting that an invalid spec is rejected and writes nothing:

```bash
node tests/run-tests.js
```

Refresh the committed golden output after an intentional change to generated markup:

```bash
UPDATE_GOLDEN=1 node tests/run-tests.js
```

On Windows PowerShell the environment variable is set separately:

```
$env:UPDATE_GOLDEN=1; node tests/run-tests.js
```

Review the resulting golden diff before committing — an unreviewed refresh will happily bless a regression.

`tmp/` is generated output and is ignored by git.

## Review Expectations

Generated pages should load jQuery before DevExtreme, include every initialized widget container, use scoped styling, and avoid framework or ThemeBuilder artifacts.

## Privacy

This local plugin does not include network services, analytics, telemetry, or credential collection. Generated files and temporary outputs stay in local workspace paths selected by the user or script command.

## Terms of Use

This is a personal, unlicensed DevExtreme jQuery helper plugin. Review generated output before shipping and follow DevExpress licensing terms for any DevExtreme assets or libraries used by the consuming project.
