# geeky-orchestration

[Native Codex C0 gate fix](evals/analyses/c0-commit-gate-fix-20261029/README.md)
allows pre-planning docs commits to use `Tasks: none`. Both gates pass the
regression suite and offline readiness passes. Fresh preparation and one
owner-authorized native attempt are pending; historical results are preserved.

[Codex C0 native-wire preparation](evals/analyses/c0-codex-native-preparation-20261029/README.md)
adds explicit `-LitellmWireMode native` for the Luna candidate, retaining bridge
mode by default. Seven focused offline checks pass; live completion is held.

[Claude Luna/high overtime completion](evals/analyses/c0-luna-overtime-20261028/README.md)
records final acceptance, 18 public tests, 13/13 oracle checks over three runs,
and verified cumulative parity98.44 after authorized overtime. Both evaluations are stopped.

[Luna/high sequential C0 results](evals/analyses/c0-luna-sequential-20261028/README.md)
record the Codex bridge failure and Claude timeout with 13/13 oracle results.
Langfuse readback succeeded for both; no further run or recovery is active.

[Luna/high C0 preparation](evals/analyses/c0-luna-preparation-20261028/README.md)
uses committed workflow/runner fixes and an explicit Luna-only qualification waiver.
Claude supports `-Effort high`; both MXC harnesses stay held for separate launch authority.

[Claude inside MXC, Messages API checks](evals/analyses/mxc-claude-messages-20261027/README.md)
verified four real MCP/tool-result roundtrips and recorded two provider-resource
404s. This is minimal harness proof; both C0 evaluations remain stopped.

[The reasoning bridge normalization](evals/analyses/bridge-reasoning-normalization-20261027/README.md)
passed the saved failing streams and small actual HTTP-bridge calls for MiniMax,
DeepSeek and MiMo. Both evaluations remain stopped.

[The bounded endpoint retest](evals/analyses/litellm-bounded-retest-20261027/README.md)
resolved the Luna opaque uncertainty and finished the token-limited generations.
Completed payloads still expose wire-shape and thinking-option gaps; no C0 run started.

[Small six-model LiteLLM diagnostics](evals/analyses/litellm-six-models-20261027/README.md)
verified basic routing and selected native/bridge cases. Low-cap incompletes are
inconclusive; the three bridge passes do not establish C0 readiness. Both
evaluations remain stopped.

Use the [Responses API / Codex V2 diagnostics](evals/tools/responses_contract/README.md)
to prepare synthetic tests, validate saved data and later probe an explicit
endpoint. Native V2 and mapper compatibility are reported separately.
Both evaluations remain stopped; no endpoint was tested for this tooling work.

The [fresh sequential C0 pair](evals/analyses/c0-fresh-sequential-20261027/README.md)
is terminal: Codex research stopped early and Claude exhausted its budget during
plan review. No implementation was produced. Langfuse readback succeeded for both.

The [offline root-cause follow-up](evals/analyses/c0-root-causes-20261027/README.md)
adds shared budget checks through planning and a dedicated bridge rejection for
the observed tool-call text. No new evaluation was started; live effectiveness
remains unverified. Changed policies must be committed when authorized before
the runners can export them from HEAD.

Current [C0 operator readiness](evals/c0-readiness.md) records installed tools, local mock proof and paste-verbatim verification prompts. Live telemetry and paid canaries remain held. See [lessons learned](evals/lessons-learned.md) before preparing another run.

The [Codex V2 LiteLLM mapping fix](evals/analyses/codex-v2-litellm-mapping-20261027/README.md)
has offline regression coverage and one successful synthetic provider request.
It keeps native V2 roles and translates the provider wire format. Both evaluations
remain stopped pending a new explicit launch instruction.

The [C0 remediation implementation](evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/handoff.md)
is accepted offline: review/closeout instructions and compact output, one-deadline
runner records, and scoped accounting with verified score readback. Historical C0
results remain preserved; this work includes no new paid evaluation or live publication.

[Real-MXC post-remediation mock observations](evals/analyses/c0-post-remediation-mock-20261026/report.md)
record both full scripted C0 fixtures, bounded fault cases, and the original terminal
step-status inconsistency. The [minimal follow-up implementation](evals/analyses/c0-post-remediation-mock-20261026/follow-up-implementation.md)
fixes that transition and maintains guarded H1 fixtures with fresh verification.
Model-free fixture success is separate from live-agent proof.

Latest Windows C0: Codex completed `claudex-001` at runner-default thinking with
**97.46 parity**, oracle 13/13 stable over 3 repetitions and 93 public tests passing. Ten session
scores are published and verified. [Run report](evals/analyses/c0-claudex-001-win-20261026/codex/report.md).
Claude's same-folder geeky-resume continuation is now complete: **98.33 cumulative
parity**, final review PASS WITH WARNINGS, oracle 13/13 across three fresh runs,
and 60 public tests passing with 2 platform skips. All ten scores are verified.
The earlier timeout remains recorded at 90.33. The continuation used additional
time and context, so its score is not a clean initial-attempt comparison.
See the [Claude closeout report](evals/analyses/c0-claudex-001-win-20261026/claude-code/closeout-20261026/report.md)
and [comparison](evals/analyses/c0-claudex-001-win-20261026/README.md).

C1 run 3 completed: **99.6 reviewed QACT**, oracle 118/118 stable over 3 repetitions, final 110 tests, exact requested Sol/high–medium–xhigh matrix. [Report](evals/baselines/c1-csvledger/20261023T230041Z-2c3b5489/report.md) and [operator evidence](evals/adapters/codex/evidence/20261023T230039Z-run3-operator/README.md). The automatic extractor did not support this delegation shape; source-bound reviewed scoring is explicit. One paid attempt completed; no further launch authorized.

Historical C1 final-pair result: [automatic Codex 2 normalization](evals/analyses/c1-final-parity-20261024/README.md) reproduces 98.040005 without operator process mappings; Claude 6 remains 98.271809. Strict incomplete scoring fails nonzero. Guard fixtures pass; paid-session hook invocation remains unverified.

C1 evaluation records are current through [checkpoint 5](evals/codex-c1-checkpoint5.md): corrected Codex scores 96.3/98.0, complete four-run measurement and a frozen six-Claude reproduction. Runtime guard parity and Codex calibration remain explicit follow-ups; no further execution is authorized by these records.

End-to-end feature delivery: **plan it, execute it, track it**, with strong contracts between phases and conservative parallelism.

Use the shared [workflow terminology](AGENTS.md#workflow-terminology).

To set up and run an eval yourself (Linux MXC, Claude Code or Codex, LiteLLM, Langfuse), start with
[the eval quickstart](evals/QUICKSTART.md).

For the verified Windows ProcessContainer setup, free preflight launcher and
current native qualification limits, see the
[Windows MXC setup record](evals/analyses/windows-mxc-setup-20261025/README.md).
MXC telemetry now uses platform-specific environments and agent-specific user
identities; see the [naming contract](evals/telemetry/README.md#agent-and-run-identities).
The [C0 claudex-001 preparation](evals/analyses/c0-claudex-001-preparation-20261025/README.md)
records both provider configurations and the original Windows Codex launch gate.
The owner later waived qualification for the runs linked above.

For the Codex C1 evaluation adapter and its current checkpoint limits, see
[the adapter README](evals/adapters/codex/README.md). It is separate from the
Claude runner. Model-free MXC checks are implemented; the strict clean-diagnostics
gate uses the owner's exact denied user-skill-root recurrence policy and independent
isolation proof; separately source-correlated rejected-patch records remain candidate
tool failures. Unmatched diagnostics fail closed (see the adapter policy). Codex trace analysis and
QACT scorer routing are implemented, and three paid C1 contestant runs are complete. Each further paid
run needs the owner's go-ahead. Automatic Codex process extraction covers run 2's shape only: run 1
uses hand-built process evidence, and run 3 uses reviewed corrections. An independent cross-check of all
three runs is in [the Claude review](evals/analyses/c1-claude-review-20261024.md).

## What's in the box

| Component | Type | Purpose |
|---|---|---|
| `spec-research` | skill | Researches a new spec with a parallel 3-subagent team (codebase, web best practices, architecture), then writes `feature-specification.md` and `README.md` in `docs/`. Runs *before* `geeky-plan`. |
| `geeky-plan` | skill | Produces a complete planning package: implementation plan, ordered task files, PM review, kanban, references, handoff. |
| `plan-review` | skill | 4-phase quality review of a `geeky-plan` package. document alignment, issue resolution, sequencing validation, final sanity pass. Run between planning and implementation. |
| `geeky-implement` | skill | Orchestrates execution: walks the kanban, delegates `geeky-coder` subagents (up to 3 in parallel), runs per-task validation, code review, and per-phase PM review, commits in small logical groups, never pushes. |
| `impl-review` | skill | Reviews *delivered code* (not planning docs) with 3 dynamically-chosen domain-expert subagents, each covering a distinct aspect of what was built. |
| `geeky-status` | skill | Read-only snapshot of a planning folder. Lane counts, blocked items, last handoff entry, suggested next step. No agents, no edits. |
| `geeky-resume` | skill | Post-cutoff reconciliation: verifies kanban/handoff claims against live `git status`/`git log`/`git diff`, corrects lanes to verified reality (the only edits it may make), then hands off to `/geeky-implement`. Never trusts a pre-cutoff "done". |
| `archive` | skill | Archives a concluded spec: moves planning artifacts to `archives/`, creates the permanent `docs/spec-NNN-name/` folder (spec + handoff + README), updates CLAUDE.md current state. |
| `geeky-orchestrator` | agent | Intelligent workflow administrator for direct routing, read-only triage, lifecycle coordination, and focused clarification when the correct entry point is ambiguous. |
| `/spec-research`, `/geeky-plan`, `/plan-review`, `/geeky-implement`, `/impl-review`, `/geeky-status`, `/geeky-resume`, `/archive` | slash invocation | Each skill is invoked directly as a slash command (`/geeky-orchestration:<name>`). The plugin ships no separate `commands/` wrappers: a same-named command shadowed its skill, so invoking it returned the wrapper text instead of the `SKILL.md` procedure. The full procedure lives only in `skills/<name>/SKILL.md`, which non-Claude agents read too. |
| `geeky-coder` | agent | Portable coder subagent. Treats the orchestrator's brief as authoritative scope. Returns a structured summary. Safe to spawn in parallel against non-overlapping task surfaces. |
| `code-architect` | agent | Portable architecture reviewer subagent. Reviews code with a system-level lens, focusing on maintainability, scalability, modularity, and architectural best practices. |
| `code-explorer` | agent | Portable code explorer subagent. Reads the codebase to answer questions about existing patterns, dependencies, and relevant prior work. |
| `code-reviewer` | agent | Portable code reviewer subagent. Focuses on correctness, style, and adherence to the task's validation block. |
| `templates/task_template.md` | template | Canonical task shape consumed by `/geeky-plan`. |
| `scripts/validate-planning-folder.{ps1,py}` | gate | Folder completeness: verifies a folder has the artifacts `/geeky-implement` expects. |
| `scripts/validate-task-schema.{ps1,py}` | gate | Each `tasks/Tx-*.md` carries the required template sections (plan→implement boundary). |
| `scripts/validate-kanban.{ps1,py}` | gate | Kanban integrity: every task in exactly one lane, no dangling refs, WIP cap, lane coverage. |
| `scripts/check-dod.{ps1,py}` | gate | Definition-of-Done for one task: notes file exists, task in Done lane, handoff mentions it; prints the task's validation block for comparison with evidence. |
| `scripts/check-commit.{ps1,py}` | gate | Commit message is Conventional Commits + references a task (`Tasks: T<n>`). |
| `hooks/guard-planning-contract.{ps1,py}` | hook | PreToolUse guard for edits to frozen planning artifacts. Default `--mode warn` (advisory, surfaced via portable stdout+stderr); `--mode block` denies via Claude/Codex JSON (or exit 2 with `--exit-code`). |
| `AGENTS.md` + `geeky.manifest.json` | discovery | Framework-agnostic discovery layer: how non-Claude agents learn the contract and invoke the gates (human-readable + machine-readable). |
| `mcp/server.py` + `.mcp.json` | MCP server | `geeky_mcp`. stdio server exposing the six gates as MCP tools for any MCP-capable agent. Thin adapter over the same scripts. See [mcp/README.md](mcp/README.md). |

Every gate follows one contract: **arguments in, exit 0 = pass / exit 1 = fail, summary on stdout** (optional `--json` / `-Json`). Each ships paired Python + PowerShell with identical output and exit codes. See [docs/framework-agnostic-quality-gates.md](docs/framework-agnostic-quality-gates.md) for the design rationale.

## Pipeline

```
/spec-research <topic or spec-NNN>     → writes feature-specification.md + README.md in docs/<feature>/

/geeky-plan <spec or folder>          → produces docs/<feature>/...
   ├─ implementation-plan.md           (FROZEN after this point)
   ├─ feature-specification.md         (FROZEN)
   ├─ draft.md                         (FROZEN)
   ├─ references.md                    (FROZEN)
   ├─ kanban.md                        (mutable — status of truth)
   ├─ handoff.md                       (mutable — running log)
   ├─ review-development-project-manager.md
   └─ tasks/T1-...md  T2-...md  ...    (FROZEN — notes go in Tx-*.notes.md siblings)

/plan-review <folder>                  → 4-phase quality review of the planning package

/geeky-status <folder>                 → read-only snapshot

/geeky-resume <folder>                 → after a cutoff: reconcile kanban vs live git, then resume

/geeky-implement <folder>              → walks kanban Ready → Done
   ├─ delegates geeky-coder per task (max 3 parallel when safe)
   ├─ verifies each task's validation evidence; runs only justified checks
   ├─ runs code-review on each task's diff
   ├─ runs PM review at each phase boundary
   ├─ writes tasks/Tx-*.notes.md per task
   ├─ commits per phase, split into small logical commits
   └─ updates kanban.md + handoff.md continuously
                                       (never pushes)

/impl-review <folder|diff|branch>      → 3 domain-expert subagents review the delivered code

/archive <folder|spec-NNN>             → moves planning artifacts to archives/,
                                         finalizes docs/spec-NNN-name/, updates CLAUDE.md
```

## Operating profile (baked into `/geeky-implement`)

- **Autonomy:** fully autonomous until the backlog is empty or a task lands in Blocked.
- **Reviewer:** one `code-reviewer` subagent dispatch at every phase boundary, including the last, giving each task a verdict against its ACs and defined tests plus the phase verdict.
- **Commits:** per phase, split into multiple small commits (one concern per commit). Never push, never amend, never `--no-verify`.
- **Parallelism:** up to 3 concurrent `geeky-coder` subagents, gated by a checklist (no shared deps, no file-surface overlap, no shared mutable artifacts).

Override per run via flags inside the argument string:
- `--phase=<name|number>`. scope to one phase
- `--dry-run`. preview the execution model, modify nothing
- `--serial`. disable parallelism for this run

## Contract between commands

The output of `/geeky-plan` is a **read-only contract** consumed by `/geeky-implement`. The implementer never edits:

- `implementation-plan.md`
- `feature-specification.md`
- `draft.md`
- `references.md`
- `tasks/Tx-*.md` (original task bodies)

If reality diverges from the plan mid-run, the task is moved to Blocked with a note in `kanban.md` and surfaced to the user. The bundled PreToolUse hook surfaces a warning if any tool attempts to write to a frozen artifact (default `--mode warn`); switch it to `--mode block` in `hooks/hooks.json` to deny such edits outright.

Mutable artifacts (updated continuously by `/geeky-implement`):
- `kanban.md`. single source of truth for lane status
- `handoff.md`. running log + Deferred follow-ups
- `tasks/Tx-*.notes.md`. per-task summary, validation log, review findings

## Install

This plugin ships in the `geekhoo-plugins` marketplace. Once that marketplace is added to your Claude Code config:

```
/plugin install geeky-orchestration@geekhoo-plugins
```

## Typical session

```
# Session 0 — research a new spec from scratch (optional)
/spec-research spec-009 notifications

# Session 1 — planning
/geeky-plan docs/my-feature/

# Review the plan before committing to it
/plan-review docs/my-feature/

# Inspect
/geeky-status docs/my-feature/

# Session 2 — execution (autonomous until Blocked or Done)
/geeky-implement docs/my-feature/

# Pick up on a different day
/geeky-status docs/my-feature/      # where are we?
/geeky-implement docs/my-feature/   # resume

# Try a single phase first
/geeky-implement docs/my-feature/ --phase=2 --dry-run
/geeky-implement docs/my-feature/ --phase=2

# Wrap up — expert review of the delivered code, then archive
/impl-review docs/my-feature/
/archive docs/my-feature/
```

## Cross-platform notes

Every gate and the PreToolUse hook ship as **paired Python + PowerShell** implementations with identical output and exit codes:

| Script | Windows-preferred (`.ps1`) | Cross-platform (`.py`) |
|---|---|---|
| Gates (`validate-planning-folder`, `validate-task-schema`, `validate-kanban`, `check-dod`, `check-commit`) | `scripts/*.ps1` | `scripts/*.py` |
| Hook (auto-run on every Edit/Write) | `hooks/guard-planning-contract.ps1` | `hooks/guard-planning-contract.py` |

**Gates:** the skills show both invocations in their prompts; the model picks the right one based on the host OS. Each exits `0` on pass / `1` on fail and accepts `--json` (`.py`) / `-Json` (`.ps1`) for machine-readable output. The `geeky_mcp` server (Python) wraps these for tool-style invocation.

**Hook (auto-run):** `hooks/hooks.json` calls the **PowerShell** version with `"shell": "powershell"`. Claude Code then runs it without Git Bash, so it also works where Git Bash can't start, such as an MXC sandbox. The Python guard behaves identically. To use it instead (for example on macOS or Linux without `pwsh`), remove `"shell"` from `hooks/hooks.json` and set the command to:

```
bash "${CLAUDE_PLUGIN_ROOT}/hooks/py-run.sh" "${CLAUDE_PLUGIN_ROOT}/hooks/guard-planning-contract.py" --mode warn
```

Requirements:
- The Python implementations need **Python 3.8+** on PATH as `python` (or `python3`. edit `hooks.json` if your environment uses the latter). No third-party packages required. stdlib only.
- The PowerShell implementations, including the default hook, need **PowerShell 7+ (`pwsh`)** on PATH. It's present on Windows; on macOS or Linux, install `pwsh` or switch the hook to the Python guard as above.
- The `geeky_mcp` server is the exception: it needs `uv` and is pinned to **Python 3.14** by `mcp/.python-version` (`uv` downloads it on first launch if absent). The gates and hook above are unaffected. See [mcp/README.md](mcp/README.md) for why the interpreter is pinned, what the server costs at startup, and the stdio subprocess rule.

## Other notes

- `geeky-coder` is renamed from a generic `coder` agent to avoid clobbering any personal `coder` agent the user may have configured.
- Phase review dispatches this plugin's `geeky-orchestration:code-reviewer` agent; its READY TO ADVANCE / BLOCKED verdict and agent ID are recorded in `handoff.md`.

## Cross-harness agent registration (Codex / Claude / Copilot / Cursor)

Canonical agent definitions live in `agents/*.md`.

Different harnesses use different discovery paths and schemas, so this plugin ships a projection utility:

```bash
python scripts/sync-agents.py   # Python 3.8+, no dependencies
node   scripts/sync-agents.js   # Node.js, no dependencies
```

Both produce identical output. This generates harness-specific agent files under `.claude/agents/`, `.github/agents/`, `.codex/agents/`, and `.cursor/agents/`, plus the generic fallback `.agents/<name>.md`, at the repository root.

To project only the workflow router across all targets, run:

```bash
python scripts/sync-agents.py --agents geeky-orchestrator
node   scripts/sync-agents.js --agents geeky-orchestrator
```

See `docs/cross-harness-agent-registration.md` for usage flags, compatibility notes, and verification steps.

## Planned: agent eval (`/geeky-eval`)

Not yet implemented. Design decisions for evaluating, judging, and scoring coding agents/harnesses/models on quality, adherence, and consistency are recorded in [docs/agent-eval-decisions.md](docs/agent-eval-decisions.md). The three sample challenges are in `evals/cases/c1-csvledger/`, `c2-linkvault/` and `c3-minisql/`. Each folder holds:

- `spec.md`: the reference spec.
- `brief.md` and `contract.md`: the only files contestants see.
- `oracle/`: the hidden pytest suite. Run it from inside `oracle/` with `ORACLE_TARGET=<contestant repo root>`.

## Consistent C1 saved-trace scoring (2026-10-24)

[Four-run replay report](evals/analyses/c1-consistent-rescore-20261024/README.md): repaired Codex process attribution and cached own-commit validation; Codex1 96.3, Codex2 98.0, Claude6 98.3, Claude4 97.9. Original scores preserved, 306 tests + 32 subtests passed, no paid run.
