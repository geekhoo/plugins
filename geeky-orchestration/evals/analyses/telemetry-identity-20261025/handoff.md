# Telemetry identity handoff

This dated record covers model-free identity validation. Later paid C0 attempts are documented in the
[current comparison](../c0-claudex-001-win-20261026/README.md). The owner's
[publication instruction](../c0-claudex-001-win-20261026/alignment-report-2026-10-26.md)
supersedes the original no-commit checkpoint. No further paid run is authorized here.

Target: Gerald's Windows machine, PowerShell 7. Workdir:
`C:\Users\gerald.khoo\geekhoo-plugins`. Response budget: 500 words.

Before acting, verify Git HEAD is
`c83d4b941341b4094b6e7d2f4ac125e5c1b74154` and inspect `git status --short`.
Preserve all uncommitted Windows setup and telemetry identity changes.

Read in order:

1. This README.md, validation.json, live-verification.json and kanban.md.
2. ../../telemetry/README.md and this references.md.
3. ../../telemetry/telemetry.ps1, agent_identity.py, claude_identity.py,
   codex-identity.mjs and patch-codex-tracer.mjs.
4. ../../telemetry/identity-smoke.py and test_agent_identity.py.
5. ../windows-mxc-setup-20261025/README.md for the separate host/native gate state.

Verified state: platform naming is implemented for win/linux/mac; actual Windows
MXC mocks pass for both harnesses. CLI readback proves distinct orchestrator,
coder and reviewer user/trace IDs under each shared run session. Unannounced
Codex nested-header children also export correctly. No inference was used.

The pinned originals stay intact. Actor-owned traces avoid trace-level identity
overwrite; dispatch relationships remain explicit metadata. Coverage/scoring
recognize the new AGENT roots, and historical session IDs retain fallback support.

Live entry point: `C:\repos\.eval-tools\windows-eval.ps1 -Preflight`.
Credentials remain in `C:\Users\gerald.khoo\env.cloud.claude`. Do not print them
or commit raw Langfuse API metadata exports. The latest source manifest binds
the accepted files; validation records separate mocks from real evaluation.

Takeover scope requires a new user task. Do not infer authorization for paid
evaluations, judges, old-session migration, commits or pushes. Done criteria for
any identity change: focused regressions, model-free actor export/readback,
preserved native attribution and pinned originals, and updated records.
