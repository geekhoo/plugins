---
allowed-tools: Read, Glob, Grep, Bash, PowerShell, Edit
argument-hint: folder path holding the geeky-plan artifacts
description: Reconcile a geeky planning folder against live git state after a session cutoff, then hand off to /geeky-implement. Edits limited to kanban lane corrections + a handoff note.
---

Invoke the **`geeky-resume`** skill, passing along `$ARGUMENTS` (a folder produced by `/geeky-plan`). If it is missing or contains no `kanban.md`, stop and ask the user.

The skill contains the full procedure: read handoff.md and kanban.md first, snapshot via geeky-status, reconcile every In Progress / In Review / Done claim against live `git status`/`git log`/`git diff`, correct kanban lanes to verified reality with a dated handoff note, and report the next step. It never executes tasks — execution belongs to `/geeky-implement`.
