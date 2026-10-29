# Offline takeover brief

Target: Gerald's Windows host, PowerShell 7, workdir
`C:\Users\gerald.khoo\geekhoo-plugins`. Budget: return a report within 400 words.
Read this folder's README, codex.md, claude.md, then ../../c0-readiness.md,
../../../AGENTS.md and references.md. Verify `git rev-parse HEAD` is
`4228c3f73fc3894c86725cf42900406c1d2d981f` and inspect status before acting.
Preserve all current uncommitted changes and historical evidence.

Current state: both evaluations terminal/stopped. Offline patches detect the
observed Codex text-call signature and propagate the planning budget. Tests and
independent review are recorded in `outputs/c0-root-causes-20261027/verification.json`.
Live effectiveness and Codex upstream producer remain unproved. Native client
retry behavior is not controlled by the bridge. Current fixes are not in HEAD,
so the runners reject stale committed exports; old prepared commands are stale.

Takeover scope: read-only inspection of the local LiteLLM deployment source or
configuration if the owner supplies its location. Determine how `claudex-001`
routes tool schemas and parses tool-call output. Keep credentials and request
bodies out of output/repository files. Report proven facts separately from
hypotheses and identify the smallest local correction and offline regression
fixture before changing anything outside this checkout.

No evaluation, provider call, paid probe, live telemetry operation, judge,
sign-in, commit, push, retry or resume is authorized by this brief. Keep both
evaluations stopped. Done: evidence-bound attribution if possible, otherwise
the exact missing prerequisite, plus an offline fix/test proposal. New live
proof requires separate explicit authority.
