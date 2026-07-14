---
name: self-audit
description: Use when Gerald asks to look back across PAST Claude Code sessions (on disk, across every repo, not the current one) for recurring mistakes, inefficiencies, struggles, friction, wasted turns, getting stuck, or looping — e.g. "audit our conversations / do a retrospective / post-mortem / where did you have difficulty / what slowed us down / how can you do better / what patterns do you see in how we work." The deep pass that fans out one subagent per project to mine transcript history and propose durable memory/config/skill fixes; for a fast script-only friction scan first, use `session-friction-review`. Do NOT use for "what did we just do in this session" (already in context).
---

# Self-Audit — Cross-Session Retrospective

Gerald has asked for this same retrospective three times (2026-06-09, twice on 2026-06-16) and each time it was rebuilt from scratch — partition the sessions, brief subagents, define the signal patterns, compile the baseline of what's already known. This skill bundles that so the methodology, and the learning loop it feeds, don't get re-derived every time.

The point of the loop: **mine past transcripts → distinguish genuinely new friction from already-documented patterns → check whether prior fixes stuck → promote durable findings into memories/config/skills.** It's how discoveries keep moving forward instead of being re-discovered.

## Method

### 1. Inventory the sessions (reuse `list-sessions`)

Get the project partition and exact per-session file paths from the existing scanner — don't hand-roll a disk walk:

```
py "<this-plugin>/skills/list-sessions/scripts/scan_sessions.py" --format json
```

- Each group = one project/repo. The scanner already separates real conversations from background housekeeping jobs — audit only the **real** ones.
- **Index-only directories** (a `sessions-index.json` but no `.jsonl` files) have metadata but **no message bodies** — their transcripts were purged by retention. They cannot be deep-read. List them as an explicit blind spot in the final synthesis; never dispatch a subagent to read transcripts that aren't there.

### 2. Read the current memory baseline FRESH (so the audit hunts what's *new*)

Read the agent's memory store under the **current user's** home — `~/.claude/projects/<sanitized-project>/memory/` (resolve `~` on this machine; do not assume a specific user profile). Read `MEMORY.md` (the index) and every file it points to — the store is one topical file per fact (`pref-*.md`, `proj-*.md`, `feedback-*.md`, etc.), not a `feedback_*.md`/`user_profile.md` scheme. These are the already-known patterns. The audit's value is finding what is **not yet captured**, or evidence that a documented fix **didn't stick** in sessions postdating it. Read them every run — the corpus grows, and a stale baseline makes subagents re-report things you already fixed.

### 3. Fan out — one subagent per project, all dispatched in a single turn

Parallelism is the whole point; do not serialize. Spawn one `general-purpose` agent per project group in one message. Give each the brief in `references/agent-brief-template.md`, filled in with:
- that project's exact transcript file paths (+ message counts, to flag the big ones),
- the current memory baseline from step 2 (as "already known — find new or corroborating, don't rediscover"),
- the signal patterns below,
- the structured output format.

For large transcripts (1000+ messages — some real ones run 1200): instruct grep-first, targeted-window reads, never a full `Read()`. The transcript JSONL schema and the Grep-not-shell-grep guidance are in the brief template so subagents don't rediscover them.

### 4. Aggregate the returned reports

The cut that has worked well:
- **Behavioral/reasoning patterns** (changeable by memory/skill) vs **environment/infra** (needs a config fix, not a memory — e.g. a broken hook interpreter, model-routing 404s). Most "struggles" are often the latter; separating them tells you what to actually *do* about each.
- **Resolution type per incident:** self-corrected (within turn / a few calls / a later session) vs. user-corrected (quote or paraphrase the correction). Report the honest balance — usually most are self-corrected and genuine user corrections are rare and mild.
- **Cross-session latency:** flag bugs that survived their own session and were only caught later — same-session self-review is weaker than a dedicated later pass at catching schema/completeness defects.
- **Did prior fixes stick?** For each existing memory, note whether postdating sessions show it held, regressed, or wasn't exercised.
- **Blind spots:** the index-only sessions from step 1.

### 5. Propose durable fixes (then act on what the user approves)

- **Memories:** new or updated memory files following the conventions the store's own `MEMORY.md` documents (one topical file per fact, frontmatter, + a one-line index entry). Fold near-duplicates into existing memories rather than proliferating.
- **Config/env/hook fixes:** investigate root cause and prefer a single durable fix over per-file patches (e.g. fix the missing interpreter on PATH once, not every plugin hook that calls it). Plugin cache files get overwritten on update — fix at the source or at the environment layer.
- **Skills:** if the audit surfaces a recurring *method* (not just a fact), encode it as a skill — that's a more durable carrier than a memory. This skill is itself an instance of that.

## Signal patterns to search for

The signal-pattern hypotheses (tool errors, trial-and-error loops, harness
rejections, sharp user corrections, self-correction language, shell friction,
abandoned restarts) are in `references/signal-patterns.md` — include them verbatim
in every subagent brief alongside `references/agent-brief-template.md`.

## Notes

- Cap each subagent at ~6 most significant incidents (ranked by cost × generalizability), not exhaustive enumeration — signal over completeness.
- This skill consumes [[list-sessions]] for its input. Keep them in sync: if the project layout or the sanitized-path scheme changes, the scanner is the single source of truth.
- The reference brief is a template, not a frozen script — adapt per-project hints (e.g. "this project used Playwright, watch for selector retries"; "first prompt is a `<local-command-caveat>` placeholder, real request is further down").
