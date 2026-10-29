# Recorded failure boundaries

Pointers below refer to the preserved baseline
`../../baselines/c0-wordstat/20261029T062343Z-ffd63c3c/`.

## Terminal provider failure

`stream.jsonl:568` contains the final `litellm.BadRequestError`, HTTP 400,
`AI_APICallError`: `Encrypted function output content could not be decrypted
or decoded.` Line 569 records `turn.failed`. `session.jsonl:1716` timestamps
the terminal event at 2026-10-29 07:05:38.701 UTC.

The captured gateway metadata reports this sequence:

| Provider | Recorded UTC interval | Result |
|---|---|---|
| Bedrock | 07:05:31.938-07:05:33.388 | 503, Service temporarily unavailable |
| Azure | 07:05:33.393-07:05:37.778 | 400, input[178].id is call_419e1c51bd415114bfe1caf23a78c0df; expected an ID beginning with tsc |
| OpenAI | 07:05:37.783-07:05:38.499 | 400, encrypted function output decode failure |

The metadata names model group `vercel/gpt-6-luna`, canonical model
`openai/gpt-6-luna`, one model attempt and three gateway provider attempts.
Generation ID: `gen_01M637MTFNBTHWQ52YP66EEBWD`. Main native session:
`01a18654-4426-7cc2-b9e2-9352e3ca44f3`. LiteLLM's statement that no fallback
was attempted describes its layer; the nested gateway metadata reports its
own provider attempts. These records do not establish billing or independent
operator launches.

Azure's rejected ID is visible in `session.jsonl:1558` at 06:54:02.922 UTC,
in a `tool_search_call` that also carries the separate ID
`tsc_1793256842647_fuiyx6g3ll`. Its output is line 1560. The failing request's
serialized `input[178]` was not saved. The exact transformation that caused
the rejection is therefore unproven. No replay, provider probe or fix was run.

## Earlier coder behavior

The T1 transcript is
`subagents/rollout-01a18670-7133-7ae0-9a8f-53fa973eb17f.jsonl`, linked by
`rollout-manifest.json:65`. Its first line records own-history boundary ordinal
262; earlier inherited parent activity is excluded from these observations.

- Lines 280-323 contain six failed documentation patches: PowerShell heredoc
  parsing, Bash `0xC0000022`, and invalid patch termination.
- README and handoff edits then succeeded at 06:55:15.918 and 06:55:49.018 UTC.
- Line 337 reports an incorrect nested agent path. Lines 347, 373 and 403
  record messages delivered to the same actor that sent them.
- Three waits total about 349 seconds, at lines 348-351, 374-377 and 409-412.
  Interruptions appear at lines 415 and 426.
- Recorded writes target planning documents or the heartbeat. No product
  source/test patch appears, and the final workspace has no wordstat package.

Role/context confusion is an inference from these actions. Initial patch
failures explain only the first portion of the delay; the terminal provider
failure alone does not explain the earlier waiting. The coder transcript
does not establish an upstream error during that wait. Assignment payloads
are encrypted, so task visibility and the cause of the confusion remain
unproven. The worker's edits to tracking documents are preserved in the final
workspace snapshot, rather than attributed to product implementation.

Read-only diagnostic worker `/root/gate_review` returned these pointers. The
parent retained scoring, preservation, credential scans and publication.
