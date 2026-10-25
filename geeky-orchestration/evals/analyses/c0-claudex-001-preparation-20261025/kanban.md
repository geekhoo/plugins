# C0 preparation status

## Done

- Confirm `claudex-001` is listed and authenticated on LiteLLM.
- Read its router metadata without inference or server changes.
- Recheck Windows CLI/dependency versions and MXC build/source pins.
- Authenticate both Langfuse credential sets through read-only CLI requests.
- Prepare Claude provider, aliases, MCP and platform/actor telemetry config.
- Prepare Codex Responses provider, catalog and seven role layers.
- Verify both model/worker mappings and hidden eval/oracle exports.
- Retain seed-only workspaces and preparation artifacts outside real run output.
- Create process-local environment loader and a non-launching status entry point.
- Review the no-oracle/no-MXC Claude preparation branch and its export digest.

## Superseded hold. waived by owner

- The original Codex qualification hold was waived explicitly by the owner.
  The reason is recorded by the opt-in runner override. The subsequent single
  authorized Codex run completed and was scored. Claude later reached final
  review and timed out in the router-fixed retry. See the [current comparison](../c0-claudex-001-win-20261026/README.md).

## Deferred during preparation

- Contestant execution, mock evaluation, seed oracle, native qualification,
  provider inference smoke calls, LLM judges and scoring.
- Repository commits and pushes.
