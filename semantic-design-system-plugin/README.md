# Semantic Design System Plugin for Claude Code

This plugin packages semantic design-token workflows into Claude Code skills, agents, hooks, bin scripts, and an optional MCP server.

## What it provides

### Skills

- `/semantic-design-system:generate-design-system` — create a new semantic token system from product, brand, and UX requirements.
- `/semantic-design-system:derive-design-system` — inspect an existing codebase and infer primitive, semantic, and component tokens.
- `/semantic-design-system:apply-design-system` — migrate code from hardcoded styling values to semantic/component tokens.
- `/semantic-design-system:audit-design-system` — validate naming, references, accessibility risks, and migration readiness.

### Agents

- `semantic-design-system:design-token-architect`
- `semantic-design-system:codebase-token-auditor`
- `semantic-design-system:design-system-migrator`

### Utilities available through Bash while the plugin is enabled

- `ds-token-validate [token-dir]`
- `ds-token-build [token-dir] [output-css-file] [prefix]`
- `ds-style-inventory [project-root] [output-json-file]`

### MCP tools

- `validate_tokens`
- `build_css_variables`
- `extract_style_inventory`
- `generate_token_skeleton`

## Local testing

From the directory that contains this plugin folder:

```sh
claude --plugin-dir ./semantic-design-system-plugin
```

Then invoke:

```text
/semantic-design-system:generate-design-system SaaS analytics dashboard, light/dark theme, React, WCAG AA
/semantic-design-system:derive-design-system inspect this repo and produce tokens under design/tokens/
/semantic-design-system:apply-design-system migrate Button and Input to tokens
/semantic-design-system:audit-design-system design/tokens/
```

## Token location

Token source files live in **`design/tokens/`**, resolved relative to the project
(working) folder. This is the single standardized location — every skill, agent, script,
hook, and MCP tool defaults to it, with no per-install setting to configure. To target a
different directory for a one-off, pass it explicitly as the first CLI/MCP argument.

```text
design/tokens/
  primitive/
  semantic/
  component/
  themes/
  density/
src/styles/tokens.css   # generated CSS (configurable via css_output_file)
```

## Standards

Tokens follow the **DTCG Design Tokens Format Module 2025.10** — the first stable
release of the W3C Community Group specification (October 28, 2025). Authored token
files are strict JSON using the `.tokens.json` extension; `ds-token-validate` warns on
any `$type` outside the 13 standard types.

## Theming

`ds-token-build` is theme-aware. Files under `design/tokens/themes/` are emitted as overrides,
not merged into the base:

- base tokens → `:root`
- `themes/<name>.tokens.json` → `[data-theme="<name>"]`
- a `light` or `dark` theme additionally emits a `@media (prefers-color-scheme: <name>)`
  block scoped to `:root:not([data-theme])`, so the OS preference applies by default
  while an explicit `[data-theme]` attribute always wins.

A theme re-emits every exposed token whose *resolved* value differs from the base — so
overriding a single primitive or semantic also flows through to every component/semantic
token that aliases it (values are inlined, so the CSS cascade alone cannot propagate the
change).

## Agent agnosticism

The plugin does not pin a model. Skills and agents use `model: inherit`, so they run on
whatever model the host session selects. The bin scripts, hooks, and MCP server shell out
to `node` and contain no model-specific logic, and the token output is vendor-neutral
DTCG. The plugin still depends on Claude Code primitives (`${CLAUDE_PLUGIN_ROOT}`, the
plugin manifest, `hooks.json`, skills), which is expected for a Claude Code plugin.

## Notes

The utility scripts are intentionally dependency-free. They provide lightweight extraction, validation, and CSS generation. For production, pair them with your preferred design-token compiler such as Style Dictionary or a custom build step.
