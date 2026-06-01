---
name: geeky-status
description: Read-only status snapshot of a geeky-plan / geeky-implement planning folder. Reports kanban lane counts, in-progress and blocked tasks, recent task notes, the last handoff entry, deferred follow-ups, and a suggested next step. No agents, no edits, no commits. Use when asked where a planning/implementation effort stands or to inspect a kanban folder before resuming. Invoked by the /geeky-status command and usable directly by any agent.
---

# geeky-status

Fast situational awareness when resuming a planning/implementation session. Answers: where are we, what's blocked, what's deferred, what was the last thing done. Useful before invoking the `geeky-implement` skill to decide whether to resume, retarget, or hand-fix.

## Input

`$ARGUMENTS`: a folder produced by `geeky-plan`. If missing or the folder does not contain `kanban.md`, STOP and ask the user. This skill is strictly read-only — never modify, commit, or delegate.

## Tasks

1. **Validate the folder.** Pick the runtime by host OS (`${CLAUDE_PLUGIN_ROOT}` is the root of the `geeky-orchestration` plugin):
   - Windows: `pwsh -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.ps1" -Path "<folder>"`
   - macOS / Linux / cross-platform: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"` (use `python3` if `python` is not on PATH)

   If it returns non-zero, print its output and stop.

   Then run the read-only **kanban-integrity** gate and fold its findings into the `Inconsistencies:` section of the report (do not fix anything — this skill is read-only):
   - Windows: `pwsh -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.ps1" -Path "<folder>"`
   - cross-platform: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"`

2. **Read** `kanban.md`, `handoff.md`, and the last `review-*.md` in the folder. If `tasks/` exists, glob `tasks/T*.md` (excluding `*.notes.md`) to get the total task count.

3. **Parse `kanban.md`** into lane counts. Recognise these lane headings (case-insensitive, any heading depth): Backlog, Ready, In Progress, Blocked, In Review, Done. For each task in `In Progress` or `Blocked`, capture the task ID, the line, and any trailing `<!-- ... -->` timestamp comment.

4. **Read recent `tasks/Tx-*.notes.md` files** (sorted by modified time, most recent 3). Pull out the SUMMARY line and the VALIDATION line from each, if present.

5. **Print a compact status report** to the user in this exact shape:

   ```
   Planning folder: <absolute path>

   Lane counts:
     Backlog:     <n>
     Ready:       <n>
     In Progress: <n>
     Blocked:     <n>
     In Review:   <n>
     Done:        <n> / <total>

   In Progress:
     - <Tid> — <task title> <timestamp if present>
     - ...

   Blocked:
     - <Tid> — <reason if present in kanban>
     - ...

   Validation checklist:
     <reproduce the Validation Checklist block from kanban.md, preserving [ ]/[x]>

   Last 3 task notes (most recent first):
     - <Tid>: <SUMMARY first sentence> | validation: <PASS|FAIL>
     - ...

   Last handoff entry:
     <heading + first ~3 lines of the most recent dated section in handoff.md>

   Deferred follow-ups:
     <bullet list under the "Deferred follow-ups" section in handoff.md, if any>

   Suggested next step:
     <one of:
        "Resume with /geeky-implement <folder>" if Ready > 0 and Blocked == 0
        "Resolve blocked: <Tid> before resuming" if Blocked > 0
        "Backlog only — promote tasks to Ready or extend plan" if Ready == 0 and Backlog > 0
        "Done — final PM review may be appropriate" if Done == total
     >
   ```

6. Do not call any subagent. Do not edit any file. If anything in the folder looks inconsistent (e.g. kanban counts don't add up to total tasks), include an `Inconsistencies:` section listing what doesn't match, but still produce the report.

## Acceptance criteria

- Output is exactly the layout above (with real numbers / task IDs substituted).
- No files modified, no agents spawned, no commits made.
- Runs in under 5 tool calls in typical folders.
