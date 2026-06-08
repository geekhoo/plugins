# dev-workflows — packaging & external dependencies

This plugin's skills are self-contained **except** for a few that delegate to skills shipped by
other plugins. The Figma dependency is now declared via the plugin standard (see below), so it
auto-installs on a clean machine. The remaining cross-references are documented for context.

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

**How it's declared** (cross-marketplace, because `dev-workflows` lives in `geekhoo-plugins`):
- `dev-workflows/.claude-plugin/plugin.json` →
  `"dependencies": [ { "name": "figma", "marketplace": "claude-plugins-official" } ]`
  (unversioned, so it tracks the marketplace's latest and always installs; pin with a `version`
  semver range later if `figma` ever ships a breaking change — note that requires upstream
  `figma--v*` git tags, or you get a `no-matching-tag` error).
- Root `geekhoo-plugins/.claude-plugin/marketplace.json` →
  `"allowCrossMarketplaceDependenciesOn": ["claude-plugins-official"]`
  — required, or the cross-marketplace dependency is blocked at install with a `cross-marketplace`
  error. Only the root (installing) marketplace's allowlist is consulted.

On install, Claude Code resolves and installs the `figma` plugin automatically and enables it
alongside `dev-workflows`. The dependent skills reference the Figma skills by their namespaced
names (`figma:figma-use`, `figma:figma-generate-library`).

`figma-inventory` is in-plugin and ships with the plugin; it composes the `figma` plugin's skills/MCP.

## Other external references (no action required for local use)
- `/geeky-plan`, `/geeky-status` — real commands in the **geeky-orchestration** plugin (install that plugin for `align-docs` and `backend-api-spec` to use them).
- `code-review`, `implement`, `verify`, `browser-verify` — built-in / other-plugin skills referenced by name; `parallel-audit` and others degrade gracefully (they name the skill, not a hard import).
- `browser-qa`, `browser-probe` — **bundled** in this plugin (used by `test-and-seed`). OK.
- All other cross-skill references (`env-check`, `db-seed`, `parallel-audit`, `figma-inventory`, etc.) are **in-plugin**. OK.

## Quick check before publishing
- `grep -r "figma-use\|figma-generate-library" dev-workflows/skills` → confirm each occurrence is either vendored or documented as a prerequisite.
- Verify no SKILL.md references a skill that is neither in `dev-workflows/skills/` nor a declared dependency.
