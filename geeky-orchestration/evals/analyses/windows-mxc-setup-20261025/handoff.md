# Windows MXC setup handoff

This dated record covers host setup. Later paid C0 attempts are documented in the
[current comparison](../c0-claudex-001-win-20261026/README.md). The owner's
[publication instruction](../c0-claudex-001-win-20261026/alignment-report-2026-10-26.md)
supersedes the original no-commit checkpoint. No further paid run is authorized here.

Target: Gerald's Windows machine, PowerShell 7. Workdir:
`C:\Users\gerald.khoo\geekhoo-plugins`. Response budget: 500 words.

Verify `git rev-parse HEAD` equals
`c83d4b941341b4094b6e7d2f4ac125e5c1b74154` and inspect `git status --short` before
acting. Setup changes are intentionally uncommitted; preserve them.

Read in order:

1. This folder's README.md and setup-validation.json.
2. This folder's references.md and kanban.md.
3. ../../QUICKSTART.md and ../../mxc-litellm-runbook.md.
4. ../../adapters/codex/profile/mxc-pin.json and the two native summary folders here.
5. ../../adapters/codex/run-native-probe.ps1 and paid-diagnostic-audit.py if native
   qualification is the assigned takeover scope.

Verified state: host setup is complete; Claude C0 73 checks/196 observations,
Codex C0 nine checks/10 observations, standard native Codex 21 checks pass. The
LiteLLM classic-tool native attempt fails and remains explicitly unqualified.
No paid inference, commit or push occurred. Credentials stay in
`C:\Users\gerald.khoo\env.cloud.claude`; never print or commit their values.

Local entry point: `C:\repos\.eval-tools\windows-eval.ps1 -Preflight`.
Current retained build: `C:\repos\.eval-tools\windows-mxc\bin`.
Full disposable native runs are retained in
`C:\repos\.eval-tools\windows-setup\qualification`.

Takeover scope requires a new user task. For Windows LiteLLM native qualification,
preserve the 21-check contract, denied-root isolation and exact build/source
verification. A passing standard Code Mode fixture is insufficient for classic
JSON tools. Done criteria for that follow-up: reviewed compatible fixture,
model-matched native evidence and successful existing paid prelaunch audit,
without model inference or weakened gates. Paid runs need separate authorization.
