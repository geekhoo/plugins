# dev-workflows — packaging & external dependencies

This plugin's skills are self-contained **except** for a few that delegate to skills shipped by
other plugins. The Figma dependency is declared in the Codex manifest (see below). Claude Code users must install the Figma plugin separately. The remaining cross-references are documented for context.

## Figma dependency (resolved — declared as a plugin dependency)
Three skills delegate to the Figma skills `figma-use` and `figma-generate-library`. Those skills —
and, crucially, the **Figma MCP server** they call (`use_figma`, `get_metadata`,
`get_variable_defs`, …) — are shipped by the official **`figma`** plugin in the
`claude-plugins-official` marketplace. Vendoring the skill folders alone would ship broken skills
(no MCP server), so `dev-workflows` depends on the whole `figma` plugin instead.

| Referenced skill | Provided by | Used by |
|---|---|---|
| `figma-use` | `figma` plugin (`claude-plugins-official`) | `figma-inventory`, `figma-consolidate`, `figma-design-loop` |
| `figma-generate-library` | `figma` plugin (`claude-plugins-official`) | `figma-consolidate` |

**Manifest declarations:**

- `dev-workflows/.codex-plugin/plugin.json` lists `figma` from `claude-plugins-official` and `geeky-orchestration` as dependencies.
- Root `.claude-plugin/marketplace.json` lists `claude-plugins-official` in `allowCrossMarketplaceDependenciesOn`.
- `dev-workflows/.claude-plugin/plugin.json` does not declare dependencies.

For Claude Code, install the `figma` plugin separately when those skills are needed. The dependent skills reference the Figma skills by their namespaced names (`figma:figma-use`, `figma:figma-generate-library`).

`figma-inventory` is in-plugin and ships with the plugin; it composes the `figma` plugin's skills/MCP.

## Other external references (no action required for local use)
- `geeky-plan`, `geeky-status` — skills in the **geeky-orchestration** plugin (install that plugin for `align-docs` and `backend-api-spec` to use them).
- `code-review`, `implement`, `verify`, `browser-verify` — built-in / other-plugin skills referenced by name; `parallel-audit` and others degrade gracefully (they name the skill, not a hard import).
- `browser-qa`, `browser-probe` — **bundled** in this plugin (used by `test-and-seed`). OK.
- All other cross-skill references (`env-check`, `db-seed`, `parallel-audit`, `figma-inventory`, etc.) are **in-plugin**. OK.

## Quick check before publishing
- `grep -r "figma-use\|figma-generate-library" dev-workflows/skills` → confirm each occurrence is either vendored or documented as a prerequisite.
- Verify no SKILL.md references a skill that is neither in `dev-workflows/skills/` nor a declared dependency.
