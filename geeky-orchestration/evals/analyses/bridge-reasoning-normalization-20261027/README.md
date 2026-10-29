# Minimal bridge reasoning normalization, 27 October 2026

**All three small live HTTP-bridge retests passed. Both C0 evaluations remain
stopped.** The patch adds 53 lines to mapper.py, plus a small diagnostic reporting
adjustment and focused regression tests. No commit or push was made; source HEAD
remains `4228c3f73fc3894c86725cf42900406c1d2d981f` with local changes.

| Requested model | Output cap | HTTP / selected client contract | Reported output / reasoning tokens |
|---|---:|---|---:|
| `vercel/minimax-m3` | 192 | 200 / PASS | 80 / 13 |
| `vercel/deepseek-v4.1-flash-1017` | 192 | 200 / PASS | 106 / 18 |
| `vercel/mimo-v2.6-pro` | 768 | 200 / PASS | 464 / 402 |

Exactly three client requests went through the actual authenticated loopback
HTTP bridge to LiteLLM, one per model. No automatic client/bridge retries,
returned-tool execution, evaluation, judge or explicit telemetry operation ran.
The diagnostic listener was closed and joined afterward. Reported output totals
650 tokens; gateway attempts and billing are not independently reconciled.

## Change and preservation boundaries

- Missing or null reasoning summaries become `[]`; existing summaries remain.
- Provider reasoning content tagged `output_text` becomes Codex-supported
  `reasoning_text`, retaining its text and other payload fields.
- A final reasoning item may reuse the already forwarded completed item only
  for the captured duplicate representation: same output index and ID, exact
  reasoning text, known metadata shape, empty annotations, and identical
  encrypted-content presence/value. Contradictory text, summaries, ciphertext,
  unknown metadata or identities are not silently overwritten.
- The completed-item cache is request-local and updated after successful
  provenance processing. Functions are never reconciled by this reasoning fix.
- Bridge diagnostics retain raw wire findings separately and revalidate the
  mapped client stream. Native validation is unchanged. Raw parse/truncation,
  ordering, mode and function conflicts remain failures.

HTTP server code is unchanged. Saved before/after source copies and diffs make
the bounded patch reviewable. The prior raw captures and scores are unchanged.

## Verification

**178 regression tests passed**: original encryption/provenance, function mapping,
text-call guard, HTTP/lifecycle and contract tests, plus 20 reasoning cases and
seven diagnostic separation cases. All three previously failing saved captures
pass strict client reconstruction after mapping, with their original bytes,
function arguments and call IDs preserved. Independent review found no required
issues; adversarial conflicts remain errors.

The live path was native synthetic request → authenticated HTTP bridge → LiteLLM
flat function request → normalized SSE → strict native client-shape validator.
Each response had matching item-done/final objects, exact fixture arguments,
namespace/name and explicit plaintext metadata. This proves the selected bridge
case; native upstream support and a full Codex/MXC workflow were not tested.
Thinking remained active despite requested effort `none`; this patch does not
establish thinking-off behavior.

Ignored evidence: `outputs/bridge-reasoning-fix-20261027/`: before/, mapper.py.diff,
cli.py.diff, regression-tests.log, authorization.json, per-model request/normalized
response/report captures, results.json, cleanup.json and verification.json.
Raw upstream bodies are not logged by the HTTP bridge; retained earlier raw
captures supply the deterministic before/after proof.

Updated records: root/plugin READMEs, adapter/tool README, readiness and lessons.
Earlier probe reports remain historical; source pins must be refreshed for later
preparation. Both evaluations stay held pending separate explicit launch authority.
See [kanban](kanban.md), [handoff](handoff.md), [references](references.md).
