---
name: review-remediation
description: Use when the user provides "review comments", "PR feedback", or "audit findings", or asks to "address", "triage", or "remediate" findings; verify each claim against source, then implement or plan the fixes.
---

# Review Remediation

## Overview

Turn review output into prioritized, validated work. Verify every finding against current source before treating it as true, then either implement confirmed fixes or produce an actionable remediation plan.

## Prerequisites And Clarification

- Identify the review artifacts, target repo, protected paths, and allowed write scope.
- Read the original comments or findings, not only summaries of them.
- Ask whether the user wants fixes, a plan only, or both when the request does not make that clear.
- Ask before changing behavior for low-confidence, conflicting, broad, or policy-sensitive findings.
- Preserve user-owned changes and unrelated worktree state.

## Workflow

1. Normalize findings.
   Convert comments into a matrix with: source comment, severity, affected files, status, rationale, planned action, and validation.

2. Verify against current source.
   Inspect current files, tests, docs, configs, and call sites. Mark each finding as `confirmed`, `rejected`, `duplicate`, `needs-clarification`, or `already-fixed`.

3. Prioritize remediation.
   Order confirmed findings by severity, user impact, security risk, contract impact, and blast radius. Group duplicates under the strongest source comment.

4. Plan the smallest fix.
   Map each confirmed finding to specific files and checks. Keep changes scoped to the requested remediation and avoid opportunistic refactors.

5. Execute if requested.
   Apply fixes only for confirmed findings that are in scope. Do not implement speculative fixes for `needs-clarification`, `rejected`, or unverified items.

6. Validate and report.
   Run targeted tests, builds, linters, browser checks, or schema checks that prove the changed behavior. Report the final finding matrix and cite unrun checks as residual risk.

## Complexity Split

- For multiple independent reviewers, route orchestration to `parallel-review-orchestrator`.
- For saved or reusable findings, route persistence to `findings-persistor`.

## Verification Gates

- G0 Scope gate: review artifacts, target source, allowed edits, protected paths, and desired output are known.
- G1 Evidence gate: every finding is verified against current source before acceptance.
- G2 Plan gate: confirmed findings map to specific remediation steps and validation checks.
- G3 Execution gate: fixes are applied only within the allowed scope.
- G4 Validation gate: tests, builds, checks, or source review cover changed behavior.
- G5 Reporting gate: final output maps each comment to its outcome, rationale, files changed, validation, assumptions, and unresolved risks.

## Acceptance Criteria

- No unverified finding is treated as confirmed.
- Every fix maps back to one or more specific review comments.
- Rejected, duplicate, already-fixed, and needs-clarification findings have short evidence-backed rationales.
- Validation covers the behavior or contract affected by the fixes.
- The final answer distinguishes implemented fixes from planned or blocked remediation.

## Expected Outcome

A resolved findings matrix plus either implemented, validated fixes or a scoped remediation plan the user can execute.

## Common Mistakes

- Accepting reviewer claims without reopening current source.
- Fixing low-confidence or conflicting findings without asking.
- Expanding remediation into unrelated cleanup or refactors.
- Losing the mapping between comments, code changes, and validation.
- Reporting `done` without naming unrun checks or residual risks.
- Treating duplicate or already-fixed comments as separate implementation work.
