# Sources

- [Restart outcome](geeky-resume-restart-outcome.json): requested fresh session,
  same workspace/config, first-request provider rejection, zero tool calls.
- [Attempt outcome](run-outcome.json), [telemetry](telemetry-audit.json),
  [execution-health score readback](health-scores-verified.json).
- [Original run](../../../baselines/c0-wordstat/20261025T183455Z/run.json).
- [Same-session recovery](../../../baselines/c0-wordstat/20261025T183455Z-recovered/run.json).
- [Requested restart](../../../baselines/c0-wordstat/20261025T183455Z-geeky-resume-recovered/run.json).
- [Resume skill](../../../../skills/geeky-resume/SKILL.md): ledger reconciliation
  for an existing planning package; no execution was possible at the rejected API request.
- [Claude environment settings](https://code.claude.com/docs/en/env-vars).
- [LiteLLM OpenCode session requirements](https://docs.litellm.ai/docs/providers/opencode_go).

Configured headers and upstream-reported MissingSessionID are separate facts.
The actual dropped/ignored header hop has not been established. No qualification
hold was introduced, no alternative alias selected, and no shared gateway edited.
