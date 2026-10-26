---
name: impl-review
description: Use when requested to review implemented code after `/geeky-implement` completes. This skill dispatches multi-angle implementation reviewers and returns blocker/major/minor findings against the done work.
---

Use the shared [workflow terminology](../../AGENTS.md#workflow-terminology).

# Implementation Review

Deploy 3 domain-expert reviewer subagents to evaluate completed implementation work. The reviewers are NOT hardcoded — they are dynamically selected based on what was actually built, ensuring each covers the most significant and distinct aspect of the delivered code.

## Review boundary

This skill owns final implementation review. Task reviews establish AC and test results; phase reviews establish collective requirements and readiness to advance. Use those verdicts and evidence as inputs, then review the approved outcome and cross-phase integration within each assigned domain. Do not repeat earlier reviews or tests unless changed dependencies, contradictory evidence or a concrete defect invalidate them. Record the reason for reopening a surface.

Persist each domain reply immediately in its `review-impl.md` section with reviewer agent ID, reviewed revision or file hashes, findings, verdict and `<!-- reviewer-complete: <domain> -->`. Collect all domain findings before remediation. Batch compatible fixes by owner, then validate and re-review the affected scope. Preserve unaffected verdicts and evidence; do not dispatch a separate review for every small correction.

Once required findings are resolved and affected checks pass, record the final verdict and finish required closeout. Do not add another review or hardening pass. Reopen only when concrete evidence invalidates acceptance; optional suggestions remain follow-ups.

## Arguments

Accept a `geeky-implement` package path or diff reference (e.g., `docs/notifications/`, `HEAD~5..HEAD`, or a branch name). If no argument is given, apply this deterministic precedence: (1) if uncommitted changes exist (`git diff --stat` is non-empty), review those; (2) otherwise, scan `docs/` for the most recent feature package (folder with `implementation-plan.md` and newest `handoff.md` timestamp) and review commits since its stated baseline.

## Workflow

**Resume contract (check FIRST):** this skill writes its consolidated report to `review-impl.md` inside the package folder (or `docs/` root for diff-only reviews), marking each reviewer section with `<!-- reviewer-complete: <domain> -->` as it lands. On invocation, if a `review-impl.md` exists for the same target with completed reviewer sections, this is a resumed run: skip the completed domains, dispatch only the missing reviewers, and merge into the existing report. Reuse completed domains only while their reviewed revision and relevant dependencies remain valid. Record the reviewer agent ID and reviewed revision or file hashes with each section; consolidate saved, still-valid sections without redispatch. If those inputs change, reopen only affected domains and record why; a completed marker alone is not proof of current validity.

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

    ### Required Findings (must fix; include severity)
    - [list or "None found"]

    ### Nonblocking Warnings (follow-ups)
    - [list or "None found"]

    ### Suggestions (nice to have)
    - [list]

    ### Verdict: [PASS / PASS WITH WARNINGS / NEEDS FIXES]

Any unmet requirement, mandatory constraint, unresolved required finding or missing required evidence means NEEDS FIXES, regardless of its severity label. PASS WITH WARNINGS is only for nonblocking follow-ups with all required evidence passing.
Be specific — reference exact file paths and line numbers.
Do NOT modify any files.
````

### Phase 4: Consolidate and Report

Save each reply as it arrives, before waiting for the others. After all 3 domain sections are saved and current:

1. Deduplicate findings across the saved sections.
2. Separate required findings from nonblocking follow-ups, then prioritize by severity.
3. Consolidate in `review-impl.md` and present the report below. Overall PASS requires all three current domain verdicts to be PASS or PASS WITH WARNINGS, with required findings resolved and complete passing evidence. Domain PASS WITH WARNINGS consolidates to PASS under those conditions; otherwise Overall NEEDS FIXES. Unknown or missing reviewer evidence cannot pass.

```
## Implementation Review: [SPEC-NAME]

### Reviewers Deployed
1. [Domain 1] — [focus]
2. [Domain 2] — [focus]
3. [Domain 3] — [focus]

### Required Findings (across all reviewers, with severity)
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

### Overall: [PASS / NEEDS FIXES (N required findings or evidence gaps)]
```

### Phase 5 (Conditional): Fix Required Findings

If required findings remain, present them and ask whether to apply fixes unless already authorized. If the user declines, report NEEDS FIXES and stop. Optional warnings and suggestions do not trigger a fix/review loop.

If approved, dispatch `geeky-coder` with the required findings; do not edit product code or tests directly. Validate and re-review only affected domains, preserve unchanged sections, then consolidate their current verdicts. Commit the fixes (same command on all platforms):

```bash
# Linux/macOS (bash) or Windows (pwsh) — identical command
git commit -m "fix(spec): Address N required review findings from impl-review" -m "[1-line summary per fix]" -m "Tasks: <IDs touched>"
```

Use the subject verbatim.

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
- **Fix required findings** — through `geeky-coder`, regardless of severity label; nonblocking warnings and suggestions remain follow-ups. Do not dispatch review merely to remove them.
