---
name: self-audit
description: Cross-session retrospective — scans ALL past Claude Code conversations across every repo to find recurring patterns where Claude took more turns than necessary, got stuck, looped on a failing approach, misunderstood the request, or had to be corrected, and documents how each resolved (self-corrected vs. user-corrected), then proposes durable memory/config/skill fixes. Fans out via parallel subagents, one per project. Use this WHENEVER Gerald asks to look back across past sessions for mistakes, inefficiencies, struggles, friction, wasted turns, or "where did you have difficulty / what slowed us down / audit our conversations / do a retrospective / post-mortem / how can you do better / what patterns do you see in how we work." Do NOT use it for "what did we just do in this session" (already in context) — this is specifically for mining the on-disk transcript history of many past sessions. For a FAST deterministic per-session friction scan (signature counts + --since delta, no subagents) use `session-friction-review` first; this self-audit is the deeper orchestrated pass that builds on it.
---

# Self-Audit — Cross-Session Retrospective

Gerald has asked for this same retrospective three times (2026-06-09, twice on 2026-06-16) and each time it was rebuilt from scratch — partition the sessions, brief subagents, define the signal patterns, compile the baseline of what's already known. This skill bundles that so the methodology, and the learning loop it feeds, don't get re-derived every time.

The point of the loop: **mine past transcripts → distinguish genuinely new friction from already-documented patterns → check whether prior fixes stuck → promote durable findings into memories/config/skills.** It's how discoveries keep moving forward instead of being re-discovered.

## Method

### 1. Inventory the sessions (reuse `list-sessions`)

Get the project partition and exact per-session file paths from the existing scanner — don't hand-roll a disk walk:

```
py "C:\Users\gerald.khoo\.claude\skills\list-sessions\scripts\scan_sessions.py" --format json
```

- Each group = one project/repo. The scanner already separates real conversations from background housekeeping jobs — audit only the **real** ones.
- **Index-only directories** (a `sessions-index.json` but no `.jsonl` files) have metadata but **no message bodies** — their transcripts were purged by retention. They cannot be deep-read. List them as an explicit blind spot in the final synthesis; never dispatch a subagent to read transcripts that aren't there.

### 2. Read the current memory baseline FRESH (so the audit hunts what's *new*)

Read every `feedback_*.md` and `user_profile.md` under `C:\Users\gerald.khoo\.claude\projects\C--Users-gerald-khoo--claude\memory\`. These are the already-known patterns. The audit's value is finding what is **not yet captured**, or evidence that a documented fix **didn't stick** in sessions postdating it. Read them every run — the corpus grows, and a stale baseline makes subagents re-report things you already fixed.

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

- **Memories:** new or updated `feedback_*` files following the conventions in `MEMORY.md`'s own format + a one-line index entry. Fold near-duplicates into existing memories rather than proliferating.
- **Config/env/hook fixes:** investigate root cause and prefer a single durable fix over per-file patches (e.g. fix the missing interpreter on PATH once, not every plugin hook that calls it). Plugin cache files get overwritten on update — fix at the source or at the environment layer.
- **Skills:** if the audit surfaces a recurring *method* (not just a fact), encode it as a skill — that's a more durable carrier than a memory. This skill is itself an instance of that.

## Signal patterns to search for

Hypotheses, not a rigid checklist — always read surrounding context, don't pattern-match blindly:

- `is_error` / `"is_error":true` in tool_result blocks → a tool failed and needed a retry.
- The same tool called repeatedly with small variations → trial-and-error loop.
- Harness rejection strings: `"doesn't want to proceed with this tool use"`, `"STOP what you are doing"` → user rejected a tool call.
- Short sharp user messages: `no`, `don't`, `stop`, `that's not what I meant`, `wrong` → explicit correction.
- Assistant self-correction language: `let me reconsider`, `I made a mistake`, `apologies`, `that didn't work`, `actually` → backtracking.
- `command not found`, `exit code 1`, `Cancelled: parallel tool call` → environment/shell friction.
- Repeated identical first-prompts across sessions minutes apart → abandoned restarts (often infra/model-routing, not reasoning — check before blaming the assistant).

## Notes

- Cap each subagent at ~6 most significant incidents (ranked by cost × generalizability), not exhaustive enumeration — signal over completeness.
- This skill consumes [[list-sessions]] for its input. Keep them in sync: if the project layout or the sanitized-path scheme changes, the scanner is the single source of truth.
- The reference brief is a template, not a frozen script — adapt per-project hints (e.g. "this project used Playwright, watch for selector retries"; "first prompt is a `<local-command-caveat>` placeholder, real request is further down").
