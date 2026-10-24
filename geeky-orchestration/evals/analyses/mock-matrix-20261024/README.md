# Mock matrix, 2026-10-24

Both harnesses on C1-C3, model-free, inside MXC on Linux (Ubuntu 24.04, Bubblewrap backend), with Langfuse telemetry on.
Plugin at `c58f7d0` plus the uncommitted telemetry and portability changes this record ships with. Run with `scripts/run-mock-matrix.ps1`.
The Codex rows are the rerun after the space-free tracer launcher (`adapters/codex/langfuse-tracer.py`); the first full matrix (`matrix-full.json`) also passed all six.

| Harness | Case | Result | Checks passed | Telemetry | Langfuse observations | Wall (s) |
|---|---|---|---:|---|---:|---:|
| claude-code | c1-csvledger | PASS | 25 | delivered | 122 | 37 |
| claude-code | c2-linkvault | PASS | 25 | delivered | 122 | 38 |
| claude-code | c3-minisql | PASS | 25 | delivered | 122 | 39 |
| codex | c1-csvledger | PASS | 8 | delivered | 9 | 19 |
| codex | c2-linkvault | PASS | 8 | delivered | 9 | 21 |
| codex | c3-minisql | PASS | 8 | delivered | 9 | 19 |

Claude mock: 25 checks per case, including `telemetry.stop_hook`, `telemetry.hook_log` and `telemetry.thinking_summaries`; the session reached Langfuse with 63 generations and 58 tool calls.
Codex mock: 8 checks per case; the `telemetry` check requires the tracer to record the turn in its `.langfuse` delivery sidecar.
Token figures inside mock runs are synthetic. Windows ProcessContainer was not re-run for this record.

## C0 (added with the case)

| Harness | Case | Result | Checks passed | Telemetry | Langfuse observations | Wall (s) |
|---|---|---|---:|---|---:|---:|
| claude-code | c0-wordstat | PASS | 25 | delivered | 122 | 28 |
| codex | c0-wordstat | PASS | 8 | delivered | 9 | 23 |

The post-run coverage step ran on both. Mocks do not run the real workflow, so coverage is incomplete by design. The Claude mock misses only `nested_subagents`; the Codex mock has a single synthetic turn. `matrix-c0.json` holds the run.
