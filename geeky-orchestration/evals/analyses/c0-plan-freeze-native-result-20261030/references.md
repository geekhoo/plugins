# Evidence references

- Baseline: `../../baselines/c0-wordstat/20261030T063816Z-9860724b/`; run.json binds source, profile, deadline, single invocation, process result and oracle repetitions. oracle-output.txt contains all three runs.
- Same capture session.jsonl:2448: terminal blocked outcome. stream.jsonl records process-visible messages and command failures; solution.bundle preserves committed candidate history.
- Same capture subagents/rollout-01a18bca-f6b9-7c01-b425-6d1d42df0cb6.jsonl:11,15,22,24: complete addressed task, denial, full follow-up and generic turn failure. See evidence/worker-audit.md for other examples and attribution boundaries.
- final-workspace/docs/spec-001-feature/kanban.md:13 and handoff.md:15: T1 Blocked; review-plan.md:35-39 is planning sequencing review, not implementation phase review.
- evidence/langfuse-readback.json: explicit readback using LANGFUSE_CODEX_PUBLIC_KEY, LANGFUSE_CODEX_SECRET_KEY and LANGFUSE_CODEX_BASE_URL. Full observations remain in ignored outputs/c0-w6-native-20261030/.
- evidence/scoring.log and scoring-exit.txt: strict source-bound scorer exit 2. evidence/parity.log and parity-exit.txt: missing Quality prerequisite; no fallback score.
- evidence/prelaunch-readiness.json, verification.json, live-role-readback.json, observed-model-contexts.json and native-protocol.json: exact source hashes, effective prompt hash, eight configured roles, 24 actual thread contexts and native record checks.
- evidence/source-audit.md and source-delta.txt: source comparison with Claude 0b1f5fb, including parity-detector change 9baaba3; no scoring source changed in this W6 operation.
- evidence/terminal-credential-scan.json and staged scan record: literal rotated credential matching, path/line reporting only, no values.
- evidence/terminal-evidence-pins.json: raw capture and final workspace byte preservation.
- Local operator folder: outputs/c0-w6-native-20261030/. Launch guard exits occurred before the atomic attempt claim and before live invocation; no extra paid attempt was made.
