---
name: geeky-resume
description: Use when resuming a geeky-plan / geeky-implement run after a session cutoff, compaction, crash, or dead subagent — "resume the implementation", "continue where we left off", "are you stuck". Reconciles kanban lanes and handoff claims against live git status/diff before any work continues; never trusts a pre-cutoff "done". For a snapshot without resuming, use geeky-status; to continue execution after reconciliation, hand off to geeky-implement.
---

Use the shared [workflow terminology](../../AGENTS.md#workflow-terminology).

# geeky-resume

A session cutoff, a compaction summary, and a subagent's "done" are all **claims about state you have not observed**. This skill re-grounds a geeky run in live ground truth before anything continues. It is the geeky-orchestration form of the standing resume reflex: read the durable ledger first, then reconcile it against the repo.

## Input

`$ARGUMENTS`: a folder produced by `geeky-plan`. If missing or it contains no `kanban.md`, STOP and ask the user.

## Procedure

1. **Read the durable ledger first** — `handoff.md` and `kanban.md`, before touching anything else. Note the last handoff entry's date/claims and every task sitting in `In Progress`, `In Review`, or recently moved to `Done`.

2. **Snapshot via geeky-status.** Run the `geeky-status` skill (or its validators directly) for lane counts, blocked tasks, and inconsistencies. Its output is the *claimed* state.

3. **Reconcile claims against live git — the core step.** For the repo the planning folder targets:
   - `git status` + `git log --oneline` since the last handoff timestamp, and `git diff` / `git diff --cached` for uncommitted work.
   - For each task claimed `Done` or `In Review` since the previous handoff entry: verify its artifacts and saved validation/review evidence against the current files or cited revision. Verify any cited commit, but a missing commit alone does not invalidate accepted work awaiting a phase commit.
   - For each task in `In Progress`: inspect matching worktree changes, commits and saved evidence. An empty or interrupted subagent response does not establish whether work was done.
   - Reuse saved passing validation while its tested files or revision, dependencies and relevant environment remain valid. A bare PASS claim is insufficient; run only missing, invalidated or explicitly required independent checks.

4. **Classify each discrepancy** and correct the ledger to match verified reality — the *only* edits this skill may make are kanban lane moves and a dated reconciliation note in `handoff.md`:
   - claimed Done, evidence shows missing or incomplete work → move to `Ready` if absent, `In Progress` if partial, or `In Review` if implementation is complete but acceptance evidence is missing. Record the reason with a `<!-- reconciled YYYY-MM-DD: ... -->` comment.
   - claimed In Progress, no live worker and no matching artifacts, commits or saved progress → move back to `Ready`.
   - uncommitted work that matches a task → retain the evidence-supported lane and note the pending commit for geeky-implement at its normal commit boundary.
   - work in the tree matching **no** task → flag as user-owned or out-of-band; never revert or clean it.

5. **Report and hand off.** Print: verified lane counts (post-reconciliation), the discrepancy list with evidence (file paths / commit hashes), and the next step — normally `Resume with /geeky-implement <folder>`, or `Resolve blocked: <Tid>` if anything is blocked. Do not start executing tasks yourself; execution belongs to `geeky-implement`.

## Hard rules

- Read `handoff.md` + `kanban.md` **before** any other action; re-`Read` any file before editing it (the pre-cutoff view is stale).
- A pre-cutoff "done" claim requires verifiable artifacts and acceptance evidence. Missing communication or a pending commit alone does not justify reopening accepted work.
- Edits limited to: kanban lane corrections + one dated handoff reconciliation note. No task work, no commits of product code, no subagents.
- Preserve user-owned changes unconditionally.

## Acceptance criteria

- Every lane correction cites the artifacts and evidence that establish the discrepancy; a missing commit or empty diff alone is insufficient.
- The handoff gains exactly one dated reconciliation entry.
- The report separates verified state from unverified claims and names the next step.
