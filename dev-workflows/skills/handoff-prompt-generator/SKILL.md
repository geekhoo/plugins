---
name: handoff-prompt-generator
description: Use when the user asks for a "handoff", "takeover prompt", "resume prompt", "implementation packet", or "read order"; produce a complete takeover prompt with objective, constraints, read order, expected outputs, and validation gates.
---

# Handoff Prompt Generator

## Overview

Produce a complete takeover prompt that lets the destination actor continue without hidden conversation context. Optimize for actionable continuity: objective, read order, constraints, expected outputs, validation gates, assumptions, and redaction notes.

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
8. Add reporting requirements: what completion should include, what evidence to cite, and how to flag limitations.
9. Redact sensitive data or mark uncertain sensitive details for user review before transfer.

## Verification Gates

- G0: Audience and destination environment are known, or unknowns are called out.
- G1: Source artifacts needed for the handoff were inspected, or unavailable artifacts are called out.
- G2: Objective and scope boundaries are explicit.
- G3: Read order is concrete and ordered.
- G4: Constraints, sensitive-data handling, and assumptions are explicit.
- G5: Validation and reporting requirements are included.
- G6: The prompt is usable without relying on hidden conversation context.

## Acceptance Criteria

- Another agent can start from the prompt and know what to read, what to build or investigate, what to avoid, and how to report completion.
- Sensitive data is omitted, generalized, or marked for user review.
- The handoff distinguishes confirmed facts from assumptions and unresolved questions.

## Expected Outcome

A complete handoff prompt or addendum with objective, read order, constraints, expected outputs, validation gates, assumptions, and redaction notes.

## Common Mistakes

- Writing a status summary instead of a takeover prompt.
- Omitting read order, validation gates, or expected outputs.
- Assuming the recipient has access to hidden conversation history.
- Copying secrets, private tokens, or unnecessary sensitive details.
- Inventing commands, paths, tool availability, or repository state instead of marking them as unknown.
- Using this skill for planning packets that require spec, tasks, kanban, and acceptance mapping; use `planning-packet` for that broader workflow.
