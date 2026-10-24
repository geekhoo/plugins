# Run 3 validation matrix

Authorized scope: one MXC-contained C1 run3, monitored through completion, evidence-backed final report. No automatic retry/resume, paid judge, administration-repository commit/push or contestant assistance.

| Area | Evidence/command | Acceptance |
|---|---|---|
| Launch identity | authorization.json, run-paths.json, launch-source-manifest.json | Exact pinned plugin/harness; requested role matrix; existing shared dirty work preserved |
| Monitoring | monitor.jsonl, raw stream/stderr; read-only Git without optional locks | Continued observation, no interventions or contestant file edits |
| Runner completion | runner-completion.json, run.json, full recursive rollouts, solution.bundle | Completed contestant execution; preserve all failures and diagnostics |
| Native/diagnostic isolation | native-proof-validation.json and diagnostic-report.json | Both reviewer proofs intact; no unmatched infrastructure error; pin/export identity retained |
| Actual paid matrix | Own-history turn contexts of main and every descendant | Sol/high main, Sol/medium tasks/default, Sol/xhigh both reviewer role types |
| Oracle | runner's oracle-output.txt and run.oracle | Stored three-run oracle result and stability explicitly reported; scorer does not rerun oracle |
| Process | analyze-run.py --harness codex --analysis-only --out <new derived folder> | Supported automatic normalization; no guessed missing facts |
| Task validation/scoring | score-run.py --harness codex --workspace <isolated bundle clone> --manual <run3 judgments> --require-complete --out <new derived folder> | First own-task-commit validation, complete score, no needs_judge; never historical caches |
| Manual judgments | New source-backed run3 manual-verdicts.json | Physical thread/ordinal/commit evidence; no paid judge |
| Final preservation | Source/raw/evidence hashes, Git status, records links | Originals retained; no staging/administration commit/push; limitations stated |

Browser/build checks do not apply to this Python CLI evaluation; native tooling/isolation and the C1 oracle are the relevant integration checks. Model capability, causal ranking, paid-hook invocation without direct evidence, and unavailable API cost/latency are not inferred.
