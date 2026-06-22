---
name: codex-operational-stabilizer
description: Use when the user asks to stabilize Codex learning into repeatable workflows, reduce wasted rounds, remember skill routing, create or update workflow skills, align agents/subagents with guidelines, build environment preflight tools, inspect or repair Codex hooks, or turn conversation-audit findings into durable local Codex operating assets.
---

# Codex Operational Stabilizer

## Overview

Convert repeated Codex friction into durable, validated operating assets: skill routing, memory notes, warning-only hooks, subagent/agent guidance, and small deterministic tools.

Use this skill as the coordinating wrapper. Load only the referenced guardrail skill that matches the current failure shape.

## Operating Defaults

Apply these defaults when stabilizing future Codex work:

- Start broad tasks with a source inventory: what will be scanned, what will be excluded, and the stop condition.
- Treat named workflows, packet folders, target paths, `kanban.md`, `handoff.md`, and task notes as execution contracts.
- Use Windows preflight early: confirm shell, cwd, repo root, commands, env vars, and likely validator path before deep debugging.
- Avoid broad recursive scans unless justified; prefer known indexes, explicit folders, `rg`, and narrow evidence paths.
- Validate before claiming completion: define the claim, run the smallest proof, read output, and report pass/fail/gap.
- Keep durable artifacts current during work, including task notes, handoffs, kanban state, reports, prompts, and output files.
- Prefer `C:\Users\gerald.khoo\geekhoo-plugins` as the durable source-of-truth plugin for stable skills, hooks, tools, and agent configuration; keep `.codex` copies only as the active installed/runtime layer until plugin exposure is verified.
- Use subagents only for bounded independent slices, with concrete prompts and parent-owned integration.
- Treat output format as a contract: JSON, table, report, review, prompt, or checklist shape comes before commentary.
- Separate host/tool failures from repo defects after one or two unrelated failures, then switch strategy instead of thrashing.
- Lead final answers with outcome, evidence, changed files or artifacts, and remaining risks. Keep process recap secondary.

## Workflow

1. Scope the stabilization target:
   - Identify the source evidence: audit report, session logs, memory note, failing hook, agent config, or repeated user correction.
   - State allowed write roots before editing. Typical roots are `C:\Users\gerald.khoo\geekhoo-plugins`, `~/.codex/skills`, `~/.codex/hooks`, `~/.codex/agents`, `~/.codex/memories/extensions/ad_hoc/notes`, and the current workspace `outputs`.
   - Treat production systems, credentials, marketplace publishing, pushes, and destructive cleanup as out of scope unless explicitly requested.

2. Classify the friction:
   - Read `references/routing-map.md` when choosing which guardrail skills, agent roles, or hooks should handle the situation.
   - Prefer improving an existing skill or hook rule before creating a new artifact.
   - Create a new skill only when the pattern is stable, repeated, and not already covered by a narrower skill.

3. Stabilize through the least invasive durable layer:
   - Skill: add or update concise workflow instructions when future agents need procedural guidance, preferring `dev-workflows/skills/<skill-name>` in the core plugin for stable reusable workflows.
   - Script/tool: add a deterministic script when the same inspection or validation would otherwise be rewritten, bundling it inside the owning skill or plugin hook folder.
   - Memory note: write one ad-hoc note only when the user explicitly asks to remember, carry forward, or preserve a durable preference.
   - Hook: add warning-only routing when a cheap prompt/command pattern can prevent repeated mistakes. Keep hooks stdin-based and non-blocking, and preserve the working `.codex/hooks` shim until plugin hook exposure is verified.
   - Agent guidance: route to existing agents by role; avoid creating or editing agent TOML unless a concrete missing role blocks work.

4. Align with this Windows host:
   - Use `windows-host-preflight` before command-heavy, repo, validator, SDK, package-manager, DB, hook, or plugin work.
   - Run `scripts/codex_operational_preflight.py` when checking local Codex readiness, hook shape, skills, agents, commands, and session stores.
   - After two unrelated host-command failures, classify the host/tool boundary and switch strategy.

5. Repair hooks conservatively:
   - Inspect `~/.codex/hooks.json` and referenced hook scripts before editing.
   - Preserve working PowerShell shim patterns: stdin payloads, `UseShellExecute = $false`, warning-only guards, bounded timeout.
   - Patch only the failing or missing rule. Validate with a small representative payload or static parse.

6. Use agents/subagents deliberately:
   - Use `explore` for repo facts, `researcher` for official external docs, `dependency-expert` for package choices, `executor` for scoped implementation, `verifier` for completion proof, `critic` for plan/design challenge, and `test-engineer` for test strategy.
   - Use `subagent-orchestration-hygiene` before parallel subagents. Worker prompts must be concrete, bounded, placeholder-free, and parent-owned for integration.

7. Validate and close:
   - Run `quick_validate.py` for skill changes.
   - Run the preflight script for environment-alignment changes.
   - For hook edits, validate JSON and run a representative hook payload when safe.
   - Report changed files, validation commands, pass/fail results, skipped gates, and remaining risks.

## Resources

- `references/routing-map.md`: friction-to-skill, agent-role, durable-layer, and hook-routing map.
- `scripts/codex_operational_preflight.py`: local Codex environment, hook, skill, agent, command, and session-store inspection.
