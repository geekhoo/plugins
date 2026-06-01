---
allowed-tools: Read, Glob, Grep, Bash, PowerShell
argument-hint: folder path holding the geeky-plan artifacts
description: Read-only status snapshot of a geeky-plan / geeky-implement planning folder. No agents, no edits.
---

Invoke the **`geeky-status`** skill, passing along `$ARGUMENTS` (a folder produced by `/geeky-plan`). If it is missing or contains no `kanban.md`, stop and ask the user.

The skill contains the full procedure: validate the folder, parse `kanban.md` into lane counts, capture In Progress / Blocked tasks, summarize the most recent task notes and handoff entry, list deferred follow-ups, and print a compact status report with a suggested next step. It is strictly read-only — no agents, no edits, no commits.
