# Source and evidence references

- Historical source HEAD: `4228c3f73fc3894c86725cf42900406c1d2d981f`.
- [Latest terminal pair](../c0-fresh-sequential-20261027/README.md).
- [Codex trace](../../baselines/c0-wordstat/20261026T202318Z-fc8f0aa8/session.jsonl): physical lines 93 and 96; [stream](../../baselines/c0-wordstat/20261026T202318Z-fc8f0aa8/stream.jsonl): lines 33, 37–38.
- [Claude trace](../../baselines/c0-wordstat/20261026T202649Z/session.jsonl), [run](../../baselines/c0-wordstat/20261026T202649Z/run.json), [analysis](../../baselines/c0-wordstat/20261026T202649Z/analysis.json).
- [Shared workflow clock](../../../scripts/workflow-budget.py), [clock regression tests](../../../test_workflow_budget.py).
- [Bridge guard](../../adapters/codex/litellm_bridge/mapper.py), [transport error](../../adapters/codex/litellm_bridge/server.py), [regression tests](../../adapters/codex/litellm_bridge/test_bridge.py).
- [Runner lifecycle/export guard](../../scripts/run-lifecycle.ps1), [runner fake-boundary tests](../../scripts/test_run_lifecycle.py), [common prompt](../../prompts/end-to-end.md).
- [Research policy](../../../skills/spec-research/SKILL.md), [plan policy](../../../skills/geeky-plan/SKILL.md), [review policy](../../../skills/plan-review/SKILL.md).
- Original manifests: `outputs/codex-v2-bridge-verification-20261027/original-evidence-sha256.json` (49 files), `outputs/c0-fresh-sequential-mapped-20261027/terminal-output-pins.json` (66 files).
- New verification: `outputs/c0-root-causes-20261027/verification.json`.
