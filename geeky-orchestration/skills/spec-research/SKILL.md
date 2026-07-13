---
name: spec-research
description: Use when asked to research and write a new feature specification in `docs/<feature-folder>/`. This skill runs parallel research, synthesizes findings, and drafts `feature-specification.md` plus README scaffold before planning.
---

# Spec Research & Authoring

Deploy a parallel research team to investigate requirements for a new spec, then synthesize findings into a complete feature specification document. The research phase uses 3 subagents with distinct investigation angles to ensure comprehensive coverage before writing begins.

## Arguments

Accept a spec topic or folder path (e.g., `notifications`, `feature-007`, `docs/notifications/`, or a plain description like "real-time notifications system").  
If a stub README already exists in the feature folder (for example `docs/feature-name/README.md`), read it for initial scope constraints.

## Workflow

### Phase 1: Scope Discovery

Before dispatching researchers:

1. Determine the feature folder name. If the argument is already a folder path, use it. Otherwise derive `docs/spec-NNN-<kebab-slug>/`: read `CLAUDE.md` `## Current State` for the current sequence if present. If `CLAUDE.md` is missing, malformed, or the `## Current State` section is absent, continue with fallback naming logic: list existing `docs/spec-*` folders and use the highest number + 1. If no numbered folders exist, follow whatever folder convention prior specs in `docs/` use; if `docs/` is empty, ask the user to confirm the folder name before proceeding.
2. Read any existing stub (`docs/<folder>/README.md`) for scope constraints.
3. Scan the codebase for existing patterns and integration points.
4. Identify 3 distinct research angles based on what the feature needs to cover.

### Phase 2: Define 3 Research Angles

Select 3 non-overlapping research angles based on the feature domain. Each agent investigates a different facet.

Typical per-domain configurations (infrastructure / domain-feature / security-compliance, always anchored by a Codebase Analyst) are in `references/research-angle-menus.md` — load it when picking the angles.

### Phase 3: Dispatch Research Team in Parallel

Deploy all 3 researchers simultaneously.

- **Codebase Analyst**: use `geeky-orchestration:code-explorer` agent type.
- **Web Researchers (2)**: use `general-purpose` agent type with instructions to use `WebSearch` and `WebFetch`.

Each research brief ends with:

```
Produce a structured report with:
- Key findings (numbered, specific)
- Constraints discovered (what the spec MUST respect)
- Recommendations (what the spec SHOULD include)
- Sources (URLs for web research, file paths for codebase)

DO NOT create or modify any files.
```

### Phase 4: Synthesize into Spec Document

After all 3 researchers report back:

1. Consolidate findings: merge overlap, resolve contradictions, and note confidence gaps.
2. Define scope: goals, non-goals, delegation items.
3. Write the requirements document using the project’s established conventions in:
   - `docs/<feature-folder>/feature-specification.md`
   - `docs/<feature-folder>/README.md`

   Do not create `SPEC-NNNN-*.md` files — that naming is legacy; `feature-specification.md` is the canonical filename consumed by /geeky-plan and the freeze hooks.

   If a stub README already exists, preserve its stated scope and only update the Status line and missing sections; otherwise create the README stub:

   ```markdown
   # [Feature Name]

   [One-paragraph scope summary.]

   **Status:** Spec written — not yet planned
   **Spec:** `feature-specification.md`
   **Next:** /geeky-plan docs/<feature-folder>/
   ```

Use the 11-section recommended spec structure in `references/spec-structure-template.md` (adapt sections to the feature domain; include citations and explicit assumptions at the end of major findings).

### Phase 5: Commit and Suggest Next Steps

Commit the spec (same command on all platforms). The spec is not yet frozen — it only becomes part of the frozen planning contract after /geeky-plan runs:

```
git add docs/<feature-folder>/
git commit -m "docs: author feature specification in <feature-folder>" -m "[1-line summary of the spec focus]" -m "Research conducted by: codebase analyst, researcher 2 domain, researcher 3 domain" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

Then suggest next steps:
```
Spec written. Next steps:
- /geeky-plan docs/<feature-folder>/   (to create implementation plan, tasks, kanban)
- /plan-review docs/<feature-folder>/  (to validate the planning package)
- /geeky-implement docs/<feature-folder>/ (to execute)
```

## Research Quality Standards

- **Recency**: Target sources from roughly the past 18 months; avoid older sources unless they cover stable fundamentals.
- **Authority**: Prefer official documentation (Microsoft Learn, AWS docs, RFC specs) over blogs or forums.
- **Specificity**: Include concrete findings (resource types, API versions, package versions, pricing tiers).
- **Adversarial verification**: If researchers disagree on a fact, preserve both positions and flag for user decision.

## Rules

- **Always 3 researchers** — one codebase analyst + two web/domain researchers.
- **Parallel dispatch** — all 3 in a single turn for maximum speed.
- **Research before writing** — do not start the spec document until all researchers report back.
- **Cite sources** — every major claim in the spec should trace to research.
- **Respect existing stubs** — if a README stub exists, treat its stated scope as authoritative unless research justifies adjustments.
- **Follow project conventions** — spec format, naming, and folder structure should match prior specs in `docs/`.
