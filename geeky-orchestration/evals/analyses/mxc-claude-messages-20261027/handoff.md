# Takeover brief

Target Gerald's Windows host, PowerShell 7, workdir
`C:\Users\gerald.khoo\geekhoo-plugins`. Report within 350 words.
Read `geeky-orchestration/AGENTS.md`, this folder's README/references.md, then
`outputs/mxc-claude-messages-20261027/verification.json` and corrected-route/results.json.
Verify HEAD `4228c3f73fc3894c86725cf42900406c1d2d981f` and inspect status.
Preserve dirty work, runtime evidence and all previous captures/scores.

Current state: native Claude 2.1.311 inside verified MXC SDK1.0.1 ProcessContainer
completed MCP echo/tool_result/final-marker roundtrips for Luna, GLM, Haiku and
MiMo. MiniMax and DeepSeek returned provider-resource/routing 404s before tool use.
Correct-route forwarded attempts total ten; initial six misrouted attempts and
their correction remain separate. Four further client attempts after provider
errors were blocked locally. Both C0 evaluations remain stopped.

Takeover scope: read-only investigation of retained Messages errors and deployed
provider routing if access is supplied. Do not rerun run_checks.py/corrected_route.py.
Their authorization markers intentionally prevent duplicate live probes. Real
provider credentials remain in the owner's external env file; never display/copy.

No new endpoint/MXC workload, provider request, actual tool execution, evaluation,
judge, telemetry operation, sign-in, commit or push is authorized by this brief.
Done: evidence-bound cause or exact missing prerequisite, with both evaluations held.
