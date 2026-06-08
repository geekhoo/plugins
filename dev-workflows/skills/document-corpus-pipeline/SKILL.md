---
name: document-corpus-pipeline
description: Use when the user asks to process many documents, analyze a document corpus, convert PDF or Markdown, classify each article with confidence, or synthesize source-backed reports by running a per-document pipeline over a large document set.
---

# Document Corpus Pipeline

## Overview

Run large document-set work without overloading context. Preserve file-level evidence first, then synthesize only from traceable per-file artifacts.

## Prerequisites And Clarification

- Identify the source folder/files, desired output format, taxonomy or labels, confidence scale, citation requirements, and destination for generated artifacts.
- Ask when classification labels, report audience, output format, source scope, or citation rules are unclear.
- Ask before destructive conversion, deleting intermediate artifacts, or overwriting generated outputs.
- Use `corpus-sharder` when inventorying, chunking, or prompt generation needs a separate bounded shard plan.
- Use `parallel-review-orchestrator` only when the user explicitly requests subagent or one-agent-per-document sharding.

## Workflow

1. Define the corpus and target output.
   - Confirm included files, excluded files, output type, audience, taxonomy, confidence scale, and citation style.
2. Inventory files.
   - List each source path, type, size when useful, readable status, and whether conversion is required.
   - Record skipped or unreadable files with reasons immediately.
3. Convert source files when needed.
   - Convert PDFs, Markdown, or other formats into inspectable text artifacts without replacing originals unless explicitly approved.
   - Preserve source filenames or stable IDs through conversion and downstream outputs.
4. Plan shards.
   - Shard by file, topic, or bounded batch so each pass can finish within context and tool limits.
   - Define the per-file output schema before processing begins.
5. Produce per-file evidence artifacts.
   - Capture source path, summary, relevant excerpts or citations, labels, confidence, uncertainty, and any extraction issues.
   - Do not synthesize across files until the per-file pass is complete enough for the requested scope.
6. Normalize results.
   - Reconcile labels, confidence values, citation style, file IDs, and skipped-file reasons across artifacts.
7. Synthesize the final output.
   - Build the requested report, table, or deck from per-file artifacts.
   - Keep claims bounded by recorded evidence and cite the supporting file artifacts.
8. Report coverage.
   - Include processed files, skipped files, conversion notes, unresolved uncertainty, and where outputs were written.

## Verification Gates

| Gate | Requirement |
| --- | --- |
| G0 | Corpus scope and output target are known. |
| G1 | File inventory is complete, including skipped or unreadable files. |
| G2 | Taxonomy, confidence scale, output schema, and shard plan are defined. |
| G3 | Per-file passes are completed or explicitly marked skipped with reasons. |
| G4 | Final synthesis references per-file evidence and does not exceed it. |
| G5 | Final report lists coverage, skipped files, limitations, and output locations. |

## Acceptance Criteria

- Every included file has traceable evidence or a documented skip reason.
- Classification labels and confidence values use the agreed taxonomy and scale.
- Final synthesis cites or maps back to per-file evidence artifacts.
- Skipped files, failed conversions, and uncertainty are visible in the final output.
- No destructive conversion or overwrite occurs without explicit user approval.

## Expected Outcome

A source-backed corpus synthesis with per-file artifacts, normalized labels and confidence, coverage reporting, and the requested final report, table, or deck.

## Common Mistakes

- Jumping directly to synthesis before creating per-file evidence.
- Losing source filenames or file IDs during conversion.
- Letting the final report imply coverage of skipped or unreadable files.
- Inventing classifications, confidence values, or citations beyond the recorded evidence.
- Running subagent sharding without explicit user request.
- Overwriting originals or generated outputs without approval.
