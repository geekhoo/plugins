# Source and history references

## History pins

| Purpose | Commit |
|---|---|
| Before MXC host | `c957a431e4e1144b4280cee92d15bb90646e21ee` |
| First MXC host | `554c50acb90ecf15f161dc8f88e9ad12c8f015eb` |
| Baseline procedure | `3a1d8aa3fed469de1294a6ca8639a5506b5418b1` |
| First baseline runner | `01846e963e817977711e6bc2ef795b25d7c2f17a` |
| First retained C1 run source | `24c4e6daa6199be8196970ece35c79d6f184e8a4` |
| Reviewed HEAD | `ea94635d2f76918f4a01699aea3e356f90954033` |

Read the [first run metadata](../../geeky-orchestration/evals/baselines/c1-csvledger/20261020T114232Z/run.json) and [first comparison](../../geeky-orchestration/evals/baselines/c1-csvledger/comparison-20261021T0530Z.md) for the recorded start and run conditions. Commit dates describe source history, not the time a test executed.

## Owning source

- Workflow: [AGENTS](../../geeky-orchestration/AGENTS.md), [implementation skill](../../geeky-orchestration/skills/geeky-implement/SKILL.md), [execution protocol](../../geeky-orchestration/skills/geeky-implement/references/execution-protocol.md), [DoD gate](../../geeky-orchestration/scripts/check-dod.py), [commit gate](../../geeky-orchestration/scripts/check-commit.py), [budget implementation](../../geeky-orchestration/scripts/workflow-budget.py).
- Registration: [canonical implementation orchestrator](../../geeky-orchestration/agents/geeky-implement-orchestrator.md), [projection generator](../../geeky-orchestration/scripts/sync-agents.js), [Codex MCP declaration](../../geeky-orchestration/.codex-plugin/mcp.json).
- Sandbox: [host Program.cs](../../mxc-sandbox/scripts/host/MxcClaude/Program.cs), [wrapper](../../mxc-sandbox/scripts/mxc.ps1), [hook configuration](../../geeky-orchestration/hooks/hooks.json), [dated probe decisions](../../geeky-orchestration/docs/agent-eval-decisions.md).
- Codex: [runner](../../geeky-orchestration/evals/scripts/run-codex-baseline.ps1), [profile generation](../../geeky-orchestration/evals/adapters/codex/prepare-profile.py), [bridge server](../../geeky-orchestration/evals/adapters/codex/litellm_bridge/server.py), [guard bridge](../../geeky-orchestration/evals/adapters/codex/guard-bridge.py).
- Evaluation: [case definitions](../../geeky-orchestration/evals/cases/), [scorer](../../geeky-orchestration/evals/scripts/score-run.py), [parity evaluator](../../geeky-orchestration/evals/scripts/parity-eval.py), [coverage adapter](../../geeky-orchestration/evals/telemetry/langfuse-coverage.py), [scoped score publisher](../../geeky-orchestration/evals/telemetry/langfuse-scores.py).
- Packaging: [Codex manifest](../../dev-workflows/.codex-plugin/plugin.json), [Claude manifest](../../dev-workflows/.claude-plugin/plugin.json), [marketplace](../../.claude-plugin/marketplace.json).

## Local review evidence

The ignored `outputs/docs-refresh-20261103/` folder contains the original 457-path inventory with hashes, `initial-status.txt`, `before.zip`, registration backups, `source-before.json`, collated/applied replacements and eight agent reports. Final evidence is in `validation.json`, `whitespace-validation.json`, `reports/agents/integration.json` and `reports/operations/integration-review.json`. The integration-review findings were resolved in the final documentation. Each agent reports its own audit scope. The [current-state index](README.md) links the later campaign reports individually; those `outputs/` links are machine-local evidence and do not ship in a clone.

The CSV last-update fields come from Git author dates. Existing uncommitted changes are marked separately. Historical evidence and original scoring outputs retain their captured bytes; this refresh changes current documentation and registration summaries.

The local `outputs/docs-refresh-20261103/publication/` folder records the refresh-only blob plan, excluded pre-existing hunks, original worktree hashes, commit-message gate results, commit SHAs and final preservation checks. The [handoff](handoff.md#local-documentation-commits) records the authorized commit groups.
