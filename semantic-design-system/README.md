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
- `tokens-to-figma-sync`: push a validated DTCG token directory into Figma variable collections (code→Figma one-way). Claude Code only — it composes the figma plugin's `figma-use` / `figma-generate-library` skills, so it has no Codex mirror.

Utilities:

```sh
ds-token-validate [token-dir]
ds-token-build [token-dir] [output-css-file] [prefix] [--allow-partial]
ds-style-inventory [project-root] [output-json-file]
```

MCP tools:

- `validate_tokens` — read-only (`readOnlyHint: true`)
- `build_css_variables` — writes and overwrites the CSS output (`destructiveHint: true`)
- `extract_style_inventory` — scans read-only but overwrites the inventory JSON it writes (`destructiveHint: true`)
- `generate_token_skeleton` — writes token files; refuses to overwrite without `force` (`destructiveHint: true`)

### MCP workspace boundary

Every caller-supplied path is validated against a workspace root before use. The server follows the MCP `roots` mechanism: if the client advertises the `roots` capability, the server issues `roots/list` and uses the declared roots; otherwise it falls back to the configured project directory. `notifications/roots/list_changed` re-queries.

Read and write surfaces are separate, and the write surface is the narrower one:

- Read roots: every declared `file://` root, or the project directory when none are declared.
- Write root: a single directory — the project directory when it sits inside a declared root, otherwise the first declared root.

`validate_tokens` and the `rootDir` of `extract_style_inventory` are checked against the read roots. Every output path — `build_css_variables` `outputFile`, `extract_style_inventory` `outputFile`, `generate_token_skeleton` `outputDir` — is checked against the write root.

Containment resolves the target rather than comparing prefixes: relative paths are resolved against the project directory, symlinks and junctions are followed through the deepest existing ancestor, and the result must be inside a root by `path.relative`. A prefix test would wrongly accept a sibling such as `/app/data-evil` for a root of `/app/data`. Paths outside a root are refused with the resolved target in the message; they are never silently rewritten to fit.

`generate_token_skeleton` will not clobber existing token files. If any target file exists the call is refused whole and nothing is written; `force: true` is required to overwrite. The result reports `written`, `skipped`, and `overwritten` by relative path. All skeleton writes go through a temp file that is JSON-parsed before the rename.

Subprocess calls made by the server are bounded by a timeout (`DS_SUBPROCESS_TIMEOUT_MS`, default 60000) and an output cap (`DS_SUBPROCESS_MAX_BUFFER`, default 4 MiB).

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

### Build failure behavior

The build resolves and validates every layer before it generates a single line of CSS, and it fails closed. If an exposed `semantic.*` or `component.*` token cannot be resolved, the build exits non-zero, writes nothing, and names the token:

```json
{
  "ok": false,
  "error": "1 exposed token(s) failed to resolve; no CSS was written. ...",
  "failures": [
    {
      "layer": "base",
      "tokenPath": "semantic.color.broken",
      "kind": "missing-reference",
      "error": "Unresolved alias: primitive.color.DOES_NOT_EXIST"
    }
  ]
}
```

Failure classes reported in `kind`:

- `missing-reference` — the alias points at a token that does not exist.
- `circular-alias` — the alias chain returns to a token already on the path.
- `unsupported-value-shape` — the value resolved, but not to a CSS scalar (typically a composite `typography`/`gradient` shape the builder cannot flatten).
- `resolution-error` — any other resolver failure.

Each theme is validated independently against the base tree, so `layer` distinguishes `base` from `theme:<name>`. A theme that breaks a token is attributed to that theme rather than merged away. Failures already present in the base are not repeated per theme.

`--allow-partial` restores the older lenient behavior: unresolvable tokens are dropped and the resolvable subset is emitted, with `partial: true` in the result. It is opt-in; the default is to fail.

Counts in the JSON result:

| Key | Meaning |
| --- | --- |
| `variables` | Declarations written (unchanged; kept for compatibility) |
| `emitted` | Same count, named for the emitted/skipped/failed triple |
| `skipped` | Base-layer tokens deliberately not exposed as CSS variables (primitives) |
| `failed` | Exposed tokens that could not be resolved |

The output file is written through a temp file and renamed into place only after the generated CSS validates, so a failed build never truncates or replaces a previously good stylesheet.

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

## Post-Edit Hook

`scripts/post-edit-design-token-check.mjs` runs on `PostToolUse` after a `.tokens` file is written. PostToolUse cannot block an edit that already happened, so the hook always exits 0. It reports through `hookSpecificOutput.additionalContext` rather than plain stdout, which is what actually reaches the model. It stays silent when there is nothing to check (the edited file is not a token file, or the project has no `design/tokens/`) and speaks up in two distinct cases: validation failed, or the check itself could not run (validator missing, spawn error, timeout, output overflow). The second case never reads as a pass.

## Privacy

This local plugin does not include network services, analytics, telemetry, or credential collection. Token files, generated CSS, style inventories, and validation results stay in local workspace paths selected by the user or script command.

## Terms of Use

This plugin is provided as a local design-system helper. Review generated tokens and CSS before shipping, and confirm that consuming projects follow the licensing and accessibility requirements that apply to their product.
