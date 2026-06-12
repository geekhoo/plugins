---
name: impl-review
description: Use when requested to review implemented code after `/geeky-implement` completes. This skill dispatches multi-angle implementation reviewers and returns blocker/major/minor findings against the done work.
---

# Implementation Review

Deploy 3 domain-expert reviewer subagents to evaluate completed implementation work. The reviewers are NOT hardcoded — they are dynamically selected based on what was actually built, ensuring each covers the most significant and distinct aspect of the delivered code.

## Arguments

Accept a `geeky-implement` package path or diff reference (e.g., `docs/notifications/`, `HEAD~5..HEAD`, or a branch name). If no argument is given, apply this deterministic precedence: (1) if uncommitted changes exist (`git diff --stat` is non-empty), review those; (2) otherwise, scan `docs/` for the most recent feature package (folder with `implementation-plan.md` and newest `handoff.md` timestamp) and review commits since its stated baseline.

## Workflow

### Phase 1: Discover What Was Built

Before selecting reviewers, analyze the implementation scope:

1. Read the spec folder handoff/kanban to understand delivered tasks (e.g., `docs/feature-name/implementation-plan.md`, `handoff.md`, `kanban.md`).
2. Run `git diff --stat` against the base to identify changed files.
3. Categorize the work into 3-5 distinct technical domains (e.g., "Bicep IaC modules", "GitHub Actions CI/CD", "OpenTelemetry instrumentation", ".NET EF Core persistence", "Docker containerization", "security/RBAC", "API design").

### Phase 2: Select 3 Distinct Reviewers

From the discovered domains, select the **3 most significant and non-overlapping** expertise areas. Each reviewer must cover a distinct dimension — no two reviewers should evaluate the same files from the same angle.

**Significance ranking criteria (choose the top 3):**
- **Impact:** Areas affecting user-facing behavior, data integrity, or cross-cutting concerns (auth, observability, deployment)
- **Risk:** Areas with security implications, external integrations, or state management complexity
- **Complexity:** Areas with the highest cyclomatic complexity, deepest call chains, or most inter-module dependencies
- **Coverage:** Prioritize domains that collectively cover >80% of changed lines; avoid niche file types unless they carry high risk

**Define each reviewer with:**
- A domain title (e.g., "Azure Infrastructure & Bicep")
- A 1-sentence focus statement (what specifically to evaluate)
- The subset of files/patterns to review
- 4-6 evaluation criteria specific to that domain

### Phase 3: Deploy Reviewers in Parallel

Dispatch all 3 reviewer subagents simultaneously using the `geeky-orchestration:code-reviewer` agent type (lightweight read-only reviewer from this plugin). Each receives a brief structured as:

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

If critical issues are found, present the list and ask the user whether to apply fixes. If the user declines, report the findings and stop.

If approved, apply fixes directly and commit (same command on all platforms — duplication is intentional for per-environment copy/paste clarity):

```bash
# Linux/macOS (bash) or Windows (pwsh) — identical command
git commit -m "fix(spec): Address N critical review findings from impl-review" -m "[1-line summary per fix]" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Dynamic Reviewer Examples

The examples below illustrate how reviewer selection adapts to different work domains — they are not prescriptive templates. The actual reviewers chosen for your implementation will depend on what was built and the significance ranking in Phase 2.

**For a CI/CD spec:**
1. CI/CD & GitHub Actions — workflow correctness, job dependencies, caching
2. .NET & OpenTelemetry — telemetry setup, metrics design, package compatibility
3. Security & Deployment Safety — secret management, supply chain, blast radius

**For an IaC spec:**
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
