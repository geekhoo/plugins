---
name: derive-design-system
description: Use when deriving a semantic design-token system from an existing web codebase, CSS/theme files, component styles, or hardcoded values.
disable-model-invocation: true
allowed-tools: Read Grep Glob Write Bash(node *) Bash(ds-style-inventory *) Bash(ds-token-validate *)
---

# Derive Semantic Design System

Use the canonical workflow in `skills/derive-design-system/SKILL.md`.

Codex compatibility notes:

- Use `PLUGIN_ROOT` for plugin files when available.
- Write generated tokens under `design/tokens/` unless the user gives another path.
- Inventory styles with `node "$PLUGIN_ROOT/scripts/extract-style-inventory.mjs" . .design-system/style-inventory.json`.
- Validate generated tokens with `node "$PLUGIN_ROOT/scripts/validate-tokens.mjs" design/tokens`.

Derive primitive, semantic, and component layers from observed code, then explain confidence and migration gaps.
