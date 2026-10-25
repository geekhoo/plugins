# Sources and reconciliation

- [Original run record](../../../baselines/c0-wordstat/20261025T154802Z-c140d9e7/run.json).
- [Oracle log](../../../baselines/c0-wordstat/20261025T154802Z-c140d9e7/oracle-output.txt).
- [Final parity](parity.json), [manual judgments](manual-verdicts.json),
  [reviewed validation anchors](validation-anchors.json), and score.json rerun_results.
- [Trace/identity audit](telemetry-audit.json), [coverage correction](coverage-corrected.json),
  [published scores](langfuse-scores-verified.json), [replay recovery](host-flush-recovery.json).
- [Evaluator tests](evaluation-tool-regressions.log) and source-manifest.json.
- [Preparation](../../c0-claudex-001-preparation-20261025/README.md): its initial
  qualification hold is superseded by the owner's explicit waiver and this run.
- [Telemetry identity](../../telemetry-identity-20261025/README.md).
- [Decisions](../../../../docs/agent-eval-decisions.md): D103 comparable scoring;
  H1/D27 task commit policy is unchanged.

Concrete source correlations:

- `session.jsonl:575` is a compaction-output write_stdin proposal, not an executed
  missing-output call; no result was synthesized.
- `subagents/rollout-01a173dc-5e9d-7621-be4a-56e5204bbe11.jsonl:40-42` records the
  rejected apply_patch; line 46 records the separate real shell writes.
- `session.jsonl:393/396`, `:490/493`, `:566/570` record commit helpers and their
  3/3/2 successful gate outputs.
- Done calls are at `session.jsonl:384/389`, `:483/488`, `:557/562`; exact coder
  start references are in validation-anchors.json.
- Final report ordinal 679 / stream item 111 is the CRLF/BOM understatement;
  candidate tests/test_cli.py:17-24, 78-82, 101-119 provide counterevidence.

Stale current guidance naming qualification as a hold is updated to the owner
override. Historical failed qualification evidence, original raw run metadata,
and earlier derived score snapshots are retained. Current root/plugin README
links to this report. No older benchmark score or cloud session was rewritten.
