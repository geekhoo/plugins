---
name: derive-design-system
description: Analyze an existing web codebase and derive a semantic design-token system from observed CSS, theme files, component styles, Tailwind config, CSS-in-JS, and hardcoded styling values.
argument-hint: "[scope, token output dir, framework, migration goals]"
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash(node *) Bash(ds-style-inventory *) Bash(ds-token-validate *)
model: inherit
effort: high
---

# Derive Semantic Design System from Codebase

Analyze the existing repository and derive a migration-ready semantic design-token system.

User request:

```text
$ARGUMENTS
```

Use the shared taxonomy in `${CLAUDE_PLUGIN_ROOT}/references/semantic-token-taxonomy.md` and the output contract in `${CLAUDE_PLUGIN_ROOT}/references/output-contract.md`.

## Required process

1. Inventory styling sources:
   - global CSS, CSS modules, Sass/Less, Tailwind config, theme files, CSS variables, CSS-in-JS, inline style objects, Storybook, package themes.
2. Extract raw styling values:
   - colors, typography, spacing, sizing, radius, borders, shadows, opacity, blur, motion, z-index, breakpoints.
3. Cluster repeated and near-duplicate values.
4. Infer semantic roles from selectors, file paths, component names, prop names, state selectors, and variants.
5. Identify inconsistencies and accessibility risks.
6. Create normalized `primitive.*` tokens from observed values.
7. Create `semantic.*` tokens from inferred UI roles.
8. Create `component.*` tokens only for reusable components or meaningful variants/states.
9. Include confidence metadata in `$extensions`:
   - `source`, `observedValues`, `confidence`, `migrationNote`.
10. Provide a phased migration plan with before/after examples.

## Useful utility commands

Run this when you need a first-pass style inventory:

```sh
ds-style-inventory . .design-system/style-inventory.json
```

Run this to validate generated tokens:

```sh
ds-token-validate tokens
```

## Rules

- Do not flatten every raw value into a semantic token.
- Do not assume all inconsistencies are mistakes; flag them with confidence.
- Do not invent dark-mode values unless clearly marked as proposed.
- Preserve current visuals where possible during migration.
- Prefer aliases and stable paths over hardcoded replacements.

## Required output

Follow `${CLAUDE_PLUGIN_ROOT}/references/output-contract.md`, including the codebase-derived sections.
