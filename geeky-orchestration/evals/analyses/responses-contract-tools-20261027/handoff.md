# Takeover brief

Target: Gerald's Windows host, PowerShell 7, workdir
`C:\Users\gerald.khoo\geekhoo-plugins`. Report within 400 words.
Read `geeky-orchestration/AGENTS.md`, this folder's README/references.md,
then `geeky-orchestration/evals/tools/responses_contract/README.md` and sources.json.
Verify `git rev-parse HEAD` equals `4228c3f73fc3894c86725cf42900406c1d2d981f`
and inspect status. Preserve dirty work and historical evidence.

Current state: tools verified with offline/loopback tests; example pinned plans
and verification are in `outputs/responses-contract-tools-20261027/`.
Both evaluations remain stopped. No endpoint has been tested; a bridge pass
does not establish native V2 support.

Takeover scope: read-only orientation and offline verification. If later given
specific endpoint authorization, obtain its URL/model and secure credential
environment, prepare fresh pinned plans and run only the selected cases/limits
with `probe --allow-network`. Preserve failures, not-run cases and partial/redacted
hash distinctions. Never execute returned tools or substitute arbitrary captured
conversations into a probe. Reuse validated reasoning/call state only as designed.

No endpoint/provider call, evaluation, live telemetry operation, judge, sign-in,
commit, push, retry or resume is authorized by this brief. Done for offline
takeover: verified pins/tests plus precise readiness/limits. Later live work
requires separate explicit authority; keep evaluations stopped.
