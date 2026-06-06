---
name: generate-design-system
description: Use when creating a new semantic design-token, theme, or web styling foundation from product, brand, UX, accessibility, and stack requirements.
disable-model-invocation: true
allowed-tools: Read Grep Glob WebFetch Write Bash(node *) Bash(ds-token-validate *) Bash(ds-token-build *)
---

# Generate Semantic Design System

Use the canonical workflow in `skills/generate-design-system/SKILL.md`.

Codex compatibility notes:

- Use `PLUGIN_ROOT` for plugin files when available.
- Write strict JSON token files under `design/tokens/` unless the user gives another path.
- Validate tokens with `node "$PLUGIN_ROOT/scripts/validate-tokens.mjs" design/tokens`.
- Build CSS variables with `node "$PLUGIN_ROOT/scripts/build-css-vars.mjs" design/tokens src/styles/tokens.css ds`.

Generate a layered DTCG 2025.10 token system with primitive, semantic, component, and theme files.
