---
name: resume-inventory
description: Use when the user asks to "resume", "continue", "check status", "what is done and pending", or "where does the work stand" — inventory completed and pending work from the current worktree before continuing.
---

# Resume Inventory

## Overview

Resume from evidence, not memory. Build a current-state inventory before reporting status or continuing work so user changes, stale assumptions, blocked tasks, and pending validation are visible.

## Prerequisites And Clarification

- Identify the current repo, worktree, branch, protected paths, and write scope before editing.
- Inspect git state, dirty files, untracked files, recent files, task docs, handoff docs, run logs, and relevant validation artifacts.
- Prefer current source evidence over prior summaries or memory.
- Ask only when multiple plausible task contexts exist and choosing one would risk wrong edits or destructive/external action.

## Workflow

1. Inventory the branch, dirty files, untracked files, task trackers, docs, logs, recent outputs, and validation artifacts.
2. Classify each meaningful item as `complete`, `pending`, `blocked`, or `unknown`.
3. Separate confirmed facts from assumptions, stale evidence, and unavailable artifacts.
4. Identify user-owned changes and avoid reverting, overwriting, or cleaning them without explicit instruction.
5. Name the next safe action and the evidence that supports it.
6. If the user asked only for status, report and stop unless they explicitly continue.
7. If the user asked to continue, proceed from the next safe action after the inventory.

## Verification Gates

- G0 Scope gate: current repo, worktree, branch, write scope, and protected paths are known.
- G1 Evidence gate: state sources were inspected, or unavailable sources are called out.
- G2 Plan gate: status classification and next safe action are explicit.
- G3 Execution gate: any continued work stays inside the allowed scope and preserves user changes.
- G4 Validation gate: checks or citations prove completed work when validation is relevant.
- G5 Reporting gate: final or interim report separates confirmed state from assumptions, pending work, blockers, and risks.

## Acceptance Criteria

- Continuation uses current worktree facts rather than stale conversation state.
- Complete, pending, blocked, and unknown items are explicit.
- User-owned changes are preserved.
- Status-only requests do not silently turn into implementation work.
- Continue requests move forward after inventory instead of stopping at a report.

## Expected Outcome

A reliable status inventory with a next-action plan, or continued work that starts from verified current state.

## Common Mistakes

- Starting implementation before inspecting git state and recent artifacts.
- Treating memory or a previous handoff as confirmed current state.
- Collapsing `pending`, `blocked`, and `unknown` into a vague status summary.
- Ignoring untracked files, generated outputs, or validation logs.
- Reverting, deleting, or overwriting user changes during cleanup.
- Continuing after a status-only interruption.
- Stopping after inventory when the user explicitly asked to continue.
- Inventing commands, validation results, paths, or task status.

## Complexity Split

- Use `status-interrupt` for status-only interruptions during active work.
- Use `git-hygiene` when branch, dirty-tree, commit, push, or PR details dominate the request.
