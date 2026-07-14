---
name: handoff-prompt-generator
description: Use when the user asks for a "handoff prompt", "takeover prompt", "resume prompt", "implementation packet", or "read order"; produce a complete takeover prompt with objective, constraints, read order, expected outputs, and validation gates. For updating or creating HANDOFF.md files, use the handoff skill instead.
---

# Handoff Prompt Generator

## Overview

Produce a complete takeover prompt that lets the destination actor continue without hidden conversation context. Optimize for actionable continuity: objective, read order, constraints, expected outputs, validation gates, assumptions, and redaction notes.

**Why this earns its keep:** two sessions built this way each delivered a full work package on a *single* human message — the planning session wrote the kickoff prompt to a file with acceptance gates baked in, and the executing session pasted it, worked autonomously, and closed with evidence. That is the highest steering leverage on record; a well-formed kickoff file replaces a dozen mid-run steers.

## Prerequisites And Clarification

- Identify the audience: Codex thread, external agent, subagent, human engineer, or future self.
- Ask whether the destination environment differs from the current machine, tools, credentials, repo, branch, or runtime.
- Ask whether secrets, private paths, account identifiers, or sensitive operational details must be redacted.
- If the user asks for only an addendum, preserve the existing handoff shape and add only missing context.

## Workflow

1. Restate the objective and current status in one concrete paragraph.
2. Inspect or explicitly mark unavailable the source artifacts needed for the handoff.
3. List the read order for files, docs, logs, tickets, or artifacts the recipient should inspect first.
4. Capture scope boundaries, constraints, ownership cautions, and explicit "do not do" items.
5. Include known completed work, pending work, blockers, assumptions, and decisions already made.
6. Define expected outputs: files to create or edit, reports to return, artifacts to produce, or questions to answer.
7. Add validation gates with exact commands or checks only when they are known from evidence; otherwise mark them as "derive from repo before running."
8. Add the reporting contract: the recipient must **lead with gate status and raw evidence** (command + exit code + salient output), and state any gate not run as **"NOT RUN"** in those words — never imply verification that did not happen.
9. **Persist the prompt to a file** so the human's only job is to paste it into a fresh session. Convention: `docs/<package>/kickoff-<task>.md` for package/repo work, or `~/.claude/kickoffs/<task>.md` for meta/infra work. Name it for the task, not the date. (Skip only if the user explicitly wants it inline in chat.)
10. Redact sensitive data or mark uncertain sensitive details for user review before transfer.

## Verification Gates

- G0: Audience and destination environment are known, or unknowns are called out.
- G1: Source artifacts needed for the handoff were inspected, or unavailable artifacts are called out.
- G2: Objective and scope boundaries are explicit.
- G3: Read order is concrete and ordered.
- G4: Constraints, sensitive-data handling, and assumptions are explicit.
- G5: Validation and reporting requirements are included (reporting contract = gate status + evidence first, "NOT RUN" stated explicitly).
- G6: The prompt is usable without relying on hidden conversation context.
- G7: The prompt is saved to a file under the naming convention (or the user explicitly chose inline).

## Acceptance Criteria

- Another agent can start from the prompt and know what to read, what to build or investigate, what to avoid, and how to report completion.
- Sensitive data is omitted, generalized, or marked for user review.
- The handoff distinguishes confirmed facts from assumptions and unresolved questions.

## Expected Outcome

A complete handoff prompt or addendum with objective, read order, constraints, expected outputs, validation gates, assumptions, and redaction notes — saved to a file under the naming convention (unless the user chose inline), ready to paste into a fresh session with no other setup.

## Common Mistakes

- Writing a status summary instead of a takeover prompt.
- Omitting read order, validation gates, or expected outputs.
- Assuming the recipient has access to hidden conversation history.
- Copying secrets, private tokens, or unnecessary sensitive details.
- Inventing commands, paths, tool availability, or repository state instead of marking them as unknown.
- Using this skill for planning packets that require spec, tasks, kanban, and acceptance mapping; use `planning-packet` for that broader workflow.
