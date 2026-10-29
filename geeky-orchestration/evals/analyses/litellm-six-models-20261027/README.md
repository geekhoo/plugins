# Small LiteLLM model probes, 27 October 2026

The refreshed LiteLLM key was read from `C:\Users\gerald.khoo\env.cloud.claude`
and used in the probe process only. No credentials were displayed or written to
another configuration. The six requested model routes each returned HTTP 200
on the basic request. This verifies routing/authentication and a response, not
successful completion of every tiny-budget contract.

Exactly **18 client HTTP requests**, zero client retries: one basic JSON request
and one SSE `collaboration.send_message` request in each native/bridge profile
per model. Basic output cap was 32 tokens; native/bridge caps were 96 each.
Reasoning was left at endpoint defaults; deadline 30 seconds per request.
No returned tool, evaluation, judge, sign-in or telemetry exporter was executed.
Both evaluations remain stopped. No source commit or push was made.

| Requested model | Basic route | Native V2 selected probe | In-process bridge selected probe |
|---|---|---|---|
| `vercel/gpt-6-luna` | HTTP 200; marker PASS | Structured namespaced call with opaque message; encryption/arguments unverified | PASS |
| `vercel/minimax-m3` | HTTP 200; output cap reached | Exact plaintext arguments but absent `encrypted_function_args: []` | Inconclusive: output cap reached |
| `vercel/glm-5.3-flash` | HTTP 200; output cap reached | Inconclusive: output cap reached | PASS |
| `vercel/deepseek-v4.1-flash-1017` | HTTP 200; output cap reached | HTTP 400: selected function not found in tools | Inconclusive: output cap reached |
| `vercel/claude-haiku-5.5` | HTTP 200; marker PASS | HTTP 400: selected function not found in tools | PASS |
| `vercel/mimo-v2.6-pro` | HTTP 200; output cap reached | Plaintext declaration absent; SSE item mismatch and missing reasoning summary | Inconclusive: output cap reached |

All budget-limited cases explicitly report `max_output_tokens`; they are not
proof of absent tool support. No caps were raised and no probes repeated.
Luna's opaque native argument is not assumed decrypted or correct merely from
its prefix. Minimax and MiMo's exact plaintext without the marker reproduces the
specific native plaintext-contract gap documented in the prior investigation.

Bridge PASS means raw flat function calls were validated and mapping restored
the original namespace/name and explicit plaintext declaration. The empty
declaration is mapper-produced. It does not establish native V2 endpoint support,
native Codex execution, encryption/decryption, messaging roundtrips or C0 readiness.
These were one-case probes, not the full diagnostic matrix.

## Accounting and evidence

The client issued 18 calls and performed no retries/redirects. DeepSeek's native
HTTP 400 error contains gateway routing metadata reporting 20 internal provider
attempts. Server-side retries/fallbacks are outside this probe's control. Do not
equate client count with underlying provider attempts or use captured successful
usage as complete billing. Reported token usage, including reasoning/cached fields,
is retained without a cost reconciliation; some fields are inconsistent.

Ignored evidence directory: `outputs/litellm-six-models-20261027/`:
authorization.json, results.json, interpreted-results.json, verification.json,
run-small-probes.py, per-model source-pinned plans/reports and redacted raw/client
captures. The attempt marker prevents accidental repetition. Source is bound to
HEAD `4228c3f73fc3894c86725cf42900406c1d2d981f` plus the tool source hashes.
Historical captures and scores are unchanged. See [kanban](kanban.md),
[handoff](handoff.md), [references](references.md).
