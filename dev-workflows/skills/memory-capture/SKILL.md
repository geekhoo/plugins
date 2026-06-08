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
   - Scope, repo, path, or situation where it applies.
   - Rule, preference, blocked state, cleanup guardrail, or workflow instruction to preserve.
   - Brief evidence or context that makes the note understandable later.
2. Write exactly one small Markdown note under the user's Codex memory notes directory (`~/.codex/memories/extensions/ad_hoc/notes/`; ask the user if the location differs).
3. Name the note `<timestamp>-<short-slug>.md`; use a timestamp precise enough to avoid collisions.
4. Keep the note focused. Prefer short sections such as `Scope`, `Memory`, and `Context`.
5. Do not edit `MEMORY.md`, `memory_summary.md`, rollout summaries, generated memory indexes, or unrelated notes.
6. In the final response, name the created note path and summarize the captured memory.

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
