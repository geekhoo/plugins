---
name: list-sessions
description: Inventories every Claude Code session/conversation across ALL project directories under ~/.claude/projects (or any --claude-dir), grouped by repo/project path, with background housekeeping jobs (memory-consolidation agents, daily-log summarizers) separated out from real conversations. Use this whenever the user asks to find, list, recall, or search past sessions or conversations "across all repos/projects," "everywhere," or "across the whole machine" — including typo'd phrasings like "conversions" — or asks what's been worked on historically outside the current session's own context. Also use it to spot-check whether a specific past conversation exists, on what date, or in which repo, when `.remember/recent.md` doesn't have it because it wasn't deemed "notable" enough for that rollup. Do NOT use this for "what did we just do" or "what happened earlier in this session" (already in context) or for git history questions (use git log) — this is specifically for cross-session Claude Code transcript history that requires scanning disk.
---

# List Sessions

Gerald has asked for a full cross-repo session inventory three times (2026-06-10, twice on 2026-06-16) because there was no fast way to get it — each time required a fresh full-disk scan of `~/.claude/projects`. This skill bundles that scan into one script so the methodology doesn't get re-derived from scratch every time.

## Quick path

Run the bundled script and relay its Markdown output (lightly edited, if at all):

```bash
python scripts/scan_sessions.py
```

This scans `~/.claude/projects` by default. It's plain Python with no shell-specific syntax, so it runs the same way from PowerShell or Bash.

Useful flags for follow-up questions — reach for these instead of re-scanning by hand:

- `--project <substring>` — narrow to one repo, e.g. `--project v2` or `--project mf-dx-cc`
- `--since <ISO date>` — only sessions created on/after that date, e.g. `--since 2026-06-01`
- `--show-background` — list background jobs individually instead of just a count
- `--format json` — structured output, for when you need to compute something further rather than display a report
- `--claude-dir <path>` — point at a different profile's `.claude` dir (relevant if Gerald ever confirms the second `GERALD-1-KHO` profile shares this disk)

## What it does and why

For each subdirectory of `~/.claude/projects` (one per sanitized cwd path):

1. **Prefers `sessions-index.json` when present.** Some project directories only retain this index — the raw `.jsonl` transcripts get purged by the `cleanupPeriodDays` retention setting, but the index survives and still has `firstPrompt`/`messageCount`/timestamps per session. Reading it is the only way to recover those sessions at all.
2. **Falls back to scanning top-level `*.jsonl` files** for everything not already covered by the index. It samples the first ~40 lines of each file (just enough to find the first real `user`-type prompt, the `cwd`, and `gitBranch`) rather than loading the whole file — some transcripts run several MB and don't need a full parse just to find a topic. It still counts every line for an approximate message count, but that's cheap line-counting, not JSON parsing.
3. **Never counts subagent runs as separate conversations.** Subagent transcripts live nested under `<session-uuid>/subagents/*.jsonl`, which a non-recursive `*.jsonl` glob on the project directory naturally skips. Index entries with `isSidechain: true` are excluded the same way.
4. **Classifies background housekeeping jobs by first-prompt content**, not by location — sessions whose first prompt matches a known stereotyped pattern (the `.remember` skill's memory-consolidation and daily-log-summary agents) get bucketed separately and rolled up to a count instead of listed individually, since they aren't conversations Gerald had. The pattern list is `DEFAULT_BACKGROUND_PATTERNS` at the top of `scripts/scan_sessions.py`. **If you spot a new stereotyped background-job prompt that isn't caught**, add it to that list rather than passing `--background-pattern` ad hoc each time, so every future run catches it automatically.
5. **Resolves each group's display path from real data, not guesswork.** It prefers `cwd` (from a transcript line) or `projectPath` (from the index) over reverse-engineering the sanitized directory name, because that sanitization (`:`, `\`, `.` all collapse to `-`) is lossy and ambiguous wherever the real path itself contains a dash (e.g. `mf-dx-cc`). If no session in a group has either field, the report shows the raw directory name and flags it as inferred rather than guessing wrong.

## Presenting results

Group by resolved project path, real conversations first (as a table: created timestamp, message count, first prompt), then a one-line background-job rollup per group, then a totals line at the end (files / real conversations / background jobs / project count) — this is what the script already renders, so in the common case just relay it. Only reformat if Gerald asks for something the script's flags don't already cover.

## A faster, curated alternative — when available

`mcp__ccd_session_mgmt__list_sessions` (check via `ToolSearch("session management list sessions")`) returns a smaller, human-titled, deduplicated list with `isArchived`/`isRunning`/`lastActivityAt`. It's nicer to read when present, but its availability has been inconsistent session-to-session on this machine, and it doesn't cover the purged-transcript or background-job classification cases the script handles. Treat it as a quick first look, not a replacement — fall back to the script whenever completeness matters or the tool isn't loaded.

## Also check `.remember/` first for "what mattered recently"

`.remember/recent.md` and `.remember/today-*.md` are a curated, human-readable rollup maintained by background agents — fast to read, but sparse (only sessions judged "notable" show up). Good for a quick recency check before running the full scan; not a substitute for it when Gerald wants the exhaustive list.
