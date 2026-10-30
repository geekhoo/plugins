# References

- Terminal baseline: `../../baselines/c0-wordstat/20261030T150121Z-a55a910b/`. `run.json` binds source, one invocation, crash and oracle summary. `stream.jsonl:204-205` records proxy 502 and `turn.failed`; `stderr.txt` separately records a startup access-denied warning.
- `oracle-output.txt:212,425,638` records 13 setup errors for each repetition; the root `wordstat/` package is missing. `solution.bundle` preserves committed candidate history. `final-workspace/` preserves the uncommitted plan-review state.
- Eight `subagents/rollout-*.jsonl` session metadata records contain `forked_from_id`; no cold implementer was captured.
- `evidence/verification.json`, `langfuse-readback.json`, `scoring.log`, `parity.log`, `evaluation-inputs.json`, and `terminal-evidence-pins.json` record role/prompt readback, telemetry summary, withheld scoring and byte hashes. Full observations are in local ignored `outputs/c0-native-run-20261030b/`.
- The prior prepared-only baseline is `../../baselines/archive/c0-wordstat-20261030T143704Z-4ab4c0dc-prepared-only/`. Fresh preparation baseline and prior operator artifacts remain under `outputs/c0-native-run-20261030b/`.
- Credential scans: `evidence/terminal-credential-scan.json` and local `outputs/c0-native-run-20261030b/final-staged-credential-scan.json`. These check current literal values, not unknown or transformed credentials.
