---
name: status-interrupt
description: Use when the user interrupts active work to ask "what is happening", "where are you", "what have you done", "still working?", or "status only" — give a concise progress snapshot while work continues.
---

# Status Interrupt

## Overview

Provide a short, accurate progress update without losing the active task. Treat status-only interruptions as temporary check-ins unless the user explicitly asks to pause, stop, or change direction.

## Prerequisites And Clarification

- Identify the active task before reporting status.
- Determine whether the newest request asks for status only, or asks to pause, stop, redirect, or decide something.
- Ask no questions unless work is blocked and user input is required.
- Use `resume-inventory` first when the active state is unknown.

## Workflow

1. State what has been completed.
2. State the current step or investigation focus.
3. State the next step.
4. Name blockers or say there are none known.
5. State the validation state only as far as it is true: not started, in progress, passed, failed, or blocked.
6. Continue the active work after reporting unless the user explicitly asked to stop or pause.
7. Preserve current plan item statuses; do not restart the plan or mark unfinished work complete.

## Verification Gates

- G0 Active task gate: the active task is identified before answering.
- G5 Status gate: the update names actual completed work and the current blocker, if any.

## Acceptance Criteria

- Status is accurate, concise, and does not imply completion.
- The response separates completed work from current work and next work.
- Blockers and validation state are explicit when relevant.
- Work continues when appropriate.

## Expected Outcome

A short progress update followed by uninterrupted continuation of the active task.

## Common Mistakes

- Treating a status request as permission to stop work.
- Restarting exploration or redoing inventory when current state is already known.
- Saying or implying the task is complete before validation is done.
- Asking the user what to do next when there is a clear next step.
- Changing plan statuses just to make the status update look tidy.
