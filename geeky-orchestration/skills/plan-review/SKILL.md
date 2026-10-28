---
name: plan-review
description: Use when asked to sanity-check a completed planning folder before implementation. This skill reviews plan-to-task consistency, sequencing, and execution readiness so `/geeky-implement` can start with fewer blockers.
---

Use the shared [workflow terminology](../../AGENTS.md#workflow-terminology).

# Plan Review

Multi-phase planning package quality review that validates document alignment, resolves inconsistencies, validates execution sequencing, and performs a final sanity pass. Targets the `/geeky-plan` output folder (implementation-plan.md, kanban.md, tasks/, references.md, review-development-project-manager.md, handoff.md, plus execution-schedule.md if the plan produced one).

## Arguments

Accept a planning folder path (e.g., `docs/feature-name/`). If no argument is given, scan `docs/` for the most recent folder containing an `implementation-plan.md`.

## Time budget and checkpoint

At entry, before each numbered task or phase, after a lengthy direct operation,
and immediately before and after each worker dispatch or blocking wait, run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/workflow-budget.py" --stage plan-review --json`.
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

If the budget stops this stage, preserve the completed review sections and unresolved checks in `review-plan.md` and handoff; do not declare READY FOR IMPLEMENTATION. Resume with the existing invalidation rules.

## Workflow

Execute the four phases in order, except for the safe Phase 2/3 overlap described under Execution Strategy. Each phase uses the findings it depends on.

**Resume contract:** append each phase's output to its existing `review-plan.md` section as it completes (tagged `<!-- phase-N-complete -->`), including reviewer agent ID where applicable, reviewed revision/file hashes, findings and verdict. Reuse completed phases only when their inputs remain valid against a complete diff, including untracked additions; a marker alone is insufficient. Recheck changed content and affected references for local mechanical fixes. Requirement/AC/task-scope/coverage changes invalidate alignment; dependency/order/phase/gate/resource/validation-feasibility changes invalidate sequencing. More than five changed files or cross-document task-ID/dependency/order changes require the full Phase 1 recheck and fresh affected sequencing verdict. Missing baseline/diff, omitted untracked additions, conflicts or unbounded impact require full sanity and fresh affected reviewer verdicts. Record what was reused, rechecked and why; do not re-apply already verified fixes.

---

### Phase 1: Document Alignment Audit

**Pre-flight:** Check for required validator scripts under `${CLAUDE_PLUGIN_ROOT}/scripts/` (validate-task-schema.py, validate-kanban.py, validate-planning-folder.py). If `${CLAUDE_PLUGIN_ROOT}` is unset or scripts are missing, skip to the fallback semantic review below — no blocker.

If scripts are available, run the bundled deterministic validators and treat any non-zero exit as a Critical finding (`python` form works cross-platform; paired `.ps1` scripts exist — see AGENTS.md):

- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"`
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"`
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"`

**Fallback (when scripts unavailable):** Proceed directly to the semantic review below — the subagent performs manual structural checks that scripts would have automated.

Deploy a review subagent for the semantic cross-validation the scripts cannot cover; request concise, actionable findings and evidence rather than restating the package — read the ENTIRE spec/plan folder and cross-validate:

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
10. **Accuracy** — technical claims match reality (file paths, package names, resource types)
11. **References** — cross-document references point to correct paths, sections and task IDs
12. **Non-conflicting instructions** — documents do not contradict each other on the same topic
13. **Completeness** — table-of-contents sections exist and every “see X” link resolves
14. **Freshness** — dates, versions and task counts are current
15. **Convention adherence** — applicable CLAUDE.md/AGENTS.md conventions are reflected in tasks

**Handling optional sections:** If a document contains a section stub marked as optional or placeholder (e.g., "[Optional: X]", "TBD"), do NOT flag it as missing content — optional stubs are valid and expected in planning packages.

**Output:** In `review-plan.md` Phase 1, save the alignment reviewer ID, input revision/file hashes, findings and verdict with severity levels (Critical / Warning / Suggestion, within the plan-review scope).

### Phase 2: Issue Resolution

For each finding from Phase 1:

- **Critical issues** (broken references, missing tasks, contradictory dependencies): Fix immediately by editing the affected document(s).
- **Warnings** (inconsistent wording, unclear gate criteria, missing details): Fix if the correction is unambiguous (see criteria below); flag for user if judgment is required.
- **Suggestions** (style, optional improvements): Note but do not block.

**Unambiguous auto-fix criteria:** A fix is unambiguous when it (a) corrects a mechanical inconsistency (typo, broken link, mismatched ID), (b) does not change task scope or ordering, and (c) has exactly one valid correction. Examples: fixing a task ID typo, adding a missing task file for a declared task, correcting a file path. Requires judgment: rephrasing goals, splitting/merging tasks, reordering dependencies.

After fixes, re-run the deterministic validators (if available), then apply the resume invalidation rules above. A local mechanical correction with bounded impact needs a changed-content/reference check; scope, requirements and sequencing edits need fresh affected verdicts. Preserve independent alignment and sequencing reviewers, including on resume.

**Output:** A table of finding → action taken → status (fixed / flagged / deferred).

### Phase 3: Sequencing & Parallelization Validation

Deploy a **time-master planner** subagent (`geeky-orchestration:code-architect` type; fall back to `general-purpose` only if that agent type is unavailable) with this brief:

> Analyze the implementation plan and task files for sequencing correctness. The package declares ordering via task numbering (`Tx-`) and `Dependencies:` fields; derive the execution structure from those. Validate:
>
> 1. **Dependency graph is acyclic** — no circular dependencies
> 2. **Critical path** — derive the longest dependency chain; if the plan states one, verify it matches
> 3. **Parallelization opportunities are maximized** — derive groups of mutually independent tasks suitable for parallel dispatch (up to 3 concurrent) and propose them as a recommendation if the plan doesn't already group them. Distinguish required behavior or contract dependencies from shared-file scheduling constraints. Shared files require coordinated ownership, not automatically a dependency edge. Allow safe, authorized preparation while acceptance prerequisites are pending, without bypassing dependencies. Resolve dependency changes during planning; frozen dependencies remain binding during execution.
> 4. **Validation blocks are achievable** — each task's Tests/Validation commands can be run with the tools/access available
> 5. **Ordering is safe** — no task is sequenced before its dependencies complete
> 6. **Task estimates are realistic** — flag any task marked S that touches multiple files/modules, or any L task that could be split into independent S/M tasks
> 7. If the plan explicitly defines waves/phases or gates, additionally verify their internal consistency — do not flag their absence
>
> Produce a concise sequencing report with evidence and actionable findings, without restating the plan:
> - Dependency-graph validity (pass/fail)
> - Critical path (nodes + depth)
> - Parallelization score (actual parallel tasks vs theoretical maximum)
> - Recommendations (tasks to reorder, parallel groups to declare, splits to consider)

Save the sequencing reviewer ID, input revision/file hashes, findings and verdict in `review-plan.md` Phase 3. Apply sequencing fixes (reorder tasks, update dependency declarations in the plan) that have no dependency side-effects. Flag trade-offs for user review. Apply the same invalidation rules to these corrections before the final pass.

### Phase 4: Sanity Pass

The parent checks unresolved findings, both current reviewer verdicts, the complete document diff since their recorded inputs (including untracked additions), and changed content/affected references. Reuse the initial whole-folder coverage of all six sanity dimensions; reopen reviews only under the invalidation rules above. If the baseline or impact cannot be bounded, perform the full sanity pass and obtain fresh affected verdicts.

After all corrections, including sequencing corrections, re-run all three Phase 1 validators (or their stated fallback if unavailable). Save commands/results and reuse/recheck decisions in `review-plan.md` Phase 4. Required findings or missing required evidence prevent READY FOR IMPLEMENTATION; optional suggestions alone need no further review.

**Output:** Final status report:
```
## Plan Review Complete

- Documents reviewed: N
- Phase 1 findings: X critical, Y warnings, Z suggestions
- Phase 2 resolutions: X/X critical fixed, Y/Y warnings addressed
- Phase 3 sequencing: [pass/adjusted] — N recommendations applied
- Phase 4 sanity: [clean / N items flagged] — [coverage reused / scope rechecked and reason]; final validator results

Overall: READY FOR IMPLEMENTATION / NEEDS ATTENTION (list remaining items)
```

## Execution Strategy

- **Phase 1**: Deploy as a background subagent (`geeky-orchestration:code-reviewer` type) — it reads all files without editing
- **Phase 2**: Execute fixes directly (the orchestrator applies edits based on Phase 1 findings)
- **Phase 3**: Deploy as a background subagent (`geeky-orchestration:code-architect` type) — independent analysis of sequencing. Always dispatch it as its own subagent, separate from Phase 1, even when Phase 1 found nothing; the orchestrator does not do the sequencing review inline.
- **Phase 4**: Execute directly — final verification pass

If Phase 1 finds no critical issues and Phase 2 corrections do not affect sequencing inputs, Phase 3 may run in parallel. Otherwise, complete Phase 2 first.

## Commit Behavior

After all phases complete, if any files were modified (same command on all platforms):

```
git add <modified-spec-files>
git commit -m "chore(plan): Plan review — align documents, fix sequencing" -m "[summary of Phase 1 fixes]" -m "[summary of Phase 3 adjustments]" -m "Tasks: <IDs touched>"
```

Use the subject verbatim, em dash included.

## Rules

- **Never delete tasks** — only move, rename, or add
- **Preserve user intent** — do not restructure goals or change scope
- **Flag ambiguity** — if a fix requires judgment about scope or priority, ask the user
- **Minimize churn** — small targeted fixes over wholesale rewrites
- **Report transparently** — always show what was found and what was changed
