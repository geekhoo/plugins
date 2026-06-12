---
allowed-tools: "*"
argument-hint: spec topic or number (e.g. "spec-009 notifications" or a plain description)
description: Research a new spec with a parallel 3-subagent team, then write feature-specification.md + README stub in docs/
---

Invoke the **`spec-research`** skill, passing along `$ARGUMENTS` (a spec topic, number, or plain description — if missing, ask the user what the spec should cover).

The skill contains the full procedure: deploy 3 parallel research subagents (codebase analysis, web best practices, architecture patterns), synthesize findings into a complete `feature-specification.md` requirements document plus a README stub in `docs/`. It writes the spec itself — not the implementation plan. After it completes, suggest `/geeky-plan <folder>` to turn the spec into a planning package.
