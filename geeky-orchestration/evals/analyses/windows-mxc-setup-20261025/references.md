# References and superseded records

- [Quickstart](../../QUICKSTART.md): Linux-first setup and cross-harness scoring;
  this Windows setup record supplements it, without changing historical results.
- [Runbook](../../mxc-litellm-runbook.md): preflight, credentials, telemetry and
  pitfalls. Its Linux native behavior does not establish Windows qualification.
- [Telemetry](../../telemetry/README.md) and [pins](../../telemetry/pins.json).
- [Windows baseline procedure](../../baseline-runs.md).
- [Codex adapter](../../adapters/codex/README.md),
  [native probe](../../adapters/codex/run-native-probe.ps1),
  [paid audit](../../adapters/codex/paid-diagnostic-audit.py).
- [Current build pin](../../adapters/codex/profile/mxc-pin.json): replaces the
  historical Program.cs/build hashes after current-source standard qualification.
- [Canonical policy](../../../docs/agent-eval-decisions.md): D101–D104 distinguish
  telemetry cohorts, comparable parity scoring and LiteLLM authentication.

Historical adapter handoffs and native proofs remain dated evidence; they were
not rewritten to describe this machine setup. The earlier root README versions
were corrected by fetched upstream work. This record adds a current Windows
entry point to the plugin README and adapter README. It does not change C1
scores, the rejected parity package, or historical run eligibility.
