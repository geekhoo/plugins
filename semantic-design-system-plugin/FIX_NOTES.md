# Fix notes

## Version 0.2.0

Standards alignment (DTCG Format Module 2025.10, first stable release) and bug fixes:

- **Theme corruption fixed (critical):** `ds-token-build` previously deep-merged every
  `.tokens.json` file — including `themes/*` — into a single `:root`, so theme files
  silently overwrote base values (the bundled dark theme corrupted the light base) and no
  themed selectors were ever produced. The builder is now theme-aware: base → `:root`,
  `themes/<name>.tokens.json` → `[data-theme="<name>"]`, and `light`/`dark` themes also
  emit a `@media (prefers-color-scheme: <name>)` block scoped to `:root:not([data-theme])`.
  A theme re-emits every exposed token whose *resolved* value differs from base, so an
  override of a primitive or semantic propagates to every component/semantic that aliases
  it (inlined values can't cascade on their own); a primitive-only theme override now
  produces a correct, non-empty themed block instead of being silently dropped.
- **Token location standardized to `design/tokens`:** the source directory is now a single
  hard default resolved relative to the project/working folder, replacing the `tokens`
  default. The `token_dir` user-config option and all of its environment plumbing were
  removed (including a never-populated `CLAUDE_PLUGIN_OPTION_TOKEN_DIR` lookup in the hook
  and the `DEFAULT_TOKEN_DIR` injection in `.mcp.json`), so scripts, the MCP server, and the
  post-edit hook all agree without any configuration. An explicit first CLI/MCP argument is
  the only override. Generated CSS output stays configurable via `css_output_file`.
- **Skill name typo fixed:** `apply-design-system` skill declared `name: apply-desing-system`,
  which broke the documented `/semantic-design-system:apply-design-system` invocation.
- **`$type` validation added:** `ds-token-validate` now warns (non-fatal) on any `$type`
  outside the 13 standard DTCG 2025.10 types.
- **Token-file matching tightened:** only `.tokens`, `.tokens.json`, and `.tokens.jsonc`
  files are read. Stray `package.json`/`tsconfig.json` under the token directory are no
  longer parsed as tokens.
- **Model-agnostic:** the three agents now use `model: inherit` instead of `model: sonnet`.
- **Strict-JSON guidance:** docs/skills clarify that authored token files are strict JSON
  (JSONC only for illustrative inline snippets), matching the stable spec and tool interop.

### Cross-file alignment pass

- **Skill tool permissions matched to instructions:** `generate-design-system` now allows
  `Write` plus `ds-token-validate`/`ds-token-build` (it previously instructed writing files
  and building CSS without the tools to do so); `derive-design-system` now allows `Write`
  so the tokens it creates can actually be written and validated.
- **MCP tool descriptions refreshed:** `validate_tokens` notes the `$type` check,
  `build_css_variables` documents theme-aware emission, and all token-dir arguments document
  the `design/tokens` default.
- **Agents brought in line:** the auditor and migrator agents now reference the shared
  taxonomy/accessibility references and the standardized `design/tokens` location, matching
  the architect agent and the skills; "DTCG-style" wording updated to "DTCG 2025.10".
- **Example demonstrates theming:** `examples/minimal-tokens/themes/dark.tokens.json` added
  so the bundled example exercises the theme-aware build (`:root` + `[data-theme="dark"]` +
  `prefers-color-scheme`).

## Version 0.1.1

Version 0.1.1 fixes the Claude Code plugin manifest validation error:

- Removed the redundant `skills` manifest field because the default `skills/` directory is auto-discovered.
- Changed `agents` from the invalid directory value `"./agents/"` to explicit agent Markdown files:
  - `./agents/design-token-architect.md`
  - `./agents/codebase-token-auditor.md`
  - `./agents/design-system-migrator.md`

The current Claude Code plugin schema expects the `agents` manifest field to reference custom agent files, not a directory.
