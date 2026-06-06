---
name: generate-design-system
description: Use when creating a new semantic design-token, theme, or web styling foundation from product, brand, UX, accessibility, and stack requirements.
argument-hint: "[product, brand, stack, themes, accessibility, components]"
disable-model-invocation: true
allowed-tools: Read Grep Glob WebFetch Write Bash(node *) Bash(ds-token-validate *) Bash(ds-token-build *)
model: inherit
effort: high
---

# Generate Semantic Design System

Create a new semantic design-token system from the user request:

```text
$ARGUMENTS
```

Use the shared taxonomy in `${CLAUDE_PLUGIN_ROOT}/references/semantic-token-taxonomy.md` and the output structure in `${CLAUDE_PLUGIN_ROOT}/references/output-contract.md`.

## Required process

1. Interpret the user's product, brand, UX, accessibility, component, theme, and implementation requirements.
2. State assumptions only when required information is missing.
3. Define a layered architecture:
   - `primitive`: raw palettes and scales.
   - `semantic`: UI roles consumed by product code.
   - `component`: component aliases for variants and states.
   - `theme`: mode, brand, density, and breakpoint overrides.
4. Generate DTCG (2025.10 stable) tokens using `$value`, `$type`, `$description`, `$deprecated`, and `$extensions` where useful. Files written to disk MUST be strict JSON (`.tokens.json`); reserve JSONC for illustrative inline snippets only.
5. Cover the fundamental styling surface:
   - color, typography, spacing, sizing, layout, radius, border, elevation, shadow, opacity, blur, motion, z-index, interaction states, breakpoints, density, component tokens.
6. Include at least light and dark mode strategy.
7. Include CSS variable examples using the configured prefix, defaulting to `--ds-*`.
8. Include usage examples in the user's target stack if known.
9. Include governance and CI validation rules.
10. Offer to write files only after presenting the proposed structure, unless the user explicitly asks you to create files immediately. Write token files under `design/tokens/` (the standardized location). After writing, validate and build:

```sh
ds-token-validate design/tokens
ds-token-build design/tokens src/styles/tokens.css ds
```

## Token philosophy

- Product code should use `semantic.*` and `component.*` tokens.
- `primitive.*` tokens are implementation details.
- Semantic tokens should usually reference primitives.
- Component tokens should usually reference semantics.
- Theme overrides should preserve the same semantic paths.
- Do not name semantic tokens after raw colors such as `white`, `gray900`, or `blue500`.

## Required output

Follow `${CLAUDE_PLUGIN_ROOT}/references/output-contract.md`.

When writing files, prefer this structure:

```text
design/tokens/
  primitive/
  semantic/
  component/
  themes/
  density/
src/styles/tokens.css
```
