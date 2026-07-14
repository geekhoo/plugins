---
name: memory-capture
description: Use when the user explicitly asks to "remember this", "save to memory", "note for next time", "carry forward", or "preserve a preference or rule" — capture a durable preference, guardrail, or instruction into the memory store.
---

# Memory Capture

## Overview

Use this skill only for explicit durable memory requests. Create one scoped ad-hoc memory update note and do not edit canonical memory files directly.

## Prerequisites And Clarification

- Verify the user explicitly asked to remember, note, save, memorize, carry forward, or preserve something.
- Confirm the memory content is small, scoped, and actionable.
- Ask before writing if the requested memory is ambiguous, sensitive, too broad, or not clearly durable.
- Do not write memory for ordinary task context, inferred preferences, or incidental facts.

## Workflow

1. Extract the memory contract:
   - Scope, repo, path, or situation where it applies. **Prefer the narrowest scope that is still true** — a workspace/repo-specific memory beats a global one when the fact only applies there.
   - Rule, preference, blocked state, cleanup guardrail, or workflow instruction to preserve.
   - Brief evidence or context that makes the note understandable later.
2. Write into the **active harness's memory store** (not a Codex-only path):
   - **Claude Code** (this harness): follow the agent's memory-store convention — one Markdown file per fact under the session's memory directory (`~/.claude/projects/<sanitized-project>/memory/`), with frontmatter (`name`, `description`, `metadata.type` = user | feedback | project | reference), then a one-line pointer appended to that store's `MEMORY.md` index. Before creating a new file, check for an existing memory that already covers the fact and update it instead of duplicating.
   - **Codex**: write one ad-hoc note under the Codex memory notes directory (`~/.codex/memories/extensions/ad_hoc/notes/`).
   - If the store location is unclear, ask the user rather than guessing.
3. Name a new file `<short-kebab-slug>.md` (Claude Code) or `<timestamp>-<short-slug>.md` (Codex ad-hoc).
4. Keep it focused — the single fact plus, for feedback/project types, **Why:** and **How to apply:** lines.
5. In Claude Code, the `MEMORY.md` index line is expected and correct; do NOT rewrite unrelated memories, generated indexes, or another store's notes. In Codex, do not edit canonical summaries or rollout files.
6. In the final response, name the created/updated file path (and the index line, if added) and summarize the captured memory.

## Verification Gates

- G0: An explicit user request to remember exists.
- G2: The note content is scoped, small, and actionable.
- G4: Exactly one note file was created in the ad-hoc notes directory.
- G5: The final response names the note path.

## Acceptance Criteria

- Only one focused note is created.
- The memory is scoped to a repo, path, workflow, preference, or durable situation when relevant.
- No canonical memory files or unrelated notes are edited.
- Ambiguous, sensitive, or broad memory requests are clarified before writing.

## Expected Outcome

A durable, minimal ad-hoc memory update note that future memory indexing can ingest without bloating or silently changing canonical memory.

## Complexity Split

- Use `scope-guard` when the remembered content is about protected paths, write boundaries, cleanup rules, or user-owned changes.
- Use `resume-inventory` when available and the remembered content is mainly about blocked or resumable work state.

## Common Mistakes

- Capturing memory because context seems useful but the user did not explicitly ask.
- Writing broad preferences that lack scope or later decision value.
- Editing canonical memory files directly.
- Creating multiple notes for one memory request.
- Omitting the note path from the final response.
