# Native Luna/high C0 attempt: crash during plan review

Run `20261030T150121Z-a55a910b` is **NOT ACCEPTED**. The single authorized initial invocation at source `ef2cd7f989b83b23b025a986dc5c2640c5cbaba9` crashed after 809.255 seconds, during plan-review revisions and reviewer rechecks. The stream reports `502 Bad Gateway: upstream http error` through the local native proxy followed by `turn.failed`; this does not identify the upstream root cause. A separate startup access-denied warning is not established as the cause. Implementation and final review were not reached.

| Measure | Result |
|---|---|
| Profile and authorization | Native LiteLLM; eight configured Luna/high roles; 6000 seconds / 60-second reserve; one invocation, zero recoveries, retries, resumes or overtime |
| Source and prompt | `ef2cd7f989b83b23b025a986dc5c2640c5cbaba9`; prompt SHA-256 `124eba9b416324a052c8e25031f1660200f52a05a74c9a1d9ce13527b270ddde` |
| Specification and planning | Spec commit `3a40199903c4026e5372f9cd17144e96f52cfd40`; planning artifacts remained uncommitted; plan-review in progress |
| Oracle | 0/13 on each of three repetitions; 13 missing-package setup errors each; repeated failure, not a passing result |
| Langfuse | Explicit CODEX-key readback: 9 traces, 198 observations, 82 generations, 107 tool calls, zero reported truncation |
| Cold workers | No cold implementation workers captured. All eight recorded subagents had forked-parent metadata. The brief-delivery fix remains unverified by this run. |
| Strict scoring and scoped parity | Withheld: strict scorer exit 2 on incomplete failed trace and missing cumulative token count; scoped parity exit 1 because no score source exists. No synthetic input or score published. |
| Credential scan | Terminal baseline scan passed for current literal credentials; final staged scan performed before commit. |

## Cause, found after closeout

The 502 came from LiteLLM, not from the local proxy. The proxy passes any upstream 4xx or 5xx status through unchanged (`litellm_bridge/server.py`), and its own 502 paths carry other codes. The failing request was the main thread's first call after a recheck reviewer's verdict arrived at 15:15:06.991Z. The turn ended at 15:15:07.161Z, so the gateway answered in under 0.2 seconds: a fast rejection, not a timeout. The proxy kept no error body, Langfuse holds only Codex-side traces, and this LiteLLM key gets 403 on `/spend/logs`. The upstream cause is unknown.

One 502 ended the run because the run profile set Codex's `request_max_retries` and `stream_max_retries` to 0. Codex would otherwise retry a 5xx.

The `agent_message` lowering (`3bfc927`) did run live. Six reviewer messages to the main thread were lowered, and each was followed by a successful request. Cold implementation workers were not reached, so their brief delivery is still unverified.

The commit that adds this section also changes the harness: the run profile allows 2 request and 2 stream retries, and the proxy writes each upstream error's status, trace headers and a redacted body excerpt to its stderr log. Native probes keep zero retries. The verdict stands: NOT ACCEPTED, capture bytes unchanged.

## Preparation and provenance

The original preparation `20261030T143704Z-4ab4c0dc` at `7cf5b3f` never launched. Its untracked baseline caused the first launch script invocation to fail before claim; it was archived in `ef2cd7f`. On relaunch, the first offline preparation stopped at an existing provenance report; that report and prior preparation artifacts were preserved and offline preparation was rerun. Its eight role files and prompt hash passed; its new preparation baseline was moved to the ignored operator folder with hashes verified before the clean-tree launch gate. The live runner generated a separate run ID and one attempt claim. The carried authorization-reference string in run metadata names the original `7cf5b3f`; the owner's relaunch explicitly authorized this attempt after the archive commit and run.json binds the actual source `ef2cd7f`. No source, prompt, scoring code or rubric was changed.

Captured baseline and final workspace are preserved with byte hashes. Full Langfuse observations and operator logs remain local in `outputs/c0-native-run-20261030b/`. See [kanban](kanban.md), [handoff](handoff.md), [references](references.md), and [readback](evidence/langfuse-readback.json). The attempt is consumed; no retry or further paid action is authorized here.
