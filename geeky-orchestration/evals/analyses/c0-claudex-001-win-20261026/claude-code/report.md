# Claude C0. provider-blocked attempts and requested restart

Historical scope: this report covers attempts before the owner's router fix.
The later [router-fixed geeky-resume retry](router-fixed/report.md) reached
implementation/final review, passed oracle 13/13 and timed out; parity 90.33.
The statements below describe the earlier attempts only.

**C0 did not complete. No comparable code-quality/parity score is assigned.**
The provider returned HTTP400 `MissingSessionID`, stating that
`x-opencode-session` was missing and no fallback was attempted.

The user authorized the same model/case/default-thinking run as Codex, then
explicitly requested a fresh Claude restart in the same folder set using
`geeky-resume`. That restart was performed, but its first model request failed
before any tool or skill could execute.

## Preserved folder set

- Workspace: `C:\repos\c0-claudex-001\eval-c0-wordstat-20261025T183455Z`
- Configuration: `C:\repos\c0-claudex-001\.eval-cfg-20261025T183455Z`
- Model: `claudex-001`, LiteLLM Messages, Claude harness/provider default thinking.
- Native executable: Claude Code 2.1.304; Windows MXC ProcessContainer.
- Git HEAD remains seed `d06eb6d`; no implementation or later commit exists.
- The only workspace addition is the saved handoff. No new seed workspace was created.

## Attempt history

| Attempt | Native session | Result |
|---|---|---|
| Initial `20261025T183455Z` | `cb9fee8c-3bf6-463c-a093-82b8de2d7843` | Research activity; provider400 before specification. Exit 1; 2328s. |
| Same-session recovery | same native session | Both stable headers supplied at startup; same400. No new implementation. |
| Explicit user `geeky-resume` restart | `38156247-f588-4dac-86a1-df2c93fec26b` | Same workspace/config, fresh Claude process and session. First API request failed; zero tool calls, zero reported model tokens. |

The initial `geeky-orchestrator` dispatch recorded denied global-cache plugin
paths in handoff.md. Main Claude subsequently invoked `spec-research` through
the registered Skill tool and dispatched research perspectives. No completed
specification, kanban, implementation plan or product was produced before the
terminal provider fault.

A run-scoped settings hot reload was attempted, then one bounded recovery used
startup headers in the same native session. Both interventions were recorded.
The user's subsequent restart explicitly added `geeky-resume` reconciliation
instructions and readable run-local `CLAUDE_PLUGIN_ROOT` / `PLUGIN_ROOT` paths.
The restart did not reach those instructions because the provider rejected its
first request. Existing handoff/brief/contract were preserved.

The installed resume skill requires a planning folder with kanban.md. None had
been created, so the restart prompt instructed state reconciliation followed by
stage-aware routing to the earliest unfinished stage, without fabricating a plan
or assuming prior completion. This prerequisite was not the terminal blocker;
the API failure occurred before skill execution.

## Header evidence and limit

Configured headers were:

- `x-litellm-session-id: <native session UUID>`
- `x-opencode-session: <native session UUID>`

They were present in the run settings and explicitly passed into the MXC startup
environment. The upstream still reported MissingSessionID. This establishes a
request-path problem requiring inspection between the Claude client, LiteLLM
complexity router and selected upstream. It does not establish which hop drops
or ignores the configured values. No shared gateway configuration was changed,
and no alternative model was substituted.

## Evaluation and telemetry

No `wordstat` package exists. The oracle therefore records zero passes and 13
import/setup errors, stable across three repetitions; these are not 13 failed
implemented behaviors. `score-run.py` correctly declines with
`no planning folder (docs/*/kanban.md)`. Numerical parity and Quality are N/A.
Do not compare this incomplete infrastructure-blocked attempt as a zero against
Codex's completed 97.46 result.

CLI readback of the initial/recovery session verified 11 traces, 224 observations,
103 generation observations and four user IDs in `mxc-win`. Initial native
reported tokens total 2, 633, 720; that is a harness-reported scope, not an exact
billing figure. The fresh requested restart has one trace,two observations and
zero tool calls. See [run-outcome.json](run-outcome.json),
[telemetry-audit.json](telemetry-audit.json), and
[geeky-resume-restart-outcome.json](geeky-resume-restart-outcome.json).

Five execution-health scores were published on the initial/recovery session:
execution_status=blocked-provider, run_completed=false, provider_api_error=true,
harness_coverage_complete=false, operator_interventions=2. No numeric parity or
code-quality score was published for Claude.

Original records remain under baseline directories `20261025T183455Z`,
`20261025T183455Z-recovered`, and
`20261025T183455Z-geeky-resume-recovered`. API exports and settings snapshots
remain outside Git under `C:\repos\.eval-tools\c0-claudex-001\evaluation`.
No candidate product files, shared repository commits or pushes were made.

Next step: inspect session-header propagation/route configuration before another
paid attempt. A workspace-resume procedure cannot execute until the gateway
accepts the model request.
