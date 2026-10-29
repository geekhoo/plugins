# Codex C0 — focused native-wire preparation

Prepared only; both evaluations remain stopped. Source HEAD is
`0b1f5fbc0e84b110ea0f9fa59ddfa711b46cf53a`, with an uncommitted operator-runner
option and focused tests. Contestant workflow/prompt, model and effort are unchanged.

## What the failed trace proves

Run `20261028T114114Z-eb4361e5` successfully executed structured research dispatches,
waits and the first review. The first failing re-reviewer executed four shell
commands before `bridge_mapping_error`; a second reviewer and then the main turn
failed the same way. These were not deadline exhaustion or the earlier literal
wait-markup failure.

The exact mapping exception cannot be recovered: request/response bytes were not
saved and the bridge returned a generic error. Offline reconstruction of all
captured histories passes:352main,342first-reviewer and353second-reviewer items.
Thus no specific encryption/catalogue defect is falsely declared the historical
cause. A shrinking-catalogue history rejection is reproducible separately, but
is unproved for this run and was not patched speculatively.

## Minimal preparation change

`run-codex-baseline.ps1` now accepts `-LitellmWireMode bridge|native`. Bridge
remains the default. The Luna candidate explicitly selects native, using
`https://litellm.markefin.com/v1` directly. No mapping listener or V2-to-V1
conversion is involved. Native V2 namespaces and encryption semantics reach the
gateway unchanged; classic JSON tools and the existing V2 catalogue remain.

This route is supported by saved native Luna send/receive proof: HTTP200 and
exact recovery from the opaque message, plus an altered-value negative that
returned the unreadable sentinel. It is selected protocol proof, not a complete
native C0 workflow or a cryptographic-authentication qualification claim.

Fresh preparation materializes a seed-only workspace, isolated HOME/CODEX_HOME,
all eight role layers explicitly `vercel/gpt-6-luna`/high, detailed reasoning
summaries, configured Langfuse hooks, and a verified private18-file MXC build.
Settings stay6000-second timeout,60-second reserve, one attempt, zero recoveries.
The recorded Luna waiver is referenced without inventing fresh qualification.

Seven focused tests pass, including an actual fake native-launch path whose
bridge starter deliberately throws if called. No real MXC workload, provider
call, judge, source commit or push was performed.253 retained capture/snapshot
pin checks pass. Both evaluations remain stopped.

Local evidence: `outputs/c0-codex-native-preparation-20261029/` contains
preparation.json, verification.json, history-replay.json, focused-tests.log,
role-readback.json, build/source/tool pins and the exact unexecuted
launch-command.ps1.txt. The live command creates a fresh attempt deadline;
do not replay the preparation record's expired absolute deadline.

Future completion must be established by the real five-stage workflow, final
review PASS, accepted task/phase gates,13/13oracle over3runs and Langfuse readback.
Offline checks cannot certify that a future model run will finish. No new live
compatibility claim or automatic retry is included here.

Stale documents: the older bridge-based Luna launch recipes are superseded for
this candidate and preserved unchanged. The original failure and Claude results
remain historical. Current root/plugin READMEs and readiness point here.
