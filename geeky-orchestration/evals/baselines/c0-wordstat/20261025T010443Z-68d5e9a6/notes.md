# Codex C0 attempt 2 (ant-claude via LiteLLM, Linux MXC, RUST_LOG=info)

Exit 255 after 179 s, the same way as attempt 1: every thread stopped at once with no task_complete, no
pending command, and no log line at the end, so the process was killed rather than exiting. The run did
show model-side noise: an unsupported `exec` call, an integer sent as "1000", one task name with hyphens,
and a benign fallback-metadata warning at child start-up. Next: trusted-exec ignores SIGHUP and records the
exact return code/signal in launch-evidence/codex-exit.json. Not reference-eligible; kept as evidence.
