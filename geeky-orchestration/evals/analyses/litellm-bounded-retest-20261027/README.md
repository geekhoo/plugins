# Bounded token/thinking retest and Luna opaque receive

27 October 2026. Both C0 evaluations remain stopped. This work made **12 further
client HTTP requests**, with no automatic transport retries, actual tool/agent
execution, evaluation, judge or explicit telemetry operation. Credentials were
read fresh from the owner's external env file and retained only in process memory.
No source commit or push was made.

Eight previously token-limited cells were retested. Conclusive earlier results
were carried forward rather than buying identical checks. Basic caps rose from
32 to 64 (GLM 128); bridge caps rose from 96 to 192; GLM native used 384.
MiMo bridge alone required cap steps 192 → 384 → 768, then completed with 277
reported output tokens. No final retested cell remains token-limited.

| Model, all `vercel/` | Native V2 | Bridge |
|---|---|---|
| `gpt-6-luna` | **Selected opaque receive PASS**; altered opaque value did not recover marker | Prior selected PASS |
| `minimax-m3` | Prior exact plaintext call omitted plaintext declaration | Completed function payload; strict wire FAIL: missing reasoning summary and item mismatch |
| `glm-5.3-flash` | Completed without the required structured call; item/summary failures | Prior selected PASS |
| `deepseek-v4.1-flash-1017` | Prior HTTP 400: function not found | Completed function payload; strict wire FAIL: missing reasoning summary and item mismatch |
| `claude-haiku-5.5` | Prior HTTP 400: function not found | Prior selected PASS |
| `mimo-v2.6-pro` | Prior plaintext declaration absent; stream mismatch | Completed function payload at cap 768; strict wire FAIL: missing reasoning summary and item mismatch |

The new basic replies from MiniMax, DeepSeek and MiMo contained the exact marker,
but failed the full selected wire contract because their reasoning items omit
`summary`. GLM basic passed. A correct marker or function payload is distinct
from a valid complete Responses stream. Raw failures are preserved, not repaired
in place or converted into passing reports.

## Thinking controls

Sent `reasoning.effort="none"` for Luna, MiniMax, DeepSeek and MiMo. GLM was sent
`"low"`: its official docs describe thinking as required. These are documented
shared Responses controls; no speculative native-provider override was sent.

Positive reasoning-token usage and reasoning content remained on the MiniMax,
DeepSeek and MiMo routes despite `none`, so **thinking-off is not established**
there. The path may ignore, override or fail to forward that request. Public docs
do not identify which deployed layer is responsible. No known-good alternate
thinking-disable parameter through this exact LiteLLM Responses path was found.
Further cap increases do not repair that mapping or the wire-shape failures.

[Vercel reasoning controls](https://vercel.com/docs/ai-gateway/models-and-providers/reasoning),
[GLM thinking requirements](https://docs.z.ai/guides/vlm/glm-5.3-flash),
[MiniMax Responses](https://platform.minimax.io/docs/api-reference/responses-create),
[DeepSeek controls](https://api-docs.deepseek.com/guides/thinking_mode/),
[MiMo native Chat example](https://mimo.mi.com/models/en-US/mimo-v2.6-pro).
Native Chat thinking switches are not proven LiteLLM Responses passthroughs.

## Luna opaque issue

Reused the exact 164-character opaque argument from the earlier native response:
source SHA256 `6156d2dac04541a5e50feb2203725fc642dc384d6dd801fed2634284343ff84b`,
opaque-value SHA256 `3de1d8322d7a063ad797ba91bf76526d2cf03a871ec9d3c54c3b0505544cdf9b`.
No new send-message generation was needed.

A fresh request placed only that value inside native `agent_message` /
`encrypted_content`, with no original plaintext marker, function history, tools
or previous-response ID. Luna completed and returned the exact original marker.
A second request changed one internal character, preserving length/prefix/alphabet;
it completed with the requested unreadable sentinel and did not recover the marker.
Both HTTP statuses were 200; no explicit cryptographic API rejection was observed.

This supports selected native opaque send/receive behavior through the endpoint.
The earlier plaintext-probe failure did not establish defective ciphertext. Missing
`encrypted_function_args: []` is legitimate for a genuine encrypted message: the
pinned router selects `Direct`, which the V2 handler maps to encrypted content.
This result proves neither a particular encryption algorithm nor authenticated
agent identities, every V2 tool, or full Codex/MXC workflow readiness.

The [pinned wire source](https://raw.githubusercontent.com/openai/codex/6aaac694803004a63c6f393d153c96d22521a6b9/codex-rs/protocol/src/models.rs)
defines `AgentMessageInputContent::EncryptedContent` and requires a vector-valued
`Reasoning.summary`; the missing summary is an actual selected contract gap.

## Evidence and state

Ignored evidence: `outputs/litellm-bounded-retest-20261027/` contains authorization,
per-cap source-pinned plans/reports, redacted raw/client captures, Luna valid and
tampered request/response pairs, results.json, mimo-supplement-results.json,
interpreted-results.json, verification.json and three offline envelope/tamper tests.
Prior captures and the preceding 18-call probe remain unchanged. Client request
counts do not establish underlying gateway attempts or independently reconciled
billing. Models are requested aliases; backend equivalence is not established.

Root/plugin READMEs and readiness link this follow-up. Earlier reports and scores
remain historical. See [kanban](kanban.md), [handoff](handoff.md), [references](references.md).
