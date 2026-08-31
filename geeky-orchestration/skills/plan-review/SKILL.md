---
name: plan-review
description: Sanity-check a completed planning folder before implementation. Reviews plan-to-task consistency, sequencing, and execution readiness so `/geeky-implement` starts clean.
---

# Plan Review

Four-phase quality review of a `/geeky-plan` output folder. Validates document alignment, fixes inconsistencies, checks execution sequencing, then does a final sanity pass. Targets implementation-plan.md, kanban.md, tasks/, references.md, review-development-project-manager.md, handoff.md, and execution-schedule.md if the plan produced one.

## Arguments

Accept a planning folder path (e.g., `docs/feature-name/`). No argument → scan `docs/` for the most recent folder with an `implementation-plan.md`.

## Workflow

Run all four phases in order. Each phase builds on the prior one's findings.

**Resume contract:** append each phase's output to `review-plan.md` in the planning folder as it completes (tagged `<!-- phase-N-complete -->`). If `review-plan.md` already exists, skip phases tagged complete and pick up at the first missing one. Never repeat a completed phase or re-apply its fixes.

---

### Phase 1: Document Alignment Audit

**Pre-flight:** Check for validator scripts under `${CLAUDE_PLUGIN_ROOT}/scripts/` (validate-task-schema.py, validate-kanban.py, validate-planning-folder.py). If `${CLAUDE_PLUGIN_ROOT}` is unset or scripts are missing, skip to the fallback — not a blocker.

Scripts available? Run them. Non-zero exit = Critical finding. The `python` form works cross-platform; paired `.ps1` scripts exist (see AGENTS.md):

- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"`
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"`
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"`

**Fallback (no scripts):** Jump straight to the semantic review. The subagent does the structural checks manually.

Deploy a review subagent for the semantic cross-validation scripts can't cover. It reads the entire spec/plan folder:

**Files to read:**
- `feature-specification.md` (preferred requirements doc)
- `draft.md` (if present)
- `SPEC-NNNN-*.md` (legacy requirements, if present)
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
3. Waves/phases and gate criteria (if defined) are consistent across all documents. Their absence is fine — the geeky-plan template doesn't require them.
4. `Dependencies:` in task files match the plan's ordering. If `Blocks`/wave fields exist, check bidirectional consistency.
5. If `execution-schedule.md` exists, gate criteria match the Tests/Validation blocks in task files
6. Files referenced in tasks exist in the codebase (or are explicitly to-be-created)
7. Acceptance criteria in the requirements doc are covered by at least one task
8. No orphaned tasks (in task files but missing from kanban or plan)
9. No phantom tasks (in kanban/plan but no task file)

**Optional sections:** Stubs marked optional or placeholder (e.g., "[Optional: X]", "TBD") are valid. Don't flag them as missing.

**Output:** Structured findings report with severity levels: Critical / Warning / Suggestion (maps to geeky-implement's blocker / major / minor-nit taxonomy).

### Phase 2: Issue Resolution

For each Phase 1 finding:

- **Critical** (broken references, missing tasks, contradictory dependencies): Fix now. Edit the affected document(s).
- **Warnings** (inconsistent wording, unclear gate criteria, missing details): Fix if the correction is unambiguous. Flag for user if judgment is needed.
- **Suggestions** (style, optional improvements): Note. Don't block.

**When is a fix unambiguous?** It (a) corrects a mechanical inconsistency — typo, broken link, mismatched ID — (b) doesn't change task scope or ordering, and (c) has exactly one valid correction. Examples: fixing a task ID typo, adding a missing task file, correcting a file path. Requires judgment: rephrasing goals, splitting/merging tasks, reordering dependencies. Those get flagged, not auto-fixed.

After fixes, re-run the deterministic validators (if available) and spot-check semantic findings on changed files. Re-run threshold: if >5 files changed or changes touch cross-document references (task IDs, dependencies, ordering), redeploy the Phase 1 subagent for a full re-check. Otherwise spot-check the edited files only.

**Output:** Table of finding → action taken → status (fixed / flagged / deferred).

### Phase 3: Sequencing & Parallelization Validation

**This is why the layered review exists.** `geeky-implement` walks the board by eligibility — a task runs only when it's in Backlog or Ready *and* every dependency is Done. That loop can't distinguish "work is finished" from "graph is unsatisfiable." A dependency cycle, a task depending on something deleted, or a subgraph that can never become eligible all look like a clean, quiet finish with tasks left undone.

That failure can't surface mid-implementation, where the package is frozen and the only remedy is Blocked plus a handoff contradiction. **Catch it here.** An unsatisfiable graph is Critical: the package isn't ready, and Phase 4 reports `NEEDS ATTENTION` instead of passing it through.

Deploy a **time-master planner** subagent (`geeky-orchestration:code-architect` type; fall back to `general-purpose` only if that agent type is unavailable) with this brief:

> Analyze the implementation plan and task files for sequencing correctness. The package declares ordering via task numbering (`Tx-`) and `Dependencies:` fields; derive the execution structure from those. Validate:
>
> 1. **Dependency graph is acyclic** — no circular dependencies. A cycle is CRITICAL: every task in it is permanently ineligible.
> 1b. **Every task is reachable** — walk the graph forward from tasks with no unmet dependencies. Confirm the walk reaches all of them. Any task it can't reach can never become eligible. That's CRITICAL. Name the specific unsatisfiable dependency for each.
> 1c. **Every declared dependency resolves** — each `Dependencies:` entry names a task that exists in `tasks/` and appears in the kanban. A dependency on a missing or renamed task is CRITICAL.
> 2. **Critical path** — derive the longest dependency chain; if the plan states one, verify it matches
> 3. **Parallelization opportunities** — derive groups of mutually independent tasks suitable for parallel dispatch (up to 3 concurrent). Propose them as a recommendation if the plan doesn't already group them.
> 4. **Validation blocks are achievable** — each task's Tests/Validation commands can run with the tools/access available
> 5. **Ordering is safe** — no task is sequenced before its dependencies complete
> 6. **Task estimates are realistic** — flag any S task touching multiple files/modules, or any L task that could split into independent S/M tasks
> 7. If the plan defines waves/phases or gates, verify their internal consistency. Don't flag their absence.
>
> Produce a sequencing report:
> - Dependency-graph validity (pass/fail)
> - Critical path (nodes + depth)
> - Parallelization score (actual parallel tasks vs theoretical maximum)
> - Recommendations (tasks to reorder, parallel groups to declare, splits to consider)

Apply sequencing fixes (reorder tasks, update dependency declarations) that have no dependency side-effects. Flag trade-offs for user review.

### Phase 4: Sanity Pass

Final read-through of all spec documents after Phases 1-3 edits. Check:

1. **Accuracy** — technical claims match reality (file paths, package names, resource types)
2. **References** — all cross-document references resolve (file paths, section numbers, task IDs)
3. **Non-conflicting instructions** — no two documents contradict each other on the same topic
4. **Completeness** — every section in a table of contents exists; every "see X" link resolves
5. **Freshness** — dates, version numbers, task counts are current
6. **Convention adherence** — CLAUDE.md conventions show up in task instructions

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

## Review scope: start at the closest Backlog task

**Never inspect or reason about freeze state.** This skill doesn't check whether a package is frozen, and doesn't change behavior based on the answer. It scopes by lane instead.

A task in `Ready`, `In Progress`, `In Review`, or `Done` is already committed — `geeky-implement` has taken it. Reviewing or rewriting it now would be revising an executed decision. So:

- **Find the closest Backlog task** — the lowest-numbered task still in `Backlog`. Make it the start of the review scope.
- **Scope = that task and everything after it**: every remaining `Backlog` task, plus all shared planning documents insofar as they describe that remaining work.
- **Everything before it is read-only context.** Read committed tasks to understand what the remaining work builds on. Don't re-sequence, re-scope, or edit their task files.
- **No task in Backlog?** Nothing left to review. Report the package is fully committed and stop.

On a fresh package every task is in Backlog, so the scope is everything and the four phases run as written. On a partially-executed package the same four phases run against the uncommitted remainder.

**Lane moves aren't this skill's job.** `geeky-implement` owns promotion to Ready and all kanban state. Record Phase 3's parallel groups and dependency corrections in `implementation-plan.md` and the task files' `Dependencies:` blocks, where the implement run will read them. Don't move tasks between lanes to express a sequencing decision.

## Execution Strategy

- **Phase 1**: Background subagent (`geeky-orchestration:code-reviewer` type) — reads all files, edits nothing
- **Phase 2**: Orchestrator applies edits directly from Phase 1 findings
- **Phase 3**: Background subagent (`geeky-orchestration:code-architect` type) — independent sequencing analysis
- **Phase 4**: Orchestrator runs the final verification pass directly

Phase 1 found no critical issues? Dispatch Phase 3 in parallel while Phase 2 handles warnings. Otherwise run sequentially: 1 → 2 → 3 → 4.

## Commit Behavior

After all phases complete, if any files changed:

```
git add <modified-spec-files>
git commit -m "chore(plan): Plan review — align documents, fix sequencing" -m "[summary of Phase 1 fixes]" -m "[summary of Phase 3 adjustments]" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Rules

- **Never delete tasks** — move, rename, or add only
- **Preserve user intent** — don't restructure goals or change scope
- **Flag ambiguity** — if a fix needs judgment about scope or priority, ask the user
- **Minimize churn** — small targeted fixes over wholesale rewrites
- **Report transparently** — always show what was found and what changed
