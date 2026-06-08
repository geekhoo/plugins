---
name: figma-inventory
description: This skill should be used when the user asks "what is in this Figma file", "audit the design file", "find duplicate components or tokens", or wants a pre-merge audit — read-only enumeration of pages, variables, and components, flagging duplicates, orphans, and non-brand collections.
user-invocable: true
argument-hint: "<Figma file key(s)>"
---

# Figma Inventory

A read-only primitive that maps what exists in Figma file(s) before any change is made. De-risks destructive merges by surfacing duplicates and a dedupe/exclude plan. `figma-consolidate` calls this as its first phase.

## 1. Clarify before reading
- Confirm the **file key(s)** and, if relevant, which are **sources vs the target**.
- Load the `figma-use` skill first if any step needs JavaScript execution in the file context (`figma-use` is provided by the `figma` plugin, declared as a `dev-workflows` dependency; it appears namespaced as `figma:figma-use`). All reads below use the Figma MCP tools (`get_metadata`, `get_variable_defs`, etc.).

## 2. Inventory (read-only — make no edits)
Enumerate, paging to avoid timeouts (don't pull everything in one call):
- **Pages** and their top-level frame structure (`get_metadata`).
- **Variable collections** and modes (`get_variable_defs`) — note tiers (primitive / semantic / component) and Light/Dark modes.
- **Components / component sets** and recurring patterns.
- Convert node IDs from URLs (`-` → `:`) when needed.

## 3. Classify and flag
- **Duplicates & near-duplicates** (variables, components, styles).
- **Orphans** (unused tokens/components).
- **Non-brand collections to exclude** (e.g. DevExtreme `.dx*`, 6000+ vars — not design tokens).
- Propose a **token-tier mapping** (which primitives → `global/standard/*` chromatic vs `global/grays/*` neutral; which become semantic vs component).

## 4. Verification gates / acceptance criteria
- Every page, collection, and component set is accounted for (no "etc." gaps).
- Each flagged duplicate/orphan cites where it lives.
- Output includes an actionable **dedupe + exclude + tier plan**, not just a raw list.
- **Nothing in Figma was modified** (confirm read-only).
Acceptance = complete inventory + a concrete plan a consolidation can execute against.

## 5. Expected outcome
An inventory report (pages/variables/components, duplicates, orphans, exclusions) plus a proposed dedupe/tier plan. Read-only — no Figma writes.
