---
name: git-hygiene
description: Use when the user asks to "create or switch branches", "stage and commit", "push or prepare a PR", "group logical commits", or "report git status" — perform clean, atomic git operations and preserve uncommitted work.
---

# Git Hygiene

## Overview

Use this skill to keep git operations traceable and to avoid staging, reverting, overwriting, or losing unrelated or user-owned work.

## Prerequisites And Clarification

- Know the repository and intended git operation before acting.
- Run `git status --short --branch` before any branch, stage, commit, push, PR, release, archive, reset, checkout, or cleanup operation.
- Ask before destructive commands, force pushes, resets, checkout of dirty files, broad cleanup, or staging unrelated changes.
- Ask when multiple unrelated change sets need commit grouping and the grouping is not obvious from the request or diff.
- Use `scope-guard` first when the task also includes edits, no-edit paths, protected files, or user-owned changes.

## Complexity Split

- Use `scope-guard` before edits or cleanup that could cross protected, unrelated, or user-owned work.
- Use `handoff-prompt-generator` when PR or branch state must be transferred to another agent, thread, or human.

## Workflow

1. Record the current branch, upstream, staged files, unstaged files, and untracked files.
2. Identify which files belong to the requested operation and which appear unrelated or user-owned.
3. For nontrivial changes, state the staging and commit plan before staging.
4. Stage only intended files. Prefer explicit paths over broad commands such as `git add .`.
5. Follow repository commit-message rules from local docs, history, or user instruction.
6. Run the requested commit, branch, push, PR, release, or archive step.
7. Re-check `git status --short --branch` after the operation.
8. Report the exact outcome, including branch, commit hash if created, push or PR state if relevant, and remaining dirty files.

## Verification Gates

- G0: Repository and intended git operation are known.
- G1: Dirty state is inspected before git operations.
- G2: Staging and commit plan are defined for nontrivial or mixed changes.
- G3: Git operation is performed only within the staged or approved scope.
- G4: Post-operation status is checked.
- G5: Final report includes branch, commit hash if created, and remaining dirty state.

## Acceptance Criteria

- No unrelated changes are staged, reverted, deleted, or overwritten.
- User-owned changes remain intact.
- Commit messages follow repo conventions or explicit user instructions.
- Branch, push, PR, release, or archive state is clear after the operation.

## Expected Outcome

Clean, traceable git operations with explicit dirty-tree reporting and preserved unrelated work.

## Common Mistakes

- Running `git add .` in a dirty worktree with unrelated files.
- Treating untracked files as disposable without checking ownership or scope.
- Reverting, resetting, or checking out files to make status look clean.
- Creating a commit before separating logical change sets.
- Skipping the final status check after a commit, push, or branch switch.
- Reporting "clean" without naming the branch and verifying the post-operation state.
