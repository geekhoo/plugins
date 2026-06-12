---
name: plan-review
description: This skill should be used when the user asks to "review a plan", "validate plan documents", "validate spec documents", "align plan tasks", "check plan consistency", "review the planning package", "is this plan ready to implement", "sanity check this plan", "review the spec-006 plan", "check if this plan is ready", or invokes /plan-review. Performs a 4-phase quality review of a geeky-plan output folder — document alignment, issue resolution, sequencing validation, and final sanity pass — using subagents for thoroughness.
---

# Plan Review

Multi-phase planning package quality review that validates document alignment, resolves inconsistencies, validates execution sequencing, and performs a final sanity pass. Targets the `/geeky-plan` output folder (implementation-plan.md, kanban.md, tasks/, execution-schedule.md, handoff.md).

## Arguments

Accept a planning package folder path (e.g., `docs/spec-007-infrastructure/`). If no argument given, scan `docs/` for the most recent folder containing an `implementation-plan.md` or `SPEC-*.md` file.

## Workflow

Execute all four phases sequentially. Each phase builds on findings from the prior phase.

---

### Phase 1: Document Alignment Audit

Deploy a review subagent to read the ENTIRE spec folder and cross-validate:

**Files to read:**
- `SPEC-NNNN-*.md` — requirements document (sections, goals, acceptance criteria)
- `implementation-plan.md` — task list, waves, dependency DAG, critical path
- `kanban.md` — task states and blocked-by relationships
- `execution-schedule.md` — wave assignments, gate criteria, parallelism groups
- `tasks/T*.md` — every task file (title, wave, depends-on, blocks, implementation)
- `handoff.md` — status, deviations, next steps
- `references.md` — links (if present)
- `README.md` — summary (if present)

**Cross-validation checks:**
1. Every task in `implementation-plan.md` has a matching file in `tasks/`
2. Task IDs in `kanban.md` match those in `implementation-plan.md` exactly
3. Wave assignments are consistent across all documents
4. Dependency chains (`Depends On` / `Blocks`) are bidirectionally consistent
5. Gate criteria in `execution-schedule.md` match the verification blocks in task files
6. Files referenced in tasks actually exist in the codebase (or are to-be-created)
7. Acceptance criteria in the spec doc are covered by at least one task
8. No orphaned tasks (in task files but not in kanban or plan)
9. No phantom tasks (in kanban/plan but missing task file)

**Output:** A structured findings report with severity levels (Critical / Warning / Info).

---

### Phase 2: Issue Resolution

For each finding from Phase 1:

- **Critical issues** (broken references, missing tasks, contradictory dependencies): Fix immediately by editing the affected document(s).
- **Warnings** (inconsistent wording, unclear gate criteria, missing details): Fix if the correction is unambiguous; flag for user if judgment is required.
- **Info** (style, optional improvements): Note but do not block.

After fixes, re-run the cross-validation checks from Phase 1 on changed files to confirm resolution. Do not introduce new inconsistencies.

---

### Phase 3: Sequencing & Parallelization Validation

Deploy a **time-master planner** subagent (use `feature-dev:code-architect` or `general-purpose` type) with this brief:

> Analyze the implementation plan and task files for sequencing correctness. Validate:
>
> 1. **Dependency DAG is acyclic** — no circular dependencies
> 2. **Critical path is correctly identified** — longest chain matches stated critical path
> 3. **Parallelization opportunities are maximized** — independent tasks within each wave are correctly grouped for parallel dispatch (up to 3 concurrent)
> 4. **Gate criteria are achievable** — each wave's gate can be verified with the tools/access available
> 5. **Checkpoints are correctly placed** — gates between waves prevent downstream tasks from starting with incomplete prerequisites
> 6. **Task estimates are realistic** — flag any task marked < 10 min that involves multiple file changes, or > 45 min that could be split
> 7. **Wave assignment optimization** — check if any task could safely move to an earlier wave (all its dependencies completed in prior waves)
>
> Produce a sequencing report:
> - DAG validity (pass/fail)
> - Critical path (nodes + depth)
> - Parallelization score (actual parallel tasks vs theoretical maximum)
> - Recommendations (tasks to move, waves to restructure, gates to add/remove)

Apply sequencing fixes (reorder tasks, move between waves, update DAG in plan) that have no dependency side-effects. Flag trade-offs for user review.

---

### Phase 4: Sanity Pass

Final read-through of all spec documents after Phases 1-3 edits. Check:

1. **Accuracy** — Technical claims match reality (file paths, API versions, package names, resource types)
2. **References** — All cross-document references point to correct locations (file paths, section numbers, task IDs)
3. **Non-conflicting instructions** — No two documents give contradictory guidance for the same topic
4. **Completeness** — Every section referenced in a table of contents exists; every "see X" link resolves
5. **Freshness** — Dates, version numbers, and task counts are current
6. **Convention adherence** — CLAUDE.md conventions (YAML 2-space indent, kebab-case job names, etc.) are reflected in task instructions

**Output:** Final status report:
```
## Plan Review Complete

- Documents reviewed: N
- Phase 1 findings: X critical, Y warnings, Z info
- Phase 2 resolutions: X/X critical fixed, Y/Y warnings addressed
- Phase 3 sequencing: [pass/adjusted] — N recommendations applied
- Phase 4 sanity: [clean / N items flagged]

Overall: READY FOR IMPLEMENTATION / NEEDS ATTENTION (list remaining items)
```

---

## Execution Strategy

- **Phase 1**: Deploy as a background subagent (`feature-dev:code-reviewer` type) — it reads all files without editing
- **Phase 2**: Execute fixes directly (the orchestrator applies edits based on Phase 1 findings)
- **Phase 3**: Deploy as a background subagent (`general-purpose` type) — independent analysis of sequencing
- **Phase 4**: Execute directly — final verification pass

If Phase 1 finds no critical issues, dispatch Phase 3 in parallel while Phase 2 addresses warnings. Otherwise, execute sequentially (Phase 1 → Phase 2 → Phase 3 → Phase 4).

---

## Commit Behavior

After all phases complete, if any files were modified:
```bash
git add <modified-spec-files>
git commit -m "chore(spec-NNN): Plan review — align documents, fix sequencing

- [summary of Phase 1 fixes]
- [summary of Phase 3 adjustments]

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Rules

- **Never delete tasks** — only move, rename, or add
- **Preserve user intent** — do not restructure goals or change scope
- **Flag ambiguity** — if a fix requires judgment about scope or priority, ask the user
- **Minimize churn** — small targeted fixes over wholesale rewrites
- **Report transparently** — always show what was found and what was changed
