# Evidence references

Historical timeout record. The [completed continuation](../closeout-20261026/report.md)
supplies the later final review and T4 verdict. The state below describes the
timeout capture and retains its 90.33 score.

- [Comparable parity](parity.json), [artifact quality/task reruns](score.json),
  [manual source decisions](manual-verdicts.json), [verified scores](langfuse-scores-verified.json).
- Raw run folder: `geeky-orchestration/evals/baselines/c0-wordstat/20261025T183455Z-geeky-resume-router-fixed-20261025T195444Z-recovered`.
- Private full API exports and replay tools: `C:\repos\.eval-tools\c0-claudex-001\evaluation\router-fixed`.
  They remain outside Git because full content/SDK metadata can contain keys.
- Native stream lines 5445, 5479, 5529: three final reviewer replies; line 5512:
  last root text waiting for final reviewer. Zero result records in stream.
- Native stream 4945: independent orchestrator full suite; 4963 acknowledges bad
  sample path; 4967 records corrected successful contract JSON.
- Candidate handoff.md:153–173: T4 review BLOCKED, parent handoff fix, deferred
  findings and explicit resume instructions. No review-impl.md or Run Summary.
- Native coder transcript intervals and hashes are summarized in manual-verdicts.json.
- [Corrected coverage](coverage-corrected.json), [telemetry](telemetry-audit.json),
  [evaluation source fingerprints](source-manifest.json).
- [Prior provider failures](../report.md) remain historical; [Codex comparator](../../codex/report.md)
  remains 97.46 when replayed with the current parity evaluator.

Stale-document actions: current result README, plugin README and QUICKSTART point
to this retry; prior Claude report/kanban/handoff gain historical-scope notices.
Candidate documents are left untouched, including stale headings/status, because
they are the evaluated artifacts. Original failed-attempt and raw records remain intact.
