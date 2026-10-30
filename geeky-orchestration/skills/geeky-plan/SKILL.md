---
name: geeky-plan
description: Use when asked to turn a specification folder into a frozen implementation package. This skill creates implementation-plan.md, tasks, kanban, references, and handoff artifacts, runs planning gates, and outputs a package ready for `/geeky-implement`.
---

Use the shared [workflow terminology](../../AGENTS.md#workflow-terminology).

# geeky-plan

Create a set of plan / tasks / Kanban based on provided research and specification requirements.

This is the _planning_ phase. After this run, use the `plan-review` skill (or `/plan-review <folder>`) to audit the package, then the `geeky-implement` skill (or `/geeky-implement <folder>`) to execute it, or the `geeky-status` skill (or `/geeky-status <folder>`) to inspect state.

## Input

`<requirement>`: a user-provided specification, design file, research files, or a folder path specifying all of these. **IF MISSING, ask the user for it/them.** Throughout this document, references to `$ARGUMENTS` mean this requirement input.

## Constitution

**DO THIS SEQUENTIALLY IN THIS ORDER.** Resolve the working folder deterministically: if `$ARGUMENTS` is a folder path, use it; if it is one or more file paths, use the directory containing them; if it is a plain-text requirement with no files, ask the user for (or propose) a feature folder, e.g. `docs/<feature-name>/`, before creating any artifact. Save all artifacts in that folder.

## Time budget and checkpoint

At entry, run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/workflow-budget.py" --stage geeky-plan --json`.
Recheck before each phase or dispatch batch and when a blocking wait returns; a
check made earlier in the same turn covers it, and consecutive direct operations
need no recheck between them. Each shell call has a fixed startup cost (about 8 s
in a sandbox), so make rechecks with the `geeky_workflow_budget` MCP tool when it
is available (same report), or chain the script with the next command.
Resolve `${CLAUDE_PLUGIN_ROOT}` to the installed plugin root containing this skill
when the environment variable is unset, and use an available Python interpreter.
If the helper cannot run or its output is unreadable, stop and report the missing
budget check; do not assume unlimited time. Read the JSON status, not just the
exit code: `unbounded` means no deadline was provided; `active` continues; `reserve` or `exhausted` stops starting new work
and checkpoints the incomplete stage; `invalid` stops and reports the configuration
error. A zero exit also covers `reserve`, so it is not permission to continue.
The stage target is advisory, not a gate or guarantee: after it is exceeded,
finish required work with the smallest sufficient evidence and defer optional
expansion. Never skip a required review, validator or acceptance condition, or
claim an incomplete stage passed. Pass the hard deadline, closeout reserve, and
stage target from the check to every child brief. If the deadline is absent, say
unbounded; if only the target is absent, say the target is unavailable. Do not
invent either value. Tell each child to return its current evidence,
unresolved questions and status before the available work time ends. Bound waits by
the remaining usable time where the host supports it; if it cannot, record that
limitation rather than claiming cancellation. Recheck after a wait; a child report alone does not override the budget result.

If the budget stops this stage, record missing artifacts, reviews and validators in the handoff; do not declare the package complete or frozen.

## Tasks

1. Build an implementation plan to satisfy all requirements in `$ARGUMENTS`.

2. Save completed implementation plan to a markdown file `implementation-plan.md`.

3. Deep-dive into the implementation plan and analyse it thoroughly to break it down into tasks.

4. Create task markdown files using the canonical task template bundled with this plugin at `${CLAUDE_PLUGIN_ROOT}/templates/task_template.md` (where `${CLAUDE_PLUGIN_ROOT}` is the root of the `geeky-orchestration` plugin). If for any reason that file cannot be read, fall back to the inline template below — but prefer the bundled one. A task must be clearly defined and self-contained. Each task includes tests to validate and verify the task BEFORE proceeding to the next task. Consider the order of the tasks, and name each task file with prefix `Tx-taskname` where `x` is the order number **starting at T1** (e.g., `T1-setup-database.md`, `T2-implement-auth.md`). Tests can be a separate file or within the task file itself.

   If the bundled template is unreadable, use the inline fallback in
   `references/task-template-fallback.md` (kept in sync with `templates/task_template.md`;
   the bundled template is canonical).

   Each task's Tests/Validation block must contain a check for every one of that task's acceptance criteria, including required error status, streams and wording. Tests may live in a separate file, but the task must run them before it advances; a test that exists only in a later task does not count as evidence for an earlier one. Expected outputs and messages, including error text and their matching predicates, must quote the source requirement verbatim; do not paraphrase them or loosen a positional condition (prefix, suffix, exact line).

5. **Coverage check — MUST not miss anything.** Write `draft.md` to disk: a `# Coverage Matrix` table mapping every requirement in `$ARGUMENTS` to the task(s) that satisfy it. Required columns (exact): Requirement ID, Requirement Summary, Covered by Task(s), Status. Each requirement must have at least one task; each task must trace to at least one requirement. Then read `draft.md` back and verify completeness. Also self-check each task's acceptance criteria against its own validation block: every criterion needs a check that can run before the task advances, without relying on tests added only by a later task. Verify expected outputs, messages and their predicates against the source requirement verbatim. Fix gaps before proceeding.

6. Delegate a PM-style review of the plan + tasks as a whole. **Reviewer selection order (first match wins):**
   1. A `development-project-manager` agent if available in the environment
   2. A `planning-coordinator` agent if available
   3. A general-purpose subagent briefed with explicit PM-review instructions
   4. Perform the review directly in a dedicated pass

   The review must check coverage, sequencing, dependency correctness, and scope gaps. For every task, require a check in its own validation block for every acceptance criterion; later-task-only tests are not evidence for an earlier task. Check that expected outputs, messages and matching predicates quote the source requirement verbatim. Request actionable findings with requirement/task references and a concise verdict; avoid restating the package. Record suggestions separately from required fixes. Save the result as `review-development-project-manager.md` (exact filename — downstream skills look for it). Intelligently resolve all gaps but note them inside the review document.

7. Create a Kanban markdown `kanban.md` for tracking task progress. Standard lanes: Backlog, Ready, In Progress, Blocked, In Review, Done, plus a Validation Checklist (release gate). Place every newly-created task in **Ready** unless an explicit dependency keeps it in Backlog.

8. Create a markdown `references.md` containing references to the design docs, the plan, the task files, the tests, the kanban — with full descriptions and instructions for implementation. Double-check that nothing is missing.

9. Create/Update `handoff.md` with a brief and detailed summary of this session's work, plus preparation and instructions for the next session. Explicitly recommend `plan-review <folder>` (the `plan-review` skill / `/plan-review` command) as the next step to audit the package, and `geeky-implement <folder>` after it passes.

10. **Validation gate — run the deterministic checks before declaring the plan done.** Do not rely on judgment alone that the package is complete; run the bundled validators and fix until each exits 0 (`${CLAUDE_PLUGIN_ROOT}` is the plugin root; see `AGENTS.md` / `geeky.manifest.json` for the full invocation matrix):
    - Task-file schema: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"`
    - Kanban integrity: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"`
    - Planning-folder completeness: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"`

    The `python` form works cross-platform; if Python is unavailable, use the paired PowerShell scripts, e.g. `pwsh -NoProfile -File "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.ps1" -Path "<folder>"` (same pattern for the other two).

    Gate calls: each shell call pays a fixed startup cost (about 8 s in a sandbox). When the `geeky_*` MCP gate tools are in your tool list and run without a permission prompt, use them; they wrap the same scripts and return the same reports. Otherwise chain the validators in one shell call. Re-run a validator only after its inputs changed since its last pass.

    If any exits non-zero, read its output, correct the artifact, and re-run until green. Only then finalize.

## Acceptance criteria

1. `implementation-plan.md`
2. `tasks/` folder with `Tx-taskname.md` files
3. PM review of plan + tasks (saved as `review-development-project-manager.md` — exact filename)
4. `kanban.md`
5. `references.md`
6. `handoff.md`

Additional artifacts may be created beyond these.

## Frozen planning contract

The planning contract freezes once plan-review completes its final verdict, and stays frozen from geeky-implement onward. Until then, plan-review may correct `implementation-plan.md`, `draft.md`, `references.md`, and `tasks/Tx-*.md`; each correction follows plan-review's invalidation rules. A bounded mechanical fix needs a changed-content/reference check; scope, requirement, AC or sequencing edits need a fresh affected verdict. `feature-specification.md` stays frozen except for mechanical fixes. Downstream implementation sessions record per-task notes in `tasks/Tx-*.notes.md` instead; `kanban.md` and `handoff.md` stay mutable. Missing or unknown guard stage keeps the default frozen classification; the plan-review skill supplies its stage explicitly when correcting the package.
