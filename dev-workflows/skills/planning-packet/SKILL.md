---
name: planning-packet
description: Use when the user asks for a "planning packet", "spec plus plan plus tasks plus kanban plus handoff", "geeky-plan-style packet", "acceptance-criteria mapping", or a "gap review of packet files"; produce or audit a linked multi-artifact planning packet.
---

# Planning Packet

## Overview

Turn broad requirements into a linked, delivery-ready planning packet another agent can implement. Favor repo-grounded evidence, explicit scope, consistent task IDs, and validation gates over a conceptual memo.

## Prerequisites And Clarification

- Gather the target repo, objective, user requirements, existing docs, task trackers, constraints, protected paths, and requested delivery format.
- Ask when the objective, acceptance criteria, target repo, allowed edit surface, output folder, or packet format is ambiguous.
- Block implementation planning when unresolved ambiguity creates high risk; if the user wants progress anyway, document the assumption and risk in the packet.
- Inspect current repo/context before relying on memory or prior summaries.

## Workflow

1. Define scope and outcome.
   - State the implementation objective, non-goals, affected systems, protected paths, and expected final state.
   - Record assumptions separately from confirmed evidence.
2. Gather evidence.
   - Inspect relevant source, docs, configs, tests, trackers, prior packets, and validation scripts.
   - Cite current files, commands, tickets, or user requirements that justify each major plan decision.
3. Draft the packet files requested by the user.
   - Include spec, tasks, kanban, references, acceptance criteria, and handoff when the format is open.
   - Keep IDs stable across files, for example `T001`, `AC001`, and `R001`.
4. Map work to acceptance.
   - Every implementation task must map to at least one acceptance criterion or explicitly be setup/validation work.
   - Every acceptance criterion must have owning tasks and a validation method.
5. Build the kanban.
   - Use statuses that reflect reality: planned, ready, in-progress, blocked, done, or deferred.
   - Include blockers and dependencies instead of hiding them in prose.
6. Write the handoff.
   - Include read order, scope boundaries, task order, validation gates, expected outputs, known risks, and open questions.
   - Use `handoff-prompt-generator` for standalone takeover prompts that do not need the full packet.
7. Validate packet structure before implementation starts.
   - Check ID consistency, task/status alignment, acceptance coverage, references, and handoff completeness.
   - For geeky-plan-format packets, run the geeky-orchestration plugin's validators: `geeky_validate_kanban`, `geeky_validate_task_schema`, and `geeky_check_dod` (MCP tools; `geeky_validate_planning_folder` covers the whole folder). For other formats, perform a manual consistency pass and state that no validator was available.
8. Report state.
   - Mark the packet `ready`, `partial`, or `blocked`.
   - List changed files, evidence inspected, validation performed, assumptions, and unresolved risks.

## Verification Gates

The geeky validators (`geeky_validate_kanban` / `geeky_validate_task_schema` / `geeky_check_dod`) apply only to geeky-plan-format packets; for other formats their absence does not block packet creation, but requires a stated manual consistency checklist.

| Gate | Requirement |
| --- | --- |
| G0 | Objective, scope, output format, and protected paths are known or called out. |
| G1 | Relevant repo/context, requirements, docs, trackers, and constraints were inspected. |
| G2 | Packet files are drafted with linked task, acceptance, reference, and handoff IDs. |
| G3 | Tasks map to acceptance criteria, dependencies, statuses, and validation methods. |
| G4 | Packet consistency is checked by the geeky validators (geeky-format packets) or by a manual pass. |
| G5 | Final report identifies ready, blocked, or partial state with assumptions and risks. |

## Acceptance Criteria

- Packet is complete enough for another agent to implement without hidden conversation context.
- Tasks map to acceptance criteria, and acceptance criteria map to validation methods.
- Kanban statuses, task IDs, references, and handoff instructions are consistent across packet files.
- Handoff includes read order, validation gates, expected outputs, risks, and open questions.
- High-risk ambiguity is resolved before implementation or documented as a blocker/assumption.

## Expected Outcome

A delivery-ready planning packet containing implementation scope, spec, task breakdown, kanban/status view, acceptance mapping, references, risks, open questions, and handoff instructions.

## Common Mistakes

- Writing a narrative memo instead of linked packet artifacts.
- Starting implementation while objective, acceptance criteria, or target repo is still ambiguous.
- Letting task IDs, acceptance IDs, references, or kanban statuses drift across files.
- Omitting validation gates or inventing commands that were not derived from repo evidence.
- Treating blocked assumptions as ready work.
- Producing only a standalone handoff when the user asked for spec, tasks, kanban, and acceptance mapping.
