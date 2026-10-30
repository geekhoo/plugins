# Sources

- [Independent GPT-6.1 Terra/xhigh investigation](terra-investigation.md), requested
  directly by the owner: source-only findings, qualifications and regression matrix.

- Raw `../../baselines/c0-wordstat/20261029T160022Z-45641609/run.json`: finalized
  process 0; oracle 13 errors / 0 passes stable over three; budget and attempt.
- Same capture session.jsonl:1057: frozen query returns true at 16:27:29.215 UTC.
- Same capture session.jsonl:1212: root final explicitly Not accepted.
- Snapshot `final-workspace/docs/spec-001-feature/review-plan.md:12`: Critical gap.
- Snapshot `tasks/T2-cli-interface.md:24`: required error acceptance;
  line 36 starts incomplete validation; line 40 has malformed prefix wording.
- Snapshot `implementation-plan.md:28`: Phase 1 gate.
- Committed 1e921e0: AGENTS.md:53; geeky-plan/SKILL.md:99;
  plan-review/SKILL.md:101,131,155; mcp/server.py:324;
  hooks/guard-planning-contract.py:119.
- evidence/scoring-initial.log: strict scorer exit 2; no implementation commit.
- evidence/langfuse-readback.json: exact session counts, no truncation reported.
- evidence/acceptance.json, results.json, cleanup.json and terminal-evidence-pins.json.
- evidence/scan-worker-commit.json, scan-protocol-commit.json,
  scan-evidence-commit.json: zero hits in 7, 16 and 257 staged files.
- evidence/terminal-credential-scan.json: 101 files, zero literal hits.
- Independent read-only gate_review audit confirmed the real validation gap and
  canonical freeze/edit conflict; it performed no runtime or source edits.
