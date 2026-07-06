---
name: pragmatic-scope-guard
description: Use when implementation work risks over-engineering, scope creep, unnecessary files, new dependencies, broad refactors, drive-by formatting, or unrequested tests/docs/config — or when the user signals "only change X", "keep it simple", "too much", "don't change that", "read only", "follow existing convention", or "stop".
---

# Pragmatic Scope Guard

Use restraint as an engineering control, not as an excuse to under-deliver. The goal is the smallest change that genuinely handles the user's request, with enough evidence to trust it.

Distinct from `scope-guard` (which records allowed/protected edit paths) and `minimal-change-patch` (a recipe for one known small fix): this skill is the standing discipline against over-engineering across a whole task.

## Operating Rules

1. Honor the user's named scope.
   - Treat explicit files, folders, workflows, packet IDs, issue IDs, and artifact names as the scope contract.
   - If the user says read-only, orientation, review, or plan, do not edit files.
   - If the user names a workflow skill (`geeky-plan`, `geeky-implement`, `handoff`, etc.), load and follow it before inventing a process.

2. Prefer the smallest working implementation.
   - Reuse local patterns and helpers before adding new abstractions — in Markefin repos this means existing `Markefin.*` namespaces, MediatR handler conventions, and DevExtreme option patterns already in the file.
   - Keep code where the existing codebase would expect it.
   - Avoid new files, dependencies, config, framework changes, or generated scaffolds unless the request requires them.
   - Avoid drive-by formatting, import sorting, renames, comment rewrites, or cleanup unrelated to the task.
   - No structural changes unless explicitly asked — "follow existing convention" is the standing default.

3. Verify without expanding scope.
   - Run focused validation for changed behavior whenever practical: targeted `dotnet build`/`dotnet test --filter`, a browser check for UI, or a small runtime probe.
   - Do not add a test suite, fixture framework, docs page, or CI config unless the user asked or the risk justifies it.
   - If validation is blocked by host/tooling problems, report the exact blocker and separate it from repo defects.

4. Preserve user work.
   - Check `git status` before edits when working in a repo.
   - Never revert changes you did not make unless the user explicitly requests it.
   - If unrelated changes exist, ignore them; if they affect the task, work with them and explain the constraint.

5. Ask only at real decision points.
   - Ask before adding a dependency, changing public contracts, broadening a refactor, deleting code, or touching unrelated files.
   - When a reasonable, low-risk assumption keeps the task moving, make it and state it briefly. Do not add confirmation gates to work that was already requested — deliver in the same turn.

## Environment Defaults

- Use the dedicated Grep/Glob/Read/Edit tools for search and patching; PowerShell (quoted paths) for git and commands.
- Use the session scratchpad for temporary assets, never the repo; `outputs/` only for user-facing deliverables.
- Author durable skills/plugins in `C:\Users\gerald.khoo\geekhoo-plugins`; do not alter `~\.claude\plugins\cache\` or global hooks unless requested.
- Respect phased delivery: if the request names steps ("do 1 2 3, defer 4"), implement exactly those steps and stop.
- For UI work, analyze the Figma node first (file key `f23wB7B5Sq16GncjfLNEYL`) and verify with browser evidence when the app needs runtime rendering.
- For ProgramsV2 grid work, scope includes the full CSS/JS interdependency set for the touched columns — that is required scope, not creep.

## Scope Triage

Classify the task before editing:

- **Narrow fix:** one bug, one small UI change, one command, one file. Make the minimal edit and run the nearest focused check.
- **Workflow request:** named skill, packet, handoff, kanban, report, or plugin evaluation. Follow the named workflow and create only its expected artifacts.
- **Review or audit:** inspect and report findings first. Do not patch unless the user asks for remediation.
- **Build request:** implement the requested usable feature, but resist unrelated platform changes or decorative extras.
- **Ambiguous broad request:** do a short orientation pass, define the likely scope, then proceed only where the request is clear.

## Overreach Triggers

Stop and tighten the approach when any of these appear:

- The diff touches files the user did not mention and the task does not require them.
- A simple change grows into a new abstraction, service, wrapper, factory, interface, or helper folder.
- A package, SDK, build tool, formatter, or project config changes without explicit need.
- A one-line or one-function fix becomes a whole-file rewrite.
- Validation failures lead to cascading unrelated fixes.
- The final answer starts explaining unrelated improvements instead of the requested outcome.
- The user signals dissatisfaction with breadth, such as "too much", "only X", "don't change that", or "revert".

## Intervention Levels

### L1: Minor Drift

Trigger: small formatting, naming, comment, or import changes slipped into an otherwise scoped diff.

Action: remove the unrelated change; continue with the requested task.

### L2: Clear Scope Creep

Trigger: new files, extra docs/tests/config, broad helper extraction, or edits to unrelated modules.

Action: pause implementation, re-read the user request, keep only the smallest necessary change set, and ask before keeping anything outside the original scope.

### L3: Cascading Work

Trigger: one fix causes another unrelated fix, validation pushes into project-wide cleanup, or more than a few files change unexpectedly.

Action: stop the cascade, separate required blockers from opportunistic cleanup, and report the minimum path to finish the user's request.

### L4: User Course Correction

Trigger: the user says to stop, revert, keep it simple, or that the work is too much.

Action: stop editing, state what changed, identify which changes directly served the request, and revert your own unnecessary changes when safe — ask before any destructive operation.

## Delivery Check

Before the final response, confirm:

- The changed surface matches the user's request.
- No unrelated files, dependencies, config, docs, or generated assets were added.
- Existing local patterns were reused where practical.
- Verification was run, or the blocker is clearly reported.
- The final answer leads with outcome, changed files/artifacts, evidence, and remaining risk.
