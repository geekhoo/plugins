---
name: plugin-skill-lifecycle
description: Use when the user asks to "create, install, or enable a plugin or skill", "evaluate or benchmark a plugin", "debug the plugin cache or marketplace", or "run quick_validate" — manage the plugin and skill lifecycle end to end.
---

# Plugin Skill Lifecycle

## Overview

Use this skill for evidence-first plugin and skill lifecycle work. Preserve current local paths, Windows-compatible fallbacks, and user-owned changes while producing validation evidence.

## Prerequisites And Clarification

- Inspect the named plugin, skill, marketplace, cache, or target path before acting.
- Ask where to create a new skill only when the user did not specify a path; default to the auto-discovered skills path only when appropriate.
- Ask before installing, enabling, publishing, or writing outside the requested path.
- If plugin or skill availability is unknown, use `capability-inventory` first.
- If discovering new reusable skill opportunities from past sessions, use `codex-session-request-mining`.

## Workflow

1. Define the lifecycle action: create, install, enable, evaluate, benchmark, debug, update, or validate.
2. Inventory current evidence: local paths, `SKILL.md`, plugin metadata, marketplace entries, cache IDs, validation scripts, and documented commands.
3. Record allowed write scope and protected paths before editing or installing anything.
4. Use official init, generation, validation, or plugin-eval tooling when present.
5. If a literal CLI is missing, derive any Windows substitute or fallback from current local docs, scripts, or metadata; do not invent commands.
6. Execute the requested lifecycle operation inside the allowed scope.
7. Validate with `quick_validate.py`, plugin eval, targeted tests, or a stated reason when a gate is not applicable.
8. Report created, installed, enabled, evaluated, updated, and validated state with command evidence.

## Verification Gates

- G0 Scope gate: target plugin or skill, action, write scope, and external-system permissions are known.
- G1 Evidence gate: current path, metadata, scripts, docs, or source references have been inspected.
- G2 Plan gate: lifecycle steps and expected outputs are explicit before writes or installs.
- G3 Execution gate: changes remain inside the allowed scope and preserve unrelated work.
- G4 Validation gate: `quick_validate.py`, plugin eval, or targeted checks run, or the skip reason is explicit.
- G5 Reporting gate: final output includes changed files, commands, results, assumptions, and unresolved risks.

## Acceptance Criteria

- Skill frontmatter and triggers are correct when creating or updating a skill.
- Plugin or skill paths are current and not stale cache IDs unless the cache path is the intended target.
- Installation or enablement state is verified from current local evidence.
- Evaluation, benchmark, or validation results are reported with exact commands.
- No marketplace files, sibling skills, or plugin configuration files are changed unless explicitly in scope.

## Expected Outcome

A created, installed, enabled, evaluated, benchmarked, debugged, updated, or validated plugin or skill with clear path evidence and validation results.

## Common Mistakes

- Using memory or old cache IDs instead of inspecting the current filesystem.
- Treating a missing CLI as permission to guess a fallback command.
- Installing or enabling a plugin without explicit user approval.
- Editing marketplace files or sibling skill folders when the requested scope is narrower.
- Claiming success without running the relevant validator or explaining why it could not run.
