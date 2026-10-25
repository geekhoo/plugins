# References and record reconciliation

- [Telemetry identity contract](../../telemetry/README.md#agent-and-run-identities).
- [Quickstart](../../QUICKSTART.md): now reads the readable telemetry session ID.
- [Runbook](../../mxc-litellm-runbook.md): platform environments and actor identity.
- [Decisions](../../../docs/agent-eval-decisions.md): D105 records this change.
- [Windows setup](../windows-mxc-setup-20261025/README.md): retained historical
  `mxc` preflight evidence is not relabelled; this record supersedes its naming defaults.
- [Langfuse skill](C:/Users/gerald.khoo/.codex/skills/langfuse/SKILL.md) and its
  instrumentation/CLI references guided documentation-first implementation and readback.
- [Tracing best practices](https://langfuse.com/docs/observability/best-practices).
- [Sessions](https://langfuse.com/docs/observability/features/sessions).
- [Users](https://langfuse.com/docs/observability/features/users).
- [Environments](https://langfuse.com/docs/observability/features/environments).
- [Metadata](https://langfuse.com/docs/observability/features/metadata).

Stale current guidance in the telemetry README and runbook was replaced: generic
`mxc` environment, `geeky-eval-agent` user, old trace names, and the assumption
that the Langfuse session is always the native UUID. Historical analyses remain
dated evidence. The plugin README links to the new contract. No old run scores,
judgments, transcripts or cloud sessions were rewritten.
