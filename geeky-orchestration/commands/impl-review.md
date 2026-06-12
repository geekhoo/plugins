---
allowed-tools: "*"
argument-hint: spec folder, diff reference, or branch (defaults to uncommitted changes or most recent spec folder)
description: Review delivered implementation work with 3 dynamically-chosen domain-expert subagents
---

Invoke the **`impl-review`** skill, passing along `$ARGUMENTS` (a spec folder path, diff reference like `HEAD~5..HEAD`, or branch name — if missing, use the current uncommitted changes or the most recent spec folder).

The skill contains the full procedure: select 3 domain-expert reviewer subagents based on what was actually built (each covering a distinct, non-overlapping aspect), run them against the delivered code, and present a unified report. Critical findings are fixed only with user approval. This reviews delivered code — for reviewing planning documents before implementation, use `/plan-review` instead.
