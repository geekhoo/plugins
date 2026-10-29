# Evidence

- [Failed Codex record](../../baselines/c0-wordstat/20261028T114114Z-eb4361e5/run.json) and [native root](../../baselines/c0-wordstat/20261028T114114Z-eb4361e5/session.jsonl).
- [First failed reviewer](../../baselines/c0-wordstat/20261028T114114Z-eb4361e5/subagents/rollout-01a1825e-0d8d-71b1-ae38-561fab386f9e.jsonl): own four commands succeeded; error at line367.
- [Runner](../../scripts/run-codex-baseline.ps1), [fake-boundary tests](../../scripts/test_run_lifecycle.py).
- [Saved native opaque proof and bounds](../litellm-bounded-retest-20261027/README.md).
- Local `outputs/c0-codex-native-preparation-20261029/`: exact profiles, replay proof,7-test log, source/build/tool pins, verification and held launch command.
