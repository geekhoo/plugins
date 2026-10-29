# Responses API and Codex V2 contract tester

The [reasoning bridge follow-up](../../analyses/bridge-reasoning-normalization-20261027/README.md)
repairs a narrow upstream representation. Bridge reports keep `wire_errors` and
`wire_stream_errors` as upstream evidence, while the outcome validates the mapped
client contract and recomputes item consistency. Native checks remain strict;
parsing/truncation and unrepaired conflicts still fail. Existing prepared plans
need fresh source pins after this change.

Python 3.10+ standard library; pytest is needed only for tests. No Codex process,
MXC, judge, Langfuse exporter or real collaboration tool is started. Only
`probe --allow-network` contacts the configured endpoint. Both C0 evaluations
remain stopped; creating these tools authorized no endpoint call.

Native structures are pinned to Codex `rust-v0.164.0`, commit
`6aaac694803004a63c6f393d153c96d22521a6b9`. [sources.json](sources.json)
records official source URLs, hashes, symbols and limits. This is a selected
synthetic subset, not a complete API schema or native workflow qualification.

| Profile | Endpoint traffic | What a pass establishes |
|---|---|---|
| `responses` | Common flat-function/text Responses subset | Selected JSON/SSE, structured calls and result handoffs |
| `codex-v2-native` | Native namespaces and agent/tool messages | Selected native plaintext V2 cases; no decryption proof |
| `codex-v2-bridge` | Existing mapper translates requests/responses in-process | Selected mapper compatibility; native endpoint support is **not tested** |

Twelve cases: `message`, `function`, `function_roundtrip`, `v2_spawn`, `v2_send`,
`v2_followup`, `v2_wait`, `v2_parallel_spawn`, `v2_agent_message`,
`v2_named_output`, `v2_unpaired_output`, `v2_send_roundtrip`.
`--cases all` selects those available in the chosen profile.

Checks cover call identity, exact argument JSON, unique/correlated call IDs,
parallel calls, namespace preservation, explicit `encrypted_function_args: []`
for plaintext spawn/send/follow-up, named paired/unpaired results, and agent
message content. Roundtrips introduce a distinct result marker only in the tool
result, retaining actual returned call IDs and validated reasoning/call state.
Returned tools are never executed. Extraneous assistant messages and tool syntax
in ordinary text fail function-call probes.

Opaque function encryption fails as unsupported. Reasoning `encrypted_content`
is separate opaque API state. Encrypted agent/tool content receives structural
checks only. A genuinely encrypted native response can be outside these plaintext
probes; failure does not prove every V2 mode unsupported.

SSE requires `response.completed`, matching completed items, consistent text and
argument deltas, and valid terminal ordering. `[DONE]` alone, premature/duplicate
`[DONE]`, duplicate JSON keys, non-finite numbers, partial streams, refusals,
incomplete responses and wrong JSON/SSE modes fail.

## Offline use

From the repository root, using an available Python interpreter:

```powershell
python geeky-orchestration/evals/scripts/responses-contract.py catalog
python geeky-orchestration/evals/scripts/responses-contract.py prepare --profile responses --model claudex-001 --cases all --stream both --max-requests 8 --output outputs/responses-basic-plan
python geeky-orchestration/evals/scripts/responses-contract.py prepare --profile codex-v2-native --model claudex-001 --cases all --stream both --max-requests 28 --output outputs/responses-native-plan
python geeky-orchestration/evals/scripts/responses-contract.py prepare --profile codex-v2-bridge --model claudex-001 --cases all --stream both --max-requests 28 --output outputs/responses-bridge-plan
```

Model and limits are editable. Effort is omitted unless `--reasoning high` (or
another supported effort) is supplied. Defaults: 256 output tokens, 30-second
total deadline per HTTP attempt, 2 MiB response cap. Small output caps can yield
legitimate incomplete results. Every output directory must be new.

Preparation saves source-pinned `plan.json` and synthetic request files.
Probe/replay rebuild fixtures and verify pins, rejecting arbitrary prompt/tool
edits and stale sources. Re-prepare after code changes. These plans do not change
the held C0 settings or constitute signed authorization.

Validate a saved request without credentials/network or copying its payload:

```powershell
python geeky-orchestration/evals/scripts/responses-contract.py validate-request --profile codex-v2-native --input outputs/responses-native-plan/v2_send-json.request.json --output outputs/request-validation
```

Replay a previously saved endpoint body:

```powershell
python geeky-orchestration/evals/scripts/responses-contract.py replay --plan outputs/responses-basic-plan/plan.json --item function-json --response saved-response.raw --output outputs/response-replay
```

Replay validates one response; it does not execute a second turn or establish
live capability. JSON replay shares the live strict decoder; SSE replay checks
event consistency. Saved-request validation covers only the documented subset.

## Later endpoint probe

Set `RESPONSES_API_KEY` securely outside commands/repository files. After specific
endpoint diagnostic authorization, an example is:

```powershell
python geeky-orchestration/evals/scripts/responses-contract.py probe --plan outputs/responses-basic-plan/plan.json --endpoint $env:RESPONSES_ENDPOINT --api-key-env RESPONSES_API_KEY --allow-network --output outputs/responses-basic-probe
```

Exact custom routes and Azure `api-version` queries are preserved. Root/`/vN`
bases get `/responses` appended. Bearer auth is default; `--auth api-key` supports
Azure, `--auth none` supports unauthenticated services, and `--headers-env NAME`
loads extra headers from an environment JSON object (such as `x-api-key` or
organization/project headers). Conflicting transport/auth headers, URL userinfo,
fragments and credential-like query names are rejected. Keep secrets out of URLs;
name-based detection cannot recognize credentials under benign query names.

No retries, redirects or automatic model discovery occur. Failure stops the
matrix unless `--continue-on-failure` requests other cases, still within the cap.
Counts are local attempts, not proven receipt/billing. Deadlines bound client
DNS/connect/TLS/send/read waits, not remote cancellation; a timed-out OS DNS thread
may finish later. Direct HTTP/1.1, verified TLS and one resolved address are used,
without environment proxies or address fallback. Unsupported compression is
rejected before retaining a body. HTTP/2-only endpoints, WebSockets, compact,
multimodal/custom/built-in tools and actual decryption are outside this version.

## Evidence

`attempt.json` precedes network activity; `progress.json` precedes each attempt.
`report.json` records case errors/unreached cases, timings, requested/reported
model, source pins, hashes and counts. No comparison score is produced.
Each turn saves the exact serialized request body and captured response body
after HTTP framing removal. Authentication headers are never stored. Known
configured secrets are redacted in literal/mixed JSON-escaped spellings, including
derived values and keys. Redacted stored hashes differ from original body hashes;
flags record this. Unknown secrets and arbitrary encodings are not detected.
Use ignored `outputs/` for captures.

Partial captures have `captured_body_sha256`, `response_body_complete=false` and
null full-response hash. Bridge captures also include client request/response JSON
for comparison with the wire. In-process mapping tests neither listener lifecycle
nor actual Codex execution. HTTP 200, alias/model fields and mapper passes do not
establish backend identity or full workflow readiness.

Exit codes: `0` selected checks/preparation passed; `1` contract/endpoint failure;
`2` configuration, input, stale-pin or I/O error.

```powershell
C:/Python314/python.exe -m pytest -q geeky-orchestration/evals/tools/responses_contract
```

The package suite passed 93 offline/loopback tests on 27 October 2026. Live
TLS/provider behavior remains unverified. See the
[implementation record](../../analyses/responses-contract-tools-20261027/README.md).
