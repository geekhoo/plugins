# Investigation: framework-agnostic hooks, scripts & quality gates

*Status: investigation complete — P1–P7 implemented (June 2026).*

> This document is the original investigation and rationale. Section 5 below describes
> the *proposed* gates; a few proposals were deliberately narrowed when built (e.g.
> `check-dod` asserts notes/lane/handoff signals and **prints** the task's validation
> block for the caller to re-run rather than executing commands or diffing files;
> `validate-kanban` checks placement/dangling/WIP/lane-coverage rather than Done→commit).
> For authoritative **as-built** behavior and invocation, see `AGENTS.md` and
> `geeky.manifest.json`.

Goal: use hooks, scripts, and tools to make the geeky-orchestration workflow more
**consistent and higher quality**, while keeping every mechanism usable from agent
frameworks **other than Claude Code** (the same reason `/geeky-*` commands were
converted into portable Skills).

---

## 1. The one architectural principle

Across the agent ecosystem there is an empirically converged convention:

> **The trigger is framework-specific. The logic is a language-agnostic CLI that
> reads JSON on stdin (or argv) and signals via POSIX exit code.**

Claude Code, Cursor, Windsurf, OpenAI Codex CLI, GitHub Copilot CLI, and Gemini CLI
all shell out to an external command and pass event JSON on stdin; most honor
`exit 2 = block` (Cursor uses an equivalent stdout `permission:"deny"`). This plugin
already follows that principle — `hooks.json` is the Claude-specific trigger; the
guard and validator are portable scripts. The work is to (a) close the gaps that make
them *Claude-only in practice*, and (b) add more deterministic gates.

### Two invocation clusters (a gate is only portable if it has a story for both)

| Cluster | Frameworks | How a gate runs |
|---|---|---|
| **CLI-agent** | Claude Code, Cursor, Windsurf, Codex CLI, Copilot CLI, Gemini CLI | Native subprocess hook: JSON on stdin, exit codes. Our scripts drop in directly. |
| **In-process SDK** | OpenAI Agents SDK, LangGraph/LangChain | No subprocess hook. Wrap the script: `subprocess.run([...])` inside a guardrail / graph node; raise a tripwire / `interrupt()` on nonzero exit. |
| **MCP (orthogonal)** | Any MCP-capable agent | Expose the validator as an MCP tool. The only *universal active* invocation path. |

### Critical consequence for our Skills-first design

Hooks **only auto-fire in frameworks that have a hook system.** A non-Claude agent that
merely *reads the Skill* will not auto-run anything. Therefore the gates must be reachable
two ways that don't depend on a hook firing:

1. **Explicit steps in the Skill body** — e.g. `geeky-implement` says "run
   `scripts/validate-kanban.py`; if it exits non-zero, fix and re-run until green."
   Deterministic checks invoked by instruction work in *every* framework.
2. **MCP tools** — for agents that prefer tool discovery over shelling out.

The Claude `hooks.json` then becomes an *automation convenience* on top, not the only
line of defense.

---

## 2. Standards & conventions (real vs proposal)

| Item | Status | Use here |
|---|---|---|
| **POSIX exit codes** (`0` ok / nonzero fail) | Real standard | Base contract for all scripts. |
| **`exit 2 = block`** | Convention (Claude-originated, copied by Codex/Windsurf) | Block mode for the guard. NOT POSIX — document it. |
| **JSON-over-stdio decisions** (`permissionDecision`, `additionalContext`) | Shared CLI-cluster convention | Portable warn/block channel. |
| **pre-commit / linter contract** (argv in, `0`/`1`, summary on stdout) | Real, ubiquitous | Already used by `validate-planning-folder`. Keep for all validators. |
| **MCP** | Closest thing to a cross-vendor standard (Anthropic + OpenAI + Google) | Optional universal tool wrapper. |
| **AGENTS.md** | Strong adopted convention (Linux Foundation / AAIF; read by Codex, Cursor, Copilot, Gemini, Aider, Windsurf) | Discovery doc so non-Claude agents learn the contract + validators. |
| **JSON Schema for structured outputs** | Real, shipping in OpenAI + Anthropic | Contract for task-file validation. |
| A formal cross-framework "agent hooks" spec | **Does not exist** | We rely on de-facto convergence, not a spec. |

---

## 3. Quality-gate best practices (evidence-based)

1. **Deterministic validators beat LLM self-report.** LLM pipelines "fail open" — confident,
   well-structured, subtly wrong output that propagates. Deterministic checks "fail stop" with
   localized errors. Check the artifacts on disk instead of asking the model "did you finish?".
2. **Gate the boundaries:** prepare → validate → approve → commit. On failure, block the handoff,
   quarantine, remediate before any irreversible step (commit/push).
3. **Schema/contract validation between stages** keeps every step machine-parseable.
4. **Feedback loop:** run validator → fix → repeat (cf. Aider `--test-cmd`).
5. **Fail-stop at irreversible boundaries; warn only for advisory.**
6. **Gates must be fast (<5s) and idempotent** — they run on every matching event. (`hooks.json`
   already sets `timeout: 5`.)
7. **Verify, don't trust** — re-run tests/checks rather than believing the transcript. (Already a
   rule in `geeky-implement`: "Do NOT trust the coder's claim that validation passed — re-run it.")

---

## 4. Gaps in what exists today

- **Guard is warn-only via stderr + exit 0.** Weakly surfaced even in Claude Code (exit-0 stderr
  is not reliably shown to the model); invisible in other frameworks. → needs a portable channel.
- **Only two gates exist** (frozen-artifact guard, planning-folder existence validator). The
  highest-value consistency checks — *is the kanban internally consistent? do task files have the
  required shape? is a task actually Done?* — are left to LLM self-report today.
- **No discovery layer** for non-Claude agents: nothing tells Codex/Cursor/etc. that these
  validators exist or how to call them.

---

## 5. Prioritized recommendations

Each carries its dual invocation story. Scripts ship as `.py` + `.ps1` mirrors (existing convention).

### P1 — Kanban-integrity linter `scripts/validate-kanban.(py|ps1)`
Deterministic checks: every `tasks/Tx-*.md` appears in exactly one lane; lane headings are the known
set; Done tasks reference a commit; In-Progress count ≤ WIP cap; lane counts sum to task count.
Contract: argv in, `0`/`1`, summary on stdout (+ `--json`).
*Invocation:* Skill step in `geeky-implement` after each lane move; Claude `Stop`/`SubagentStop` hook;
pre-commit; SDK node / output-guardrail; MCP `validate_kanban`.
**Why first:** replaces the most error-prone self-reported step (board upkeep) with a fail-stop check.

### P2 — Task-file schema validator `scripts/validate-task-schema.(py|ps1)`
Validate each `Tx-*.md` against the task template contract (required sections: Task Name, Scope/In
scope, Dependencies, Acceptance Criteria, Tests/Validation, Priority). The plan→implement boundary gate.
*Invocation:* end of `geeky-plan`; start of `geeky-implement`; pre-commit; SDK guardrail; MCP tool.

### P3 — Definition-of-Done checker `scripts/check-dod.(py|ps1)`
Per task, assert deterministically: the declared in-scope files actually changed; the task's validation
command exits 0; acceptance checkboxes are ticked; a `Tx-*.notes.md` exists; handoff updated.
Embodies "verify, don't trust."
*Invocation:* before moving a task to Done; Claude `Stop` hook; SDK node; MCP tool.

### P4 — Upgrade the guard to a portable warn/block gate
Add `--mode warn|block`. `warn` emits via **stdout JSON `additionalContext`** (surfaces in Claude *and*
Codex) instead of stderr; `block` returns `permissionDecision:"deny"` / **exit 2**. Keep default `warn`.
*Invocation:* existing `hooks.json`; add documented Cursor/Windsurf/Codex hook snippets reusing the same script.

### P5 — Commit-message / format gate `scripts/check-commit.(py|ps1)`
Enforce conventional-commit + task-ID reference (matches `geeky-implement`'s commit format).
**Most natively portable** — git `commit-msg`/pre-commit hooks are universal; also a Claude `PreToolUse`
matcher on `Bash(git commit *)`.

### P6 — Discovery layer: `AGENTS.md` + `geeky.manifest.json`
Root `AGENTS.md` (read natively by most non-Claude agents) documents the planning-folder contract, the
frozen-artifact rule, and the validator commands. `geeky.manifest.json` lists each validator + how to
invoke it, so SDK wrappers and MCP servers can discover them programmatically.

### P7 — ✅ BUILT: validators wrapped as an MCP server
`mcp/server.py` is a stdio FastMCP server (`geeky_mcp`) registered via `.mcp.json`. It exposes six
read-only tools — `geeky_validate_planning_folder`, `geeky_validate_task_schema`,
`geeky_validate_kanban`, `geeky_check_dod`, `geeky_check_commit`, `geeky_check_frozen_artifact` —
callable from Claude, Cursor, OpenAI Agents SDK, LangGraph, etc., with no per-framework hook config.
It is a **thin adapter**: each tool shells out to the same validator script with `--json` and returns
the parsed report, so there is zero logic duplication and MCP output matches the CLI/hook output.
Run with `uv run --with mcp python mcp/server.py` (or `pip install mcp && python mcp/server.py`).

---

## 6. Suggested sequencing

1. **P1 + P4** — biggest consistency win (kanban linter) + fixes the one real defect (guard channel).
2. **P2 + P6** — schema gate + discovery doc; together they make the plan→implement handoff verifiable
   from any framework.
3. **P3 + P5** — DoD and commit gates close the "is it really done / committed cleanly" loop.
4. **P7** — MCP wrapper once the script contracts are stable.

Throughout: every new validator must (a) keep the argv-in / `0`-`1`-out linter contract, (b) ship `.py`
and `.ps1` mirrors with identical output and exit codes, (c) be referenced as an explicit step in the
relevant Skill body — not just wired into `hooks.json` — so non-Claude agents actually run it.

---

## Sources
- Claude Code hooks: https://code.claude.com/docs/en/hooks
- Cursor hooks: https://cursor.com/docs/hooks
- OpenAI Codex hooks: https://developers.openai.com/codex/hooks
- GitHub Copilot CLI: https://htekdev.github.io/copilot-cli-reference/
- OpenAI Agents SDK guardrails: https://openai.github.io/openai-agents-python/guardrails/
- LangGraph human-in-the-loop: https://docs.langchain.com/oss/python/langchain/human-in-the-loop
- AGENTS.md: https://agents.md/ · AAIF: https://aaif.io
- MCP spec: https://modelcontextprotocol.io/specification/2025-11-25
- Exit-code standards: https://en.wikipedia.org/wiki/Exit_status
- Reliability patterns: https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/ · https://dstreefkerk.github.io/2026-02-agentic-architecture-playbook-patterns-for-reliable-llm-workflows/
