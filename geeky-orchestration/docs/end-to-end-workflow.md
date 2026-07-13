# Geeky Orchestration End-to-End Workflow

This is the sequential operating guide for the `geeky-orchestration` workflow:

1. `spec-research`
2. `geeky-plan`
3. `plan-review`
4. `geeky-implement`
5. `impl-review`
6. `archive`

Use it as the canonical runbook for taking a feature from researched specification to implemented, reviewed, archived delivery.

---

## Global workflow contract

- Work from a feature/spec folder, normally `docs/<feature-folder>/`.
- Prefer numbered folders such as `docs/spec-NNN-<kebab-slug>/` when that convention exists.
- Keep artifacts in the feature folder until archive time.
- Use deterministic validation scripts whenever available; fix failures before proceeding.
- Treat `kanban.md` as the source of truth during implementation.
- Do not push to remote during implementation.
- Do not use `--amend`, `--force`, or `--no-verify`.
- Once planning is frozen, do not edit planning contract files during implementation:
  - `feature-specification.md`
  - `implementation-plan.md`
  - `draft.md`
  - `references.md`
  - `tasks/Tx-*.md`
- During implementation, write per-task execution notes to `tasks/Tx-*.notes.md` instead of editing the task body.

---

## 1. `spec-research` — research and author the feature specification

**Purpose:** Produce a researched feature specification and README scaffold before planning.

### Input

Accept either:

- a spec topic,
- a feature folder path,
- a plain-language feature description,
- or an existing stub such as `docs/<feature-folder>/README.md`.

### Steps

1. Resolve the feature folder.
   - If a folder path is supplied, use it.
   - Otherwise derive `docs/spec-NNN-<slug>/` from `CLAUDE.md ## Current State` when available.
   - If unavailable, inspect existing `docs/spec-*` folders and use highest number + 1.
   - If there is no clear convention and `docs/` is empty, ask the user to confirm the folder name.
2. Read any existing `README.md` stub and preserve its scope constraints.
3. Scan the codebase for existing patterns and integration points.
4. Define exactly 3 non-overlapping research angles.
5. Dispatch 3 researchers in parallel:
   - 1 codebase analyst using `geeky-orchestration:code-explorer`.
   - 2 web/domain researchers using `general-purpose` with web search/fetch instructions.
6. Require each researcher to report:
   - key findings,
   - constraints the spec must respect,
   - recommendations the spec should include,
   - sources as URLs or file paths,
   - and no file modifications.
7. Synthesize after all 3 reports complete.
8. Write:
   - `docs/<feature-folder>/feature-specification.md`
   - `docs/<feature-folder>/README.md`
9. Use `feature-specification.md` as the canonical specification filename. Do not create legacy `SPEC-NNNN-*.md` files.
10. Include assumptions and citations for major findings.
11. Commit the spec:

```bash
git add docs/<feature-folder>/
git commit -m "docs: author feature specification in <feature-folder>" \
  -m "<1-line summary of the spec focus>" \
  -m "Research conducted by: codebase analyst, researcher 2 domain, researcher 3 domain" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Required output state

- `feature-specification.md` exists.
- `README.md` exists or is updated.
- README status says the spec is written but not yet planned.
- The next recommended step is `geeky-plan docs/<feature-folder>/`.

---

## 2. `geeky-plan` — create the frozen planning package

**Purpose:** Convert the specification into a complete implementation package ready for implementation.

### Input

Accept a specification, design file, research files, plain requirement, or folder path. If the requirement input is missing, ask for it.

### Steps

1. Resolve the working folder deterministically.
   - Folder path: use it.
   - File path(s): use the containing directory.
   - Plain text only: ask for or propose a feature folder before creating artifacts.
2. Build an implementation plan satisfying all requirements.
3. Save it as `implementation-plan.md`.
4. Break the plan into self-contained ordered tasks.
5. Create task files under `tasks/`, named from `T1` onward, for example:
   - `tasks/T1-setup-database.md`
   - `tasks/T2-implement-auth.md`
6. Use `${CLAUDE_PLUGIN_ROOT}/templates/task_template.md` as the canonical task template. Fall back to the inline template only if the bundled template cannot be read.
7. Each task must include:
   - task name,
   - context,
   - in-scope and out-of-scope boundaries,
   - module/system,
   - dependencies,
   - technical notes,
   - acceptance criteria,
   - definition of done,
   - validation commands before the next task,
   - estimate,
   - priority.
8. Create `draft.md` as the coverage matrix with required columns:
   - Requirement ID,
   - Requirement Summary,
   - Covered by Task(s),
   - Status.
9. Verify every requirement maps to at least one task and every task maps to at least one requirement. Read `draft.md` back and fix gaps.
10. Run a PM-style review of the plan and tasks. Reviewer selection order:
    1. `development-project-manager`, if available.
    2. `planning-coordinator`, if available.
    3. `general-purpose` subagent with explicit PM-review instructions.
    4. Direct dedicated review pass.
11. Save the PM review exactly as `review-development-project-manager.md`.
12. Create `kanban.md` with lanes:
    - Backlog,
    - Ready,
    - In Progress,
    - Blocked,
    - In Review,
    - Done,
    - Validation Checklist.
13. Put every new task in Ready unless an explicit dependency keeps it in Backlog.
14. Create `references.md` linking the design docs, plan, task files, tests, kanban, and implementation instructions.
15. Create or update `handoff.md` with session summary, preparation, next-session instructions, and explicit recommendations to run `plan-review`, then `geeky-implement` after review passes.
16. Run validators and fix until all exit 0:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"
```

If Python is unavailable, use the paired PowerShell scripts under `${CLAUDE_PLUGIN_ROOT}/scripts/`.

### Required output state

The folder must contain:

- `feature-specification.md`
- `implementation-plan.md`
- `draft.md`
- `tasks/Tx-*.md`
- `review-development-project-manager.md`
- `kanban.md`
- `references.md`
- `handoff.md`

After this step, the planning package is the frozen implementation contract.

---

## 3. `plan-review` — audit planning package before implementation

**Purpose:** Validate that the planning package is aligned, complete, correctly sequenced, and ready for execution.

### Input

Accept a planning folder path. If missing, scan `docs/` for the most recent folder containing `implementation-plan.md`.

### Steps

#### Phase 1 — document alignment audit

1. Check whether validator scripts exist under `${CLAUDE_PLUGIN_ROOT}/scripts/`.
2. If available, run:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"
```

3. Treat non-zero validator exits as Critical findings.
4. Run semantic cross-validation over the entire planning folder, including:
   - `feature-specification.md`,
   - `draft.md`,
   - legacy `SPEC-NNNN-*.md` if present,
   - `implementation-plan.md`,
   - `kanban.md`,
   - `execution-schedule.md` if present,
   - all `tasks/T*.md`,
   - `handoff.md`,
   - `references.md`,
   - `review-development-project-manager.md`,
   - `README.md`.
5. Validate:
   - every planned task has a task file,
   - every kanban task matches the plan,
   - phase/wave/gate criteria are consistent when present,
   - dependencies are coherent and acyclic,
   - task validation blocks are achievable,
   - referenced files exist or are explicitly to be created,
   - requirements are covered,
   - no orphaned or phantom tasks exist.
6. Report findings as Critical, Warning, or Suggestion.

#### Phase 2 — issue resolution

1. Fix Critical issues immediately when mechanical and unambiguous.
2. Fix Warnings only when the correction is unambiguous.
3. Record Suggestions without blocking.
4. Do not change scope, goals, or priorities without user decision.
5. Re-run validators and re-check modified files.
6. If more than 5 files changed, or references/order/dependencies changed, repeat full Phase 1 review.

#### Phase 3 — sequencing and parallelization validation

1. Use `geeky-orchestration:code-architect` if available, otherwise `general-purpose`.
2. Derive the task graph from `Tx-` numbering and `Dependencies:` fields.
3. Verify:
   - no circular dependencies,
   - safe ordering,
   - critical path,
   - parallel groups up to 3 concurrent tasks,
   - achievable validation commands,
   - realistic estimates,
   - internally consistent explicit waves/phases/gates when present.
4. Apply safe sequencing fixes that do not change scope or create dependency side effects.
5. Flag trade-offs for user review.

#### Phase 4 — sanity pass

Final read-through after edits. Confirm:

- technical claims match reality,
- references resolve,
- instructions do not conflict,
- referenced sections exist,
- task counts, dates, and versions are fresh,
- project conventions are reflected.

### Required output state

Return a final status report:

```markdown
## Plan Review Complete

- Documents reviewed: N
- Phase 1 findings: X critical, Y warnings, Z suggestions
- Phase 2 resolutions: X/X critical fixed, Y/Y warnings addressed
- Phase 3 sequencing: [pass/adjusted] — N recommendations applied
- Phase 4 sanity: [clean / N items flagged]

Overall: READY FOR IMPLEMENTATION / NEEDS ATTENTION
```

If files changed, commit:

```bash
git add <modified-spec-files>
git commit -m "chore(plan): Plan review — align documents, fix sequencing" \
  -m "<summary of Phase 1 fixes>" \
  -m "<summary of Phase 3 adjustments>" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Rules

- Never delete tasks; move, rename, or add only.
- Preserve user intent.
- Flag ambiguity.
- Minimize churn.
- Report what was found and changed.

---

## 4. `geeky-implement` — execute the reviewed planning package

**Purpose:** Execute the frozen planning package using `geeky-coder`, validation gates, reviews, kanban updates, per-task notes, and phase commits.

### Input

Pass a folder containing at minimum:

- `implementation-plan.md`
- `kanban.md`
- `tasks/Tx-*.md`
- `references.md`
- `handoff.md`

Optional flags:

- `--phase=<name|number>` — limit execution to one phase.
- `--dry-run` — print execution model only; modify nothing.
- `--serial` — disable parallel execution.

### Phase 0 — validate and model the package

1. Run planning-folder validation first. Stop on failure.

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"
```

Windows alternative:

```pwsh
pwsh -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.ps1" -Path "<folder>"
```

2. If validators fail, print output and stop. Do not regenerate planning artifacts.
3. Read every planning file and task file.
4. Build an execution model:
   - task graph from `Dependencies:`,
   - phase grouping from plan headings, kanban comments, or dependency layers,
   - file-overlap inference from task scope fields,
   - eligibility where task is Ready and dependencies are Done.
5. If `--dry-run`, print phase order, batches, parallel groups, and justifications; then stop.

### Phase 1 — execute tasks by phase

For each phase, in plan order:

1. Select the next eligible batch.
2. Limit concurrency to 3 unless `--serial` is set.
3. A batch is parallel-safe only when:
   - no task depends on another task in the batch,
   - file surfaces do not overlap,
   - no shared mutable artifact is edited,
   - tasks are conceptually independent,
   - concurrency does not exceed the cap.
4. Move selected tasks from Ready to In Progress in `kanban.md` and add timestamp comments.
5. Delegate each implementation to `geeky-coder`.
6. For parallel batches, dispatch all coders in one message with parallel agent calls.
7. Each coder brief must include:
   - full task file text,
   - relevant plan/spec sections by heading and line range,
   - acceptance criteria verbatim,
   - validation block verbatim,
   - instruction not to modify outside declared scope,
   - `subagent_type: "geeky-coder"`.
8. After each coder returns, run the task validation block yourself.
9. If validation fails:
   - capture output,
   - re-delegate once with failure context,
   - if it still fails, move the task to Blocked, update handoff, report, and stop.
10. Move task(s) to In Review.
11. Run per-task review with `code-review` or `review`, scoped to the task diff surface only.
12. Consolidate findings as blocker, major, minor, or nit.
13. Create `tasks/Tx-*.notes.md` for each touched task, including:
   - parallelization decision,
   - coder summary,
   - validation command/results,
   - review findings,
   - fixed vs deferred findings,
   - final touched files.
14. Fix blockers and majors before Done.
15. Minor/nit findings may be deferred, but must be logged in `handoff.md` under Deferred follow-ups.
16. Before moving a task to Done, run:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/check-dod.py" --path "<folder>" --task T<x>
python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"
```

17. Move to Done only when validation is green and no blocker/major review findings remain.
18. Repeat until no eligible Ready tasks remain in the phase.

### Phase 2 — phase-end PM review and commits

1. At phase end, run PM-level review using the same reviewer type used during planning where possible.
2. Provide the reviewer:
   - phase name,
   - Done task IDs,
   - aggregated phase diff,
   - per-task notes,
   - relevant plan section.
3. Ask for cross-task consistency, integration risk, and anything per-task review could miss.
4. Fix PM blockers/majors before proceeding.
5. Log deferred minors/nits in `handoff.md`.
6. Commit the phase diff as small logically grouped commits. One concern per commit.
7. Validate each commit message:

```bash
printf '%s' "$msg" | python "${CLAUDE_PLUGIN_ROOT}/scripts/check-commit.py"
```

8. Commit format:

```text
feat(<phase-short-name>): <what this commit changes>

Tasks: T<x>, T<y>
Refs: docs/<planning-folder>/tasks/Tx-*.md
```

9. Update `handoff.md` with:
   - phase name/date/duration,
   - tasks completed/blocked,
   - commits created,
   - PM review highlights,
   - deferred follow-ups.

### Phase 3 — end of run

When all phases are complete, backlog is empty, or a task blocks:

1. Append a Run Summary to `handoff.md`.
2. Include total completed tasks, commits, blocked items, deferred follow-ups, and suggested next-session steps.
3. Verify kanban lane counts equal the original task count.
4. Report Done, Blocked, and Deferred counts to the user.
5. Suggest `geeky-status <folder>` as the lightweight follow-up.

### Successful output state

- `kanban.md` reflects truth; every task is in exactly one lane.
- Done tasks are checked.
- In Progress and Blocked tasks include timestamp comments.
- `handoff.md` includes per-phase entries and a Run Summary.
- `tasks/Tx-*.notes.md` exists for every touched task.
- Project tree contains local commits that map to executed phases.
- No edits were made to frozen planning contract files.

---

## 5. `impl-review` — multi-angle review of completed implementation

**Purpose:** Review implemented work after `geeky-implement` completes, using 3 dynamically selected domain reviewers.

### Input

Accept:

- a planning package path,
- a diff reference such as `HEAD~5..HEAD`,
- or a branch name.

If missing:

1. Review uncommitted changes when `git diff --stat` is non-empty.
2. Otherwise scan `docs/` for the most recent feature package and review commits since its stated baseline.

### Steps

1. Discover what was built.
   - Read `handoff.md`, `kanban.md`, and the implementation plan.
   - Run `git diff --stat` against the base.
   - Categorize changed work into 3-5 technical domains.
2. Select exactly 3 significant, non-overlapping reviewer domains.
3. Rank domains by:
   - impact,
   - risk,
   - complexity,
   - coverage of changed lines.
4. Define each reviewer with:
   - domain title,
   - focus statement,
   - file subset/patterns,
   - 4-6 domain-specific criteria.
5. Dispatch all 3 reviewers in parallel using `geeky-orchestration:code-reviewer`.
6. Reviewers must not modify files.
7. Reviewers must cite exact file paths and line numbers.
8. Each reviewer reports:
   - Critical Issues,
   - Warnings,
   - Suggestions,
   - Verdict: PASS, PASS WITH WARNINGS, or NEEDS FIXES.
9. Consolidate findings:
   - deduplicate overlaps,
   - prioritize Critical > Warning > Suggestion,
   - present unified report.
10. Overall verdict is either READY TO SHIP or NEEDS FIXES.
11. If critical issues exist, ask the user whether to apply fixes.
12. If approved, fix only critical issues and commit:

```bash
git commit -m "fix(spec): Address N critical review findings from impl-review" \
  -m "<1-line summary per fix>" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Rules

- Always use exactly 3 reviewers.
- Reviewers must be non-overlapping.
- Run all reviewers in parallel.
- Findings must be evidence-based.
- Fix only critical issues automatically after user approval; warnings and suggestions are reported, not auto-fixed.

---

## 6. `archive` — finalize and archive completed planning package

**Purpose:** Move implementation planning artifacts into `archives/` and leave the final delivered docs clean and canonical.

### Prerequisites

- `/archive` must be wired to invoke the archive skill.
- Use only after `geeky-implement` is complete.
- The package must have:
  - all tasks completed in kanban,
  - quality gates passing or explicitly recorded as skipped,
  - checks documented in handoff,
  - team sign-off recorded in handoff.

### Input

Pass the planning folder path, for example:

```text
docs/<feature-folder>/
```

If missing, scan `docs/` for the most recent folder with `implementation-plan.md` and a complete `handoff.md`.

### Steps

1. Resolve the planning folder.
2. Stop immediately if any required file is missing:
   - `handoff.md`,
   - `kanban.md`,
   - `implementation-plan.md`.
3. Read `handoff.md` and confirm status is `Complete`.
4. If not complete, stop and report the current status.
5. Create archive destination:

```text
archives/docs/<folder-name>-planning/
```

6. Keep `docs/<folder-name>/` as the final canonical artifact set.
7. Use `git mv` to move planning-only artifacts into the archive:
   - `kanban.md`
   - `execution-schedule.md`, if present
   - `references.md`
   - `tasks/` directory
   - `tasks/T*.notes.md`, if present
   - `review-development-project-manager.md`, if present
   - `implementation-plan.md`
   - `draft.md`, if present
   - any `*-prompt.md` files
   - other generation-only working docs not meant to remain canonical
8. Keep only permanent docs in `docs/<folder-name>/`:
   - `feature-specification.md` or implemented requirements document,
   - `handoff.md`,
   - `README.md`.
9. Refresh `README.md` with:
   - spec title and completion date,
   - What Was Delivered,
   - reviews/optimizations applied,
   - Delegation to Future Spec/Tasks,
   - pointer to `archives/docs/<folder-name>-planning/`.
10. Remove empty directories under the source plan folder.
11. Update `CLAUDE.md` and `AGENTS.md` `## Current State` sections:
    - mark the folder complete,
    - record task counts/status,
    - keep `docs/<folder-name>/` as canonical reference,
    - update next-folder pointer if known.
12. Commit:

```bash
git add -A
git commit -m "chore: Archive completed planning package" \
  -m "Move planning artifacts to archives/docs/<folder-name>-planning/" \
  -m "Keep implementation specification, handoff, and README in docs/<folder-name>/" \
  -m "Update CLAUDE.md / AGENTS.md current state"
```

13. Verify:
   - `implementation-plan.md` is archived, not final-folder-local.
   - `tasks/` and task notes are fully archived.
   - `feature-specification.md`, `handoff.md`, and `README.md` remain in the final folder.
   - `CLAUDE.md` and `AGENTS.md` reflect final state.
   - final docs have no broken references.

### Rules

- Use `git mv` for all moves.
- Never delete canonical artifacts; archive them.
- `archives/` is git-tracked and intentionally excluded from AI context.
- Do not archive incomplete work.
- Stop on missing required files.
- Make every move traceable in git history.
- The final README must be self-contained enough to understand the outcome without opening task history.

---

## Complete command sequence

```text
/spec-research docs/<feature-folder>/
/geeky-plan docs/<feature-folder>/
/plan-review docs/<feature-folder>/
/geeky-implement docs/<feature-folder>/
/impl-review docs/<feature-folder>/
/archive docs/<feature-folder>/
```

Optional implementation variants:

```text
/geeky-implement docs/<feature-folder>/ --dry-run
/geeky-implement docs/<feature-folder>/ --serial
/geeky-implement docs/<feature-folder>/ --phase=<name|number>
```

---

## Final lifecycle state

A fully completed and archived feature should leave:

```text
docs/<feature-folder>/
  feature-specification.md
  handoff.md
  README.md

archives/docs/<feature-folder>-planning/
  implementation-plan.md
  draft.md
  references.md
  kanban.md
  tasks/
  review-development-project-manager.md
  execution-schedule.md, if present
  other planning-only artifacts
```

The repository history should show:

1. researched spec commit,
2. planning package commit(s),
3. plan-review fix commit(s), if any,
4. implementation phase commits,
5. critical impl-review fix commit(s), if any,
6. archive commit.
