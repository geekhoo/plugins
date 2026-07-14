---
name: geeky-resume
description: Use when resuming a geeky-plan / geeky-implement run after a session cutoff, compaction, crash, or dead subagent — "resume the implementation", "continue where we left off", "are you stuck". Reconciles kanban lanes and handoff claims against live git status/diff before any work continues; never trusts a pre-cutoff "done". For a snapshot without resuming, use geeky-status; to continue execution after reconciliation, hand off to geeky-implement.
---

# geeky-resume

A session cutoff, a compaction summary, and a subagent's "done" are all **claims about state you have not observed**. This skill re-grounds a geeky run in live ground truth before anything continues. It is the geeky-orchestration form of the standing resume reflex: read the durable ledger first, then reconcile it against the repo.

## Input

`$ARGUMENTS`: a folder produced by `geeky-plan`. If missing or it contains no `kanban.md`, STOP and ask the user.

## Procedure

1. **Read the durable ledger first** — `handoff.md` and `kanban.md`, before touching anything else. Note the last handoff entry's date/claims and every task sitting in `In Progress`, `In Review`, or recently moved to `Done`.

2. **Snapshot via geeky-status.** Run the `geeky-status` skill (or its validators directly) for lane counts, blocked tasks, and inconsistencies. Its output is the *claimed* state.

3. **Reconcile claims against live git — the core step.** For the repo the planning folder targets:
   - `git status` + `git log --oneline` since the last handoff timestamp, and `git diff` / `git diff --cached` for uncommitted work.
   - For each task claimed `Done` or `In Review` since the previous handoff entry: verify its artifacts actually exist on disk and its commit actually landed (check the hash cited in the task notes; if none is cited, treat the claim as unverified).
   - For each task in `In Progress`: check whether any matching changes exist in the worktree at all. A subagent that returned empty/0 tokens or died at the boundary progressed **nothing**, even though the kanban says In Progress.
   - Never re-run validation that demonstrably passed pre-cutoff (a cited, real commit + a PASS line in the task's notes) — read the recorded result instead of burning turns repeating it.

4. **Classify each discrepancy** and correct the ledger to match verified reality — the *only* edits this skill may make are kanban lane moves and a dated reconciliation note in `handoff.md`:
   - claimed Done, no commit/artifacts → move back to `Ready` (or `In Progress` if partial work exists in the worktree), with a `<!-- reconciled YYYY-MM-DD: ... -->` comment.
   - claimed In Progress, zero trace in worktree → move back to `Ready`.
   - uncommitted work that matches a task → leave the lane, note "uncommitted work present" so geeky-implement commits it before starting anything new.
   - work in the tree matching **no** task → flag as user-owned or out-of-band; never revert or clean it.

5. **Report and hand off.** Print: verified lane counts (post-reconciliation), the discrepancy list with evidence (file paths / commit hashes), and the next step — normally `Resume with /geeky-implement <folder>`, or `Resolve blocked: <Tid>` if anything is blocked. Do not start executing tasks yourself; execution belongs to `geeky-implement`.

## Hard rules

- Read `handoff.md` + `kanban.md` **before** any other action; re-`Read` any file before editing it (the pre-cutoff view is stale).
- A pre-cutoff "done" (yours or a subagent's) without a verifiable commit/artifact is a hypothesis, not a fact.
- Edits limited to: kanban lane corrections + one dated handoff reconciliation note. No task work, no commits of product code, no subagents.
- Preserve user-owned changes unconditionally.

## Acceptance criteria

- Every lane correction cites the evidence (missing commit, empty diff, existing artifact) that justified it.
- The handoff gains exactly one dated reconciliation entry.
- The report separates verified state from unverified claims and names the next step.
