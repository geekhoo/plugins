# Native Luna/high C0 attempt, 2026-10-31

Run `20261030T174312Z-26cab838` (UTC ID; 2026-10-31 in Singapore) completed its single initial invocation after 3420.686 seconds. The contestant recorded an overall final implementation review **PASS**, and the oracle passed 13/13 three times. The runner's `workflow_acceptance` remains `not-established`; it is the lifecycle's initialized default and is not an independent adverse review verdict. The final review and tracking files were uncommitted in the contestant workspace. No qualification or comparable parity claim follows from process exit 0.

| Measure | Result |
|---|---|
| Source / profile | `7f079186af3411400580ca770d90f789bdcac94b`; native LiteLLM; eight configured Luna/high roles; request and stream retry settings both 2 |
| Budget / operator actions | 6000 seconds, 60-second reserve; one initial invocation; zero recoveries, operator retries, resumes, provider probes or overtime |
| Candidate | `c9d55883f644fe0c85ef963610e9f66d15438891`; task commits `19f20a3` (T1), `c9d5588` (T2); review overall PASS, one lane PASS WITH WARNINGS; 21 passed / 1 skipped recorded by reviewer |
| Oracle | 13/13 x3; no failures or errors |
| Langfuse | Explicit CODEX-key readback: 19 traces, 911 observations, 394 generations, 498 tool calls; zero reported truncations |
| Cold briefs | Four cold subagents had local addressed assignments and task-consistent initial behavior. Their first input-token counts vary with brief length. Proxy-forwarded request bodies are not retained, so the `Agent message envelope:` in the actual first provider-bound request and exact receipt remain unverified. |
| Scoped parity | Withheld as a comparable score: strict `--no-rerun --require-complete` exited 1 with 12 missing task-process/own-commit validation fields and four pending judgments. Scoped parity exited 0 and generated a 73.68 diagnostic from incomplete inputs; it is not a strict comparable parity result. No score was published. |
| Proxy diagnostics | No `upstream_http_error` lines. Sixteen `upstream_transport_error` events record `ConnectionAbortedError` after stream start; the log does not establish the cause or identify the failing side. |

Example retained proxy line (UTC):

```json
{"error": "ConnectionAbortedError", "event": "upstream_transport_error", "stream_started": true, "ts": "2026-10-30T17:46:22Z"}
```

Readiness, the prompt hash `124eba9b416324a052c8e25031f1660200f52a05a74c9a1d9ce13527b270ddde`, roles and retry settings passed before launch. The generated preparation baseline was moved to the ignored operator folder with matching hashes before the clean-tree gate. The run's proxy and baseline passed current-literal credential scans; the final staged index was scanned before commit. Captured baseline and final workspace are preserved with byte pins; full Langfuse observations remain local in `outputs/c0-native-run-20261031/`. See [kanban](kanban.md), [handoff](handoff.md), and [references](references.md). The attempt is consumed; further paid action requires new authority.
