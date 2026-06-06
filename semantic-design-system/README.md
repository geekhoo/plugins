# Semantic Design System Plugin

Semantic design-token workflows for Codex and Claude Code. The plugin provides skills, agents, hooks, CLI utilities, and an optional MCP server for generating, deriving, validating, and applying DTCG-compatible token systems.

## Host Compatibility

- Codex plugin id: `semantic-design-system`
- Codex manifest: `.codex-plugin/plugin.json`
- Codex hooks and MCP config: `.codex-plugin/hooks.json`, `.codex-plugin/mcp.json`
- Codex skills: `.codex-plugin/skills/`
- Claude Code manifest: `.claude-plugin/plugin.json`
- Claude hooks and MCP config: `hooks/hooks.json`, `.mcp.json`
- Claude skills and agents: `skills/`, `agents/`

Runtime scripts accept Codex-style `PLUGIN_ROOT` / `PLUGIN_PROJECT_DIR` and Claude-style `CLAUDE_PLUGIN_ROOT` / `CLAUDE_PROJECT_DIR`. If project env vars are not set, scripts resolve project-relative paths from the current working directory.

## Capabilities

Skills:

- `generate-design-system`: create a new semantic token system from product, brand, UX, accessibility, and stack requirements.
- `derive-design-system`: inspect an existing codebase and infer primitive, semantic, and component tokens.
- `apply-design-system`: migrate code from hardcoded styling values to semantic/component tokens.
- `audit-design-system`: validate naming, references, accessibility risks, and migration readiness.

Utilities:

```sh
ds-token-validate [token-dir]
ds-token-build [token-dir] [output-css-file] [prefix]
ds-style-inventory [project-root] [output-json-file]
```

MCP tools:

- `validate_tokens`
- `build_css_variables`
- `extract_style_inventory`
- `generate_token_skeleton`

## Token Contract

Token source files default to `design/tokens/` relative to the project folder. Pass an explicit first CLI or MCP argument to use a different token directory.

```text
design/tokens/
  primitive/
  semantic/
  component/
  themes/
src/styles/tokens.css
```

Authored token files are strict JSON using `.tokens`, `.tokens.json`, or `.tokens.jsonc`. Bare `.json` and `.jsonc` files are ignored so package/config files under token folders are not parsed as tokens.

Tokens follow the DTCG Design Tokens Format Module 2025.10. `ds-token-validate` fails on unresolved aliases, circular references, missing `$type`, component-to-primitive leakage, and literal semantic color names. Non-standard `$type` values are warnings, not hard failures.

`ds-token-build` emits only `semantic.*` and `component.*` tokens as CSS custom properties. Primitive tokens stay implementation details and are resolved into the exposed values.

## Theming

Theme files under `design/tokens/themes/` are emitted as overrides instead of being merged into the base `:root` block.

- Base tokens emit to `:root`.
- `themes/<name>.tokens.json` emits to `[data-theme="<name>"]`.
- `light` and `dark` themes also emit `@media (prefers-color-scheme: <name>)` blocks scoped to `:root:not([data-theme])`.
- A theme re-emits every exposed token whose resolved value differs from base, so primitive or semantic overrides propagate through component aliases.

## Release Notes

Version 0.2.0 fixed the critical theme-corruption bug where theme files were deep-merged into `:root`, standardized token source files on `design/tokens/`, tightened token-file matching, added DTCG `$type` validation warnings, fixed the `apply-design-system` skill name, aligned tool permissions with skill instructions, and updated agents/MCP descriptions for DTCG 2025.10.

Version 0.1.1 fixed Claude Code manifest validation by making `agents` point at explicit agent Markdown files instead of a directory.

## Local Verification

```sh
node --test tests/*.test.mjs
npm run coverage
node scripts/validate-tokens.mjs examples/minimal-tokens
node scripts/build-css-vars.mjs examples/minimal-tokens tmp/example-tokens.css ds
```

## Privacy

This local plugin does not include network services, analytics, telemetry, or credential collection. Token files, generated CSS, style inventories, and validation results stay in local workspace paths selected by the user or script command.

## Terms of Use

This plugin is provided as a local design-system helper. Review generated tokens and CSS before shipping, and confirm that consuming projects follow the licensing and accessibility requirements that apply to their product.
