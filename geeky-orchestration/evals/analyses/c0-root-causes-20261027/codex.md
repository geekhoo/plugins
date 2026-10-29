# Codex literal tool-call output: offline investigation

The failure is established at the Codex client boundary: the assistant produced
the malformed `wait_agent` markup inside a completed `output_text` message,
not a structured function call. The main turn then completed and the children
were interrupted. The producer and reason for the malformed representation are
not established by the retained evidence. The patch below is a fail-closed
detection measure, not a repair of the provider's generation or a successful
workflow replay.

## Evidence and attribution

- Baseline `20261026T202318Z-fc8f0aa8/session.jsonl`, physical line 93
  (ordinal 92), contains the full assistant output, including
  `<tool_call><function=collaboration__wait_agent_a96e42dcffba0586</parameter><parameter=timeout_ms>300000</parameter></function></tool_call>`.
  Line 96 records `task_complete` repeating that text. `stream.jsonl` line 33
  records an earlier disconnect before `response.completed` and a reconnect;
  lines 37-38 record the text and turn completion. That order does not prove the
  disconnect caused the malformed output, nor which component closed it.
- `mapper.py` flattens a namespaced function into a label plus the first 16 hex
  digits of the SHA256 of `json.dumps((namespace, name))`. For
  `('collaboration', 'wait_agent')` that suffix is `a96e42dcffba0586`, exactly
  the suffix in the recorded text. The name is consistent with the bridge's
  mapped wire identity. Successful structured spawn calls in the same session
  show that the mapping worked for those calls, not that wait would work.
- The original mapper changed names only on structured `function_call` items;
  it left `output_text` unchanged. Thus it offered no guard against a model or
  intermediary emitting tool-call syntax as text. It cannot turn such text
  into a valid call without guessing. The saved observation is generated from
  the downstream native trace, not a byte capture of upstream SSE or requests.
  The bridge does not log request or response bodies. No preserved upstream
  tool definitions, exact SSE bytes, or upstream model template were found in
  the inspected run artifacts; do not attribute the representation to the
  model, router, or bridge without further evidence.
- Descriptions are copied into flattened tools, including the namespace
  description. A native prompt / flattened-name or provider grammar mismatch
  is a possible compatibility hypothesis, but the actual forwarded tool
  descriptions and provider prompt/template were not captured. Changing
  instructions to demand structured calls could be evaluated with a controlled
  compatibility fixture, but would be speculative as a root-cause fix here.

## Offline change and limits

`litellm_bridge/mapper.py` rejects the exact prefix
`<tool_call><function=` followed by an advertised wire name in assistant
output text, including across text deltas for the same item/content index,
and checks completed output messages and non-streaming responses. It never
parses, reconstructs, or executes text as a function call. The bridge sends a
sanitized `bridge_tool_call_as_text` error and stops forwarding when it encounters
the signature. JSON responses receive HTTP 502; an SSE response emits the error
event after its already-sent HTTP 200 headers.
SSE headers and earlier partial text may already have been sent; the offending
event and completion are not forwarded. Client retry behavior is not controlled
by this bridge. An assistant legitimately quoting the same exact advertised
signature is also rejected, and other tool-markup dialects, changed names or
variants are not guaranteed to be detected. This narrow guard is not a general
tool-call parser, output validator, or proof of provider compatibility.

`test_bridge.py` exercises the exact recorded malformed message, all split
points of the signature, item isolation, ordinary output, unknown names,
completed event and JSON handling, and a loopback fake-upstream SSE failure
without a forwarded completion or synthetic function call. Separate loopback
JSON and SSE checks verify the dedicated, sanitized error code. Existing
structured call mapping remains covered by the suite.

Validation on Windows, offline: `C:/Python314/python.exe -m pytest -q
geeky-orchestration/evals/adapters/codex/litellm_bridge/test_bridge.py
geeky-orchestration/evals/adapters/codex/test_litellm_bridge_lifecycle.py`:
**58 passed in 41.77s**. The first attempt using `python` failed because that
Python 3.13 installation lacks pytest; the installed Python 3.14 was used.
No provider, contestant, judge, telemetry publication, or evaluation was run.

The native `session.jsonl` SHA256 is
`a141ba0f845ef046b1e0e1c4b3c84b07308fadd51933e8fcf5b9391e6bcf6f6c`;
`stream.jsonl` SHA256 is
`8afbff04cd673c9ee23f311f6d9bae276441033f9babdb848df51bae0f4fd364`.
The source pin used for the historical attempt is in
`outputs/c0-fresh-sequential-mapped-20261027/source-pin.json`; this offline
patch changes the bridge after that pin and requires new readiness/source pins
before any separately authorized live activity.
