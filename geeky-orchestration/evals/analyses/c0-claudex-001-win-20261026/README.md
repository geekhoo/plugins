# C0 / claudex-001 / Windows MXC. 2026-10-26

Codex completed its authorized end-to-end run. After the owner reconfigured the
router, Claude's geeky-resume retry in the same folder set passed implementation
tests and reached final review, then timed out before workflow closeout. The
owner-authorized continuation has now completed review and closeout in the same
workspace, with cumulative resumed parity 98.33.

| Harness | Parity | Quality | Adherence | Consistency | Oracle | Wall time |
|---|---:|---:|---:|---:|---|---|
| Codex 0.164.0 | **97.46** | 95.64 | 97.83 (45/46) | 100.00 | 13/13, stable over 3 | 47m 26s |
| Claude Code 2.1.304, original attempt | **90.33** | 96.67 | 88.10 (37/42) | 83.16 | 13/13, stable over 3 | 90m 02s; timeout |
| Claude Code, cumulative after continuation | **98.33** | 95.71 | 100.00 (42/42) | 100.00 | 13/13, three fresh passes | 119m 40s active; continuation 29m 38s |

Model alias: `claudex-001` through LiteLLM. Codex used runner-default thinking
(`high` for main/workers), Windows ProcessContainer, platform environment
`mxc-win`, and per-agent Langfuse identities. Qualification was explicitly
waived by the owner; it is not reported as freshly verified.

Read [the full Codex report](codex/report.md), [parity.json](codex/parity.json),
[verified published scores](codex/langfuse-scores-verified.json), and
[telemetry audit](codex/telemetry-audit.json).
Read [the completed Claude continuation](claude-code/closeout-20261026/report.md),
[cumulative parity](claude-code/closeout-20261026/parity.json), and
[verified published scores](claude-code/closeout-20261026/langfuse-scores-verified.json).
The earlier [timeout](claude-code/router-fixed/report.md) and its scores remain intact.
Earlier [provider failures](claude-code/report.md) remain historical evidence.

Codex passes 93 public tests; resumed Claude passes 60 with two platform skips. Both pass
the independent 13-test oracle. The original Claude attempt's deductions concern unfinished closeout
and T4's unreissued phase verdict; Codex's concern one incomplete task-commit
snapshot and one inaccurate follow-up statement. Claude's seven extracted task
commands pass at their own commits. The continuation fixed a large-positive-top
edge case, completed final review and obtained the revised T4 verdict. Ten scores
per session are published and read back; the timeout still retains 90.33.

Only parity.json is comparable. These attempts have different resume context and
router configuration; the same alias does not establish an identical backend.
The cumulative continuation has extra time and conversation context and is not
another clean initial attempt. No controlled causal ranking is claimed. No paid process remains
running and no further retry is scheduled.

The owner authorized grouped commits and a push to origin. The
[closeout alignment](alignment-closeout-2026-10-26.md) and
[publication record](publication-closeout-2026-10-26.md) list document changes,
commit groups, and validation. The [first publication](publication-2026-10-26.md)
retains the timeout-era scope and runtime exclusions.
