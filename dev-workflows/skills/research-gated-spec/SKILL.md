---
name: research-gated-spec
description: Use when the user asks to "research first", "compare current options with sources", "use official docs or web search", "cite sources", or "write a spec only after research"; gate spec authoring behind a cited, source-backed research pass.
---

# Research-Gated Spec

## Overview

Use this skill to turn current research into a source-backed decision note or implementation spec before code changes begin. The goal is to avoid outdated assumptions and connect findings to repo-specific requirements.

## Prerequisites And Clarification

- Determine whether current web research is required because facts are time-sensitive, niche, legal, financial, product-specific, API-specific, or vendor-specific.
- Ask about decision criteria when the user goal, tradeoff priorities, or target system constraints are not obvious.
- Ask before doing broad research when the requested implementation scope is small and stable.
- Confirm the target repo, docs, protected paths, and output shape when they are not already clear.

## Workflow

1. Restate the research question, decision criteria, scope boundaries, and expected spec output.
2. Convert the ask into focused source queries that can answer the decision, not a broad literature search.
3. Prefer primary sources, official docs, current vendor references, standards, changelogs, and repo evidence.
4. Record source links, publication or updated dates when available, and any freshness limits.
5. Synthesize tradeoffs, constraints, and recommendations; separate confirmed facts from assumptions.
6. Map each meaningful finding to an implementation choice, requirement, non-goal, or unresolved question.
7. Produce a decision note or implementation spec, then review gaps before implementation starts.

## Verification Gates

- G0: Research question, decision criteria, scope, and output shape are known.
- G1: Source quality and recency have been checked; primary sources are preferred where available.
- G2: Findings are mapped to implementation choices and repo constraints.
- G3: Decision note or spec has been produced within the agreed scope.
- G4: Citations are included and current where needed.
- G5: The spec states confidence, assumptions, unresolved risks, and any research gaps.

## Acceptance Criteria

- Sources are relevant, traceable, and recent enough for the decision.
- Recommendations connect directly to user goals and repo constraints.
- The spec distinguishes facts, inferences, assumptions, and open questions.
- Implementation does not start until research gaps are addressed or explicitly documented.

## Expected Outcome

A source-backed decision note or implementation spec with citations, tradeoffs, recommended direction, confidence level, assumptions, unresolved risks, and implementation-facing requirements.

## Common Mistakes

- Starting implementation while source quality, recency, or decision criteria are still unclear.
- Treating summaries, blogs, or memory as equivalent to current primary sources.
- Citing links without extracting the decision-relevant fact, date, and implication.
- Producing generic recommendations that do not map back to user goals or repo constraints.
- Use `evidence-review` for review-only source-backed critiques, `docs-sync` for documentation refresh work, and `planning-packet` for larger multi-file planning packets.
- Using this skill for larger multi-file delivery plans; use `planning-packet` for that scope.
