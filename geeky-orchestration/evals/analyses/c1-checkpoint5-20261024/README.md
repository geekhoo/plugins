# Checkpoint 5: frozen current harness, historical six-run replay

All six historical Claude runs reproduce all four raw dimensions and the raw composite exactly (30 numeric comparisons). Analysis and scoring exit successfully for all six runs. The final manifest covers 67 current working-tree Python harness, invoked gate and case files; every original file across the six run folders (106 files) is preserved. Before/after SHA-256 manifests establish stability.

The first successful replay is preserved in `attempt1/`. Its freeze omitted five invoked plugin gates, so a final replay expanded the source manifest to include `validate-planning-folder.py`, `validate-task-schema.py`, `validate-kanban.py`, `check-dod.py`, and `check-commit.py`. These gates import only standard-library modules; no MCP code is invoked by this path. The repeat addresses dependency-freeze coverage only. The replay script now refuses to overwrite existing outputs and exits nonzero on command failure, score differences, source drift or original-input drift. To repeat, first preserve all existing outputs in a new attempt folder, as done for `attempt1/`.

| Historical run | Raw composite |
|---|---:|
| 20261020T114232Z | 77.18882170544698 |
| 20261020T155628Z | 77.00575408865282 |
| 20261022T065938Z | 86.73459522699092 |
| 20261022T125647Z | 97.89164053124497 |
| 20261023T062603Z | 93.82471845252947 |
| 20261023T104412Z | 98.27180923451854 |

Run from the repository root in PowerShell:

```powershell
& 'C:\repos\.eval-tools\agent-py\Scripts\python.exe' -B geeky-orchestration/evals/analyses/c1-checkpoint5-20261024/replay.py
```

The script verifies HEAD bee7b14 and no staged files, copies original run inputs into a new temporary directory, clones each original solution bundle, and uses original manual judgments. Retained untracked `.heartbeat` bytes are copied only after verifying retained workspace HEAD matches the bundle clone; their hashes and locations are recorded. The initial bundle-only trial omitted those bytes and consequently failed heartbeat checks in four runs. Restoring the source inputs resolves those differences without changing the scorer.

`report.json` contains raw comparisons, preservation flags and supplementary-input provenance. `hashes-before.json` and `hashes-after.json` preserve source and original-run hashes. `git-evidence.json` retains log, dirty status, upstream divergence and staged-file checks. Each `runs/<stamp>/commands.json` contains exact commands, exit codes, stdout and stderr; adjacent score files contain derived results. All writes are restricted to this evidence folder and new isolated temporary copies.

This is historical reproduction using `--no-rerun` and saved trace evidence (`validation_evidence: trace only`). No contestant validation commands, paid runs, model calls, API calls, commits or pushes were performed. This does **not** establish strict measurement completeness or own-commit validation-cache completeness: `--require-complete` and a bound validation cache were deliberately not requested. The unchanged historical scores alone must not be described as fresh runtime validation. Prior qualified six-run evidence was used to identify the six original runs, not substituted for execution.
