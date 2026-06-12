---
name: spec-research
description: This skill should be used when the user asks to "research and write a spec", "investigate what we need for spec-NNN", "write spec-NNN", "create the next spec", "what should spec-NNN cover", "research spec requirements", or invokes /spec-research. Deploys a parallel research team (3 subagents) to investigate requirements from different angles — codebase analysis, web research on best practices, and architecture patterns — then synthesizes findings into a complete SPEC-NNNN.md document and README stub in docs/. This skill writes the spec requirements document itself — not the implementation plan. For creating the implementation plan from an existing spec, use /geeky-plan. Use whenever a new spec needs to be written from scratch with proper research backing, before /geeky-plan is run.
---

# Spec Research & Authoring

Deploy a parallel research team to investigate requirements for a new spec, then synthesize findings into a complete SPEC-NNNN document. The research phase uses 3 subagents with distinct investigation angles to ensure comprehensive coverage before writing begins.

## Arguments

Accept a spec topic or number (e.g., `spec-007 infrastructure`, `spec-009 notifications`, or a plain description like "real-time notifications system"). If a stub README already exists in `docs/spec-NNN-*/`, read it for initial scope constraints.

## Workflow

### Phase 1: Scope Discovery

Before dispatching researchers, establish the investigation scope:

1. Check CLAUDE.md `## Current State` for the current spec number and what preceded it
2. Read any existing stub (`docs/spec-NNN-*/README.md`) for pre-defined scope hints
3. Scan the codebase for relevant patterns — what infrastructure/code already exists that the spec will build upon
4. Identify 3 distinct research angles based on what the spec needs to cover

### Phase 2: Define 3 Research Agents

Select 3 non-overlapping research angles based on the spec's domain. Each agent investigates a different facet:

**Typical configurations:**

For an infrastructure spec:
1. **Codebase Analyst** — audit existing code for all dependencies, configuration points, connection strings, and integration surfaces the new infrastructure must satisfy
2. **Technology Researcher** — web search for current best practices, latest API versions, pricing models, and recommended patterns for the target technology (2025-2026)
3. **Architecture Patterns** — web search for deployment patterns, security models, cost optimization, and disaster recovery strategies used by similar B2B SaaS platforms

For a domain/feature spec:
1. **Codebase Analyst** — trace existing domain boundaries, shared kernel interfaces, event contracts, and patterns established by prior specs
2. **Domain Expert** — web search for industry best practices, data models, and workflows for the feature domain (e.g., campaign management, billing, notifications)
3. **Integration Researcher** — identify third-party services, APIs, SDKs, and their latest documentation relevant to the feature

For a security/compliance spec:
1. **Codebase Analyst** — audit current security posture, auth patterns, secret management, and vulnerability surface
2. **Standards Researcher** — web search for relevant compliance frameworks (SOC2, GDPR, OWASP), certification requirements, and audit checklists
3. **Tooling Researcher** — web search for security tooling, scanning services, policy-as-code frameworks, and their integration patterns

### Phase 3: Dispatch Research Team in Parallel

Deploy all 3 researchers simultaneously. Each receives a structured brief:

- **Codebase Analyst**: Use `feature-dev:code-explorer` agent type. Brief it to audit specific directories, trace execution paths, and produce a structured inventory of what exists and what the new spec must interface with.

- **Web Researchers** (2): Use `general-purpose` agent type with explicit instruction to use `WebSearch` and `WebFetch` tools. Brief each with specific questions to answer, sources to prioritize (official docs over blogs), and output format (structured sections with source URLs).

Each agent brief ends with:
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

1. **Consolidate findings** — merge overlapping discoveries, resolve contradictions, note where researchers agree (high confidence) vs disagree (flag for user decision)
2. **Identify the spec's scope** — based on combined findings, define goals, non-goals, and delegation items
3. **Write the SPEC document** following the project's established format:

```markdown
# SPEC-NNNN: [Title]

**Status:** Not Started
**Dependencies:** [prior spec]
**Layer:** [Infrastructure / Domain / Security]
**Priority:** [Critical Path / Important / Nice-to-have]
**Estimated Complexity:** [N tasks across M waves]

---

## 1. Executive Summary
## 2. Problem Statement
### Current State
### Impact of Inaction
## 3. Goals & Non-Goals
## 4. Architecture
## 5. Detailed Design
## 6. Cost Estimates (if applicable)
## 7. Task Outline (Preliminary)
## 8. Risks & Mitigations
## 9. Acceptance Criteria
## 10. Dependencies on Prior Specs
## 11. Delegation to Future Specs
```

4. **Create the folder structure:**
   - `docs/spec-NNN-name/SPEC-NNNN-name.md` — the full spec
   - `docs/spec-NNN-name/README.md` — summary stub

### Phase 5: Commit and Suggest Next Steps

Commit the spec document:
```bash
git add docs/spec-NNN-name/
git commit -m "docs(spec-NNN): Research and author SPEC-NNNN-name

- [1-line summary of what the spec covers]
- Research conducted by: codebase analyst, [researcher 2 domain], [researcher 3 domain]

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Then suggest next steps:
```
Spec written. Next steps:
- /geeky-plan docs/spec-NNN-name/   (to create implementation plan, tasks, kanban)
- /plan-review docs/spec-NNN-name/  (to validate the planning package)
- /geeky-implement docs/spec-NNN-name/  (to execute)
```

## Research Quality Standards

- **Recency**: Web research must target 2025-2026 patterns. Reject pre-2024 articles unless they cover stable fundamentals.
- **Authority**: Prefer official documentation (Microsoft Learn, AWS docs, RFC specs) over blog posts or Stack Overflow.
- **Specificity**: Researchers must produce concrete findings (resource type names, API versions, package versions, pricing tiers) — not vague "consider using X" recommendations.
- **Adversarial verification**: If two researchers disagree on a fact, note both positions and flag for user decision rather than silently picking one.

## Rules

- **Always 3 researchers** — one codebase analyst + two web/domain researchers
- **Parallel dispatch** — all 3 in a single turn for maximum speed
- **Research before writing** — never start the spec document until all researchers report back
- **Cite sources** — every major claim in the spec should trace back to a researcher's finding
- **Respect existing stubs** — if a README stub exists, treat its scope as authoritative constraints (goals and non-goals) unless the research reveals it should change
- **Follow project conventions** — the spec format, naming, and folder structure must match prior specs in `docs/`
