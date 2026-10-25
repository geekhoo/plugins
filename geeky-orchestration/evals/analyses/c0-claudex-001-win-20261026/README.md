# C0 / claudex-001 / Windows MXC. 2026-10-26

Codex completed its authorized end-to-end run. After the owner reconfigured the
router, Claude's geeky-resume retry in the same folder set passed implementation
tests and reached final review, then timed out before workflow closeout.

| Harness | Parity | Quality | Adherence | Consistency | Oracle | Wall time |
|---|---:|---:|---:|---:|---|---|
| Codex 0.164.0 | **97.46** | 95.64 | 97.83 (45/46) | 100.00 | 13/13, stable over 3 | 47m 26s |
| Claude Code 2.1.304 | **90.33** | 96.67 | 88.10 (37/42) | 83.16 | 13/13, stable over 3 | 90m 02s; timeout |

Model alias: `claudex-001` through LiteLLM. Codex used runner-default thinking
(`high` for main/workers), Windows ProcessContainer, platform environment
`mxc-win`, and per-agent Langfuse identities. Qualification was explicitly
waived by the owner; it is not reported as freshly verified.

Read [the full Codex report](codex/report.md), [parity.json](codex/parity.json),
[verified published scores](codex/langfuse-scores-verified.json), and
[telemetry audit](codex/telemetry-audit.json).
Read [the latest Claude report](claude-code/router-fixed/report.md),
[parity](claude-code/router-fixed/parity.json), and
[verified published scores](claude-code/router-fixed/langfuse-scores-verified.json).
Earlier [provider failures](claude-code/report.md) remain historical evidence.

Codex passes 93 public tests; Claude passes 56 with two platform skips. Both pass
the independent 13-test oracle. Claude's deductions concern unfinished closeout
and T4's unreissued phase verdict; Codex's concern one incomplete task-commit
snapshot and one inaccurate follow-up statement. Claude's seven extracted task
commands pass at their own commits. Ten scores per session are published/read back.

Only parity.json is comparable. These attempts have different resume context and
router configuration; the same alias does not establish an identical backend.
No controlled causal model/harness ranking is claimed. No paid process remains
running and no further retry is scheduled.

Repository publication is authorized separately. See the
[2026-10-26 alignment and publication handoff](alignment-report-2026-10-26.md)
for stale-document actions and verification.

The [publication record](publication-2026-10-26.md) lists commit groups,
validation, and the runtime files retained locally.
