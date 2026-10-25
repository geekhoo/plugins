# Baseline c0-wordstat 20261025T020134Z

Approach: canonical prompt, Claude Code isolated in MXC.
Interventions: none.
Oracle verdicts: (fill in for any failure)


## Outcome (operator note)

First C0 run on mxc-sandbox 0.2.1 (spawn-thread fix): no sandbox kill, exit 0 at 695 s. The model
completed spec-research (`5a652fc`), then the provider behind LiteLLM `ant-claude` rejected the next
request (geeky-plan skill load) with `stop_reason: content_filter`, "The request was rejected because
it was considered high risk", ending the session. Not a harness failure. Langfuse: 129 observations,
env `mxc`, trace name `geeky-eval c0-wordstat claude-code`.
