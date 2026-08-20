---
name: tokens-to-figma-sync
description: Use when pushing a DTCG design-token directory into Figma as variable collections — "sync tokens to Figma", "push design tokens to Figma variables", "mirror the token system in Figma". Code→Figma one-way. Not for extracting tokens from Figma (use derive-design-system) or migrating code (use apply-design-system).
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash(node *) Bash(ds-token-validate *)
---

# Tokens → Figma Sync

Use the canonical workflow in `skills/tokens-to-figma-sync/SKILL.md`.

Codex compatibility notes:

- Use `PLUGIN_ROOT` for plugin files when available.
- The default token source is `design/tokens/` relative to the workspace.
- Validate before syncing — never push an invalid set: `node "$PLUGIN_ROOT/scripts/validate-tokens.mjs" design/tokens`.
- Figma writes require a connected Figma MCP server. Load that server's own
  usage guidance before the first write call; if no Figma server is configured,
  stop after producing the mapping plan and report what would be written.
- The canonical skill's `figma:figma-use` / `figma:figma-generate-library`
  composition steps are Claude Code skill references — on Codex, treat them as
  "follow the Figma MCP server's documented write procedure" instead.

Direction is code→Figma only. Keep DTCG aliases as Figma variable aliases rather
than flattened literals, never delete Figma variables (report orphans), and
verify by reading the collections back before reporting done.
