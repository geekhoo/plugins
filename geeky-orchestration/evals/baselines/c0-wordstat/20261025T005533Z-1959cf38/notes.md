# Codex C0 attempt 1 (ant-claude via LiteLLM, Linux MXC)

Exit 255 after 134 s, mid-turn: the main thread and its three spec-research subagents stopped at the
same moment with no task_complete, no panic or error in stderr and no OOM. Two spawns failed earlier
with "unknown agent_type 'general-purpose'" (a Claude Code built-in the skills name), fixed in 0fac95b by
registering that role. Relaunched with -CodexRustLog info as 20261025T010443Z-68d5e9a6 to capture the cause.
Not reference-eligible; kept as evidence.
