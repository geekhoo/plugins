---
name: geeky-plan
description: Use when asked to turn a specification folder into a frozen implementation package. This skill creates implementation-plan.md, tasks, kanban, references, and handoff artifacts, runs planning gates, and outputs a package ready for `/geeky-implement`.
---

# geeky-plan

Create a set of plan / tasks / Kanban based on provided research and specification requirements.

This is the _planning_ phase. After this run, use the `plan-review` skill (or `/plan-review <folder>`) to audit the package, then the `geeky-implement` skill (or `/geeky-implement <folder>`) to execute it, or the `geeky-status` skill (or `/geeky-status <folder>`) to inspect state.

## Input

`<requirement>`: a user-provided specification, design file, research files, or a folder path specifying all of these. **IF MISSING, ask the user for it/them.** Throughout this document, references to `$ARGUMENTS` mean this requirement input.

## Constitution

**DO THIS SEQUENTIALLY IN THIS ORDER.** Resolve the working folder deterministically: if `$ARGUMENTS` is a folder path, use it; if it is one or more file paths, use the directory containing them; if it is a plain-text requirement with no files, ask the user for (or propose) a feature folder, e.g. `docs/<feature-name>/`, before creating any artifact. Save all artifacts in that folder.

## Tasks

1. Build an implementation plan to satisfy all requirements in `$ARGUMENTS`.

2. Save completed implementation plan to a markdown file `implementation-plan.md`.

3. Deep-dive into the implementation plan and analyse it thoroughly to break it down into tasks.

4. Create task markdown files using the canonical task template bundled with this plugin at `${CLAUDE_PLUGIN_ROOT}/templates/task_template.md` (where `${CLAUDE_PLUGIN_ROOT}` is the root of the `geeky-orchestration` plugin). If for any reason that file cannot be read, fall back to the inline template below — but prefer the bundled one. A task must be clearly defined and self-contained. Each task includes tests to validate and verify the task BEFORE proceeding to the next task. Consider the order of the tasks, and name each task file with prefix `Tx-taskname` where `x` is the order number **starting at T1** (e.g., `T1-setup-database.md`, `T2-implement-auth.md`). Tests can be a separate file or within the task file itself.

   Inline fallback template (keep in sync with `templates/task_template.md` — the bundled template is canonical):

   ```markdown
   Task Name:
   [Clear action-based title]

   Context:
   [Why this task exists, what feature/user flow it supports]

   Scope:

   ## In scope:

   - [What is being changed and where]

   ## Out of scope:

   - [What is intentionally NOT being changed]

   Module/System:
   [Where this belongs]

   ## Dependencies:

   - [Tx-task-name or None]

   ## Technical Notes:

   - [Constraints, invariants, links to plan sections]

   ## Acceptance Criteria:

   -
   -

   Definition of Done:

   - Code reviewed
   - Tested (manual/unit)
   - Deployed to staging
   - No critical bugs

   Tests/Validation Before Next Task:

   - [Exact commands that must pass]

   Estimate:
   [S/M/L]

   Priority:
   [P0/P1/P2]
   ```

5. **Coverage check — MUST not miss anything.** Write `draft.md` to disk: a coverage matrix mapping every requirement in `$ARGUMENTS` to the task(s) that satisfy it. Use this exact format:

   ```markdown
   # Coverage Matrix

   | Requirement ID | Requirement Summary | Covered by Task(s) | Status |
   |----------------|---------------------|-------------------|--------|
   | REQ-001        | User authentication | T1, T2            | ✓      |
   ```

   Required columns: Requirement ID, Requirement Summary, Covered by Task(s), Status. Each requirement must have at least one task; each task must trace to at least one requirement. Then read `draft.md` back and verify completeness. Fix gaps before proceeding.

6. Delegate a PM-style review of the plan + tasks as a whole. **Reviewer selection order (first match wins):**
   1. A `development-project-manager` agent if available in the environment
   2. A `planning-coordinator` agent if available
   3. A general-purpose subagent briefed with explicit PM-review instructions
   4. Perform the review directly in a dedicated pass

   The review must check coverage, sequencing, dependency correctness, and scope gaps. Save the result as `review-development-project-manager.md` (exact filename — downstream skills look for it). Intelligently resolve all gaps but note them inside the review document.

7. Create a Kanban markdown `kanban.md` for tracking task progress. Standard lanes: Backlog, Ready, In Progress, Blocked, In Review, Done, plus a Validation Checklist (release gate). Place every newly-created task in **Ready** unless an explicit dependency keeps it in Backlog.

8. Create a markdown `references.md` containing references to the design docs, the plan, the task files, the tests, the kanban — with full descriptions and instructions for implementation. Double-check that nothing is missing.

9. Create/Update `handoff.md` with a brief and detailed summary of this session's work, plus preparation and instructions for the next session. Explicitly recommend `plan-review <folder>` (the `plan-review` skill / `/plan-review` command) as the next step to audit the package, and `geeky-implement <folder>` after it passes.

10. **Validation gate — run the deterministic checks before declaring the plan done.** Do not rely on judgment alone that the package is complete; run the bundled validators and fix until each exits 0 (`${CLAUDE_PLUGIN_ROOT}` is the plugin root; see `AGENTS.md` / `geeky.manifest.json` for the full invocation matrix):
    - Task-file schema: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"`
    - Kanban integrity: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"`
    - Planning-folder completeness: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"`

    The `python` form works cross-platform; if Python is unavailable, use the paired PowerShell scripts, e.g. `pwsh -NoProfile -File "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.ps1" -Path "<folder>"` (same pattern for the other two).

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

These artifacts form the frozen contract between planning and implementation: after this skill completes, `implementation-plan.md`, `references.md`, and `tasks/Tx-*.md` (plus `feature-specification.md` and `draft.md` if present) are guarded against edits by the bundled PreToolUse hook. Downstream sessions record per-task notes in `tasks/Tx-*.notes.md` instead; `kanban.md` and `handoff.md` stay mutable. During this planning session, guard warnings on these files are expected while iterating to green.
