---
name: codex-session-request-mining
description: Use when the user asks to "mine Codex session history", "scan Codex sessions", "audit repeated Codex requests", "rank Codex workflow candidates", or "identify skill opportunities from Codex sessions"; turn local Codex session history into an evidence-backed backlog of reusable skill and tool candidates. Not for Claude Code transcripts — for those use list-sessions, session-friction-review, session-retrospective, or self-audit.
---

# Codex Session Request Mining

## Overview

Turn local Codex session history into an evidence-backed backlog of reusable workflow skill and tool opportunities. Use this as the synthesis wrapper around `codex-session-request-miner`; keep deterministic mining and filtering logic in that companion tool.

Scope: Codex session JSONL only. Claude Code transcripts have a different layout and their own skills — route "mine/scan sessions" requests about Claude history to `list-sessions`, `session-friction-review`, `session-retrospective`, or `self-audit`.

## Companion Miner Source

- Treat `tools/codex-session-request-miner/` as local only after future repo work promotes the miner there.
- Until then, locate the fallback miner script `codex_repeated_request_miner.py` in the user's local Codex working directory; ask the user for its path if it is not obvious. Do not hardcode a machine-specific absolute path.
- If neither path exists, stop and report the missing miner; do not invent mining logic in this skill.

## Prerequisites And Clarification

- Confirm session roots when they are not obvious from the user request or source reports.
- Confirm whether archived sessions are in scope.
- Ask before writing derived reports outside the requested output folder.
- Do not ask when source reports already specify roots and the user asks to regenerate or extend them.

## Workflow

1. Inventory session roots and record which roots are included or skipped.
2. Run the promoted `codex-session-request-miner` or the fallback/source miner to extract user requests from session JSONL.
3. Filter environment context, repo guideline preambles, tool schema prompts, injected skill text, and other boilerplate that is not a real user request.
4. Classify retained user requests into workflow families with clear labels.
5. Rank candidate skills and companion tools by evidence volume and repeatability.
6. Emit both traceable Markdown synthesis and machine-readable JSON.
7. Report assumptions, filter choices, limitations, and any intentional differences from prior counts.

## Verification Gates

- G0 Scope: session roots exist and intended archives are included or excluded explicitly.
- G1 Evidence: the miner excludes known boilerplate classes before request classification.
- G2 Plan: classification labels, ranking basis, and output paths are documented.
- G3 Execution: generated artifacts stay inside the approved output folder.
- G4 Validation: outputs include source roots, retained counts, filtered counts, candidate counts, and limitations.
- G5 Reporting: final response names generated files, count differences, validation run, assumptions, and unresolved risks.

## Acceptance Criteria

- Reproduce high-level counts or explain intentional filter differences.
- Produce traceable Markdown and machine-readable JSON.
- Name candidate skills and tools with evidence volume.
- Keep mining logic in `codex-session-request-miner`; keep synthesis and prioritization in this skill.

## Expected Outcome

A ranked, evidence-backed workflow backlog plus reusable mining artifacts that can be regenerated from the named session roots.

## Common Mistakes

- Counting system prompts, environment context, repo guidelines, or tool schemas as user requests.
- Asking for clarification after the source reports already define roots and the user asked to regenerate or extend them.
- Writing reports outside the requested output folder without permission.
- Reporting only prose summaries without JSON output that downstream tools can consume.
- Treating one-off keyword hits as skill candidates without evidence volume or workflow family labels.
