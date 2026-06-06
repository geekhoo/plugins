---
name: audit-design-system
description: Use when auditing design tokens for naming quality, unresolved references, primitive leakage, accessibility risks, and migration readiness.
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash(node *) Bash(ds-token-validate *) Bash(ds-token-build *)
---

# Audit Semantic Design System

Use the canonical workflow in `skills/audit-design-system/SKILL.md`.

Codex compatibility notes:

- Use `PLUGIN_ROOT` for plugin files when available.
- The default token source is `design/tokens/` relative to the workspace.
- Validate with `node "$PLUGIN_ROOT/scripts/validate-tokens.mjs" design/tokens`.
- Check naming against `references/semantic-token-taxonomy.md` and accessibility risks against `references/accessibility-checklist.md`.

Return prioritized findings with concrete token paths, severity, and remediation.
