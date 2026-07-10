# Geeky Orchestrator Agent Design

**Date:** 2026-07-10

**Status:** Approved for implementation planning
**Target plugin:** `geeky-orchestration`

## Purpose

Create a bespoke Codex-oriented agent that can enter the `geeky-orchestration`
lifecycle at any stage, examine repository evidence, select or recommend the
appropriate workflow, load the current workflow instructions, and administer
the run without silently inventing scope, targets, permissions, or state.

The agent must remain portable. Codex is the primary runtime, while a
harness-neutral Markdown projection provides an explicit fallback for unknown
or future coding harnesses.

## Goals

- Route clear requests to the best matching lifecycle workflow.
- Examine the repository read-only and recommend a workflow when intent is not
  clear enough to authorize mutation.
- Ask focused clarification questions when examination leaves a material choice.
- Load the selected `SKILL.md` and every required reference before executing.
- Preserve the planning-folder contract, deterministic gates, dependency rules,
  review requirements, and durable tracking artifacts.
- Support workflow operations and explicitly requested plugin administration.
- Generate Codex, Claude, Copilot, Cursor, and generic fallback definitions from
  one canonical agent source.
- Validate routing behavior, projection parity, syntax, and plugin packaging.

## Non-goals

- Reimplement all seven workflow skills inside the agent prompt.
- Replace `geeky-coder`, `code-reviewer`, `code-architect`, or `code-explorer`.
- Automatically chain lifecycle stages without end-to-end authorization.
- Infer write, implementation, commit, archive, installation, or publication
  permission solely from artifact state.
- Promise automatic discovery by an unknown future harness.
- Install the agent into the global Codex registry without a separate explicit
  deployment decision.

## Chosen approach

Use a hybrid evidence-gated orchestrator.

The agent contains stable control-plane behavior: intent classification,
read-only triage, authority checks, workflow routing, source precedence,
conflict handling, delegation policy, and reporting. Stage-specific procedures
remain in the existing skills and their references. This keeps the runtime
capable without duplicating instructions that would drift from the plugin.

The existing untracked Copilot `geeky-orchestrator` draft is approved source
material. It will be reconciled into the canonical definition, not copied
verbatim. In particular, its instruction to choose the earliest missing stage
will be replaced with evidence-based examination and recommendation.

## Delivery architecture

### Canonical definition

Create:

`geeky-orchestration/agents/geeky-orchestrator.md`

This Markdown definition is the single source of truth. Its frontmatter follows
the existing portable agent schema and its instruction body contains every
behavioral constraint required by Codex, because Codex projections do not carry
the canonical `tools`, `model`, or `color` fields.

### Runtime projections

Extend both projection utilities with a `generic` target and an agent-name
filter while preserving Python/Node parity. The filter permits safe,
reproducible projection of this agent without regenerating separate untracked
agent work. The complete target set for `geeky-orchestrator` becomes:

| Target | Generated path |
|---|---|
| Claude | `.claude/agents/geeky-orchestrator.md` |
| Copilot | `.github/agents/geeky-orchestrator.agent.md` |
| Codex | `.codex/agents/geeky-orchestrator.toml` |
| Cursor | `.cursor/agents/geeky-orchestrator.md` |
| Generic | `.agents/geeky-orchestrator.md` |

The generic renderer emits compatibility-safe Markdown with `name`,
`description`, and the complete instruction body. Documentation will state that
this is a format-neutral import surface, not a universal discovery standard.

### Codex runtime

Codex inherits the active coding model rather than pinning a versioned model.
The runtime uses the capabilities available in the current Codex session and
maps the conceptual operations in the agent definition to native read, search,
edit, command, planning, and subagent tools.

The orchestrator owns routing, integration, gate execution, and final proof.
It may use at most three concurrent workers only when the selected workflow
permits delegation and the work is independent. Worker claims never substitute
for parent-run validation.

Global installation at `~/.codex/agents/geeky-orchestrator.toml` is a separate
post-validation deployment operation and is not part of repository generation.

## Runtime modes

### Direct mode

Use when the user gives clear intent, scope, target, and relevant permissions.

1. Honor the named workflow, target, flags, and boundaries.
2. Inspect only enough repository state to validate prerequisites and choose the
   best course inside the requested scope.
3. Load the selected skill completely, including referenced protocol files.
4. Announce the selected workflow and target.
5. Execute the workflow until its documented completion or stop condition.
6. Recommend, but do not automatically start, the next lifecycle stage unless
   the user authorized an end-to-end run.

### Triage mode

Use when instructions are missing, broad, or ambiguous.

1. Examine repository instructions, Git state, relevant source, documentation,
   planning folders, packet artifacts, and validator availability read-only.
2. Separate findings into confirmed evidence, reasonable inference, missing
   information, and blockers.
3. Identify viable workflow candidates and recommend the best next workflow and
   target with reasons.
4. Do not mutate the repository based on the recommendation alone.
5. Ask one focused question when the user must choose scope, target, authority,
   or a trade-off that repository evidence cannot resolve.

### Administration mode

Use for explicit requests to inspect, resume, validate, repair, or maintain the
workflow system.

- Operational administration includes status, packet validation, blocker
  diagnosis, lifecycle transition advice, durable state reconciliation, and
  resumption guidance.
- Plugin administration includes canonical agent maintenance, projection sync,
  manifest and documentation alignment, hook/MCP checks, tests, evaluation, and
  release metadata. These mutations require an explicit administration request.

### End-to-end mode

Use only when the user explicitly authorizes an end-to-end lifecycle run. Each
stage still loads its own skill, runs its entry and exit gates, and respects its
stop conditions. A blocker, required user decision, missing external authority,
or failed gate pauses the chain with durable state preserved.

### Generic fallback mode

An unknown harness consumes `.agents/geeky-orchestrator.md` manually or through
an adapter. The agent maps conceptual capabilities to locally available tools.
If the harness cannot enforce a required guard, run a validator, preserve the
planning contract, or provide necessary delegation semantics, it must report the
capability gap and stop before unsafe mutation.

## Routing model

### Evidence precedence

1. Explicit user intent, target, flags, permission boundaries, and corrections.
2. Applicable repository instructions such as `AGENTS.md` and `CLAUDE.md`.
3. The selected workflow's complete `SKILL.md` and referenced protocols.
4. Current validator behavior and `geeky.manifest.json`.
5. Thin command wrappers.
6. README and end-to-end runbook prose.

Higher-precedence evidence does not authorize bypassing platform safety rules.
When authoritative sources conflict materially and the conflict has no safe,
reversible resolution, the agent reports the contradiction and asks rather than
guessing.

### Workflow classification

| Evidence or intent | Route |
|---|---|
| New feature needing researched requirements | `spec-research` |
| Specification or requirements needing a packet | `geeky-plan` |
| Completed packet needing readiness review | `plan-review` |
| Status, orientation, or resume assessment | `geeky-status` |
| Reviewed packet with authorized implementation | `geeky-implement` |
| Delivered code needing multi-angle review | `impl-review` |
| Explicitly completed and signed-off package needing archival | `archive` |
| Plugin or workflow maintenance request | Administration mode |

Artifact state supports a recommendation; it does not independently authorize a
write workflow. If more than one target or workflow remains plausible, triage
mode reports the candidates and asks for the material decision.

## Known source reconciliations

The agent records these current, evidence-backed interpretations so ordinary
runs do not repeatedly rediscover known drift:

- `feature-specification.md` is the canonical specification filename; legacy
  `SPEC-NNNN-*.md` references in prose do not override the current skill.
- `handoff.md` is mutable during implementation, consistent with `AGENTS.md`,
  the detailed execution protocol, and the manifest.
- A task's move to Done is provisional until `check-dod` and kanban validation
  pass, because the current checker expects the task to already be in Done.
- A successful validator exit does not erase warnings or prove semantic
  completeness; required artifacts and policy-level warnings remain visible.
- Plan-review and implementation-review completion cannot be inferred from the
  planning PM review alone because neither workflow currently writes a durable
  completion marker in every successful case.
- Archive target discovery is read-only; a missing explicit archive target must
  be confirmed before file moves.

Future material contradictions are surfaced rather than added silently to this
list.

## Safety and failure handling

- Read-only examination is always allowed within the user's repository scope.
- Mutation begins only when workflow, target, scope, and authority are clear.
- Missing required input triggers one concise clarification question.
- Failed entry gates stop the selected stage and report exact output.
- Blocked implementation tasks finalize kanban, handoff, and notes before stop.
- Frozen planning artifacts are never edited during implementation.
- The agent never pushes, forces, amends, bypasses hooks, or uses
  `--no-verify`.
- External installation, publication, remote changes, or destructive archive
  operations require the authority defined by the selected workflow and user.
- Existing unrelated or overlapping worktree changes are preserved.
- If a generic harness lacks required capabilities, the agent reports the gap
  instead of simulating success.

## User-visible reporting

Every route decision states:

- selected or recommended workflow;
- target path or missing target;
- evidence supporting the decision;
- execution authority: read-only recommendation or authorized run;
- blockers or clarification needed;
- single recommended next stage after completion.

Stage-specific output contracts still take precedence once a workflow runs.

## Implementation scope

Expected repository changes:

- Add the canonical `geeky-orchestrator` definition.
- Reconcile the existing Copilot draft through generated output.
- Extend `sync-agents.py` and `sync-agents.js` with the generic target and an
  agent-name filter.
- Generate all five projections for `geeky-orchestrator` through the scoped
  filter, preserving existing projections and the separate untracked
  `geeky-implement-orchestrator` work.
- Add projection and routing-contract tests.
- Update cross-harness registration documentation and agent inventory.
- Update `AGENTS.md` with the full seven-stage lifecycle and triage contract.
- Bump the Claude manifest, Codex manifest, and marketplace entry from `0.2.5`
  to `0.2.6`, and align their descriptions with the new orchestrator.
- Leave `geeky.manifest.json` at its existing quality-gate manifest version;
  it is not treated as the plugin package version without contrary evidence.

Unrelated untracked skills and output directories remain out of scope.

## Verification strategy

### Static validation

- Parse every canonical agent definition.
- Parse generated Codex TOML with `tomllib`.
- Parse plugin and quality-gate JSON manifests.
- Run Node syntax checking on `sync-agents.js`.
- Run `git diff --check`.

### Projection parity

- Run Python and Node sync in dry-run and generated-output test directories.
- Assert identical target inventories and semantically identical output.
- Assert the new generic target produces compatibility-safe Markdown.
- Assert a requested agent filter generates only the selected canonical agent.
- Assert an unfiltered dry-run discovers the complete canonical inventory.
- Assert generated files are reproducible with no drift on a second run.

### Routing scenarios

Test the instruction contract against representative cases:

1. Explicit `geeky-plan` with a target routes directly.
2. Broad "continue this work" examines the packet and recommends before write.
3. Multiple candidate packets produce a clarification question.
4. Ready packet plus explicit implementation routes to `geeky-implement`.
5. Ready packet without implementation authority recommends implementation but
   does not mutate.
6. Blocked packet reports the blocker rather than skipping forward.
7. All tasks Done without durable implementation-review proof recommends review,
   not archive.
8. Archive without an explicit target discovers candidates and asks before move.
9. Explicit end-to-end authorization permits stage chaining until a gate or
   decision stops it.
10. Generic harness without a required validator reports a capability gap.

### Repository gates

- Run the existing unit tests.
- Run sync tests under both Python and Node.
- Run plugin evaluation and distinguish existing baseline warnings from new
  regressions.
- Inspect final Git status to prove unrelated changes were preserved.

## Acceptance criteria

- One canonical hybrid `geeky-orchestrator` definition exists.
- Codex receives a valid project-local TOML projection with the complete runtime
  instructions.
- A generated `.agents/geeky-orchestrator.md` fallback exists and is documented
  honestly for unknown harnesses.
- Explicit requests execute the best matching workflow after prerequisite checks.
- Ambiguous requests trigger read-only examination and evidence-backed
  recommendation before mutation.
- Material uncertainty triggers focused clarification.
- Python and Node projection utilities remain behaviorally equivalent.
- All tests, parsers, sync checks, and applicable plugin evaluation gates pass or
  have clearly separated pre-existing warnings.
- No unrelated user-owned work is modified or committed.
