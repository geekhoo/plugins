# Evidence references

- [Parity](parity.json), [task-commit validation](score.json),
  [source judgments](manual-verdicts.json), [verified published scores](langfuse-scores-verified.json).
- [Evaluation derivation](evaluation-inputs.json), [coverage](coverage-cumulative.json),
  [telemetry](telemetry-audit.json), [evaluator fingerprints](source-manifest.json).
- Raw continuation folder:
  `geeky-orchestration/evals/baselines/c0-wordstat/20261025T183455Z-closeout-20261026T054222Z`.
- Private full API exports and derived scoring input:
  `C:\repos\.eval-tools\c0-claudex-001\evaluation\closeout`.
  Full API content remains outside Git.
- Final report: resume-stream.jsonl:9638. Focused tests:6223; full suite:6226;
  exact JSON assertion:6628; validators:8189; all-task DoD:8192; no-match check:8196.
- Revised T4 reviewer: subagents/agent-a5fa51b4a664cae32.jsonl:54 and matching
  meta toolUseId `call_s6DFpFO0AWS67SJC6DrCojkS`; resume-stream.jsonl:9216;
  candidate handoff.md:193. Reviewed state `0a9b354`.
- Candidate review-impl.md:110-121: consolidated final verdict. Kanban:24-28:
  completed release checklist. [Hash-label erratum](review-metadata-erratum.json).
- Earlier [timeout report](../router-fixed/report.md) and score 90.33 remain historical.
- [Codex report](../../codex/report.md) remains 97.46 for its completed initial attempt.

[Closeout alignment](../../alignment-closeout-2026-10-26.md) and
[publication](../../publication-closeout-2026-10-26.md) record the later repository work.
Current comparison and README pointers are refreshed to distinguish the completed
continuation from the earlier timeout. No candidate artifact was edited by the
operator after the native process finished.
