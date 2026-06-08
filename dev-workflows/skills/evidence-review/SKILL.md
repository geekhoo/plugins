---
name: evidence-review
description: Use when the user asks for a "review", "evidence-based assessment", "source-backed critique", "PR or code or doc review", "line references", or "verify these claims"; report evidence-backed findings from current files, not memory.
---

# Evidence Review

## Overview

Ground every review in current evidence from the target repo or source artifacts. Report confirmed issues first, ordered by severity, and separate facts from assumptions.

## Prerequisites And Clarification

- Determine the review lens: code correctness, docs accuracy, security, design, architecture, tests, or mixed.
- Infer the target from the user request, current diff, named files, PR context, or nearby docs. Ask only when the target or lens cannot be inferred.
- Inspect current files before relying on memory, summaries, generated reports, or prior chat context.
- For code review, default to a findings-first response. If there are no confirmed findings, say so and name residual test or coverage risk.
- Do not edit files unless the user explicitly asks for remediation.

## Workflow

1. Map scope.
   Use `git status`, `git diff`, `rg --files`, `rg`, and relevant docs/manifests to identify changed files, call sites, dependencies, and contracts.

2. Read evidence.
   Inspect the current implementation, tests, docs, configuration, and source references that support or contradict each potential claim.

3. Analyze impact.
   Prefer confirmed bugs, regressions, contract violations, missing tests, behavioral gaps, stale docs, and security risks over style or broad refactor advice.

4. Build findings.
   Each finding needs exact file/line evidence, severity, why it matters, and the observable failure mode or risk. Avoid findings that are only guesses.

5. Report cleanly.
   Put findings first in severity order, then open questions or assumptions, then a short summary or residual-risk note.

## Verification Gates

- G0 Scope gate: review target, allowed files, and requested lens are known or a clarification was asked.
- G1 Evidence gate: current source, diff, docs, tests, and relevant call sites were inspected.
- G2 Lens gate: review category and quality bar are explicit.
- G4 Finding gate: every finding has file/line evidence plus user-impact or correctness impact.
- G5 Reporting gate: findings are first; unsupported claims are labeled as assumptions or omitted.

## Acceptance Criteria

- Findings are actionable, line-cited, and severity ordered.
- No memory-derived, assumed, or stale claim is presented as confirmed fact.
- The review avoids unrelated cleanup, speculative architecture advice, and low-value style notes unless the user requested them.
- Missing validation or unrun checks are named as residual risk.

## Expected Outcome

A concise evidence-backed review that states confirmed issues, cites current files and lines, identifies open questions, and makes the remaining risk clear.

## Complexity Split

- Use `review-remediation` when the user asks to convert findings into fixes, tasks, or implementation.
- Use `parallel-review-orchestrator` when multiple independent review domains are explicitly requested.

## Common Mistakes

- Reviewing from memory or prior summaries without reopening current files.
- Reporting likely concerns as confirmed bugs without a file/line citation.
- Burying findings below a long narrative summary.
- Letting refactor preferences dominate correctness, security, behavior, or test coverage issues.
- Ignoring call sites, tests, docs, or contracts that define the actual behavior.
