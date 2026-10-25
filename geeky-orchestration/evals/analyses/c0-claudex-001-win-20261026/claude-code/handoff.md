# Claude provider-blocked handoff

Historical handoff: use [router-fixed/handoff.md](router-fixed/handoff.md) for
the current candidate SHA and verified retry state. The old seed-only/provider
blocker statements below no longer describe the current workspace.

Target: Gerald's Windows machine, PowerShell 7. Repo:
`C:\Users\gerald.khoo\geekhoo-plugins`. Verify HEAD
`c83d4b941341b4094b6e7d2f4ac125e5c1b74154`; preserve all dirty files.
Response budget 500 words.

Read report.md, run-outcome.json, geeky-resume-restart-outcome.json,
then active-claude-run.json at `C:\repos\.eval-tools\c0-claudex-001`.
Workspace is `C:\repos\c0-claudex-001\eval-c0-wordstat-20261025T183455Z`;
config is its sibling `.eval-cfg-20261025T183455Z`. Git remains at seed d06eb6d.

User requested Claude C0 like Codex, then specifically restarted it using
geeky-resume in the same folders. Model remains claudex-001, thinking default,
MXC Windows, qualification waived by owner. Initial run and one neutral resume
were blocked by MissingSessionID HTTP400. Both stable header names were supplied.
Fresh user-authorized restart native 38156247-f588-4dac-86a1-df2c93fec26b also
failed on its first model request, before tools/skills. No process is still running.

Do not report a completed Claude C0 or invent a parity score. Only handoff.md
exists; there is no kanban/planning package or product. Oracle 13 errors are
missing implementation/import errors. Codex's completed result remains 97.46.

Credentials remain in the private env file; do not print them. Original records
and operator logs are preserved. No shared gateway edits, alias switch or repo
commits/pushes were made. No further paid retry is scheduled.

Next scope requires the user's instruction: inspect the actual headers through
Claude -> LiteLLM router -> upstream, then resume/restart only after the request
path accepts the intended model. The settings alone do not prove forwarding.
