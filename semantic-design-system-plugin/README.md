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
/semantic-design-system:derive-design-system inspect this repo and produce tokens under tokens/
/semantic-design-system:apply-design-system migrate Button and Input to tokens
/semantic-design-system:audit-design-system tokens/
```

## Recommended output locations

```text
tokens/
  primitive/
  semantic/
  component/
  themes/
  density/
src/styles/tokens.css
```

## Notes

The utility scripts are intentionally dependency-free. They provide lightweight extraction, validation, and CSS generation. For production, pair them with your preferred design-token compiler such as Style Dictionary or a custom build step.
