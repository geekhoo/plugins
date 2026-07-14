---
name: parallel-review-orchestrator
description: Use to REVIEW delivered work — the codebase, completed tasks, written code — against the expected OUTCOMES/goals of the requirements, coordinating parallel reviewer AND coder passes into one verified, integrated result (can remediate, not just report). Triggers "subagents", "parallel reviewers", "delegated coders", "multiple expert domains", "independent passes". For read-only auditing of work against task/spec requirements without fixes, use parallel-audit.
---

# Parallel Review Orchestrator

## Overview

Coordinate independent reviewer or coder passes, then merge their outputs into one verified state. Use parallelism only when the domains are genuinely separable and the user explicitly requests or available tooling clearly supports it.

## Prerequisites And Clarification

- Confirm multi-agent tooling is available or that the user explicitly requested parallel agents.
- Identify protected paths, target artifacts, source evidence, and whether remediation is in scope.
- Split only truly independent domains: examples include security, tests, docs, UI, architecture, data contracts, or separate files/modules.
- Ask when reviewer roles, domains, target artifacts, output format, or allowed write scope are unclear.
- Do not use this for a single-domain review; use `evidence-review`.
- Do not use this as the fixing workflow by itself; use `review-remediation` when the user asks to fix findings.

## Workflow

1. Define roles.
   Name each reviewer or coder role, its domain, allowed files, expected output, and validation responsibility.

2. Bound each prompt.
   Give raw artifacts, source paths, specs, diffs, logs, or user requirements. Do not pass intended conclusions, suspected findings, expected fixes, or another reviewer output unless synthesis explicitly requires it.

3. Collect outputs.
   Require findings or actions to include evidence, severity or priority, affected files, recommended next step, and validation status.

4. Normalize findings.
   Deduplicate overlaps, merge equivalent issues, discard unsupported claims, and prioritize by correctness, security, user impact, contract risk, and test coverage.

5. Verify before acting.
   Reopen current source or artifacts to confirm every finding that will drive remediation. Mark unverified claims as assumptions or residual risk, not as fixes to implement.

6. Integrate remediation if requested.
   Apply only validated fixes within the allowed scope. Preserve user-owned changes and avoid broad refactors that were not requested.

7. Run final validation.
   Validate the integrated result with repo-grounded commands, browser checks, schema checks, or source citations appropriate to the merged work.

8. Report one state.
   Provide a single integrated result, not a pile of agent transcripts. Include changed files, accepted findings, rejected or unverified findings, validation results, assumptions, and limitations.

## Verification Gates

| Gate | Requirement |
|---|---|
| G0 Scope | User explicitly requested parallel agents, or available tooling and task shape justify them. |
| G1 Evidence | Independent domains and raw source artifacts are identified. |
| G2 Prompt | Delegated prompts avoid leaking expected answers or prior conclusions. |
| G3 Collection | Outputs include evidence, priority, affected files, and validation status. |
| G4 Merge | Merged findings are verified against current source before they drive fixes. |
| G5 Reporting | Final output gives one integrated validated state. |

## Acceptance Criteria

- Reviewer or coder outputs are deduplicated, prioritized, and traceable to evidence.
- Only validated findings drive implementation, status claims, or completion decisions.
- Final validation covers the integrated changes or explicitly names skipped checks and residual risk.
- The final report separates confirmed issues, assumptions, rejected findings, changed files, and validation results.

## Expected Outcome

A merged review/remediation report and, when fixes are in scope, a validated result that reflects all accepted independent passes without leaking unverified conclusions into implementation.

## Common Mistakes

- Splitting work by agent count instead of independent domains.
- Passing suspected answers or desired conclusions into reviewer prompts.
- Treating subagent output as validated without checking current source.
- Reporting separate transcripts instead of one synthesized state.
- Implementing unverified or duplicate findings.
- Skipping final validation after merging independent work.
