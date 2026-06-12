---
allowed-tools: "*"
argument-hint: folder path holding the geeky-plan output (defaults to most recent docs/ planning folder)
description: 4-phase quality review of a geeky-plan package — alignment, issue resolution, sequencing, sanity pass
---

Invoke the **`plan-review`** skill, passing along `$ARGUMENTS` (a planning package folder produced by `/geeky-plan` — if missing, scan `docs/` for the most recent folder containing an `implementation-plan.md`).

The skill contains the full procedure: a 4-phase review of the planning package — document alignment, issue resolution, sequencing validation, and a final sanity pass — using subagents for thoroughness. After it completes, suggest `/geeky-implement <folder>` if the plan is ready, or rerun `/geeky-plan` if structural problems were found.
