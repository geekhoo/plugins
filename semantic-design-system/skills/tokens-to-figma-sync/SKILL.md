---
name: tokens-to-figma-sync
description: Use when pushing a DTCG design-token directory into Figma as variable collections — "sync tokens to Figma", "push design tokens to Figma variables", "mirror the token system in Figma". Code→Figma one-way; composes the figma plugin's figma-use (and figma-generate-library for component structure). Not for extracting tokens from Figma (use derive-design-system) or migrating code (use apply-design-system).
argument-hint: "[token dir, default design/tokens; optional Figma file/collection target]"
disable-model-invocation: true
model: inherit
effort: high
---

# Tokens → Figma Sync

Push a validated DTCG token directory into Figma variable collections so the Figma library mirrors the code-side token system. Direction is **code→Figma only** — code is the source of truth; never write Figma-side edits back into the token files during this flow.

User request:

```text
$ARGUMENTS
```

## Required process

1. Locate the token source directory (standardized `design/tokens/` relative to the project folder unless the user names another).
2. Validate before syncing — never push an invalid token set:

```sh
node "${CLAUDE_PLUGIN_ROOT}/scripts/validate-tokens.mjs" design/tokens
```

3. Parse the token files and plan the Figma structure before any write:
   - One Figma **variable collection per token tier** (primitive, semantic, component) or per top-level token file — state which and why.
   - Theme dimensions (e.g. light/dark) → collection **modes**, one mode per theme.
   - DTCG `$type` → Figma variable type: `color`→COLOR, `dimension`/`number`→FLOAT, `fontFamily`/`fontWeight`(named)/string values→STRING, `boolean`→BOOLEAN.
   - DTCG alias references (`{color.primary}`) → Figma **variable aliases** to the corresponding variable, never a flattened literal.
   - Token path segments → variable names with `/` separators (`color.bg.subtle` → `color/bg/subtle`) so Figma groups them.
   - Values with no Figma variable representation (shadows, typography composites, motion curves) → list as **not synced**; do not approximate them silently.
4. **Invoke the `figma:figma-use` skill before any Figma write** — it is the mandatory prerequisite for `use_figma` calls and carries the API gotchas (await everything, explicit scopes, no IIFE). Then create/update collections, modes, variables, and aliases per the plan. Update in place when a collection with the same name exists — match by variable name, change only what differs, and report additions/updates/orphans (Figma variables with no token counterpart — flag, don't delete).
5. If the user also wants component/library structure generated around the variables, compose `figma:figma-generate-library` after the variables land.
6. Verify: read the collections back (variable counts per collection/mode, spot-check one alias resolves) and compare against the token counts from step 3.

## Rules

- Code→Figma only. Figma-side drift is reported, never merged back here.
- Never delete Figma variables or collections; orphans are reported for the user to decide.
- Aliases must stay aliases — flattening a semantic→primitive reference destroys the token architecture in Figma.
- If validation (step 2) fails, stop and report; do not sync a broken set.

## Required output

1. Token dir and file count synced
2. Collections/modes created or updated, with variable counts per collection
3. Alias count preserved
4. Tokens not representable in Figma (skipped, with reason)
5. Orphaned Figma variables found
6. Verification result (read-back counts vs token counts)
