# Environment defaults & intervention levels

Supporting reference for `pragmatic-scope-guard`.

## Environment Defaults

- Use the dedicated Grep/Glob/Read/Edit tools for search and patching; PowerShell (quoted paths) for git and commands.
- Use the session scratchpad for temporary assets, never the repo; `outputs/` only for user-facing deliverables.
- Author durable skills/plugins in `C:\Users\gerald.khoo\geekhoo-plugins`; do not alter `~\.claude\plugins\cache\` or global hooks unless requested.
- Respect phased delivery: if the request names steps ("do 1 2 3, defer 4"), implement exactly those steps and stop.
- For UI work, analyze the Figma node first (file key `f23wB7B5Sq16GncjfLNEYL`) and verify with browser evidence when the app needs runtime rendering.
- For ProgramsV2 grid work, scope includes the full CSS/JS interdependency set for the touched columns — that is required scope, not creep.

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
