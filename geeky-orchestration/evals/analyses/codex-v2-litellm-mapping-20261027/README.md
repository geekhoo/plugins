# Codex V2 to LiteLLM wire mapping

Implemented on 27 October 2026, Singapore. **Both evaluations remain stopped.**
The owner authorized this fix and one small LiteLLM verification request. No
evaluation launch, judge call, telemetry operation, commit or push was performed.

## Change

The adapter keeps Codex's native V2 collaboration API and role configuration.
The new `evals/adapters/codex/litellm_bridge/` package maps its provider traffic:

- V2 agent messages and named, unpaired tool notifications become ordinary
  untrusted user messages with sender/recipient/metadata envelopes and preserved
  content order. Namespace functions become collision-safe flat functions.
- Schema-node `encrypted` annotations are removed before forwarding. Legitimate
  properties named `encrypted`, tool constraints, call IDs and control fields
  remain intact.
- JSON and SSE responses restore original function names/namespaces and explicitly
  mark plaintext collaboration calls with `encrypted_function_args: []`.
- Opaque or invalid encryption metadata fails closed. Tagged content is recovered
  only from exact hash-bound plaintext provenance; no cryptographic guessing or
  silent content deletion occurs. Provenance updates are atomic per JSON response
  or SSE event. Ordinary encrypted reasoning is left unchanged.

The loopback server authenticates incoming requests, uses a fixed upstream and
key from process environment, forwards a bounded User-Agent, and does not retry,
follow redirects or log bodies/credentials. `litellm-bridge.ps1` owns its process.
The runner starts it only for future `-Litellm -Launch`, records source hashes,
and stops it on completion or failure. Preparation and mock paths do not start it.
The readiness inventory now includes the mapping and lifecycle sources.

## Fresh verification

| Check | Result |
|---|---|
| Mapping, HTTP, SSE, lifecycle and readiness suite | 63 passed |
| Existing profile, worker/reviewer settings and fake-runner regressions | 63 passed, 45 subtests passed |
| Independent protocol/code review | PASS, no remaining required findings |
| Synthetic live streaming request | HTTP 200; completed; MAPPING_OK |
| Live request count / retries | One upstream POST; zero retries |
| Requested model / diagnostic effort / output cap | claudex-001 / low / 256 tokens |
| Reported response model | mimo-v2.6-pro; this does not establish a fixed alias backend |
| Reported usage | 186 input + 110 output = 296 tokens |
| Elapsed | 6.612 seconds |
| Response mapping | collaboration.send_message; encrypted_function_args=[] |
| Cleanup | Diagnostic listener stopped; no evaluation started |

The live input used synthetic task text intentionally labelled encrypted, with
an explicit hash-bound plaintext registry. The bridge preserved that task,
forwarded the ordinary wire representation, and restored the returned tool's
plaintext declaration. The returned function was not executed. The diagnostic
used low effort to keep it bounded; it did not change the held C0 all-role/high
settings.

Detailed local evidence is under the repository's ignored
`outputs/codex-v2-bridge-verification-20261027/`: `live-probe-result.json`,
the synthetic native/upstream requests, `mapping-lifecycle-readiness-tests.log`,
`existing-regression.log`, and the final source/evidence preservation report.
The live result binds the exact four mapping source hashes. The diagnostic
script's exclusive attempt file prevents accidental repetition.

## Limits and state

This proves the selected wire path through the real LiteLLM endpoint. It does not
prove a full Codex process, MXC reachability, nested workflow execution, Langfuse
delivery, or handling of every Responses feature. Namespace functions and the
generation endpoint are supported; namespaced custom tools, WebSockets and the
compact endpoint are not implemented. Unknown opaque historical handoffs need
plaintext provenance and are not repaired in place.

All 49 retained files from the three interrupted/failed C0 capture directories
are preserved and checked separately. No original score or raw trace was changed.
The old reset state remains held. New source files and runner changes are local,
uncommitted work based on `4228c3f73fc3894c86725cf42900406c1d2d981f`.

Updated records: root/plugin READMEs, adapter README, current readiness, runbook
and lessons. Old preparation pins and launch wrappers remain historical; refresh
them rather than treating this mapping probe as permission or readiness to run.
See [kanban](kanban.md), [handoff](handoff.md), and [references](references.md).
