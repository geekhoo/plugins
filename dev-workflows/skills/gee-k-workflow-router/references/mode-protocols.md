# Mode Protocols

## REVIEW

Inspect current files. Report findings first. Cite file/line evidence. Do not edit unless explicitly asked.

## IMPLEMENT

Inspect scope and dirty state. Build validation matrix. Edit only allowed paths. Validate. Report changed paths and risks.

## READ-ONLY

No file edits, generated artifacts, staging, commits, or source changes. Return findings in chat unless the user approves output files.

## STATUS/RESUME

Inspect git status, task files, handoff files, prior outputs, changed paths, and validation state. Report briefly and continue unless blocked or told to stop.

## VALIDATION

Run static/build/unit/contract/integration/browser/manual/doc-command checks as applicable. Report exact commands and results.

## BROWSER/UI

Start app only when command is known or discovered. Validate routes, console, screenshots, desktop/mobile, and user workflows. Do not infer UI readiness from backend tests.

## PLANNING/HANDOFF

Produce spec/tasks/kanban/handoff only when requested. Validate internal consistency. Do not call planning artifacts shipped behavior.

## EXTERNAL-TOOL

Preflight binary, help/version, auth, env vars, paths, branch/upstream, writable roots, and wrappers. Do not batch before preflight.

## PARALLEL-SUBAGENT

Define roles, write scopes, shared read-only files, integration owner, and validation. Integrate outputs before final reporting.
