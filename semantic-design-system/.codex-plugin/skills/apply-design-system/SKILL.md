---
name: apply-design-system
description: Use when migrating a web codebase from hardcoded styling values to an existing semantic or component design-token system.
disable-model-invocation: true
allowed-tools: Read Grep Glob Edit Write Bash(node *) Bash(ds-token-build *) Bash(ds-token-validate *)
---

# Apply Semantic Design System

Use the canonical workflow in `skills/apply-design-system/SKILL.md`.

Codex compatibility notes:

- Use `PLUGIN_ROOT` for plugin files when available.
- The default token source is `design/tokens/` relative to the workspace.
- Validate tokens with `node "$PLUGIN_ROOT/scripts/validate-tokens.mjs" design/tokens`.
- Build CSS variables with `node "$PLUGIN_ROOT/scripts/build-css-vars.mjs" design/tokens src/styles/tokens.css ds`.

Keep migrations scoped to the requested components or paths, preserve behavior, and report every changed file.
