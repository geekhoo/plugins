---
name: findings-persistor
description: Use when the user asks to "save these findings", "persist the review output", "write a dated findings file", or "record PR feedback or audit results" that already exist; persist existing source-backed findings as a durable Markdown artifact, not for a fresh review.
---

# Findings Persistor

## Overview

Persist transient review or audit findings as a durable Markdown artifact with stable naming, traceable evidence, and clear status. Do not create findings from memory; save only source-backed material or first route through `evidence-review`.

## Prerequisites And Clarification

- Identify the destination folder and filename. Ask if either is missing and cannot be inferred.
- Ask before overwriting an existing findings file.
- Confirm the findings source: review comments, audit notes, PR feedback, prior report, or current source inspection.
- Ensure each finding is source-backed before persisting. If the user only provided a vague request to save findings, use `evidence-review` to produce the findings first.

## Workflow

1. Inspect inputs.
   Read the requested findings source and any current files needed to verify evidence, status, or destination constraints.

2. Normalize findings.
   Capture severity, title, evidence, impact, recommendation, status, and validation for each finding. Use `open`, `confirmed`, `rejected`, `duplicate`, `already-fixed`, or `needs-clarification` when status is not otherwise specified.

3. Choose the file path.
   Use the user-requested filename exactly. Otherwise use a dated, descriptive Markdown filename in the confirmed destination, such as `YYYY-MM-DD-code-review-findings.md`.

4. Write the artifact.
   Include a short scope note, the findings table or sections, source references, unresolved questions, and validation performed or still pending.

5. Verify the artifact.
   Reopen the file and check that evidence, statuses, destination, and filename match the request.

## Verification Gates

- G0 Destination gate: destination folder and filename are known, or a clarification was asked.
- G1 Evidence gate: findings source was inspected and findings are source-backed.
- G3 Write gate: the Markdown file was written at the intended path.
- G4 Content gate: the file contains evidence, statuses, unresolved questions, and validation notes.
- G5 Reporting gate: final response names the persisted file and any placeholder-scan or validation results.

## Acceptance Criteria

- Persisted findings are structured, actionable, and easy to reuse.
- Filename and location match the user request or confirmed fallback.
- Existing files are not overwritten without clear user intent.
- Each finding has enough evidence and status detail to support follow-up work.

## Expected Outcome

A durable findings or audit Markdown file that preserves source-backed review output for later remediation, planning, or handoff.

## Common Mistakes

- Persisting raw chat text without normalizing severity, evidence, recommendation, status, and validation.
- Saving assumptions or memory-derived claims as confirmed findings.
- Overwriting an existing findings file without asking.
- Omitting unresolved questions or unrun validation, making the artifact look more complete than it is.
- Using this skill to create the review itself when `evidence-review` is needed first.
