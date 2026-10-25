# MXC telemetry identity. 2026-10-25

This dated record covers model-free identity validation. Later paid C0 attempts are documented in the
[current comparison](../c0-claudex-001-win-20261026/README.md). The owner's
[publication instruction](../c0-claudex-001-win-20261026/alignment-report-2026-10-26.md)
supersedes the original no-commit checkpoint. No further paid run is authorized here.

Implemented platform-specific run sessions, actor user IDs and filter metadata
for both MXC runners. Windows C0 mocks pass; Langfuse CLI readback verifies
separate orchestrator, coder and reviewer identities for both tracers.
All validation is model-free. No paid evaluation or LLM judge ran.

Base revision: `c83d4b941341b4094b6e7d2f4ac125e5c1b74154`. Changes are uncommitted
and include the preceding Windows setup work. Historical runs were not renamed
or rescored. This record supersedes the old generic `mxc` / `geeky-eval-agent`
defaults for newly prepared runs.

## Naming contract

| Surface | Value |
|---|---|
| Windows environment | `mxc-win` |
| Linux environment | `mxc-linux` |
| macOS environment | `mxc-mac` |
| Family | `codex-mxc-<platform>` or `claude-mxc-<platform>` |
| Run session | `<family>-<case>-<run-stamp>` |
| Trace | `<family>-<role>-<agent-name>`, omitting a repeated role/name |
| User ID | `<trace-name>-<native-agent-id>`, with bounded ASCII normalization |

User IDs identify actual agents/subagents. Structured native types classify
known orchestrators, coders and reviewers; unresolved types remain `unknown`.
Names/nicknames and original types remain available without prompt-based guesses.

Every agent owns a trace, with its tools and generations nested within it. All
actors from the run share one session. Parent agent, trace and observation IDs
provide logical cross-trace dispatch links. A synthetic nested-user experiment
demonstrated that assigning a child user inside the parent's trace overwrites
the parent's identity on this deployment, so independent traces are necessary.
This means the complete team is grouped through its session and metadata rather
than one physically nested cross-agent trace tree.

Filter by environment, `agent-family`, `agent-role`, harness, case, run, plugin,
`identity:agent-v1` and `mock` tags. Metadata includes identity schema, platform,
family, configured model/reasoning/provider, worker/reviewer defaults, actor ID,
role, type, name, scope, parent links, native session/thread ID and Codex path.
Actual generation model/usage/reasoning remain in their original fields.

The readable session is in `run.json.telemetry.session_id`; native
`run.json.session_id` is retained. Readback and session-score publication use the
readable ID, with a native-ID fallback for historical records. Coverage and
parity evaluation still classify agent-owned child traces as subagent activity.

## Evidence

- [Windows C0 matrix](windows-c0-matrix.json): Claude 73 checks / 196 observations;
  Codex nine checks / 10 observations; both runners exit zero and telemetry is delivered.
- [Live identity verification](live-verification.json): three distinct agent
  traces/user IDs per harness, correct roles and parent links, one run session,
  and `mxc-win`. Read back with `langfuse-cli api observations list`.
- [Unannounced Codex recovery](codex-unannounced-verification.json): a separate
  fixture has no spawn announcements and only nested structured parent headers;
  all three actors are still exported with correct identities.
- [Validation record](validation.json) and [source hashes](source-manifest.json).

The final synthetic sessions are:

- `codex-mxc-win-c0-wordstat-20261025T145154Z-identity-final`
- `claude-mxc-win-c0-wordstat-20261025T145157Z-identity-final`
- `codex-mxc-win-c0-wordstat-20261025T145524Z-identity-unannounced`

These are synthetic telemetry fixtures with zero inference. C0 mock token/cost
fields are synthetic too; `mock` tags and metadata distinguish them from paid runs.
Raw API exports remain outside Git because SDK resource metadata includes
project credentials such as the public key. The committed verification files
contain only selected identity fields and trace links.

Pinned Claude source, Codex package and original Codex bundle remain unchanged;
the installer creates a separate derived converter and helper. SDK 4.18.0 is
retained because the pinned Claude hook uses its backdated-span internals.

Linux/macOS naming is unit-tested but not executed live here. Generic unknown
agent types are not reclassified from descriptions, model names or effort.
Explicit Codex trace seeds remain supported for independent roots; true external
parents are retained as metadata when independent actor ownership is required.
This change does not resolve the separate Windows LiteLLM native-tool fixture
qualification limitation documented in the Windows setup record.

## Use

The installed Windows launcher already loads the new platform environment:

```powershell
& C:\repos\.eval-tools\windows-eval.ps1 -Preflight
```

For a new host, install the pinned tools with
`evals/telemetry/install-telemetry-tools.ps1` before preparing a run.
See [the telemetry guide](../../telemetry/README.md), [kanban](kanban.md),
[handoff](handoff.md), and [references](references.md).
