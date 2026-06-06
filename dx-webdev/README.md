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

`tmp/` is generated output and is ignored by git.

## Review Expectations

Generated pages should load jQuery before DevExtreme, include every initialized widget container, use scoped styling, and avoid framework or ThemeBuilder artifacts.

## Privacy

This local plugin does not include network services, analytics, telemetry, or credential collection. Generated files and temporary outputs stay in local workspace paths selected by the user or script command.

## Terms of Use

This is a personal, unlicensed DevExtreme jQuery helper plugin. Review generated output before shipping and follow DevExpress licensing terms for any DevExtreme assets or libraries used by the consuming project.
