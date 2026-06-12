---
name: impl-review
description: This skill should be used when the user asks to "review the implementation", "review spec-NNN code", "get expert review on the work", "review what was built", "implementation review", "code review the spec", or invokes /impl-review. Deploys 3 dynamically-chosen domain expert subagents to review implementation work from different angles — each reviewer covers a distinct, non-overlapping aspect of the delivered code. This skill reviews delivered code, not planning documents — for reviewing planning artifacts before implementation, use plan-review. Use after completing a spec implementation or before merging significant work.
---

# Implementation Review

Deploy 3 domain-expert reviewer subagents to evaluate completed implementation work. The reviewers are NOT hardcoded — they are dynamically selected based on what was actually built, ensuring each covers the most significant and distinct aspect of the delivered code.

## Arguments

Accept a spec folder path or diff reference (e.g., `docs/spec-007-infrastructure/`, `HEAD~5..HEAD`, or a branch name). If no argument given, use the current uncommitted changes or the most recent spec folder.

## Workflow

### Phase 1: Discover What Was Built

Before selecting reviewers, analyze the implementation scope:

1. Read the spec's handoff or kanban to understand delivered tasks
2. Run `git diff --stat` against the base to identify changed files
3. Categorize the work into 3-5 distinct technical domains (e.g., "Bicep IaC modules", "GitHub Actions CI/CD", "OpenTelemetry instrumentation", ".NET EF Core persistence", "Docker containerization", "security/RBAC", "API design")

### Phase 2: Select 3 Distinct Reviewers

From the discovered domains, select the **3 most significant and non-overlapping** expertise areas. Each reviewer must cover a distinct dimension — no two reviewers should evaluate the same files from the same angle.

**Selection criteria:**
- Coverage: together the 3 reviewers should cover >80% of the changed files
- Distinction: each reviewer's focus must be clearly different from the others
- Significance: prioritize areas with the most risk, complexity, or business impact

**Define each reviewer with:**
- A domain title (e.g., "Azure Infrastructure & Bicep")
- A 1-sentence focus statement (what specifically to evaluate)
- The subset of files/patterns to review
- 4-6 evaluation criteria specific to that domain

### Phase 3: Deploy Reviewers in Parallel

Dispatch all 3 reviewer subagents simultaneously using the `feature-dev:code-reviewer` agent type (lightweight read-only reviewer from the feature-dev agent family). Each receives a brief structured as:

````
You are a [DOMAIN TITLE] expert reviewing [SPEC-NAME]'s implementation.

## Focus
[1-sentence focus statement]

## Files to Review
[List of file patterns or specific paths]

## Evaluate Against These Criteria
1. [Domain-specific criterion 1]
2. [Domain-specific criterion 2]
3. [Domain-specific criterion 3]
4. [Domain-specific criterion 4]

## Report Format

    ## [Domain Title] Review

    ### Critical Issues (must fix)
    - [list or "None found"]

    ### Warnings (should fix)
    - [list or "None found"]

    ### Suggestions (nice to have)
    - [list]

    ### Verdict: [PASS / PASS WITH WARNINGS / NEEDS FIXES]

Be specific — reference exact file paths and line numbers.
Do NOT modify any files.
````

### Phase 4: Consolidate and Report

After all 3 reviewers complete:

1. Deduplicate findings that appear across multiple reviewers
2. Prioritize by severity (Critical > Warning > Suggestion)
3. Present a unified report:

```
## Implementation Review: [SPEC-NAME]

### Reviewers Deployed
1. [Domain 1] — [focus]
2. [Domain 2] — [focus]
3. [Domain 3] — [focus]

### Critical Issues (across all reviewers)
- [deduplicated list]

### Warnings
- [deduplicated list]

### Top Suggestions
- [top 5 most impactful]

### Per-Reviewer Verdicts
| Reviewer | Verdict |
|----------|---------|
| [Domain 1] | [verdict] |
| [Domain 2] | [verdict] |
| [Domain 3] | [verdict] |

### Overall: [READY TO SHIP / NEEDS FIXES (N critical)]
```

### Phase 5 (Conditional): Fix Critical Issues

If critical issues are found, present the list and ask the user whether to apply fixes. If the user declines, report the findings and stop. If approved, apply fixes directly. Commit with:
```bash
git commit -m "fix(spec-NNN): Address N critical review findings from impl-review

[1-line summary per fix]

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Dynamic Reviewer Examples

The same skill produces completely different reviewer configurations depending on the work:

**For a CI/CD spec (SPEC-0006):**
1. CI/CD & GitHub Actions — workflow correctness, job dependencies, caching
2. .NET & OpenTelemetry — telemetry setup, metrics design, package compatibility
3. Security & Deployment Safety — secret management, supply chain, blast radius

**For an IaC spec (SPEC-0007):**
1. Azure Bicep & ARM — resource types, API versions, module structure, parameters
2. Identity & RBAC — managed identity, role assignments, Entra auth, Key Vault
3. Deployment Pipeline — Deployment Stacks, OIDC, health gates, rollback logic

**For a domain module spec:**
1. Domain Design — aggregate boundaries, invariants, event sourcing
2. Persistence & EF Core — migrations, query filters, connection management
3. API & Integration — endpoint design, validation, error handling

## Rules

- **Always 3 reviewers** — not 2, not 4. Three provides diversity without diminishing returns.
- **Non-overlapping** — if two reviewers would look at the same files for the same reason, merge them and pick a different third.
- **Run in parallel** — all 3 subagents dispatch in a single turn for maximum speed.
- **Evidence-based** — reviewers must cite specific file paths and line numbers, not vague observations.
- **Fix only critical** — suggestions and warnings are reported but not auto-fixed.
