# Mock matrix 2026-10-25 (after the C0 audit)

Both harnesses on all four cases in Linux MXC (mxc-sandbox 0.2.1), no model calls, telemetry on. All 8 runs pass.

- Claude runs `-MockScenario all,happy`: the toolchain checks (pwsh, python and pytest, git identity, the plugin's .py and .ps1 gates, grants, MCP handshake, HOME outside the workspace) plus the workflow simulation, 74 checks (now including pytest for every `python3.X` on PATH).
- Codex runs its default scenario: env, skills and roles, guard hook, pwsh, python and pytest, gates (.py and pwsh), git, MCP, and the Langfuse Stop hook, 9 checks.

Outside the matrix, the real CLIs start inside the sandbox (`claude` 2.1.310, `codex` 0.164.0), the sandbox toolchain resolves (pwsh 7.5.4, pytest 9.1.1, git 2.43.0, node 22.22.0, bash 5.2), and three staggered 300 s sandboxes ran to completion (see the commit that adds this folder).
