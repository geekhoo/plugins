---
name: gee-k-workflow-router
description: Route Gee.K work to the right workflow, skill, agent role, and validation protocol. Use when the task involves review, implementation, validation, resume/status, read-only scope, planning/handoff, browser/UI, external tools, subagents, plugin/skill lifecycle, docs/AGENTS refresh, corpus work, observability, or recurring friction around evidence, validation, scope, shipped-vs-planning, memory, and environment assumptions.
---

# Gee.K Workflow Router

Use this skill to select the correct workflow before doing task work.

## Core Rule

Classify the task mode first, then activate the matching existing skill or protocol. Do not duplicate existing skills when one already covers the work.

## Fast Mode Selection

- REVIEW: read `references/mode-protocols.md`, then use `dev-workflows:evidence-review` or `review`.
- IMPLEMENT: use `implement` or the repo's implementation skill, then apply validation and scope rules.
- READ-ONLY: use `dev-workflows:scope-guard` first.
- STATUS/RESUME: use `dev-workflows:resume-inventory` or `dev-workflows:status-interrupt`.
- VALIDATION: use `dev-workflows:repo-validation-runner`.
- BROWSER/UI: use `browser-verify`, `playwright-testing`, or `dev-workflows:browser-qa`.
- PLANNING/HANDOFF: use `dev-workflows:planning-packet`, `geeky-orchestration:geeky-plan`, or `geeky-orchestration:plan-review`.
- EXTERNAL-TOOL: run environment/tool preflight before batch work.
- PARALLEL-SUBAGENT: use `dev-workflows:parallel-review-orchestrator` or `geeky-orchestration:geeky-implement`.

Read `references/activation-map.md` when the trigger is ambiguous.

Read `references/agent-roles.md` before dispatching subagents.

## Mandatory Defaults

1. Inspect current files before claims.
2. Preserve unrelated user or agent changes.
3. Treat read-only and do-not-edit as hard constraints.
4. Build validation expectations before implementation.
5. Separate confirmed, inferred, not found, and blocked.
6. Treat planning artifacts as planning evidence only.
7. Verify external commands, auth, env vars, paths, branch/upstream, and writable roots before batch operations.
8. Close with changed paths, validation, validation not run, risks, assumptions, and next action.

## Stop Conditions

Stop or ask when:
- Write permission is unclear.
- Scope is insufficient.
- Required credentials or external access are missing.
- A durable output file would violate read-only mode.
- Concurrent changes make safe editing unclear.
- The task asks for launch/readiness but required runtime or browser validation is blocked.
