---
name: plan-review
description: Use when asked to sanity-check a completed planning folder before implementation. This skill reviews plan-to-task consistency, sequencing, and execution readiness so `/geeky-implement` can start with fewer blockers.
---

# Plan Review

Multi-phase planning package quality review that validates document alignment, resolves inconsistencies, validates execution sequencing, and performs a final sanity pass. Targets the `/geeky-plan` output folder (implementation-plan.md, kanban.md, tasks/, references.md, review-development-project-manager.md, handoff.md, plus execution-schedule.md if the plan produced one).

## Arguments

Accept a planning folder path (e.g., `docs/feature-name/`). If no argument is given, scan `docs/` for the most recent folder containing an `implementation-plan.md`.

## Workflow

Execute all four phases sequentially. Each phase builds on findings from the prior phase.

**Resume contract:** append each phase's output to `review-plan.md` in the planning folder as the phase completes (tagged `<!-- phase-N-complete -->`). On invocation, if `review-plan.md` already exists for this folder, this is a resumed run — skip phases already tagged complete and continue from the first missing phase. Re-invocation must never repeat completed phases or re-apply their fixes.

---

### Phase 1: Document Alignment Audit

**Pre-flight:** Check for required validator scripts under `${CLAUDE_PLUGIN_ROOT}/scripts/` (validate-task-schema.py, validate-kanban.py, validate-planning-folder.py). If `${CLAUDE_PLUGIN_ROOT}` is unset or scripts are missing, skip to the fallback semantic review below — no blocker.

If scripts are available, run the bundled deterministic validators and treat any non-zero exit as a Critical finding (`python` form works cross-platform; paired `.ps1` scripts exist — see AGENTS.md):

- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"`
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"`
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"`

**Fallback (when scripts unavailable):** Proceed directly to the semantic review below — the subagent performs manual structural checks that scripts would have automated.

Deploy a review subagent for the semantic cross-validation the scripts cannot cover — read the ENTIRE spec/plan folder and cross-validate:

**Files to read:**
- `feature-specification.md` (preferred requirements doc)
- `draft.md` (if present and used by this package)
- `SPEC-NNNN-*.md` (legacy requirements document, if present)
- `implementation-plan.md` — task list, phases/ordering, dependencies
- `kanban.md` — task states and blocked-by relationships
- `execution-schedule.md` (if present)
- `tasks/T*.md` — every task file (title, dependencies, scope, validation block)
- `handoff.md` — status, deviations, next steps
- `references.md` — links (if present)
- `review-development-project-manager.md` — PM review (if present)
- `README.md` — summary (if present)

**Cross-validation checks:**
1. Every task in `implementation-plan.md` has a matching file in `tasks/`
2. Task IDs in `kanban.md` match those in `implementation-plan.md` exactly
3. If the plan defines waves/phases or gate criteria, they are consistent across all documents (their absence is not a finding — the geeky-plan template does not require them)
4. Dependency declarations (`Dependencies:` in task files) are consistent with the plan's ordering; if `Blocks`/wave fields exist, verify they are bidirectionally consistent
5. If `execution-schedule.md` exists, gate criteria match the Tests/Validation blocks in task files
6. Files referenced in tasks actually exist in the codebase (or are explicitly to-be-created)
7. Acceptance criteria in the requirements document are covered by at least one task
8. No orphaned tasks (in task files but not in kanban or plan)
9. No phantom tasks (in kanban/plan but missing task file)

**Handling optional sections:** If a document contains a section stub marked as optional or placeholder (e.g., "[Optional: X]", "TBD"), do NOT flag it as missing content — optional stubs are valid and expected in planning packages.

**Output:** A structured findings report with severity levels (Critical / Warning / Suggestion — mapping to geeky-implement's blocker / major / minor-nit taxonomy).

### Phase 2: Issue Resolution

For each finding from Phase 1:

- **Critical issues** (broken references, missing tasks, contradictory dependencies): Fix immediately by editing the affected document(s).
- **Warnings** (inconsistent wording, unclear gate criteria, missing details): Fix if the correction is unambiguous (see criteria below); flag for user if judgment is required.
- **Suggestions** (style, optional improvements): Note but do not block.

**Unambiguous auto-fix criteria:** A fix is unambiguous when it (a) corrects a mechanical inconsistency (typo, broken link, mismatched ID), (b) does not change task scope or ordering, and (c) has exactly one valid correction. Examples: fixing a task ID typo, adding a missing task file for a declared task, correcting a file path. Requires judgment: rephrasing goals, splitting/merging tasks, reordering dependencies.

After fixes, the orchestrator re-runs the deterministic validators (if available) and spot-checks the semantic findings on changed files. Re-run threshold is context-sensitive: if >5 files changed OR if changes affect cross-document references (task IDs, dependencies, ordering), redeploy the Phase 1 subagent for a full re-check. Otherwise spot-check the edited files only to confirm fixes did not introduce new inconsistencies.

**Output:** A table of finding → action taken → status (fixed / flagged / deferred).

### Phase 3: Sequencing & Parallelization Validation

Deploy a **time-master planner** subagent (`geeky-orchestration:code-architect` type; fall back to `general-purpose` only if that agent type is unavailable) with this brief:

> Analyze the implementation plan and task files for sequencing correctness. The package declares ordering via task numbering (`Tx-`) and `Dependencies:` fields; derive the execution structure from those. Validate:
>
> 1. **Dependency graph is acyclic** — no circular dependencies
> 2. **Critical path** — derive the longest dependency chain; if the plan states one, verify it matches
> 3. **Parallelization opportunities are maximized** — derive groups of mutually independent tasks suitable for parallel dispatch (up to 3 concurrent) and propose them as a recommendation if the plan doesn't already group them
> 4. **Validation blocks are achievable** — each task's Tests/Validation commands can be run with the tools/access available
> 5. **Ordering is safe** — no task is sequenced before its dependencies complete
> 6. **Task estimates are realistic** — flag any task marked S that touches multiple files/modules, or any L task that could be split into independent S/M tasks
> 7. If the plan explicitly defines waves/phases or gates, additionally verify their internal consistency — do not flag their absence
>
> Produce a sequencing report:
> - Dependency-graph validity (pass/fail)
> - Critical path (nodes + depth)
> - Parallelization score (actual parallel tasks vs theoretical maximum)
> - Recommendations (tasks to reorder, parallel groups to declare, splits to consider)

Apply sequencing fixes (reorder tasks, update dependency declarations in the plan) that have no dependency side-effects. Flag trade-offs for user review.

### Phase 4: Sanity Pass

Final read-through of all spec documents after Phases 1-3 edits. Check:

1. **Accuracy** — Technical claims match reality (file paths, package names, resource types)
2. **References** — All cross-document references point to correct locations (file paths, section numbers, task IDs)
3. **Non-conflicting instructions** — No two documents give contradictory guidance for the same topic
4. **Completeness** — Every section referenced in a table of contents exists; every "see X" link resolves
5. **Freshness** — Dates, version numbers, and task counts are current
6. **Convention adherence** — CLAUDE.md conventions are reflected in task instructions

**Output:** Final status report:
```
## Plan Review Complete

- Documents reviewed: N
- Phase 1 findings: X critical, Y warnings, Z suggestions
- Phase 2 resolutions: X/X critical fixed, Y/Y warnings addressed
- Phase 3 sequencing: [pass/adjusted] — N recommendations applied
- Phase 4 sanity: [clean / N items flagged]

Overall: READY FOR IMPLEMENTATION / NEEDS ATTENTION (list remaining items)
```

## Execution Strategy

- **Phase 1**: Deploy as a background subagent (`geeky-orchestration:code-reviewer` type) — it reads all files without editing
- **Phase 2**: Execute fixes directly (the orchestrator applies edits based on Phase 1 findings)
- **Phase 3**: Deploy as a background subagent (`geeky-orchestration:code-architect` type) — independent analysis of sequencing
- **Phase 4**: Execute directly — final verification pass

If Phase 1 finds no critical issues, dispatch Phase 3 in parallel while Phase 2 addresses warnings. Otherwise, execute sequentially (Phase 1 → Phase 2 → Phase 3 → Phase 4).

## Commit Behavior

After all phases complete, if any files were modified (same command on all platforms):

```
git add <modified-spec-files>
git commit -m "chore(plan): Plan review — align documents, fix sequencing" -m "[summary of Phase 1 fixes]" -m "[summary of Phase 3 adjustments]" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Rules

- **Never delete tasks** — only move, rename, or add
- **Preserve user intent** — do not restructure goals or change scope
- **Flag ambiguity** — if a fix requires judgment about scope or priority, ask the user
- **Minimize churn** — small targeted fixes over wholesale rewrites
- **Report transparently** — always show what was found and what was changed
