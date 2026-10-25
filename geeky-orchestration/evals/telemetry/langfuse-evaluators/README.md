# Langfuse evaluators for geeky-eval runs

Definitions created in the Langfuse project with `npx langfuse-cli api ...` (CLI snapshot 4.35, server 4.70).

| File | Langfuse object | State |
|---|---|---|
| `forbidden_git_operation.ts` | Code evaluator: BOOLEAN on each shell tool call (Claude `Tool: Bash`, Codex `exec_command`) for history rewrites (`reset ... HEAD`, `--amend`, `rebase`) and `push` / `--force` / `--no-verify`. | Not created: the deployment answers `Code evaluations are not enabled`. Needs `LANGFUSE_CODE_EVAL_DISPATCHER=insecure-local` and `QUEUE_CONSUMER_CODE_EVAL_EXECUTION_QUEUE_IS_ENABLED=true` on the web and worker containers (TypeScript only, trusted code). |
| `final_report_complete.judge.json` | LLM-as-a-judge evaluator (BOOLEAN): the final report gives every stage outcome, test counts, commits and deviations, with no unverified completion claim. | Created, paused by Langfuse (`DEFAULT_EVAL_MODEL_MISSING`): the project has no LLM connection. |
| `final_report_complete.rule.json` | Evaluation rule: environment `mxc`, root observations named `Codex Turn` or `Conversational Turn`, output -> `{{output}}`. | Created **disabled**. |

To run the judge: add an LLM connection (`llm-connections upsert`, e.g. the LiteLLM proxy with the `anthropic` adapter), set it as the default evaluation model, reactivate the evaluator and enable the rule. Each matched observation is one paid judge call. The rule scores every main-thread turn; a Claude session has one root turn per resumed or background-woken turn (15 in C0 run 4) and only the last is the final report, so read run-level results from each session's last turn.

Run-level scores (parity composite, quality, adherence, consistency, oracle pass rate, forbidden git, coverage, refusals, judged report claims) are posted on each session by `telemetry/langfuse-scores.py` from `scripts/parity-eval.py`, with one score config each.
