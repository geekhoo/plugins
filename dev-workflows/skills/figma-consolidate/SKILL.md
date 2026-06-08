---
name: figma-consolidate
description: This skill should be used when the user asks to "consolidate these Figma files", "clean up or dedupe the design system", or "merge into one Figma file" — perform a reductive merge into one tiered, deduped design system, composing figma-inventory and figma-generate-library.
user-invocable: true
argument-hint: "<source file key(s)> -> <target file>, or describe the consolidation"
---

# Figma Consolidate

Orchestrates a reductive design-system merge. It **delegates** the read and build phases to existing skills rather than re-implementing the Plugin API:
- audit the sources → `figma-inventory`
- build token tiers / components → `figma-generate-library` (+ `figma-use` for raw Plugin API calls)

**Prerequisite:** load the `figma-use` skill before any `use_figma` call. Honor the use_figma gotchas: no `closePlugin`/IIFE; `figma.notify()` throws; set `layoutSizing FILL` after `appendChild`; set `scopes` explicitly (never `ALL_SCOPES`, `[]` for primitives); await every promise; `use_figma` is atomic (a failed script leaves no partial state).

**Dependencies:** `figma-inventory` (this plugin), plus `figma-generate-library` and `figma-use` — provided by the `figma` plugin, which `dev-workflows` declares as a dependency (so the plugin and its Figma MCP server auto-install). They appear namespaced as `figma:figma-generate-library` / `figma:figma-use`.

## 1. Clarify before starting
- Which files are **sources** vs the **target**?
- **Recreate** components in the target (default) or keep them live-linked?
- Is **Light/Dark** theming required?

## 2. Inventory — invoke `figma-inventory`
Get the read-only map of pages/variables/components, the duplicate/orphan list, the non-brand exclusions (e.g. DevExtreme `.dx*`), and a proposed token-tier plan. **Get the user's OK on the dedupe/exclude/tier plan before writing anything.**

## 3. Build the tiers — invoke `figma-generate-library`
Build in order: **primitives** (`global/standard/*` chromatic, `global/grays/*` neutral; scope `[]`) → **semantic** (explicit scopes; theme by mode on the semantic collection) → **component** tokens → text styles → component sets with state variants → screens (reference-only). Component tokens for component internals, semantic tokens for layout/surfaces.

## 4. Staged, chunked writes
- ~60 variables per `use_figma` call; icons ~40 per batch (≈50KB) to avoid timeouts.
- Convert node IDs from URLs (`-` → `:`). Recreate text if a font (e.g. Segoe UI) won't load; PNG-export fallback for problematic vectors.
- Work in passes; report what was deduped/excluded each pass. Prefer slow, verifiable progress over bulk import.

## Verification gates / acceptance criteria
- Inventory + dedupe/tier plan approved before any write.
- No `ALL_SCOPES` anywhere; primitives have `[]`.
- Light↔Dark mode swap yields correct semantic values (spot-check e.g. `--*-fg-default`).
- No orphaned nodes; consistent naming; duplicates removed.
- Screenshot key pages.

## Expected outcome
One consolidated, tiered, deduped Figma file matching the approved plan, plus a per-pass report of what was merged/excluded.
