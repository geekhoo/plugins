# Normalized C1 scoring

`scripts/c1-normalized-score.py` applies the existing C0 `parity-eval.py` formula to a source-bound C1 campaign:

```text
(0.35 × Quality + 0.35 × Adherence + 0.20 × Consistency) / 0.90
```

Quality is the capped, source-reviewed `score-run.py` Quality component. Adherence and Consistency are evaluated from the retained Langfuse observations, Git history, final planning artifacts and explicitly reviewed judgments. Task tier is excluded, as in the C0 parity score. This is a separate metric from the QACT composite.

## Run a frozen campaign

```powershell
python geeky-orchestration/evals/scripts/c1-normalized-score.py `
  --campaign <campaign.json> --out <new-output.json>
```

The output must not already exist. The scorer makes no provider calls, telemetry uploads, score publications or contestant validation runs. It invokes the existing parity evaluator's read-only Git and deterministic planning/commit/DoD checks. The campaign must point to retained local observations, scores and candidate workspaces; it is not a Langfuse uploader. Fetch observations through the Langfuse CLI and preserve the resulting immutable snapshot before freezing a campaign.

Git inspection in the C1 wrapper disables hooks and fsmonitor and ignores inherited Git configuration environment variables; it passes arguments directly rather than using a shell. This wrapper does not alter the existing C0 evaluator.

The machine-readable campaign schema is `geeky-eval.c1-normalized-campaign/1`; output is `geeky-eval.c1-normalized-score/1`. Each run pins:

- Its run record, Langfuse observation snapshot and session ID, source-reviewed QACT quality result, manual judgments and `geeky-eval.inputs/1` scope, with SHA-256 hashes.
- The plugin SHA, prompt hash, workspace path, clean Git HEAD/status, reflog and heartbeat bytes. Only a historical untracked `.heartbeat` is permitted; any other unbound workspace change fails closed.
- The stage-evidence method: the existing parity extractor, a verified first specification-artifact commit when its subject differs, or source-validated native process intervals when encrypted handoffs require them.
- For Codex runs using reviewed process evidence, the native run folder and reviewed process sidecar. The existing `codex-trace.py` loader verifies its source references, call identities and record hashes.
- Source evidence for the reviewed judgments and quality calculation. The scorer requires an explicit false-completion judgment and a generic C1 orchestrator-code-edit judgment: the legacy parity detector itself only recognizes `wordstat` and `tests` paths.

The campaign also pins the scorer, C0 parity evaluator, scope validator, Codex trace loader, Langfuse coverage adapter and invoked gate scripts. Missing or changed sources, mismatched sessions/runs/models, incomplete QACT inputs, duplicate observations, invalid stage intervals, missing judgments, unbound workspace changes, changed engine code and existing output paths fail without producing a score. The output contains the C0 breakdown and audit trail. Runtime is reported from the run record; token totals, latency, backend and cost are not inferred from incomparable populations.

## What the number means

The computation is deterministic **for the same verified inputs and reviewed decisions**. It does not turn human judgments into automatic facts, establish complete Langfuse ingestion, or make different plugin revisions, prompts, models, hosts or telemetry configurations controlled comparisons. The normalizer does not repair or publish traces, invent task attribution, or turn missing evidence into passing checks. Future runs require their own source-bound observations, quality evidence, process review where needed, and judgments. Scope sidecars preserve their identities and source ancestry.

The initial Windows campaign uses the three retained C1 Langfuse sessions. Its workflow-first policy follows the tested `impl-review` skill's single-fix-commit instruction and interprets the final gate-success statement as eventual success; the retained conservative review scores the two ambiguous judgments differently. Both interpretations and the original raw diagnostic are preserved in the ignored run evidence. The live C1 replay was captured after the contestant exited, while the older sessions were replayed under `smoke` and `development`; these differences remain explicit.

The C0 `parity-eval.py`, its existing score files and Langfuse score scopes are unchanged. Changes to the C1 campaign or review policy require a new pinned scope and reproducibility check; never silently overwrite a historical score.
