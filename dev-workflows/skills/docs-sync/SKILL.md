---
name: docs-sync
description: Use when the user asks to "sync the docs", "refresh the README", "write a runbook", "update AGENTS or docs", or "document repo behavior"; align documentation with current repository behavior from source evidence, without inventing commands.
---

# Docs Sync

## Overview

Keep documentation aligned with current repository behavior. Treat source files, scripts, manifests, test configs, and existing linked docs as evidence; never invent commands or imply absent workflows exist.

## Prerequisites And Clarification

- Identify the target docs, audience, and linked documents that share contracts.
- Inventory source evidence before editing: code paths, scripts, manifests, test configs, current docs, runbooks, packet docs, and setup files.
- Check for protected paths, no-edit markers, user-owned changes, and stale generated artifacts before editing.
- Ask when the audience, format, or target doc set is unclear.
- Ask before replacing large docs unless the user requested a rewrite.
- Do not ask when the expected target is explicit and repo evidence is available.

## Workflow

1. Map documentation boundaries.
   - Find all docs that describe the same workflow, command, setup step, API, or artifact contract.
   - Note legacy/current splits, planning-only docs, shipped docs, and linked packet files before editing.
2. Derive behavior from source evidence.
   - Use real scripts, manifests, package files, CI/test configs, app entrypoints, schemas, and code paths.
   - Map every command reference to an existing script/file, or state that the workflow is absent.
   - Prefer concise operational wording over general process advice.
3. Update linked docs together.
   - Keep command names, environment variables, paths, workflow stages, artifact names, and validation expectations consistent across shared docs.
   - Preserve documented scope boundaries; do not expand a workflow beyond the evidence or the user's request.
4. Validate practical claims.
   - Run safe documented commands when practical.
   - If a command is risky, slow, environment-dependent, or unavailable, cite the source evidence inspected and state why it was not run.
5. Report the result.
   - List docs changed, evidence inspected, validation run, and any commands or workflows marked absent.

## Verification Gates

| Gate | Requirement |
| --- | --- |
| G0 | Doc targets and audience are known, or clarification was requested. |
| G1 | Source evidence was inspected before editing. |
| G2 | Shared contracts across linked docs were identified. |
| G3 | Edits stayed within target docs and allowed linked docs. |
| G4 | Command references map to real scripts/files or are marked absent. |
| G5 | Final report lists docs changed and validation run. |

## Acceptance Criteria

- No invented commands, paths, environment variables, workflows, or validation steps.
- No stale contradictions across linked docs that share the same contract.
- Missing or unsupported workflows are stated plainly.
- Updated docs reflect current repo behavior with validated or evidence-derived commands.

## Expected Outcome

Documentation is current, internally consistent, and operational: another agent or developer can follow it without guessing which commands, files, or workflows are real.

## Companion Skills

- If available, use `docs-command-auditor` when the main risk is command drift across docs and scripts.
- If available, use `planning-packet` when the docs are part of a spec, tasks, kanban, references, and handoff packet.

## Common Mistakes

- Editing docs from memory before reading the current repo.
- Reusing plausible commands from similar projects without mapping them to this repo.
- Updating one doc while leaving linked docs with stale names, paths, or stage descriptions.
- Omitting absent workflows because they feel like negative information.
- Reporting that docs were refreshed without listing evidence inspected and validation performed.
