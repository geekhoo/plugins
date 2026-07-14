---
name: scope-guard
description: Use when the user names EXPLICIT no-edit paths, protected directories, or specific files not to touch (e.g. "don't edit these files", "these dirs are off-limits", "only touch X/") — record the allowed and protected edit surfaces before changing code, docs, or running destructive or git operations. For general restraint against over-engineering or scope creep (no explicit path list), use pragmatic-scope-guard.
---

# Scope Guard

## Overview

Use this skill to make edit boundaries explicit before changing files. The goal is to preserve user-owned or unrelated work while completing only the requested task.

## Prerequisites And Clarification

- Inspect current git state when working in a repository.
- Inventory the requested target paths and any protected, skipped, stale, deleted, or user-owned paths before editing.
- Ask before proceeding if a protected path conflicts with required work.
- Ask before using a stale or deleted artifact that appears necessary for the task.
- Do not ask when the user already states the boundary clearly; record it and follow it.

## Workflow

1. Capture the scope record:
   - Allowed edit surfaces.
   - Disallowed paths, files, folders, or operation types.
   - Known user-owned changes or unrelated dirty work.
   - Stale artifacts that must be ignored or preserved.
2. Verify the current state with targeted commands such as `git status --short --untracked-files=all`, `rg --files`, or directory listings.
3. Re-check the scope record before applying patches, deleting files, moving files, cleaning generated output, staging changes, committing, or running destructive commands.
4. If the task cannot be completed inside the allowed scope, stop and surface the conflict before making the out-of-scope change.
5. Report relevant protected changes or untouched paths in the final answer.

## Verification Gates

- G0: Target and protected paths are identified.
- G1: Git state is inspected when the work is inside a repo.
- G3: All edits remain inside allowed paths.
- G5: The final report names any relevant untouched protected changes.

## Acceptance Criteria

- No unrelated files are modified.
- User-owned changes are preserved.
- Cleanup, deletion, revert, move, git, or generated-file operations stay within the recorded scope.
- Any unavoidable scope conflict is surfaced before work proceeds.

## Expected Outcome

A clear scope boundary, safe execution within that boundary, and a final report that distinguishes completed work from protected work left untouched.

## Common Mistakes

- Treating `git status` noise as permission to clean or revert unrelated files.
- Expanding from "inspect" to "edit" without confirming the allowed surface.
- Deleting stale-looking artifacts before checking whether the user protected them.
- Patching adjacent files because they look related but were not in scope.
- Staging broad paths such as `.` when unrelated changes exist.
