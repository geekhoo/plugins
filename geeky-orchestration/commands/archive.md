---
allowed-tools: "*"
argument-hint: completed spec folder or spec number (e.g. docs/spec-007-infrastructure/ or "spec-007")
description: Archive a completed spec's planning artifacts and finalize its permanent docs structure
---

Invoke the **`archive`** skill, passing along `$ARGUMENTS` (a completed spec folder or spec number — if missing, ask the user which spec to archive).

The skill contains the full procedure: move the planning artifacts to `archives/`, create the permanent `docs/spec-NNN-name/` folder with the spec document, handoff, and a README, and update the CLAUDE.md current-state section. Only run this when the spec is fully implemented and concluded — use `/geeky-status <folder>` first if unsure.
