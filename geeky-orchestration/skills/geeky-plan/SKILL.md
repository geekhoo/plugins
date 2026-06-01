---
name: geeky-plan
description: Planning phase of the geeky orchestration workflow. Turns research/specification artifacts into an implementation plan, self-contained task files, a development-PM review, a kanban board, references, and a handoff. Use when asked to plan a feature, break a spec into tasks, or set up a kanban/handoff package before implementation. Invoked by the /geeky-plan command and usable directly by any agent.
---

# geeky-plan

Create a set of plan / tasks / Kanban based on provided research and specification requirements.

This is the *planning* phase. After this run, use the `geeky-implement` skill (or `/geeky-implement <folder>`) to execute the plan, or the `geeky-status` skill (or `/geeky-status <folder>`) to inspect state.

## Input

`<requirement>`: a user-provided specification, design file, research files, or a folder path specifying all of these. **IF MISSING, ask the user for it/them.** Throughout this document, references to `$ARGUMENTS` mean this requirement input.

## Constitution

**DO THIS SEQUENTIALLY IN THIS ORDER**, all work and artifacts to be done and saved within the provided folder `$ARGUMENTS`, OR same folder of the requirements/research files.

## Tasks

1. Build an implementation plan to satisfy all requirements in `$ARGUMENTS`.

2. Save completed implementation plan to a markdown file `implementation-plan.md`.

3. Deep-dive into the implementation plan and analyse it thoroughly to break it down into tasks.

4. Create task markdown files using the canonical task template bundled with this plugin at `${CLAUDE_PLUGIN_ROOT}/templates/task_template.md` (where `${CLAUDE_PLUGIN_ROOT}` is the root of the `geeky-orchestration` plugin). If for any reason that file cannot be read, fall back to the inline template below — but prefer the bundled one. A task must be clearly defined and self-contained. Each task includes tests to validate and verify the task BEFORE proceeding to the next task. Consider the order of the tasks, and name each task file with prefix `Tx-taskname` where `x` is the order number. Tests can be a separate file or within the task file itself.

    Inline fallback template:

    ```markdown
    Task Name:
    [Clear action-based title]

    Context:
    [Why this task exists, what feature/user flow it supports]

    Scope:

    In scope:
    ---
    - [What is being changed and where]

    ## Out of scope:
    - [What is intentionally NOT being changed]

    Module/System:
    [Where this belongs]

    ## Dependencies:

    * [Tx-task-name or None]

    ## Technical Notes:
    - [Constraints, invariants, links to plan sections]

    ## Acceptance Criteria:

    *
    *

    Definition of Done:

    * Code reviewed
    * Tested (manual/unit)
    * Deployed to staging
    * No critical bugs

    Tests/Validation Before Next Task:
    - [Exact commands that must pass]

    Estimate:
    [S/M/L]

    Priority:
    [P0/P1/P2]
    ```

5. **MUST** make sure you do not miss anything — write `draft.md` to disk first. After writing, read `draft.md` to verify the tasks have full coverage of the implementation to meet all requirements.

6. Request/delegate the development project manager agent to review the plan + tasks as a whole as we prepare for development work. Intelligently resolve all gaps but note them inside the review document.

7. Create a Kanban markdown `kanban.md` for tracking task progress. Standard lanes: Backlog, Ready, In Progress, Blocked, In Review, Done, plus a Validation Checklist (release gate). Place every newly-created task in **Ready** unless an explicit dependency keeps it in Backlog.

8. Create a markdown `references.md` containing references to the design docs, the plan, the task files, the tests, the kanban — with full descriptions and instructions for implementation. Double-check that nothing is missing.

9. Create/Update `handoff.md` with a brief and detailed summary of this session's work, plus preparation and instructions for the next session. Explicitly recommend `geeky-implement <folder>` (the `geeky-implement` skill / `/geeky-implement` command) as the next-session entry point.

10. **Validation gate — run the deterministic checks before declaring the plan done.** Do not rely on your own judgment that the package is complete; run the bundled validators and fix until each exits 0 (`${CLAUDE_PLUGIN_ROOT}` is the plugin root; use the `.ps1` form on Windows, the `.py` form elsewhere; see `AGENTS.md` / `geeky.manifest.json` for the full invocation matrix):

    - Task-file schema: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"`
    - Kanban integrity: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"`
    - Planning-folder completeness: `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"`

    If any exits non-zero, read its output, correct the artifact, and re-run until green. Only then finalize.

## Acceptance criteria

1. `implementation-plan.md`
2. `tasks/` folder with `Tx-taskname.md` files
3. Development Project Manager review of plan + tasks (saved as `review-development-project-manager.md` or similar)
4. `kanban.md`
5. `references.md`
6. `handoff.md`

You may create MORE than these.
