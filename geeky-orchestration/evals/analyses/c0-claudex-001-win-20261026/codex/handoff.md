# Completed Codex C0 handoff

Target: Gerald's Windows host, PowerShell 7. Repo:
`C:\Users\gerald.khoo\geekhoo-plugins`. Response budget: 500 words.
Verify source HEAD `c83d4b941341b4094b6e7d2f4ac125e5c1b74154`; preserve all dirty files.

Read in order: report.md; parity.json; manual-verdicts.json;
validation-anchors.json; score.json rerun_results; telemetry-audit.json;
langfuse-scores-verified.json; references.md.

Verified completed run: `20261025T154802Z-c140d9e7`, LiteLLM `claudex-001`,
default/high main and worker thinking. Candidate workdir:
`C:\repos\c0-claudex-001\eval-c0-wordstat-codex-20261025T154802Z-c140d9e7`.
Verify its HEAD is `521f69a0b194328cecc247e942abca02374640d4`.
Run folder: `geeky-orchestration/evals/baselines/c0-wordstat/20261025T154802Z-c140d9e7`.

Final parity 97.46, Q95.64/A97.83/C100. Oracle 13/13 stable over 3 repetitions; independent public 93
passed; source-task validation9/10 (T1's first eligible code commit lacks its
test file). One final-report accuracy failure understates existing CRLF/BOM
tests; no false-completion cap. Runtime 47m26s, 12.866M tokens, 228 native response
IDs, 21 actor traces. Exact cost unknown. Owner waived qualification explicitly.

All ten Langfuse scores were published and read back under
`codex-mxc-win-c0-wordstat-20261025T154802Z-c140d9e7`, environment mxc-win.
The original coverage false flag and host replay failure remain in raw metadata;
separate corrected coverage and successful no-model replay are documented.
Earlier provisional 98.62 is superseded by task-snapshot audit. Raw stream/session
hashes are unchanged; no candidate files were fixed by the parent evaluator.

Full observations/API exports are outside Git at
`C:\repos\.eval-tools\c0-claudex-001\evaluation\20261025T154802Z-c140d9e7`.
Never print or commit credential values from SDK metadata or the private env file.

Codex is finished. Takeover scope is repository publication under the owner's
2026-10-26 instruction, coordinated by the parent agent. Do not resume or rerun
Codex. Read the [later Claude retry](../claude-code/router-fixed/report.md) and
[alignment record](../alignment-report-2026-10-26.md) for current state.
Use parity.json for comparison. A complexity-router alias does not prove a fixed backend.
