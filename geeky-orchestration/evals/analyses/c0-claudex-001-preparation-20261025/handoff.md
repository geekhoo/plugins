# C0 claudex-001 preparation handoff

Historical preparation handoff. Read the [current comparison](../c0-claudex-001-win-20261026/README.md)
and [publication alignment](../c0-claudex-001-win-20261026/alignment-report-2026-10-26.md)
first. Codex completed at parity 97.46. Claude's later router-fixed retry timed
out at parity 90.33. The owner waived qualification for those attempts.
Preparation-only instructions below describe the earlier checkpoint.
No further paid continuation is authorized by this record.

Target: Gerald's Windows machine, PowerShell 7. Workdir:
`C:\Users\gerald.khoo\geekhoo-plugins`. Response budget: 500 words.

Verify Git HEAD through `git rev-parse HEAD`:
`c83d4b941341b4094b6e7d2f4ac125e5c1b74154`. Inspect dirty state and preserve all
Windows setup, telemetry and preparation changes; none was committed.

Read in order:

1. This README.md, readiness.json and kanban.md.
2. `C:\repos\.eval-tools\c0-claudex-001\readiness.json` for current named-file hashes.
3. This references.md and ../windows-mxc-setup-20261025/README.md.
4. ../../scripts/run-baseline.ps1 (`-PrepareOnly`) and run-codex-baseline.ps1.
5. ../../adapters/codex/native-probe.py, prepare-profile.py and
   paid-diagnostic-audit.py for the exact unresolved Windows qualification.

Verified: `claudex-001` is listed, both static configurations pin it, both
Langfuse connections authenticate, MXC build/source hashes match, and no
contestant stream/start time exists. Both prepared workspaces contain only their
seed commit. The route is an `auto_router/complexity_router` alias. No inference,
oracle, mock, native fixture, paid evaluation or judge ran in this preparation.

Environment loader: `C:\repos\.eval-tools\c0-claudex-001\environment.ps1`.
Status-only command: `C:\repos\.eval-tools\c0-claudex-001\Invoke-C0.ps1`.
Credentials stay in `C:\Users\gerald.khoo\env.cloud.claude`; never print/copy values.

Takeover scope requires a new user instruction. Current instruction is prepare
only, do not run C0. Codex launch is blocked until its classic-tool fixture and
exact model-matched native proof are accepted. Standard Code Mode proof cannot
be reused. Preserve denied-root isolation, exact build pins and all required
checks. Done criteria for later paired readiness: clear that gate with evidence,
refresh the manifests, and retain explicit authorization before contestant use.
