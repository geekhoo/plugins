# Sources and preservation

- Owner instruction dated 29 October 2026: exactly one native attempt after W1-W4;
  zero retries/resumes/probes/overtime; rotated keys; literal staged scans;
  public fast-forward publication after scans.
- [Raw terminal record](../../baselines/c0-wordstat/20261029T062343Z-ffd63c3c/run.json),
  execution finalized, exit 1/crash, workflow acceptance not established.
- [Raw stream](../../baselines/c0-wordstat/20261029T062343Z-ffd63c3c/stream.jsonl),
  lines568-569: final error and turn.failed.
- [Native session](../../baselines/c0-wordstat/20261029T062343Z-ffd63c3c/session.jsonl)
  and sibling subagents/: preserved native evidence, with rollout manifest.
- [Oracle output](../../baselines/c0-wordstat/20261029T062343Z-ffd63c3c/oracle-output.txt)
  plus run.json oracle.stable_over_3:13 missing-package errors, zero passes.
- [Preparation verification](evidence/verification.json), [role readback](evidence/role-readback.json),
  [clean committed inventory](evidence/current-inventory.json), [MXC build](evidence/mxc-build.json).
- [Gate tests](evidence/gate-tests.log):10 tests and 12 subprocess subtests passed.
- [Result binding](evidence/results.json), [Langfuse readback](evidence/langfuse-readback.json),
  [cleanup](evidence/cleanup.json), [65 file pins](evidence/terminal-evidence-pins.json).
- [Scoring status](evidence/scoring-status.json), [score-run output](evidence/scoring.log),
  [parity invocation](evidence/parity.log): unavailable composite, no score publication.
- Literal scans: [code commit](evidence/scan-before-code-commit.json),
  [documentation commit](evidence/scan-before-docs-commit.json),
  [first push](evidence/scan-before-initial-push.json),
  [terminal working files](evidence/terminal-working-files-scan.json).
- Local `outputs/c0-codex-native-fix-20261029/` additionally preserves full
  Langfuse observations, launcher, one-attempt claim, monitor, derived analysis,
  unused preparation capture and uncommitted workspace patch.
- [Gate fix record](../c0-commit-gate-fix-20261029/README.md),
  [original handoff](../c0-codex-native-run-20261029/handoff.md),
  [historical Claude reference](../c0-luna-overtime-20261028/README.md).
