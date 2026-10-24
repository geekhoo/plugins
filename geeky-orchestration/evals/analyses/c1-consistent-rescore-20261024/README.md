# C1 consistent saved-trace rescore — 2026-10-24

This is a new derivation of four completed artifacts under one frozen parser/scorer version. The original run folders, original automatic/reviewed scores and all 206 original files remain unchanged. No paid contestant, judge or API inference was started. No staging, commits, pushes or cleanup occurred.

## Results

| Run | Original composite | Replayed composite | Quality | Adherence | Consistency | Task tier |
|---|---:|---:|---:|---:|---:|---:|
| Codex 1 — Sol/medium main, Luna/max workers | 81.7 | **96.3** | 95.9 | 100.0 | 100.0 | 77.7 |
| Codex 2 — Sol/medium throughout | 89.8 | **98.0** | 100.0 | 97.1 | 100.0 | 90.7 |
| Claude 6 | 98.3 | **98.3** | 98.6 | 100.0 | 100.0 | 87.6 |
| Claude 4 | 97.9 | **97.9** | 97.8 | 98.8 | 100.0 | 90.9 |

All four pass `--require-complete`, have no missing metric inputs and no unresolved judge items. This is measurement completeness under the existing rubric, not proof of model superiority or a controlled experiment. Reference eligibility and token-ceiling flags remain unchanged. API latency/cost are still unknown for Codex; the existing raw-duration fallback remains in use. Different plugin/model configurations and selection of the best Claude runs remain comparison limitations.

Machine-readable results: [summary.json](summary.json), [check/dimension changes](score-differences.json), [frozen replay commands/report](replay-report.json), [verification](verification.json).

Per-run derived reports:

- [Codex 1](runs/20261023T182024Z-5fa13924/derived/score.md): three T1 validation attempts, one T2 attempt; task-review rounds 1 and 2. T2's initial NEEDS FIXES is preserved, so its R is 0.5 rather than an invented perfect review history. Task durations are 198.2 and 360.3 seconds under the existing formula.
- [Codex 2](runs/20261023T194430Z-c5e04f3f/derived/score.md): attempts 1/1/2, review rounds 1/1/1, all four implementation commit-message checks restored. The inaccurate hook-configuration claim remains a failed adherence judgment. Eleven reviewed lane moves occur in seven actual write commands; a read-only Get-Content wrapper is no longer counted as a move.
- [Claude 6](runs/20261023T104412Z/derived/score.md): every raw dimension and the composite are unchanged.
- [Claude 4](runs/20261022T125647Z/derived/score.md): every raw dimension and the composite are unchanged; its existing kanban-after-moves failure remains.

Codex 2's new lead over Codex 1 is 1.7193 points; its gap behind Claude 6 is 0.2318 points. These are small outcome differences across confounded single runs, not statistical estimates of capability. Tokens, oracle outcomes and elapsed times did not change during rescoring.

## What was repaired

1. Source-bound process evidence can reference main and child JSONL records by file hash, record index, exact timestamp, canonical record hash and visible text. Explicit contexts and scoped intervals distinguish actual delegated activity from bulk skill prereads or late announcements.
2. Task/phase ownership and reviewer results feed adherence and task-tier calculations consistently. Repeated results from one reviewer remain separate rounds. Nested orchestrators no longer hide implementation commits or coder activity.
3. Lane/handoff mappings preserve the physical commands. Codex read-only calls and JavaScript wrappers are excluded from shell-write heuristics. `Implementation Run Summary` is recognized.
4. Critical findings, the prescribed fix and re-review evidence are represented without reclassifying them as initial implementation commits.
5. Task validation selects the actual full implementation commit, not final documentation closeout. Cache entries bind task, commit, committed task-file hash, exact command, exit status, source-document hash and retained output. Missing stderr stays unknown.
6. `--require-complete` withholds a comparable composite when required process coverage is missing. Explicitly requested missing/invalid evidence fails closed. Separate `--out` support keeps derived reports apart from source runs.

Formulas, dimension weights and hard gates were not retuned. Only the original source-backed judgment items were carried forward. Twenty deterministic overrides from Codex 2 were not copied into the new judgments; the repaired parsing now supplies those checks. Original judgment files remain in each run's `original/` directory.

## Validation reuse and tests

All **27 task-validation commands** were replayed from saved results: Codex 1=3, Codex 2=4, Claude 6=9, Claude 4=11. Every derived result has `reused=true`; `validation_rerun=false` and `validation_evidence="reused recorded results"` accurately describe this operation. **Zero case-validation commands were executed by the final rescore.**

Output completeness is explicit: Claude results retain output tails, Codex 2 T1/T2 retain summaries, and the other native checks retain full stdout. Unknown stderr was not synthesized. Final-suite evidence was not substituted for task-own-commit evidence.

The final frozen-source model-free suite passed **306 tests and 32 subtests**, no skips, in 153.33 seconds. It includes mocked source/cache rejection, missing evidence, mismatched hashes/commands/commits, review and stage behavior, read-only lane false positives, captured native/paid-trace read-only checks, and shared scorer coverage. Infrastructure installation and paid execution were not repeated.

An additional historical six-run replay reproduced all six original raw dimensions/composites, but its source-stability check failed because the final Codex-only fixes landed while it ran. [That report](historical-six-qualified.json) is retained as qualified evidence, not claimed as a frozen six-run proof. The authoritative final proof is the source-stable four-run replay plus the final test suite. Earlier local replay attempts remain in external staging; they were not published as final results.

## Self-evaluation and provenance

The owner requested the run-2 session's self-evaluation. [Its retained report](run2-self-evaluation.md) and [message provenance](self-evaluation-provenance.json) are included. The session was read; no follow-up prompt was sent. Its findings drove the metric-completeness gate, scoped activity attribution, exact commit bindings and validation reuse.

[Original input hashes](original-input-hashes.json) cover all 206 original files. Each per-run `original/` preserves its original score, analysis, metadata and verdicts. [comparison-before.md](comparison-before.md) is the byte-preserved previous scorecard. [source-manifest.json](source-manifest.json) and inert `sources/*.source` files preserve the final harness; `sources-before/` preserves the three pre-repair tool files. Builder snapshots are in `builders/`.

Core SHA-256:

| Source | SHA-256 |
|---|---|
| codex-trace.py | `cf6e879831218786318c86149a19d38f21304279314a1038fa8a723b5328ace2` |
| score-run.py | `34a54671b81203e10cec08d30524a127a44f4e3530eb33c56e4a4e09b5300ade` |
| analyze-run.py | `f74fadd1eaa84004c452fd38ffc98dac425de35a5fea87d72692575cc096bf86` |

## Reproduce without touching originals

Use copies of the original inputs and cloned solution bundles, as recorded in `replay-preparation.json`. Supply the per-run `process-evidence.json` for Codex, the per-run `validation-cache/validation-cache.json`, and `manual-consistent.json`. Run analysis and scoring with separate output directories. The recorded commands in `replay-report.json` are the exact executed commands; `builders/rescore-four.py.source` preserves the orchestration.

The scoring flags are `--no-rerun --validation-cache <cache> --require-complete --out <new-output>`, plus `--process-evidence <artifact>` for Codex. Resolve workspaces from cloned bundles; copy supplementary heartbeat bytes only from retained matching-HEAD workspaces, preserving their hashes. Do not write into a baseline folder, replace historical scores, or infer paid-run authorization from this report.
