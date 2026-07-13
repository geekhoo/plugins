---
name: phased-implementation-tracker
description: >
  Use when the user continues or resumes a multi-session implementation plan, asks
  where they left off, or checks plan progress. Trigger on phrases like "continue
  from step", "where were we", "what's next in the plan", "mark step N done", "step
  N complete", "defer step N", "show plan status", "plan progress", "resume the
  plan", or natural language like "let's keep going" — the user will rarely name the
  skill. Also trigger proactively at the start of any session when a .phased-plan.md
  file exists in the current project directory — show status without waiting to be
  asked.
---

# Phased Implementation Tracker

This skill helps Gerald manage multi-step implementation plans that span multiple
sessions. Plans are saved to `.phased-plan.md` in the current project directory so
work can pause and resume cleanly.

---

## Step 1: Check for an existing plan

At the start of every invocation, check whether `.phased-plan.md` exists in the
current working directory.

- **File found** → Read it and jump to [Showing Plan Status](#showing-plan-status).
- **File not found** → Ask the user to provide the plan steps, then jump to
  [Saving a New Plan](#saving-a-new-plan).

---

## Step 2 (new plan): Saving a New Plan

When there is no existing plan file, ask the user:

> "I don't see a .phased-plan.md here yet. Please paste or describe the steps
> for this plan and give it a title — I'll save it so we can track progress
> across sessions."

Once the user provides the steps, write `.phased-plan.md` using the format below.
All new steps start as `[ ]` (PENDING).

---

## Plan file format

Markers: `[x]` DONE, `[-]` IN-PROGRESS, `[ ]` PENDING, `[~]` DEFERRED, `[!]` BLOCKED
(reason after a colon). Always write the current date into "Last updated:" when saving.
Load `references/plan-file-format.md` for the exact file template, full legend,
example multi-session flow, and plan-file tips before writing a new plan file.

---

## Showing Plan Status

After reading `.phased-plan.md`, display the plan clearly:

```
Plan: {title}  (last updated: {date})

  [x] 1. First step              ✓ DONE
  [-] 2. Second step             ▶ IN PROGRESS
  [ ] 3. Third step              · PENDING
  [~] 4. Fourth step             ~ DEFERRED
  [!] 5. Fifth step              ! BLOCKED: reason

Next up: step 3 — Third step
```

After showing status, either:
- Automatically offer to begin the first PENDING or IN-PROGRESS step, or
- Ask "Which step should we work on?" if the situation is ambiguous.

The goal is forward momentum. Don't just show the list and wait — propose the
obvious next action.

---

## Handling user commands

Respond to these natural phrases mid-conversation:

### Mark a step done
Triggers: "mark step N done", "step N complete", "N is done", "finished step N"

1. Change step N's marker from whatever it is to `[x]`.
2. Update "Last updated" to today's date.
3. Save the file.
4. Show a brief updated status display.
5. Offer to continue to the next PENDING step.

### Defer a step
Triggers: "defer step N", "skip step N", "come back to step N later"

1. Change step N's marker to `[~]`.
2. Update "Last updated" to today's date.
3. Save the file.
4. Show a brief updated status display.
5. Move to the next PENDING step automatically.

### Mark a step blocked
Triggers: "step N is blocked", "blocking issue on step N"

1. Change step N's marker to `[!]`.
2. Ask the user for the blocking reason (one sentence is fine).
3. Write it as `[!] N. Step title (blocked: {reason})`.
4. Save the file.
5. Show updated status.

### Mark a step in progress
Triggers: "starting step N", "working on step N", "begin step N"

1. Change step N's marker to `[-]`.
2. Update "Last updated" to today's date.
3. Save the file.

---

## After completing work on a step

When a step's implementation work finishes in the current conversation:

1. Offer to mark it done: "Should I mark step N as done in the plan?"
2. If yes, update the file and show the updated checklist.
3. Then surface the next step: "Next up is step N+1 — ready to continue?"

This closes the loop so the file always reflects true current state.

---

## Saving state

Write `.phased-plan.md` after every status change. Use plain file write — no
special tooling needed. The file lives in the current working directory (the
project root, wherever Claude Code is running). Never create it somewhere else.

---

## Example flow & tips

See `references/plan-file-format.md` for a worked multi-session example and
plan-file hygiene tips (one plan per directory, renumbering on reorganization).
