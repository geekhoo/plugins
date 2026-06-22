# Operational Routing Map

## Friction To Skill

| Signal | Use |
| --- | --- |
| Windows command, path, runtime, validator, SDK, package manager, DB, or shell failures | `windows-host-preflight` |
| Browser, Playwright, Chrome, localhost, screenshots, canvas, DOM, cache, or static UI proof | `browser-ui-validation-gates` |
| Figma node scope, visual parity, DevExtreme widgets, or design-to-code validation | `figma-ui-scope-parity` |
| Named packets, `geeky-plan`, `plan-review`, `geeky-implement`, `kanban.md`, `handoff.md`, task notes, or stale-doc classification | `packet-workflow-integrity` |
| Parallel workers, subagents, teams, lane prompts, or parent integration | `subagent-orchestration-hygiene` |
| Completion claims, review-again requests, AC verification, source proof, or validation evidence | `source-backed-closeout` |
| Dirty files, baseline comparison, exact commit investigation, or no-change/read-only work | `patch-baseline-safety` |
| Session mining, all-conversation audits, repeated requests, or skill opportunity ranking | `dev-workflows:codex-session-request-mining` |
| Skill creation, validation, plugin cache, marketplace, or plugin-eval work | `skill-creator` plus `dev-workflows:plugin-skill-lifecycle` |
| Explicit "remember this", "carry forward", or "save to memory" request | `dev-workflows:memory-capture` |

## Agent Role Routing

| Need | Agent role |
| --- | --- |
| Current repo file, symbol, relationship, or local usage lookup | `explore` |
| Official docs, external API behavior, release notes, or version-aware reference | `researcher` |
| Package, SDK, framework, upgrade, replacement, license, or maintenance decision | `dependency-expert` |
| Scoped implementation or refactor | `executor` |
| Root cause or regression isolation | `debugger` |
| Completion proof and claim validation | `verifier` |
| Test plan, coverage, or flaky-test hardening | `test-engineer` |
| Plan, architecture, or design challenge | `critic` or `architect` |
| Documentation, prompts, migration notes, or user-facing guidance | `writer` |

## Durable Layer Decision

| Situation | Durable layer |
| --- | --- |
| The future agent needs to know when and how to execute a workflow | Skill |
| A repeated command or inspection needs deterministic output | Script/tool |
| The user explicitly wants a preference or rule carried forward | Ad-hoc memory note |
| A cheap pattern can prevent repeated hook-time mistakes | Warning-only hook rule |
| The work is a one-off result | Workspace output artifact |

## Hook Rules

- Keep hooks warning-only unless the user explicitly asks for enforcement.
- Prefer stdin-based payload handling over command-line JSON arguments.
- Avoid heavy filesystem scans from hooks.
- Keep hook messages short and directly tied to a routing action.
- Validate `hooks.json`, PowerShell syntax, and one representative payload after edits.
