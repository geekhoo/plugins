---
name: geeky-resume
description: Resume a geeky-plan / geeky-implement run after a session cutoff, compaction, crash, or dead subagent. Reconciles kanban and handoff against live git state before any work continues. For a snapshot without resuming, use geeky-status; to continue after reconciliation, hand off to geeky-implement.
---

# geeky-resume

A session cutoff, a compaction summary, and a subagent's "done" are all **claims about state you haven't observed**. This skill re-grounds a geeky run in what the repo actually looks like. Read the durable ledger, reconcile it against git, then decide what to do next.

## Input

`$ARGUMENTS`: a folder produced by `geeky-plan`. Missing or no `kanban.md` → STOP and ask the user.

## Procedure

1. **Read the durable ledger first** — `handoff.md` and `kanban.md`, before touching anything else. Note the last handoff entry's date/claims and every task in `In Progress`, `In Review`, or recently moved to `Done`.

2. **Snapshot via geeky-status.** Run the `geeky-status` skill (or its validators directly) for lane counts, blocked tasks, and inconsistencies. This gives you the *claimed* state.

3. **Reconcile claims against live git — the core step.** For the repo the planning folder targets:
   - `git status` + `git log --oneline` since the last handoff timestamp, and `git diff` / `git diff --cached` for uncommitted work.
   - For each task claimed `Done` or `In Review` since the previous handoff: verify its artifacts exist on disk and its commit actually landed (check the hash in task notes; no hash = unverified claim).
   - For each task in `In Progress`: check whether matching changes exist in the worktree. A subagent that returned empty/0 tokens or died at the boundary progressed **nothing**, regardless of what the kanban says.
   - Don't re-run validation that demonstrably passed pre-cutoff (a cited commit + a PASS line in task notes). Read the recorded result instead of burning turns repeating it.

4. **Classify each discrepancy** and correct the ledger to match verified reality. The *only* edits this skill may make: kanban lane moves and a dated reconciliation note in `handoff.md`.
   - Claimed Done, no commit/artifacts → move back to `Ready` (or `In Progress` if partial work exists in the worktree). Add a `<!-- reconciled YYYY-MM-DD: ... -->` comment.
   - Claimed In Progress, zero trace in worktree → move back to `Ready`.
   - Uncommitted work matching a task → leave the lane, note "uncommitted work present" so geeky-implement commits it before starting anything new.
   - Work in the tree matching **no** task → flag as user-owned or out-of-band. Don't revert or clean it.

5. **Report and hand off.** Print: verified lane counts (post-reconciliation), the discrepancy list with evidence (file paths / commit hashes), and the next step. Normally that's `Resume with /geeky-implement <folder>`, or `Resolve blocked: <Tid>` if something is blocked. Don't start executing tasks yourself — that's geeky-implement's job.

## Hard rules

- Read `handoff.md` + `kanban.md` **before** any other action. Re-read any file before editing it (the pre-cutoff view is stale).
- A pre-cutoff "done" without a verifiable commit/artifact is a hypothesis, not a fact.
- Edits limited to: kanban lane corrections + one dated handoff reconciliation note. No task work, no commits of product code, no subagents.
- Preserve user-owned changes unconditionally.

## Acceptance criteria

- Every lane correction cites the evidence (missing commit, empty diff, existing artifact) that justified it.
- The handoff gains exactly one dated reconciliation entry.
- The report separates verified state from unverified claims and names the next step.
