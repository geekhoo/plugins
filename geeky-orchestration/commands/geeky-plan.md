---
allowed-tools: *
argument-hint: include research and spec, or folder holding these artifacts
description: geeky version of creating plan and tasks and Kanban orchestration
---

<requirement>

$ARGUMENTS: user provided specification, design file, research files, or a folder path specifying all these files. IF MISSING ask user for it/them.

</requirement>



<context>

To create a set of plan/tasks/Kanban based on provided research and specification requirements.

This command is the *planning* phase. After this run, use `/geeky-implement <folder>` to execute the plan, or `/geeky-status <folder>` to inspect state.

</context>



<constitution>

**DO THIS SEQUENTIALLY IN THIS ORDER**, all work and artifacts to be done and saved within the provided folder $ARGUMENTS, OR same folder of the requirements/research files.

</constitution>



<tasks>

1. Build an implementation plan to satisfy all requirements in $ARGUMENTS.

2. Save completed implementation plan to a markdown file `implementation-plan.md`.

3. Deep-dive into the implementation plan and analyse it thoroughly to break it down into tasks.

4. Create task markdown files using the canonical task template bundled with this plugin at `${CLAUDE_PLUGIN_ROOT}/templates/task_template.md`. If for any reason that file cannot be read, fall back to the inline template below — but prefer the bundled one. A task must be clearly defined and self-contained. Each task includes tests to validate and verify the task BEFORE proceeding to the next task. Consider the order of the tasks, and name each task file with prefix `Tx-taskname` where `x` is the order number. Tests can be a separate file or within the task file itself.

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

9. Create/Update `handoff.md` with a brief and detailed summary of this session's work, plus preparation and instructions for the next session. Explicitly recommend `/geeky-implement <folder>` as the next-session entry point.

</tasks>



<acceptance_criteria>

1. `implementation-plan.md`
2. `tasks/` folder with `Tx-taskname.md` files
3. Development Project Manager review of plan + tasks (saved as `review-development-project-manager.md` or similar)
4. `kanban.md`
5. `references.md`
6. `handoff.md`

You may create MORE than these.

</acceptance_criteria>
