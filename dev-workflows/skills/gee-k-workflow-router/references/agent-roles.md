# Agent Roles

Use subagents only when work is independent enough to parallelize safely.

## Evidence Reviewer

Read-only. Cite file/line evidence. Return verdict and findings.

## Scope Guard

Read-only. Compare allowed scope to touched paths. Stop on scope drift.

## Validation Runner

Run validation matrix. Report commands and pass/fail/block.

## Browser Validator

Run browser-visible checks. Report route, console, screenshot, and viewport evidence.

## External Preflight Agent

Verify tools, auth, env, path, branch/upstream, and writable roots.

## Implementation Coder

Edit only assigned files. Add focused tests. Report changed paths and validation.

## Integration Lead

Resolve contradictions from subagents by checking current files. Run final validation. Produce one integrated report.
