---
name: automation-status
description: Use when the user asks about "automations", "recurring tasks", "monitors", "reminders", "scheduled reports", "wake-up tasks", or "automation status" — report the state of configured automations and recurring work.
---

# Automation Status

## Overview

Produce a source-backed automation status or perform a clearly requested automation change. Never invent automation state when tooling, memory, or task-board data is unavailable.

## Prerequisites And Clarification

- Discover the available automation tools, connectors, memory files, or task-board sources before creating, updating, or deleting automations.
- For create, update, or delete requests, confirm the action type and required details first: schedule, target, payload or task, owner if relevant, and notification behavior.
- If the user only asks for plain progress unrelated to scheduled automation, use `status-interrupt` instead.

## Workflow

1. Classify the request as `status`, `create`, `update`, `delete`, or `unknown`.
2. Inspect the current automation source: automation tool output, stored automation definitions, relevant memory, or task-board files.
3. For status requests, report completed, active, blocked, and next scheduled work with source-backed identifiers when available.
4. For create, update, or delete requests, apply the change only after the required parameters and user intent are clear.
5. If no automation source is available, state that limitation and do not fabricate ids, schedules, or completion state.

## Verification Gates

- G0: Automation action type is known, or the uncertainty is stated.
- G1: Current automation state has been inspected before status reporting or mutation.
- G3: Create, update, or delete operations run only with required parameters.
- G5: Final response includes automation id and status, or a clear limitation when no source is available.

## Acceptance Criteria

- Automation state is backed by an inspected source.
- Updates match the requested schedule, target, action, and notification behavior.
- Missing tooling or inaccessible memory/task-board data is reported plainly.
- The response separates completed, active, blocked, and next scheduled work when those categories exist.

## Expected Outcome

A concise automation status report or a confirmed automation update, including ids/statuses where the source provides them.

## Common Mistakes

- Treating an informal follow-up instruction as a scheduled automation without confirming schedule and notification behavior.
- Reporting remembered or guessed automation state without inspecting the current source.
- Creating or changing an automation before the target, schedule, and action are unambiguous.
- Using this skill for ordinary in-session progress updates instead of `status-interrupt`.
