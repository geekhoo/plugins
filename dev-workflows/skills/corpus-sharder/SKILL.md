---
name: corpus-sharder
description: Use when the user asks to shard a large corpus, chunk or batch files, create one prompt per file, build a coverage manifest, or plan a deterministic merge for an over-large corpus task.
---

# Corpus Sharder

## Overview

Break large corpus work into bounded, reproducible units. Preserve coverage by making every included file, exclusion, shard assignment, prompt, and merge rule explicit.

## Prerequisites and Clarification

Before planning shards, confirm:

- Corpus root or source folder.
- File filters, such as extensions, glob patterns, size limits, or generated-file exclusions.
- Output folder for the manifest, per-shard prompts, and coverage report.
- Shard size target, such as files per shard, token budget, byte budget, or logical grouping.

Ask when file priority, exclusion rules, shard size, or merge expectations are unclear.

## Workflow

1. Create a file inventory from the confirmed corpus root and filters.
2. Record explicit exclusions with reasons.
3. Assign stable shard IDs and metadata: file paths, sizes when useful, grouping rationale, and intended task scope.
4. Write per-shard prompts or task specs that include only the assigned files, expected output format, and local verification instructions.
5. Define a deterministic merge format before shard execution begins.
6. Produce coverage checks that compare intended files against assigned files and flag duplicates, omissions, or unaccounted exclusions.
7. Use `document-corpus-pipeline` when the work continues into a larger document-corpus processing pipeline.
8. Stop at inventory, shard prompts, merge format, and coverage; document conversion, classification, per-file evidence, normalization, and synthesis belong to `document-corpus-pipeline`.

## Verification Gates

- G0: Corpus root is known.
- G1: Inventory is generated from the agreed filters.
- G2: Shard plan is complete with stable IDs and metadata.
- G4: Coverage check confirms all intended files are assigned exactly once.

Do not start per-shard execution until G0 through G2 pass. Do not report the shard plan complete until G4 passes.

## Acceptance Criteria

- No intended files are dropped.
- Shard outputs can be merged deterministically.
- Exclusions are explicit and justified.
- Per-shard prompts are bounded enough for independent execution.
- The coverage report identifies included files, excluded files, duplicates, and omissions.

## Expected Outcome

Deliver a chunk manifest, per-shard execution plan, deterministic merge format, and coverage report.

## Common Mistakes

- Planning shards from memory instead of a generated inventory.
- Hiding exclusions inside prose instead of listing them in the manifest or coverage report.
- Mixing merge instructions into individual shard prompts without a single canonical merge format.
- Letting shard IDs depend on transient ordering from an unsorted file listing.
- Treating "large corpus" as a reason to skip verification instead of the reason to add coverage checks.
