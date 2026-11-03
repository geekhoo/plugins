# Documentation findings and actions

Reviewed on 3 November 2026 against the working checkout at `ea94635d2f76918f4a01699aea3e356f90954033`. Each row records a stale claim corrected during this refresh. Original run results and frozen case requirements were preserved.

| Document | Correction | Owning evidence |
|---|---|---|
| mxc-sandbox/skills/mxc-setup/SKILL.md | Match executable resolution. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:33-34 |
| mxc-sandbox/skills/mxc-setup/SKILL.md | Describe explicit containment accurately. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:221-225 |
| mxc-sandbox/skills/mxc-run/SKILL.md | Request inherits default environment. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:186-210,247-248,314-324 |
| mxc-sandbox/skills/mxc-run/SKILL.md | A passed token is available to the workload and the private directory persists. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:42,116-118,185-190,314-320 |
| mxc-sandbox/skills/mxc-run/SKILL.md | Account for the documented loopback option. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:232-241 |
| mxc-sandbox/skills/mxc-run/references/recipes.md | Avoid an exclusive authentication claim and clarify credential exposure. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:42,185-190,247-248,314-330 |
| mxc-sandbox/README.md | Environment is inherited and --env applies last. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:42,185-190,247-248,314-330 |
| mxc-sandbox/README.md | Clarify that the workload can access the value. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:190-194,321-324,450-455 |
| mxc-sandbox/skills/mxc-run/SKILL.md | Private config is persistent and environment is inherited. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:42,185-194,247-248 |
| mxc-sandbox/skills/mxc-run/SKILL.md | PowerShell hooks have been observed working. | geeky-orchestration/docs/agent-eval-decisions.md:93,339; geeky-orchestration/hooks/hooks.json |
| mxc-sandbox/skills/mxc-run/SKILL.md | Avoid universal claim; preserve observed historical limit. | geeky-orchestration/docs/agent-eval-decisions.md:93,339; geeky-orchestration/hooks/hooks.json |
| mxc-sandbox/README.md | Separate observed hook failure from other hook shells. | geeky-orchestration/docs/agent-eval-decisions.md:93,339; geeky-orchestration/hooks/hooks.json |
| mxc-sandbox/README.md | Document observed PowerShell hook without promising general runtime behavior. | geeky-orchestration/docs/agent-eval-decisions.md:93,339; geeky-orchestration/hooks/hooks.json |
| mxc-sandbox/skills/mxc-run/references/recipes.md | Scope the observation and distinguish startup from hook event handling. | geeky-orchestration/docs/agent-eval-decisions.md:93,339; geeky-orchestration/hooks/hooks.json |
| mxc-sandbox/skills/mxc-troubleshooting/SKILL.md | Scope tested failure and record PowerShell observation. | geeky-orchestration/docs/agent-eval-decisions.md:93,339; geeky-orchestration/hooks/hooks.json |
| mxc-sandbox/skills/mxc-troubleshooting/SKILL.md | Explicit opt-out supersedes enumeration. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:99-103,221-225 |
| mxc-sandbox/skills/mxc-setup/SKILL.md | Diagnostic reports source name and is not limited to isolated mode. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:108,314-330 |
| mxc-sandbox/skills/mxc-interactive/SKILL.md | Distinguish agent account environment from host environment. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:149-162,314-320 |
| mxc-sandbox/skills/mxc-run/SKILL.md | Account for platform capability and explicit opt-out. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:214-225 |
| geeky-orchestration/evals/adapters/codex/README.md | Clarify current defaults, enforcement boundary and dirty source. | run-codex-baseline.ps1:18-22,67-68; prepare-profile.py:283,298; guard-bridge.py:1,28 |
| geeky-orchestration/evals/adapters/codex/README.md | Bound the statement to its checkpoint; do not assert current live status. | README.md offline checkpoint paragraph |
| geeky-orchestration/evals/adapters/codex/handoff.md | Make the old pin and scope unambiguously historical. | handoff.md:3-9; git rev-parse HEAD |
| geeky-orchestration/evals/adapters/codex/kanban.md | Distinguish checkpoint status from current authorization. | kanban.md:3-9; evals/c0-readiness.md |
| geeky-orchestration/evals/adapters/codex/references.md | Distinguish historical references from current source. | git status --short; git log f081b984..HEAD -- geeky-orchestration/evals/adapters/codex |
| geeky-orchestration/evals/mxc-litellm-runbook.md | Opening falsely says no live run used fixes; later native capture exists. | geeky-orchestration/evals/c0-readiness.md:5-18; analyses/c0-native-result-20261031/README.md |
| geeky-orchestration/evals/mxc-litellm-runbook.md | Avoid treating historical local checks as current. | geeky-orchestration/AGENTS.md:5-7 |
| geeky-orchestration/evals/QUICKSTART.md | The listed attempt predates the later native capture. | geeky-orchestration/evals/c0-readiness.md:5-18 |
| geeky-orchestration/evals/QUICKSTART.md | Preserve scores without asserting this is the last scored result. | geeky-orchestration/evals/c0-readiness.md |
| geeky-orchestration/evals/QUICKSTART.md | A scoring procedure does not authorize a commit. | geeky-orchestration/evals/lessons-learned.md:17; supplied working conventions |
| geeky-orchestration/evals/codex-c1-checkpoint5.md | Distinguish past run instructions from current operating authority. | geeky-orchestration/AGENTS.md:5-7; geeky-orchestration/evals/baseline-runs.md |
| geeky-orchestration/evals/codex-c1-kickoff.md | Distinguish past run instructions from current operating authority. | geeky-orchestration/AGENTS.md:5-7; geeky-orchestration/evals/baseline-runs.md |
| geeky-orchestration/evals/codex-c1-run1-retrospective.md | Distinguish past run instructions from current operating authority. | geeky-orchestration/AGENTS.md:5-7; geeky-orchestration/evals/baseline-runs.md |
| geeky-orchestration/evals/codex-c1-run2-guide.md | Distinguish past run instructions from current operating authority. | geeky-orchestration/AGENTS.md:5-7; geeky-orchestration/evals/baseline-runs.md |
| geeky-orchestration/evals/codex-c1-run3-guide.md | Distinguish past run instructions from current operating authority. | geeky-orchestration/AGENTS.md:5-7; geeky-orchestration/evals/baseline-runs.md |
| geeky-orchestration/evals/c0-readiness.md | The smoke record predates a later full DeepSeek C0 attempt; preserve the historical statement and point to local evidence. | outputs/c0-deepseek-responses-openai-20261031/README.md:3-7 |
| geeky-orchestration/evals/telemetry/langfuse-evaluators/README.md | Clarify required scope, omitted values and readback-based delivery. | geeky-orchestration/evals/telemetry/langfuse-scores.py:1-10,27-64,77-135,137-163 |
| geeky-orchestration/evals/judge-calibration.md | Separate planned calibration format from current scoring output. | geeky-orchestration/evals/scripts/score-run.py:13-18,1656-1675,1721-1731,1751 |
| geeky-orchestration/evals/telemetry/README.md | Distinguish enabled collection from preparation-only and disabled telemetry. | geeky-orchestration/evals/scripts/run-codex-baseline.ps1:38-39,295,372-398; geeky-orchestration/evals/scripts/run-baseline.ps1:41,167 |
| geeky-orchestration/docs/agent-eval-decisions.md | D79 records earlier commit-gate behavior without the later docs exception. | geeky-orchestration/scripts/check-commit.py:5-17,43-44,85-88; geeky-orchestration/skills/spec-research/SKILL.md:116 |
| geeky-orchestration/docs/agent-eval-decisions.md | Historical D88/D90 paid-validation statements can be read as present status. | geeky-orchestration/docs/agent-eval-decisions.md:107-112,310; geeky-orchestration/skills/geeky-implement/SKILL.md:58-65 |
| geeky-orchestration/mcp/README.md | Codex MCP launcher omits the actual uv invocation. | geeky-orchestration/.codex-plugin/mcp.json |
| geeky-orchestration/docs/end-to-end-workflow.md | The guide puts check-dod before the Done move even though it requires the task in Done. | geeky-orchestration/scripts/check-dod.py; geeky-orchestration/skills/geeky-implement/references/execution-protocol.md:142-150 |
| geeky-orchestration/docs/end-to-end-workflow.md | The phase closeout repeats the incorrect check-dod ordering. | geeky-orchestration/skills/geeky-implement/references/execution-protocol.md:142-150 |
| geeky-orchestration/docs/end-to-end-workflow.md | Phase-review summary omits the current large-phase split. | geeky-orchestration/skills/geeky-implement/references/execution-protocol.md:152 |
| geeky-orchestration/docs/end-to-end-workflow.md | The runbook omits later budget cadence and MCP gate preference. | geeky-orchestration/skills/geeky-implement/SKILL.md:55-58; geeky-orchestration/skills/geeky-plan/SKILL.md:22-29,90 |
| geeky-orchestration/AGENTS.md | The phase-review summary omits the large-phase split. | geeky-orchestration/skills/geeky-implement/references/execution-protocol.md:152 |
| geeky-orchestration/README.md | Reviewer summary omits the large-phase split. | geeky-orchestration/skills/geeky-implement/references/execution-protocol.md:152 |
| geeky-orchestration/skills/geeky-implement/SKILL.md | The budget target requires the optional total budget; deadline and reserve alone do not compute it. | geeky-orchestration/scripts/workflow-budget.py:15-19,37-71; geeky-orchestration/test_workflow_budget.py:72-75 |
| geeky-orchestration/skills/geeky-implement/SKILL.md | A hard-wall budget alone is invalid, not an unbounded ordinary workflow. | geeky-orchestration/scripts/workflow-budget.py:37-56; geeky-orchestration/test_workflow_budget.py:59-60 |
| geeky-orchestration/skills/geeky-implement/references/execution-protocol.md | A hard-wall budget alone is invalid, not an unbounded ordinary workflow. | geeky-orchestration/scripts/workflow-budget.py:37-56; geeky-orchestration/test_workflow_budget.py:59-60 |
| geeky-orchestration/agents/geeky-implement-orchestrator.md | Preserve the required large-phase review split in the agent summary. Regenerate projections after canonical edit. | geeky-orchestration/skills/geeky-implement/references/execution-protocol.md:152 |
| README.md | Headless operation also supports Linux and macOS; the examples are Windows-specific. | mxc-sandbox/scripts/host/MxcClaude/Program.cs:196; mxc-sandbox/README.md:10 |
| dev-workflows/PACKAGING.md | Only the Codex manifest declares dependencies. | dev-workflows/.codex-plugin/plugin.json; dev-workflows/.claude-plugin/plugin.json |
| dev-workflows/PACKAGING.md | Manifests establish declarations, but not the documented installation, tag, or allowlist enforcement behavior. | dev-workflows/.codex-plugin/plugin.json; dev-workflows/.claude-plugin/plugin.json; .claude-plugin/marketplace.json |
| dev-workflows/PACKAGING.md | Claude manifest has no dependency declaration. | dev-workflows/.claude-plugin/plugin.json; README.md |
| dev-workflows/PACKAGING.md | The plugin ships these as skills; old command files were removed. | geeky-orchestration/skills/geeky-plan/SKILL.md; geeky-orchestration/skills/geeky-status/SKILL.md |
| README.md | Historical uncommitted state should not be mistaken for current lineage. | git merge-base --is-ancestor 0b4a5c0 HEAD; git show 0b4a5c0 |
| README.md | Preserves the historical scope without asserting present worktree state or current upstream outcome. | geeky-orchestration/evals/analyses/c0-offline-remediation-20261029/README.md |
| README.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |
| geeky-orchestration/README.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |
| mxc-sandbox/README.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |
| geeky-orchestration/evals/QUICKSTART.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |
| geeky-orchestration/evals/c0-readiness.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |
| geeky-orchestration/evals/baseline-runs.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |
| geeky-orchestration/evals/lessons-learned.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |
| geeky-orchestration/evals/mxc-litellm-runbook.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |
| geeky-orchestration/evals/adapters/codex/README.md | Link current source and campaign context separately from dated run records. | docs/mxc-documentation-refresh-20261103/README.md |

The canonical implementation-orchestrator summary is projected into its five harness registrations with `sync-agents.js`. All six canonical agent documents also replace a relative terminology hyperlink that broke in projected locations with an explicit portable source locator; all 30 registrations were regenerated together. Two unchanged-since-boundary canonical source documents were included for that linked correction. The CSV retains the pre-refresh Git date for every document; a working edit does not create a new Git history date.

The repository and orchestration README C0 summaries now distinguish initial closeout from the later local 95.18 parity result. The workflow guide's next step retains the gated Done state instead of describing a second Done move. Packaging list spacing and the review packet's wrapper reference were corrected during integration.

The final operational review also corrected three date/scope issues: `lessons-learned.md` now identifies the old credential file as that run's source and defers future selection to the owner's current authorization; its C1 reference is labelled historical; and `mxc-litellm-runbook.md` dates the stopped-state claim to the 27 October mapping checkpoint.

Commit scope: the credential-source correction and smoke clarification modify pre-existing, uncommitted draft sections. Those sections remain in the worktree. Their original content is not pulled into the documentation commits; the standalone index and tracked-document corrections are committed separately.

Historical captures were inventoried by path and hash, with selected packet indexes read for current-reference risks. This was not a fresh audit of every captured implementation or score. Case reviews mapped requirements to assertion families; they did not execute the oracles or establish exhaustive input coverage.
