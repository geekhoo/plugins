---
name: apply-desing-system
description: Apply an existing semantic design-token system to a web codebase by replacing hardcoded styling values with CSS variables, token imports, or framework-specific theme references.
argument-hint: "[component or path scope, token dir, migration target]"
disable-model-invocation: true
allowed-tools: Read Grep Glob Edit Write Bash(node *) Bash(ds-token-build *) Bash(ds-token-validate *)
model: inherit
effort: high
---

# Apply Semantic Design System

Migrate code to consume semantic or component tokens.

User request:

```text
$ARGUMENTS
```

Use the taxonomy in `${CLAUDE_PLUGIN_ROOT}/references/semantic-token-taxonomy.md`.

## Required process

1. Locate the token source directory, defaulting to `tokens/` or the configured `token_dir`.
2. Validate tokens before migration:

```sh
ds-token-validate tokens
```

3. Build or refresh CSS variables when appropriate:

```sh
ds-token-build tokens src/styles/tokens.css ds
```

4. Inventory the requested component or path scope.
5. Replace hardcoded values with semantic or component tokens:
   - Colors → `var(--ds-color-*)` or token imports.
   - Spacing → `var(--ds-space-*)`.
   - Radius → `var(--ds-radius-*)`.
   - Typography → typography utility, CSS variables, or theme object.
   - Motion → `var(--ds-motion-*)`.
6. Prefer component tokens for reusable component internals.
7. Prefer semantic tokens for layout and app-level surfaces.
8. Preserve visual behavior, variants, states, responsive behavior, and accessibility behavior.
9. Run available type checks, build, lint, or visual checks if the project provides them.
10. Summarize changed files, replacements, risks, and follow-up migrations.

## Replacement rules

- Do not replace a value with a primitive token in product code unless no semantic/component token exists and you explicitly explain why.
- Do not change component behavior or variant logic unless the user requested it.
- Do not introduce a token for a one-off value unless it is repeated or semantically important.
- Do not remove focus-visible, disabled, invalid, or reduced-motion behavior.
- For themeable code, prefer CSS custom properties over static literal values.

## Required output

Return:

1. Scope migrated
2. Token files used
3. CSS output generated, if any
4. Files changed
5. Before/after examples
6. Validation results
7. Remaining hardcoded values
8. Risks and recommendations
