---
allowed-tools: "*"
argument-hint: folder path holding the geeky-plan artifacts (implementation-plan.md, kanban.md, tasks/, etc.). Optionally append --phase=<name|number>, --dry-run, or --serial.
description: geeky orchestrator that executes the geeky-plan package — drives tasks through the kanban, delegates geeky-coder + reviewer subagents, validates, commits per phase, and keeps handoff.md current
---

Invoke the **`geeky-implement`** skill to run the execution phase, passing along `$ARGUMENTS` (the planning-package folder produced by `/geeky-plan`, plus any inline `--phase=<name|number>`, `--dry-run`, or `--serial` flags). If the folder is missing, ask the user.

The skill contains the full procedure: validate the planning folder, walk the kanban, delegate implementation to `geeky-coder` subagents (up to 3 in parallel when safe), verify each task's validation evidence, review task ACs and tests, require a phase readiness verdict, write `tasks/Tx-*.notes.md`, commit per phase (never pushing), and keep `kanban.md` and `handoff.md` current. Batch independent work and compatible fixes without merging task verdicts. Final implementation review uses `impl-review` when authorized; otherwise record it as the next step. `/geeky-status <folder>` remains the lightweight status follow-up.
