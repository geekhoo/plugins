# Windows setup status

This dated record covers host setup. Later paid C0 attempts are documented in the
[current comparison](../c0-claudex-001-win-20261026/README.md). The owner's
[publication instruction](../c0-claudex-001-win-20261026/alignment-report-2026-10-26.md)
supersedes the original no-commit checkpoint. No further paid run is authorized here.

## Done

- Inspect installed Windows runtimes and evaluation dependencies.
- Fast-forward the clean checkout from c58f7d0 to c83d4b9.
- Install and verify pinned telemetry hooks and Python SDK.
- Build and probe current MXC ProcessContainer host.
- Install a local environment/preflight launcher without copying credentials.
- Verify LiteLLM authentication with a read-only model-list request.
- Pass Claude C0 free preflight with telemetry.
- Correct Windows Codex mock PATH, shell and Node startup failures.
- Pass Codex C0 free preflight with telemetry and focused regressions.
- Qualify current MXC build with the standard native Codex 21-check fixture.
- Preserve successful and failed setup evidence and document the proof boundary.

## Follow-up. not part of completed host setup

- Adapt and review the native fixture for LiteLLM's classic JSON tools before
  Windows LiteLLM paid qualification. Preserve patch/guard/MCP requirements.
- Requalify the exact selected model/reviewer matrix before a paid launch.
- Run case-specific C1–C3 preflight when those cases are selected.
- Obtain explicit paid-run authorization; no paid run is authorized by setup.
- Commit or publish only if requested.
