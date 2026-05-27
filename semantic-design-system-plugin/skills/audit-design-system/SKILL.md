---
name: Audit Design System
description: Audit semantic design tokens for naming quality, unresolved references, primitive leakage, accessibility risks, component-token overreach, and migration readiness.
argument-hint: "[token dir or scope]"
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash(node *) Bash(ds-token-validate *) Bash(ds-token-build *)
model: inherit
effort: high
---

# Audit Semantic Design System

Audit tokens and their usage.

User request:

```text
$ARGUMENTS
```

Use `${CLAUDE_PLUGIN_ROOT}/references/accessibility-checklist.md` and `${CLAUDE_PLUGIN_ROOT}/references/semantic-token-taxonomy.md`.

## Required checks

1. Token structure:
   - primitive, semantic, component, and theme layers exist where appropriate.
   - `$value` and `$type` are present directly or inherited.
   - aliases resolve.
   - no circular references.
2. Naming:
   - semantic paths describe roles, not literal values.
   - logical layout names are used.
   - state names are consistent.
3. Layering:
   - product-facing code uses semantic/component tokens.
   - component tokens do not unnecessarily reference primitives.
   - theme overrides preserve semantic paths.
4. Accessibility:
   - contrast metadata or tests exist for critical foreground/background pairs.
   - focus-visible tokens exist.
   - disabled, invalid, selected, hover, active states are intentionally handled.
   - touch-target and reduced-motion tokens exist.
5. Implementation:
   - CSS variable output exists or can be generated.
   - build/migration scripts are documented.
   - validation can run in CI.

## Useful commands

```sh
ds-token-validate tokens
```

```sh
ds-token-build tokens src/styles/tokens.css ds
```

## Required output

Return:

1. Overall score: Ready / Needs minor work / Needs major work
2. Critical issues
3. Naming issues
4. Reference and type issues
5. Accessibility risks
6. Layering and governance risks
7. Migration risks
8. Recommended fixes
9. Suggested CI checks
