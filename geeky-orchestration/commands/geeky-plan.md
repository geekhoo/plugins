---
allowed-tools: "*"
argument-hint: include research and spec, or folder holding these artifacts
description: geeky version of creating plan and tasks and Kanban orchestration
---

Invoke the **`geeky-plan`** skill to run the planning phase, passing along `$ARGUMENTS` as the requirement input (a specification, design file, research files, or a folder path holding them — if missing, ask the user for it).

The skill contains the full procedure: build `implementation-plan.md`, break it into self-contained `tasks/Tx-*.md` files, get a development-PM review, and produce `kanban.md`, `references.md`, and `handoff.md`. After it completes, suggest `/geeky-implement <folder>` to execute, or `/geeky-status <folder>` to inspect state.
