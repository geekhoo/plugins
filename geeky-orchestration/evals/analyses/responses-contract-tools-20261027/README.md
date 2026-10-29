# Responses contract tools, 27 October 2026

Implemented [reusable diagnostics](../../tools/responses_contract/README.md):
offline catalog, preparation, saved-request checks and replay, plus an explicit
endpoint probe for later use. No real endpoint or evaluation was contacted.
HEAD stays `4228c3f73fc3894c86725cf42900406c1d2d981f`; changes are uncommitted.

Parallel workers owned contracts/cases and HTTP/SSE transport; parent owned CLI,
integration and records. Independent review found redaction, wire-hash, strict
JSON, stream consistency and followup filtering issues; each was fixed with
regressions and re-reviewed. Final review: no remaining required findings,
93 package tests passed offline/loopback. Existing bridge regressions and retained
capture preservation are recorded in `outputs/responses-contract-tools-20261027/verification.json`.

Three profiles distinguish common Responses, selected native V2 plaintext and
in-process mapper compatibility. Twelve cases cover JSON/SSE, single/parallel
calls, spawn/send/followup/wait, agent messages, named paired/unpaired outputs
and correlated handoffs. No returned tool is executed. See
[source pins and limits](../../tools/responses_contract/sources.json).

Prepared examples are under ignored `outputs/responses-contract-tools-20261027/`:
`basic-plan/`, `native-plan/`, `bridge-plan/`. They are diagnostics, not C0 launches
or qualification. No endpoint command was executed. Root/plugin READMEs,
adapter README and readiness link the tools; historical reports, scores and
old preparation evidence remain unchanged and are not promoted to live readiness.
See [kanban](kanban.md), [handoff](handoff.md), [references](references.md).
