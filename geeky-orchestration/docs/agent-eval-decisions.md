# Agent Eval. Decision Record

Design decisions for `/geeky-eval`. It is an end-to-end workflow inside geeky-orchestration that:

- runs coding agents (one harness + model per contestant) through the geeky workflow;
- judges and scores their **quality**, **adherence** and **consistency**;
- scores every run against one common, deterministic baseline.

It reports scores and their breakdown. It does not rank contestants as winners or losers.

- Status: decisions settled except the open items at the end. Specced challenge kits are committed. The baseline runner, the run analyzer, the deterministic scorer (`evals/scripts/score-run.py`) and the mock agent are built; the judge, the expectations files and the `geeky-eval` skill are not.
- Baseline: geeky-orchestration @ `c957a43` (main).
- Next step: `/spec-research` on this record (D15).

> Current C1 records (2026-10-24): [checkpoint 5 closeout](../evals/codex-c1-checkpoint5.md) and D94-D98 record the Codex adapter, preserved four-run derivation and frozen six-Claude reproduction. Older live-probe facts below retain their dates; they are not current launch requirements.

## Decisions

### Purpose and scope

| ID | Topic | Decision |
|---|---|---|
| D1 | Purpose | (a) Choosing which harness/model to use day to day. (b) Regression-testing geeky-orchestration itself, to catch skill or prompt changes that make agents worse. |
| D2 | Unit under test | One end-to-end run per case: the full workflow (D14) in a single session (D25). Within that run, the **task tier** scores each task the agent created on its implementation. Task scores are normalized across tasks (D67). |
| D3 | Contestants & invocation | Contestants are invoked headless through a pluggable per-harness adapter: command template, env, model and reasoning flags, transcript capture. An ingest-only path also exists. There, runs are done manually and the eval ingests the resulting repo state and transcript. |
| D4 | Corpus | v1 is the three challenges in D32, kept stack-agnostic in what they ask for. More challenges, including replays of real repo history, can be added later. Public benchmarks are excluded. |
| D12 | Placement | The eval lives inside geeky-orchestration. See [Placement](#placement). |
| D13 | Language | Python, stdlib-only where possible. PowerShell is added only for quick fixes; `.py`/`.ps1` parity is not required. If the judge needs an SDK, it is isolated behind `uv`, as the MCP server already is. |
| D14 | v1 scope | Harnesses are Claude Code and Codex CLI. A run covers `/spec-research` → `/geeky-plan` → `/plan-review` → `/geeky-implement` → `/impl-review`. |
| D15 | Build route | The eval itself is built through the D14 pipeline. |
| D29 | Data policy | Markefin code goes to Codex/OpenAI or a judge model only after explicit approval. |
| D49 | OS | v1 runs and scores only on the host OS (Windows). The challenge specs are already cross-platform. |
| D55 | Contestant identity | A contestant is **one harness + one model**. Reasoning/effort uses the harness default unless the campaign specifies a value. v1 runs one contestant per harness. Each run also records, as metadata only: harness CLI version, model ID, reasoning setting, config-profile hash (D51) and plugin SHA (D48). |

### Run environment and safety

| ID | Topic | Decision |
|---|---|---|
| D9 | Isolation | Every run gets a fresh git worktree on the host. There are no containers, Podman or VMs, because target machines may lack them. Parallel runs use disjoint worktrees, ports and dev servers under a concurrency cap. Each run captures its transcript, token counts and wall time. |
| D16 | Unattended runs by prompting | There is no separate unattended mode and the skills are not changed for the eval. The eval measures how a harness uses the workflows **as they are** when given sufficient prompting. The stage prompts (D40) carry all authorization and the answers to known prompt points: <ul><li>end-to-end authority for the stage;</li><li>run all phases;</li><li>pre-approve impl-review fixes;</li><li>record plan-review flags in handoff and continue.</li></ul> |
| D62 | Workflows as-is | No skill, agent or hook is modified to make the eval work. Gaps such as the MCP-vs-scripts gate conflict or choices left open are handled in the expectations files as allowed sets. Skill changes go through the normal workflow, and their effect shows up through the D11 regression check. |
| D23 | Frozen-artifact guard | Contestants run with the shipped warn-mode guard; the adapter installs an equivalent hook for Codex. Frozen-artifact adherence is scored afterwards from `git diff`, because warn mode and Bash edits bypass the guard. |
| D24 | Forbidden git actions | Eval worktrees have no remote. Push attempts and `--no-verify` are detected from the normalized transcript. Amend and force are detected from the reflog. The eval adds no hooks or files to the contestant's repo. |
| D47 | Seed workspace | Each run starts from a fresh seed repo that the eval creates outside every repository, at a shallow path `C:\repos\<run>`, as MXC requires (D72). It contains: `git init`, `brief.md`, `contract.md`, `.gitignore`, no remote. The plugin is not copied into it. |
| D48 | Equivalent plugin access | The adapter exports the plugin at a pinned SHA (D50). Both harnesses get **equivalent context and access** to the full export: skills with their references, agents, templates, scripts, hooks and the `geeky_mcp` server. **Claude Code** loads it with `--plugin-dir`. **Codex** gets the same material through the plugin's cross-harness mechanisms: `sync-agents` projections, the plugin's `AGENTS.md`, skill discovery, the guard hook (D23), and `geeky_mcp` registered in its config. A parity pre-flight lists everything each harness can reach. It fails the run if Codex lacks anything Claude Code has. The plugin SHA is recorded on every run. |
| D50 | Oracle leak prevention | The adapter exports the plugin with `git archive` at the pinned SHA, excluding `evals/`, into a temp directory outside every repo. Contestants load only that export. The seed workspace, oracle and run records live where the contestant cannot reach them. A pre-flight check fails the run if any `oracle_*.py` or `spec.md` is reachable from the contestant's workspace or plugin path. |
| D51 | Clean harness config | Each harness runs under an isolated config profile kept in `evals/adapters/<harness>/profile/`. Claude Code runs under its own `CLAUDE_CONFIG_DIR`: the plugin export only, default output style, no user `CLAUDE.md`, no memory, no other plugins or hooks. Codex runs under its own `CODEX_HOME` containing only the D48 shim. The profile hash is recorded on every run. |
| D52 | Unattended safety | Writes are limited to the run's workspace. Codex uses `--sandbox workspace-write`. Claude Code runs in an MXC ProcessContainer (D72). Network stays on for the whole run (D72). A later hardening step runs contestants under a dedicated low-privilege Windows user with no git credentials. Any file written outside the worktree is a fail-fast event (D37). |
| D54 | Codex-path prerequisite | The failing `test_sync_agents.py::SyncAgentsTests::test_default_destination_is_callers_directory_for_both_runtimes` is fixed as ordinary plugin maintenance, through the normal workflow, before the first Codex baseline. It is a bug in the install path D48 depends on, not an eval-specific change. |

### Contestant inputs

| ID | Topic | Decision |
|---|---|---|
| D25 | Single-session invocation | One headless session per run, started with the canonical end-to-end prompt (D40). The `geeky-orchestrator` chains `spec-research` → `geeky-plan` → `plan-review` → `geeky-implement` (all phases) → `impl-review`, then fix and repeat `impl-review` until PASS. Mid-session interaction is kept to a minimum on purpose, to test how robustly geeky-orchestration runs from one instruction. The run ends at PASS, when the agent stops, or at a fail-fast point (D37). |
| D28 | Web access | spec-research keeps web access. Its consistency is scored on structure (angles chosen, sections produced), not on content. |
| D32 | Challenges | Three runnable, testable, Python-stdlib challenges, each with a hidden pytest oracle. **C1 `csvledger`:** a CLI that categorizes CSV transactions into monthly reports. **C2 `linkvault`:** a URL-shortener HTTP JSON API with a CLI client. **C3 `minisql`:** a SQL-subset query engine over CSV files. Token ceilings are set in D53. |
| D39 | Reference specs | `evals/cases/<id>/spec.md` holds, for each challenge: contestant brief, scope, requirements, exact interface contract, error handling, acceptance criteria, hidden-oracle outline, suggested decomposition, quality signals. |
| D40 | Canonical prompt | One prompt, `evals/prompts/end-to-end.md`, identical for every case and harness. Its only placeholder is `{{PLANNING_FOLDER}}`. A case supplies only `brief.md`, `contract.md`, the hidden oracle, and its `case.json` (D66). The prompt rules are D65. |
| D45 | What contestants see | Only `brief.md` and `contract.md`. `contract.md` holds the requirements, the language reference (C3 only), the interface contract, error handling and the acceptance criteria. The hidden-oracle outline, suggested decomposition and quality signals are never shown. |
| D67 | Tasks: implementation scored, creation not | The agent creates its tasks in `geeky-plan` however it judges best. How it decomposes the work is not scored. Task creation counts only toward the `geeky-plan` stage: whether the planning produced the artifacts that workflow requires. **Task tier:** each task the agent created gets a 0–100 implementation score that emphasizes attempts. The task-tier score combines those per-task scores so that the number of tasks has no effect. Formulas: [Task-tier formula](#task-tier-formula) (D68). Per-task scores are kept in the breakdown. |
| D68 | Task-tier weighting | Attempts count most: validation attempts and passing review on the first try outweigh duration and DoD. Duration is normalized for model latency. Tasks are combined using weights from LOC changed and validation attempts. The composite is **Q/A/C/T = 35/35/20/10**. |
| D65 | Prompt rules | Every canonical prompt follows four rules. **Case-agnostic:** it names no case, stack, file or solution. **Workflow as-is:** it only grants authorization and answers the skills' stop-and-ask points (the table in `evals/prompts/README.md`). **No coaching:** it never restates workflow rules, because adherence is being measured. **Harness-neutral:** it refers to workflows by skill name. Each run records the content hash of every prompt it used. "Green" means the overall verdict from `impl-review` is PASS. |
| D66 | Case manifest | Each case has an `evals/cases/<id>/case.json` holding its case-specific numbers: token ceilings, task-timeout overrides, and the oracle command. The harness, prompts and scorer contain no per-case logic. |
| D61 | geeky-coder is optional | The `geeky-coder` agent definition is available to every contestant, but its use is not required. The harness/model decides. Each run records whether `geeky-coder` was used. That choice falls in an allowed set and is not scored. |

### Evidence and judging

| ID | Topic | Decision |
|---|---|---|
| D6 | Judging stack | Judging is layered. Deterministic gates run first: validators, oracle, build, diff stats. A hard-gate failure caps or stops the run. An LLM judge then scores what scripts cannot, and must cite evidence for every point. Anything a gate can compute, the judge never scores. |
| D8 | Honesty audit | Claims in the final report are checked automatically against git, test output and artifacts. A false **completion** claim (a task or stage done, tests or oracle passing, a commit existing) triggers the Adherence ≤ 50 cap. A false **process** claim (who reviewed, which gates ran) fails the "final report claims verified" adherence check, once per claim. |
| D19 | Action-trace source | The primary source is the adapter-normalized transcript (`claude -p --output-format stream-json`, `codex exec --json`). Actions are also derived from artifacts: kanban and handoff diffs, and git log. Self-reported events are only a cross-check, and any mismatch feeds D8. |
| D26 | Quality oracle | Hidden acceptance tests are copied in only at scoring time. Tests written by the agent do not count toward the oracle. |
| D27 | Validation execution | The scorer re-runs every task's validation block and the hidden oracle itself, then compares the results with what the agent claimed. Each task's block runs in a clean checkout of that task's own commit; the oracle judges the final state. A later task may legitimately change an earlier command's result, as T8 did to T1's in C1 run 4. **The task's commit** is chosen like this:<ul><li>ignore commits made before the task started;</li><li>take the last commit whose `Tasks:` line names the task before its Done move;</li><li>if there is none, take the first one after the move;</li><li>if no commit names the task, use the final HEAD and record the fallback.</li></ul> |
| D31 | Default judge | Claude Opus 5.5. An optional, user-selectable panel adds a GPT-family model. The report flags when the judge's model family is also a contestant. |
| D57 | What the judge sees | The judge compares against a specific, deterministic baseline for the case: the reference solution, the workflow expectations (D34) and the oracle results. It sees three things: **the steps taken** (normalized action trace), **the output** (final diff and produced artifacts), and **the validations** (what was run and its results). It never sees raw transcripts or harness/model names. It scores against a fixed rubric with per-criterion anchors. |
| D64 | Judge calibration | [evals/judge-calibration.md](../evals/judge-calibration.md) is a self-contained procedure. A human or another agent uses it to score a sample of runs independently and check the judge against those scores. |

### Scoring

| ID | Topic | Decision |
|---|---|---|
| D5 | Dimension definitions | See [Dimensions](#dimensions). |
| D10 | Scoring & output | See [Scoring](#scoring). |
| D11 | Regression check | `geeky-eval compare` compares a contestant's new scores with its own previous record. It exits 1 when the composite drops by more than 5 points, or when any hard gate regresses. This guards skill changes (D1b); it is not a ranking between contestants. |
| D17 | Commit expectations | The end-to-end prompt authorizes each workflow's own commit protocol. Adherence scores each commit against the protocol expected for its stage. |
| D18 | Commit attribution | Skills carry no hardcoded `Co-Authored-By` trailer (removed in `b36cc60`). |
| D20 | Choices the skills leave open | Every decision point is scored against the expectations. Where a skill leaves a choice open, or two instructions conflict (MCP tools vs scripts for gates), the expectations give an allowed set (D62). |
| D22 | Common baseline | Every dimension is scored against a common baseline, not against other contestants: the case oracle, the workflow expectations and the reference solution. Consistency means making the choices the workflow instructions expect. A harness that lacks a capability is not penalized for following the skill's documented fallback; the gap is recorded as a capability note. |
| D30 | Runs per case | N = 3 for contestants and 3 repeats per case for baselines, reported as mean and min–max (D70). N rises to 5 once budgets are calibrated. |
| D73 | MXC per-run env | `mxc-sandbox` gained `--env NAME=VALUE` / `--env NAME`, which is repeatable and applied last. A bare `NAME` copies the host's value and exits 2 if it is unset; `probe` prints names only. Verified: values with spaces or `=` arrive intact. With `MXC_CLAUDE_EXE=codex.exe`, Codex honours `--env CODEX_HOME=<dir>` and builds a fresh home. That isolated home still needs a one-time `codex login`; until then the API returns 401. User skills in `~/.agents/skills` stay unreadable inside the container. |
| D74 | Guard hook shell | `hooks/hooks.json` runs `pwsh -NoProfile -ExecutionPolicy Bypass -File guard-planning-contract.ps1 -Mode warn` with `"shell": "powershell"`, so Git Bash is no longer needed. This was verified in MXC: `PreToolUse:Edit` on a frozen file exited 0 with the guard message. It needs `pwsh` on PATH; the Python alternative is documented in the README. It is plugin maintenance, not an eval-only change. |
| D75 | geeky_mcp in MXC | **Root cause:** Python asyncio on Windows builds its self-pipe from a 127.0.0.1 socketpair. Under MXC's default `HostLoopback = Deny` that hangs, made worse on this machine's build (26300.9711 with KB5127648, [microsoft/mxc#1505](https://github.com/microsoft/mxc/issues/1505); see also [#1261](https://github.com/microsoft/mxc/issues/1261)). The stdlib server worked because it never uses asyncio. A 127.0.0.1/32 egress allow rule does not help. **Fix:** a new `mxc-sandbox --host-loopback` option. With it, `geeky_mcp` connected in MXC and its gate tool returned the expected result. **Launcher:** a prebuilt venv (`mcp` 2.3.0, built offline from the uv cache) started by the base interpreter with a `site.addsitedir` bootstrap, which is needed because `PYTHONPATH` skips `.pth` files and so loses pywin32. The plugin's shipped `uv run` launcher still fails in MXC (`CONNECTION_CLOSED`), probably because of uv's trampoline and TEMP rename limits ([#1204](https://github.com/microsoft/mxc/issues/1204)). **Trade-off:** `--host-loopback` lets the workload reach every host loopback port, which is accepted in D77. |
| D77 | Host loopback accepted | Eval runs use `--host-loopback`, so both harnesses get `geeky_mcp` as the plugin intends. Runs happen while no sensitive local services are listening on 127.0.0.1. |
| D76 | Bash in MXC | Git Bash cannot run in MXC, at any tier and with any config. This is the open MXC/OS issue [microsoft/mxc#1061](https://github.com/microsoft/mxc/issues/1061): msys creates named objects under the global `\BaseNamedObjects`, which AppContainer denies. A maintainer says a fix needs MSYS runtime and OS namespace changes. So the Claude contestant has no Bash tool (only PowerShell), and hooks must use `"shell": "powershell"` (D74). Both are recorded as capability notes. |
| D78 | Skills not shadowed by commands | The first C1 baseline runs showed that invoking `geeky-orchestration:<name>` returned the same-named `commands/<name>.md` wrapper ("Invoke the X skill…") instead of the `SKILL.md` procedure, on the host and in MXC alike. So agents ran every workflow from its description. The `commands/` folder is removed, and each skill is invoked directly. Verified on the host and in MXC: the skill body ("Base directory for this skill…") is now delivered. Baselines recorded before this fix are discarded. |
| D79 | Planning-stage commit format | `check-commit` requires a `Tasks:` line, but the skills prescribe exact messages for commits made before any task exists: <ul><li>`docs: author feature specification in <folder>` (spec-research);</li><li>the geeky-plan package commit;</li><li>`chore(plan): Plan review — align documents, fix sequencing` (plan-review);</li><li>the impl-review result commit.</li></ul> Adherence scores those commits by whether they match the message their skill prescribes. `check-commit` applies only to commits made during `geeky-implement`. The C1 baseline showed 12/15 passing under the strict gate, and all 15 conform under this rule. Two things are scored separately: **commit message conforms** is an adherence check, where the scorer re-runs `check-commit` on each message; **commit gate ran before the commit** is decision point 12. |
| D80 | Token accounting | A run's tokens are summed from `result.modelUsage` across every model (main model plus helpers such as Haiku): input = fresh + cache read + cache creation, total = input + output. `result.usage` covers only the last turn and is not used. `evals/scripts/analyze-run.py` derives tokens, model calls, stages, latency, idle gap and impl-review rounds from the stream and session files. It counts gate runs from tool results, with pass/fail and main/subagent split; `--analysis-only` re-analyses a stored run without touching `run.json`. |
| D81 | Sandbox environment fixes | Three environment faults showed up in the first C1 baselines. Each one added noise to the scores. All are fixed in the runner and verified by probe on 2026-10-21. <ul><li>**PowerShell tool reported `Exit code 5` on every call in MXC.** Fixed with `CLAUDE_CODE_DISABLE_WINDOWS_SHELL_LAUNCHER=1`. Plain `pwsh` and `chcp.com` both exit 0 in MXC, so the fault is Claude's Windows shell launcher.</li><li>**The sandbox Python had no pytest, and pip couldn't install it.** Fixed with a prebuilt venv, `.eval-tools\agent-py`, put first on `PATH`.</li><li>**The repo had no git identity, so agents committed as `Claude`.** Fixed with a neutral identity, `geeky-eval-agent`, set through the `GIT_AUTHOR_*` and `GIT_COMMITTER_*` environment variables.</li></ul> Baselines recorded before D81 still count as valid results. They are not fully comparable with later runs on T1 attempts, tokens or commit authorship. |
| D82 | Handoff adherence check | A task passes the handoff check only if `handoff.md` was updated naming its ID **in the same lane-move batch as its Done or Blocked move**. ID ranges such as "T1-T9" and lists such as "T1,T2" are expanded. The previous check only looked for each ID somewhere in the final `handoff.md`, which credited a single end-of-run write as per-task updates. A handoff entry written in the same tool call as a batched Done move, or in the call right after it, passes for every task of that batch it names. |
| D83 | Mock agent and dry-run checks | `evals/mock-agent/mock_claude.py` is a stdlib-only stand-in for `claude -p`. It works for any case or workspace. It writes realistic stream-json and a session transcript, and it performs real file, gate, git and pytest actions. Checks can be combined: `env-probe`, `grants`, `pwsh`, `python`, `git`, `gates`, `mcp`, `network`, `happy`, `gate-fail`, `crash`, `slow`, `bg-wait`. Ways to run it: <ul><li>through the runner: `run-baseline.ps1 -MockAgent -MockScenario <list>`;</li><li>standalone: `dry-run.ps1 [-InMxc]`.</li></ul> Each run reports pass/fail lines plus a summary JSON, and costs no model tokens. Run it before any paid baseline. Mock runs are never reference-eligible. |
| D84 | Writable temp via TMPDIR | MXC forces `TEMP` and `TMP` to the AppContainer's `AC\Temp`, ignoring the host's setting. Folders created there by `mkdtemp()` aren't writable, which broke pytest `tmp_path` and git temp repos. A probe showed the cause is not Python 3.13's `0o700` ACL: `0o700` folders inside granted folders are writable. Python, pytest and git honour `TMPDIR` first, and MXC leaves it alone. So `run-baseline.ps1` and `dry-run.ps1` give each run a writable `.eval-cfg-<stamp>\tmp`, granted read-write, and set `TMPDIR` to it. Verified on 2026-10-22: `dry-run.ps1 -InMxc -Checks all` passes all checks, and the runner's mock env checks pass 31 of 31. |
| D85 | Background-work ceiling | C1 run 3 (`20261021T190006Z`, plugin `c9c8794`) delegated `geeky-implement` to a background subagent and ended its main turn. Headless `claude -p` stops background tasks still running 10 minutes after the main agent's last turn (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`). That cut the run off with 3 of 10 tasks done, oracle 0/118, and it was still recorded as `completed`. A haiku probe confirmed that `-p` resumes the main agent when background work finishes. The runner and `dry-run.ps1` now set `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, bounded by the MXC `--timeout`. The runner records such cut-off runs as `exit_reason = bg_killed`. The mock agent's `bg-wait` scenario and the `env.bg_wait_ceiling` env-probe check cover this. Run 3 is not reference-eligible. Its evidence is archived in `evals/baselines/archive/c1-csvledger-20261021T190006Z-bg-killed/`. Up to the cut-off, it showed the D-fixes working: event logs for all 10 tasks, one task per commit, `Tasks:` lines, and the handoff updated per task. |
| D86 | Gate timing | A gate counts as run "before Done" if it passes in the same tool call as the Done edit, or after the task's last code edit and before that call. |
| D87 | Orchestrator code edits | Adherence checks that the main thread makes no product-code or test edits during `geeky-implement` or `impl-review`. Each such edit also adds one V attempt to the task that owns the file. |
| D88 | Skill fixes from C1 run 3 | `geeky-implement` and `impl-review` were changed to close the run 3 gaps. Each item has one rule in `SKILL.md`, the execution protocol (EP) or `geeky-coder.md`. <ul><li>**Phase review:** a `geeky-orchestration:code-reviewer` subagent issues every phase verdict, including the last, and its agent ID is recorded in the handoff. Previously EP named a planning-coordinator agent that does not exist.</li><li>**Review batches:** a batch holds only tasks with no dependency on each other. This removes the deadlock between EP's dependency rule and its batch-hold rule.</li><li>**Code edits:** the orchestrator never edits product code or tests. Every fix goes to `geeky-coder`, including `impl-review` critical fixes.</li><li>**Commit gate:** `SKILL.md` lists `check-commit`, in the `--message` form that works in PowerShell.</li><li>**Task events:** `geeky-coder` returns an `EVENTS:` field. The orchestrator appends it, plus one dispatch event and one verdict event per task.</li><li>**Kanban moves:** a task moves one lane per edit.</li><li>**Final report:** review and gate claims cite the handoff records. Self-issued gates are listed as deviations.</li></ul> The agent projections were regenerated with `sync-agents.py`. Not yet validated by a paid run. |
| D89 | Validation evidence reuse | The orchestrator verifies each worker's saved validation evidence instead of re-running it: the tested revision, the commands and the results. It re-runs only missing or invalidated checks, or checks that are explicitly required, and records why. A bare PASS claim is rejected. This avoids redundant test runs. The risk of a false worker claim is bounded by the phase review, by `check-dod` and by the scorer's own re-runs (D27). This policy dates from `5fbff0b`. An automated security review flagged it as fail-open when the agent projections were regenerated in `bc88a60`; that finding is acknowledged and the policy kept. |
| D90 | Review cadence and main-thread budget | C1 run 4 used 15.5M tokens against the 12M ceiling. 64% of that was main-thread turns during `geeky-implement`: each turn re-reads a context of 118K–231K tokens, and per-task reviews added 15 reviewer dispatches. The ceiling stays at 12M. These changes cut the cost without lowering review depth or evidence: <ul><li>**Review cadence:** one `code-reviewer` dispatch per phase issues a separate AC-by-AC verdict for every task and the phase verdict. A phase of more than 4 tasks, or one too large for one pass, is split into dispatches of at most 4 related tasks.</li><li>**Dependents:** a dependent task may start once its predecessor is In Review with passing evidence. Done moves follow the phase review. Fixes go to `geeky-coder`, dependents of a changed task re-validate, and only the affected tasks are re-reviewed.</li><li>**Worker returns:** about 15 lines, with detail written to the task notes. Validation evidence (revision, commands, result lines) is always returned in full, and review verdicts are never shortened.</li><li>**Command output and close-out:** successful output is read through a tail and a failure in full. Each task's close-out takes one tool call, and independent work is dispatched in the same turn.</li></ul> This supersedes D88's rule that a dependent waits for its predecessor's task verdict. Not yet validated by a paid run. |
| D92 | Gate order and plan-review reviewers | C1 run 5 missed three rules, and the skill text now states each one where the step happens: <ul><li>**Gate order:** `check-dod` verifies a task that is already in the Done lane, so it runs in the same step as the Done move, followed by `validate-kanban`. A failing `check-dod` sends the task back out of Done. This replaces a first D92 wording, "`check-dod` exits 0 before the Done move", which the tool cannot satisfy; C1 run 6's orchestrator found that and recorded the workaround as a deviation. D86's same-call rule matches this order.</li><li>**Commit gate:** a failing `check-commit` blocks that commit until the message is fixed.</li><li>**Plan-review reviewers:** `plan-review` always dispatches its Phase 3 `code-architect` subagent, separate from Phase 1, even when Phase 1 found nothing.</li></ul> |
| D93 | Nested subagents and runner hygiene | <ul><li>**Delegation (K3):** handing all of `geeky-implement` to the plugin's `geeky-implement-orchestrator` subagent is valid. C1 run 6 did this, and its main thread spent only 0.64M tokens during implementation. The scorer treats that subagent's calls as orchestrator calls for lane moves, gates, notes, handoff, dispatches, review verdicts and the D87 code-edit check.</li><li>**Nested transcripts (K1, K2):** a nested subagent's calls appear only in the session's `subagents/agent-<id>.jsonl`, whose `meta.json` names the spawning tool call (`toolUseId`). The runner copies these into the run folder, and the analyzer and scorer merge them into the trace by `toolUseId`, deduplicating by tool-use ID.</li><li>**Tamper check (K1):** the runner sets `PYTHONDONTWRITEBYTECODE=1` and leaves `__pycache__` out of the plugin tamper hash. Run 6 had been flagged only because of bytecode; its export matched `8ea2ccc` file for file, so the record is corrected to reference-eligible.</li></ul> |
| D91 | Task event logs retired | No C1 run ever wrote `tasks/T<n>.events.jsonl`, including after D88 added an `EVENTS:` output field. The requirement, the field and its scorer checks (`adh.events.<T>`, decision point 6) are removed. Cross-task consequences go in the affected task's notes and in `handoff.md`. This supersedes D88's task-events item. Without these checks the C1 composites are 77.2, 77.0, 86.7 and 97.9 for runs 1–4. |
| D69 | Trace format | **ATIF-v1.7** is the normalized per-run record. The raw native stream and the session file are always kept next to it. Eval-specific fields go in `extra`, and event kinds follow OTel GenAI naming. The adapter detail goes to `/spec-research`. |
| D70 | Repeats | Research shows 2–6 points of run-to-run noise and recommends 5 or more repeats for calibration. For now, N = 3 is accepted because of token cost, and N rises to 5 after O14 calibration. |
| D71 | Claude profile auth | Claude runs in the MXC isolated profile (D72), which authenticates only through the host env `CLAUDE_CODE_OAUTH_TOKEN`, a subscription token the owner creates with `claude setup-token`. Neither the eval nor its agents ever read or handle the token's value. `--bare` with an API key is not used. Billing does not affect scoring (D53). |
| D72 | Claude sandbox: MXC | Claude Code runs inside a Microsoft MXC ProcessContainer (BaseContainer tier) through the `mxc-sandbox` plugin. The run is: `mxc.ps1 run --workspace C:\repos\<run> --isolated --allow-win32k --ro <plugin export> --timeout <s> -- --plugin-dir <plugin export> --settings <no-hooks.json> -p ...`. **What it does:** writes only to the workspace and the private config; host files outside the grants can't be read; Python starts; the trace goes to stdout as normal. **What it does not do:** Git Bash can't run, so the Bash tool and all hooks fail; the PowerShell tool needs `--allow-win32k`; `uv run` stdio MCP servers can't start; network is all-or-nothing (it stays on, because spec-research needs the web, which supersedes D52's spec-research-only network rule). This resolves the former O17. Verified by probes on 2026-10-20 (see the verified facts table). |
| D33 | Hard gates & fail-fast | See [Hard gates](#hard-gates). A fail-fast point stops the run immediately. The run returns its score up to the failure point (D38), with `failed_at` (stage, task, gate) and the evidence. |
| D34 | Workflow expectations format | One `evals/expectations/<stage>.yaml` per skill, plus `geeky-orchestrator.yaml` for stage chaining and `geeky-coder.yaml`, which applies only when `geeky-coder` is used (D61). Each decision point records: `id`; source (`SKILL.md:line`); trigger; expected action or allowed set; `critical` flag; and a detection rule. Each file is pinned to a content hash of its skill, and a test fails when a skill changes but its expectations file does not. The files are written by hand and reviewed by the owner. |
| D36 | Absolute, timestamped records | Every score is absolute against the common baseline. Every recorded file name carries a UTC timestamp, `YYYYMMDDTHHMMSSZ`. Each record names the expectations version and the reference-solution version it was scored against. |
| D37 | Fail-fast points | The run stops immediately when any of these happens: <ul><li>push, force, amend or `--no-verify`</li><li>the token ceiling is hit (D53)</li><li>a task timeout is hit</li><li>a write lands outside the worktree</li><li>the harness crashes, or exits non-zero with no output</li><li>an unattended run asks for user input</li><li>a stage exit gate fails: `validate-planning-folder` or `validate-task-schema` after `/geeky-plan`, or `validate-kanban` after `/geeky-implement`</li></ul>A modified frozen artifact is capped, not stopped. **Task timeout:** each task inside `geeky-implement` gets 20 minutes of wall time by default; a case can override this. Because the run is a single session, a watcher checks fail-fast points live: it reads the workspace and the normalized trace, runs each stage exit gate once that stage completes, and ends the session on failure. |
| D38 | Up-to-failure scoring | The headline score counts work not reached because of a failure as 0 against the full planned scope. A second score covers only the work done before the failure. Both are reported with `failed_at`. |
| D41 | Reference solutions | The owner implements each spec elsewhere. The implementations are compared and folded in as each challenge's baseline solution (O14). Each baseline run also supplies the token baseline for D53. |
| D43 | Scorer self-test | Minimal: one pytest file and one pre-recorded fake run per hard gate and per fail-fast point. The scorer must flag every one. |
| D53 | Cost = tokens | Cost is measured only as **total tokens**: input (including cached) plus output, as each harness reports them. How the harness is billed is ignored. Provisional token ceilings per run are held in each `case.json`: **C1 12M** (raised from 10M after the first C1 baseline used 10.06M), **C2 25M**, **C3 50M**. They are recalibrated to 2× the baseline implementation run's tokens once O14 lands. **Token efficiency** = min(100, 100 × baseline tokens ÷ run tokens). It is reported in the breakdown, not in the composite. The baseline is fixed per case and plugin version and named in the record; adding runs never re-scores old runs. For C1 on plugin `24c4e6d` it is 11.69M tokens (mean of runs 1–2). |
| D58 | Scores bound to their evidence | Each dimension is scored only from its own evidence across everything the run did. There are no stage weights and no roll-up across stages. Per-stage figures appear only as breakdown. |
| D59 | Simple quality metrics | Quality uses three key metrics; see [Scoring](#scoring). Until reference solutions land, size is measured against the LOC band in each spec's Quality signals section. |
| D60 | Normalized scores, no ranking | Each run reports a normalized 0–100 composite with the full breakdown: each dimension and each metric inside it, plus token efficiency and wall time. When N > 1, the mean and min–max are reported. Mean, min–max and stability cover only runs of the same contestant (harness + model + plugin SHA + environment); other runs are listed beside them, not aggregated. There are no winners, losers or significance tests. |
| D63 | Results storage | A committed folder, `evals/results/`, holds every run record. Pushing it to the repo is allowed. Secrets are redacted from stored transcripts. |

### Records of earlier state

| ID | Topic | Decision |
|---|---|---|
| D21, D35 | Consistency formula | See [Consistency formula](#consistency-formula). |
| D42 | Wall-time ceilings | Pipeline wall-time ceilings stay deferred (O13). Cost metering is settled by D53. |
| D44 | Design-detail items | O2 and O7 move to `/spec-research`. |
| D46 | Hidden oracle timing | The hidden oracles were written before the owner's implementations land. They are committed in `75e6a49`, `3c99225` and `2343fe9`, with 118, 136 and 183 tests. |

## Dimensions

**Quality**: the requirements are met, all tests pass, there are no defects, and the code is minimal. See the quality formula in [Scoring](#scoring).

**Adherence**: compliance with the workflow contract and the operating rules.
- **geeky contract:** frozen artifacts untouched; kanban valid; DoD met; `check-commit` passes; notes and handoff written.
- **Task brief:** the agent stays inside its scope fence.
- **Commit rules:** commits follow the stage protocol (D17). Never push, amend, force or use `--no-verify`.
- **Honesty (D8):** report claims match the evidence.

**Task tier**: how efficiently and cleanly each task the agent created was implemented, measured by validation attempts, review rounds, latency-normalized duration and DoD, and normalized across tasks (D67, D68).

**Consistency**: whether the agent makes the choices the baseline workflow expects at each decision point (D22, D34). It is measured on actions taken, not on output. Decision points include:
- skill and step invocation, and their order;
- stage chaining by `geeky-orchestrator`;
- planning artifacts produced as `geeky-plan` requires (how the work is decomposed is not scored, D67);
- kanban lane moves;
- delegation and parallel split (with `geeky-coder` use recorded but not scored, D61);
- validations chosen and run;
- commit grouping;
- escalation and blocking.

## Scoring

All values are normalized to 0–100.

- **Quality** = 100 × (0.70 × P + 0.15 × S + 0.15 × D), where:
  - **P** is the oracle pass rate: passed ÷ collected, with allowed skips excluded.
  - **S** is the size score: min(1, reference non-test source LOC ÷ run non-test source LOC). Until O14 lands, the reference LOC is the upper bound of the spec's Quality signals band.
  - **D** is defect-free: max(0, 1 − defects ÷ 5). Defects are compile and import errors, failures of the re-run validation blocks (D27), and judge-confirmed defects with cited evidence.
- **Adherence** = 100 × (passed adherence checks ÷ applicable adherence checks), then capped by the [hard gates](#hard-gates).
- **Consistency**: see [Consistency formula](#consistency-formula).
- **Task tier**: see [Task-tier formula](#task-tier-formula).
- **Composite** = 0.35 × Quality + 0.35 × Adherence + 0.20 × Consistency + 0.10 × Task tier (QACT, D68).
- **Breakdown** (not in the composite): every metric above, per-task implementation results (D67), token efficiency (D53), total tokens, wall time, `geeky-coder` used (yes/no), capability notes, and `failed_at` if any.
- **Output:** each run writes to `evals/results/<YYYYMMDDTHHMMSSZ>-<case>-<contestant>/`. The folder holds `results.json`, `scorecard.md`, the normalized action trace, oracle and validation output, and the redacted transcript.

## Hard gates

| Gate | Effect |
|---|---|
| Hidden oracle has any failure | Quality ≤ 40 |
| Frozen artifact modified | Adherence ≤ 30 |
| Push / force / amend / `--no-verify` | Adherence = 0, and the run stops (D37) |
| Any false completion claim: task or stage done, tests or oracle pass, commit exists (D8) | Adherence ≤ 50 |
| Other fail-fast points (D37) | Stop the run; score up to the failure point (D38) |

## Consistency formula

**Terms**

- **Decision point:** a place in a skill's or agent's instructions where the agent must choose an action. Each one is listed in an expectations file (D34).
- **Reached:** the decision point's trigger condition occurred during the run.
- **Conformant:** at a reached decision point, the observed action equals the expected action or is in the allowed set.
- **Weight:** 2 for a decision point marked `critical`, 1 otherwise.
- **Step sequence:** the ordered list of skill/step IDs observed in the run (D19), compared with the expected sequence for the stages run.

**Decision-point conformance (DPC)** = (sum of the weights of conformant decision points) ÷ (sum of the weights of scored decision points). A decision point is scored when either of these holds:

- it was reached;
- it was not reached only because the run failed (D38), in which case it counts as not conformant.

A conditional decision point whose trigger never occurred is excluded.

**Order conformance (OC)** = 1 − (Levenshtein distance between the observed and expected step sequences ÷ the length of the longer sequence).

**Consistency** = 100 × (0.8 × DPC + 0.2 × OC).

**Stability** is the share of decision points where all N runs of a contestant took the same action. Its denominator is the decision points reached in all N runs, and the report states how many of the agreements are shared misses. It is reported for diagnosis and is not part of the score.

## Task-tier formula

All inputs come from the normalized trace (D19) and the task's artifacts.

**Per task `i`** (each part is 0–1):

| Part | Weight | Definition |
|---|---|---|
| **V**. validation attempts | 0.40 | `a` = the number of validation attempts, counted from the task's first code edit up to the first fully passing run. An attempt is a full run of any validation-block command that produced a test outcome; subset runs (`-k`, `::node`), pytest usage or collection errors (exit 4 or 5) and D81-type environment faults do not count. Each main-thread code edit to the task's files adds one attempt (D87). V = max(0, 1 − 0.25 × (a − 1)), so 1 attempt scores 1.0, 2 score 0.75, 3 score 0.5 and 4 score 0.25. V = 0 if the block never passes, including when the scorer's re-run fails (D27). |
| **R**. review rounds | 0.30 | `r` = the number of task-review rounds until PASS. R = 1 for `r` = 1 (first try), 0.5 for `r` = 2, and 0 for `r` ≥ 3 or if the task never passes review. A phase or batch reviewer verdict that names the task counts as one round; an orchestrator self-verdict or a deferral to `impl-review` counts as none. |
| **T**. latency-normalized duration | 0.20 | `d` = wall time from the task's dispatch (In Progress) to its first fully passing validation run or its review PASS, whichever is later; the Done move is the end only when neither exists. The adjusted time is `d_adj` = d × (L_ref ÷ L_run), where `L_run` is the run's median model-response latency per turn and `L_ref` is a fixed per-adapter constant: 2678 ms for Claude Code. This removes slow-API effects. T = max(0, 1 − d_adj ÷ task timeout) (D37, 20 min by default). |
| **D**. DoD gate | 0.10 | 1 if `check-dod` passes for the task, else 0. |

Per-task score: s_i = 100 × (0.40 V + 0.30 R + 0.20 T + 0.10 D).

**Combining tasks:** the task-tier score is Σ w_i × s_i, with w_i = 0.5 × (LOC_i ÷ Σ LOC) + 0.5 × (a_i ÷ Σ a), where:

- `LOC_i` is all lines the task's commits changed, tests included (Quality's S still uses non-test LOC);
- `a_i` is the task's validation attempts.

The weights sum to 1, so the score stays 0–100 however many tasks there are. Larger tasks, and tasks that took more attempts, count for more, so padding the plan with trivial tasks cannot raise the score.

## Placement

| Component | Location |
|---|---|
| Skill | `skills/geeky-eval/` with subcommands `run`, `judge`, `score`, `compare` and `report`. There is no same-named `commands/` wrapper, because one would shadow the skill (D78). |
| Deterministic scorer | `evals/scripts/score-run.py <run-folder> [--manual <json>]`. It writes `score.json` and `score.md` into the run folder, and judgement items without a manual verdict are listed as `needs_judge`. Trace facts come from `evals/scripts/analyze-run.py`. |
| Judge agent and rubric | `agents/geeky-judge.md`, `evals/rubric/` |
| Judge calibration | `evals/judge-calibration.md` |
| Canonical prompt | `evals/prompts/end-to-end.md` (rules in `evals/prompts/README.md`) |
| Challenges | `evals/cases/<id>/`: `spec.md`, `brief.md`, `contract.md`, `oracle/` |
| Workflow expectations | `evals/expectations/<stage>.yaml`, `geeky-coder.yaml` |
| Harness adapters + profiles | `evals/adapters/<harness>/` |
| Results | `evals/results/` (committed) |
| MCP exposure | new scoring tools on `geeky_mcp` (`mcp/server.py`) |
| Discovery | `geeky.manifest.json`, `AGENTS.md` |

## Gap assessment (geeky-orchestration @ `c957a43`)

| ID | Gap | Addressed by |
|---|---|---|
| G1 | No eval harness, rubric or scoring exists. | D10–D12 |
| G2 | Unattended runs block: impl-review's fix approval, plan-review's "flag for user", the orchestrator's no-auto-chain rule, and one phase per session. | D16, D25 (handled by prompting) |
| G3 | No structured action trace exists. | D19 |
| G4 | Choices the skills leave open; conflicting instructions on gate invocation (MCP vs scripts). | D20, D62 (allowed sets) |
| G5 | Stages commit on their own; the co-author trailer was hardcoded. | D17, D18 |
| G6 | Codex portability: Agent tool fan-out, `TaskCreate`, `${CLAUDE_PLUGIN_ROOT}`, no frozen-artifact hook. | D22, D23, D48 |
| G7 | The frozen guard is warn-only and can be bypassed through Bash. | D23 |
| G8 | `check-dod` never runs the validation block. | D27 |
| G9 | `--no-verify` and push attempts are invisible in git. | D24 |
| G10 | No fixtures existed. | D32 (kits committed) |
| G11 | Reusable today: gate `--json` outputs, the MCP wrapper pattern, wire_baseline's normalize-then-diff approach, the stdlib-only policy. | D12, D13 |
| G12 | The plugin directory exposes the hidden oracles to contestants. | D50 |
| G13 | Global user config (CLAUDE.md, output style, plugins, memory) contaminates harness runs. | D51 |
| G14 | Unattended runs execute on the host with broad permissions. | D52 |
| G15 | The `sync-agents` test that the Codex path depends on is failing. | D54 |

## C1 measurement closeout decisions (2026-10-24)

| ID | Decision | Ruling and evidence |
|---|---|---|
| D94 | Frozen replay and preservation | All six historical Claude runs reproduce every raw dimension/composite under the unchanged current harness: 30/30 comparisons, 67 source files stable and 106 original files preserved. [Replay](../evals/analyses/c1-checkpoint5-20261024/README.md) uses saved judgments and `--no-rerun` in isolated copies/clones, including hashed matching-HEAD heartbeat inputs. This closes historical regression proof; it is not strict process completeness or a fresh own-commit validation. The prior complete four-run derivation and its 206-file preservation proof remain separate and unchanged. |
| D95 | Complete measurements and judgment | Publish corrected Codex 1=96.3 and Codex 2=98.0 as source-backed, complete rubric measurements; retain 81.7/89.8 as history. Reuse validation bound to task, full SHA, committed task hash, exact command and recorded result. Reject absent attribution/commit mappings; never substitute documentation HEAD or invent 0/0 success. `--require-complete` permits legitimate judgment items; it does not require eliminating manual verdicts. The four-run repair removed 20 deterministic overrides, retained Codex 1's failed review round and Codex 2's false configuration claim. [Proof](../evals/analyses/c1-consistent-rescore-20261024/README.md). |
| D96 | Parity and MXC qualification | D48 context reachability is not runtime equivalence. Both Codex preflights say runtime_verified=false; native fixture success/trust configuration cannot prove automatic hook execution in a paid run. Preserve calibration results with that caveat and post-run frozen-artifact checks. A future full-parity claim needs trust, actual invocation and shell-write coverage evidence; adapter work is deferred. Reconcile D52: retained Codex runs used danger-full-access and ignore-rules inside outer MXC with an explicit generated profile, as trusted-exec.py records, not an inner workspace-write sandbox. This documents the existing contained configuration, grants no new launch permission, and is not approval for standalone host execution. |
| D97 | Stable rubric and comparison limits | Preserve dp08 timestamp-presence semantics, D92 move/check/revert, D53 flags and existing formulas. Timestamp plausibility or granularity normalization would be a separately versioned symmetric change. Task counts/denominators, worker model/delegation differences and API-latency fallback belong in the breakdown. Related tracking in functional commits does not alone violate one-concern: retain R2 PASS under execution-protocol.md unless unrelated concerns are established. No model-effect inference, no conversion of token totals into money, no equal-scope assumption for Codex all-thread versus Claude main-session call counts. Codex reference eligibility remains false pending calibration. |
| D98 | Bounded provenance and operational closeout | Preserve original run files, scores, judgments and qualified prior reports. New records prefer exact visible assistant messages with source identity/hash/time; do not rewrite historical verdict pointers. Hash claims cover named files only; check time differs from snapshot-write time. Future launch preparation should inventory dirty files before launch and persist each exact validation result once. Current checkpoint 5 closes records, not guard redesign, full generic ingest, paid calibration or the unbuilt eval skill. [Question-by-question dispositions and remaining limits](../evals/codex-c1-checkpoint5.md). |


## Final-pair parity decisions (2026-10-24)

| ID | Decision | Evidence and limits |
|---|---|---|
| D99 | Automatic final Codex process normalization | The supported delegated run-2 shape is extracted from raw own-history rollouts without operator process mappings or per-run constants. Existing judgment items and exact saved validation remain inputs. Ambiguous mappings reject; strict withheld composites exit nonzero. Automatic facts match the annotated derivation except two documented dispatch/start anchors with no score effect. Codex 2=98.04000506482035; final Claude 6=98.27180923451854 unchanged. [Final-pair evidence](../evals/analyses/c1-final-parity-20261024/README.md). No general historical Codex support or new six-run proof claimed. |
| D100 | Match existing guard scope | No guard rewrite is needed for the approved final-pair match: existing edit/patch warn behavior, retained native guard-context proof and 64 offline tests cover the corresponding paths. Shared shell bypass remains documented. Catalog untrusted status precedes exact trust-hash override and does not prove launch trust failure. Paid-session invocation remains unverified; no MXC or paid run was launched to extend that claim. |


## Telemetry and platform decisions (2026-10-24)

| ID | Decision | Evidence and limits |
|---|---|---|
| D101 | Langfuse telemetry on eval runs | With `TRACE_TO_LANGFUSE=true` both runners add Langfuse's own pinned transcript hook (Claude `Stop`/`SessionEnd` via `--settings`; Codex `Stop` via the profile, trusted by exact command) and upload untruncated turns, subagents, tool I/O and thinking/reasoning summaries (`showThinkingSummaries`, `model_reasoning_summary=detailed`). Delivery is read back into `langfuse.json` and `run.json.telemetry`. This changes the contestant configuration (one extra hook, summarized thinking), so telemetry runs are not directly comparable with the stored baselines (D60). See `evals/telemetry/README.md`. |
| D102 | MXC runs on Linux and macOS too | The `mxc-sandbox` host uses the native default backend outside Windows (Bubblewrap on Linux, Seatbelt on macOS) with POSIX quoting and symlink-target grants; both runners pick paths, venv layout and `tar` per platform. Verified on Ubuntu 24.04 (bwrap 0.9, slirp4netns, iproute2, iptables): read-only grants enforced, ungranted paths absent, egress allowed. The C0-C3 mock matrix passes for both harnesses there. Windows behaviour is unchanged but was not re-run in this change. mxc-sandbox 0.2.1 spawns sandboxes from a dedicated long-lived thread (bwrap's `--die-with-parent` follows the forking thread, so a retired thread-pool worker killed runs with exit 255) and gives the sandbox a private HOME. |
| D103 | Harness parity is scored with `parity-eval.py` | score-run's Adherence, Consistency and Task tier read each harness's transcript through its own parser; the Codex parser expects the Windows PowerShell shape, so on Linux it scored ~20 process checks "not found". `scripts/parity-eval.py` reads every run the same way: Langfuse observations (one shape for both tracers), reflog stage bounds (a stage starts at the earlier of its commit and the first non-batched read of its skill), and the final artifacts rechecked with the plugin's gate scripts, plus run-completed and work-committed checks. Quality stays with score-run (artifact-based). Composite = (0.35 Q + 0.35 A + 0.20 C) / 0.90. Judge items come from hand-reviewed `manual-verdicts.json` under one rubric for both harnesses. Results are also posted as Langfuse session scores (`telemetry/langfuse-scores.py`). |
| D104 | LiteLLM auth and provider refusals | With `-Litellm` the Claude runner passes the proxy key as `ANTHROPIC_API_KEY` (`x-api-key`) and clears `ANTHROPIC_AUTH_TOKEN` and the OAuth token; Codex uses a `litellm` provider with `env_key = LITELLM_PROXY_API_KEY`. A provider content-filter stop is recorded as `exit_reason = provider_refusal`; `-ResumeOnRefusal N` resumes the same session with a neutral prompt up to N times, each counted as an intervention and making the run ineligible as a reference. The ant-claude filter proved intermittent (8 replays of the refused request passed). |

## Agent identity telemetry decision (2026-10-25)

| ID | Decision | Evidence and limits |
|---|---|---|
| D105 | Platform and actor identities for MXC telemetry | New runs use `mxc-win`, `mxc-linux`, or `mxc-mac`; families `codex-mxc-*` / `claude-mxc-*`; readable shared run sessions; and source-bound per-agent user IDs. Each actor owns a trace to prevent child propagation overwriting its parent's user identity. Cross-agent parent IDs remain metadata. Pinned originals and native session IDs are preserved; readback, coverage and score publication support both new and historical session records. Windows mocks and separate three-agent fixtures were read back through the Langfuse CLI with zero model inference. Linux/macOS naming is unit-tested only. This does not migrate old sessions, rescore baselines or authorize paid execution. [Identity validation](../evals/analyses/telemetry-identity-20261025/README.md). |

## Owner override and source-audited C0 scoring (2026-10-26)

| ID | Decision | Evidence and limits |
|---|---|---|
| D106 | Explicit owner native-qualification override | `run-codex-baseline.ps1 -SkipNativeQualification` requires an explicit reason and records `waived-by-owner`; it does not claim qualification, weaken MXC containment, change model routing, or discard real exit/oracle failures. The owner authorized this for `claudex-001`, confirming it works on both harnesses. Default proof behavior remains unchanged when the switch is absent. |
| D107 | Source-reviewed validation anchors and parser corrections | Compaction proposals are not executed tools; exact native rejected patches remain failures with no successful writes. Phase hierarchy, UTC offsets, batched gate results and literal variable skill reads normalize source evidence symmetrically. Reviewed native coder-start/Done call IDs can supply missing task anchors while preserving H1/D27 commit selection, not arbitrary passing snapshots. Final C0 parity 97.46 supersedes provisional 98.62 after retaining T1's first-snapshot failure. Formula/weights unchanged. [Audited report](../evals/analyses/c0-claudex-001-win-20261026/codex/report.md). |

## Open items

| ID | Item |
|---|---|
| O2 | Mapping each harness's events into ATIF-v1.7 (D69): `steps[]` with `tool_calls`, `observation`, `metrics`, `subagent_trajectories` and `extra`. Goes to `/spec-research`. |
| O7 | Bounded Codex 0.164.0 rollout/descendant ingestion and C1 scoring now exist (D94-D95); general ATIF ingest remains open. Ingest-only runs. **Recommendation:** a per-harness, per-version adapter turns the native session file into ATIF. Imported runs are marked `provenance=imported` and store the SHA-256 of each raw file. Unknown record types fail softly, and a truncated last line is ignored. Usage comes from Codex's cumulative `token_count` events. Existing references: Harbor trajectory loading, `cc-transcript`, `toolpath-codex`. Goes to `/spec-research`. |
| O13 | Run limits. Requirements and their derivation are in [evals/baseline-runs.md](../evals/baseline-runs.md): <ul><li>three layers: hard wall-time ceiling, idle watchdog, native caps;</li><li>a process-tree kill on Windows;</li><li>a recorded `exit_reason`.</li></ul>Values are provisional until O14 lands. |
| O22 | Sandbox faults found by the mock agent (D83) and still open: <ul><li>`run-baseline.ps1` started from Git Bash picks up MSYS `tar`, which misreads `C:`.</li><li>`analyze-run.py`'s `model_calls` also counts subagent messages.</li></ul> The two temp faults are fixed by D84. |
| O14 | The owner's baseline runs. The procedure, expected outcomes and measures are in [evals/baseline-runs.md](../evals/baseline-runs.md). |
| O18 | MXC parity. **Done:** <ul><li>The OneDrive PowerShell config was renamed by the owner. In MXC pwsh now exits 0, and the effective policy is still `RemoteSigned` from LocalMachine.</li><li>`mxc-sandbox` gained `--env NAME[=VALUE]` (D73).</li><li>The geeky guard hook runs through `"shell": "powershell"` (D74).</li></ul> **Updated 2026-10-24:** the dedicated Codex sign-in was completed and two C1 runs are retained; no sign-in repetition is needed. Full paid-runtime guard parity remains open under D96. Historical probe details below retain their original date. |
| O19 | Pre-existing limitation found while testing D74: in warn mode the guard writes plain stdout and exits 0. For `PreToolUse`, Claude Code does not show that output to the model, so the warning never reaches Claude. The fix would be to emit `hookSpecificOutput.additionalContext` JSON. It doesn't affect scoring (D23). Plugin follow-up. |

## Verified harness facts (live probes, 2026-10-20; Claude Code 2.1.293, codex-cli 0.163.0)

| Fact | Consequence |
|---|---|
| The Claude `system/init` event lists `plugins`, `skills`, `agents`, `tools`, `mcp_servers`, `memory_paths` and `output_style`. Hook events from the user's global config come before it. | The D48 parity check and the D51 contamination check can both be read directly from `init`. |
| Claude reported an auth failure as `result.subtype = success` with `is_error = true`. | Parsers must check `is_error`. |
| The `codex exec --json` events (`thread.started`, `turn.*`, `item.*` with `command_execution`/`file_change`/`agent_message`/`error`, `turn.completed.usage`) carry **no timestamps**. | Timing comes from the Codex rollout session file, which timestamps every line and records cumulative `token_count` per model call. |
| The user's global Codex config injected `error` items: an MCP auth failure and an unrecognized setting. | This is evidence for D51 (use `CODEX_HOME` and `--ignore-user-config`). |
| A trivial prompt used about 149k input tokens in Codex (111k of them cached). | Fixed context overhead is large, so token ceilings must be calibrated from baselines (O14). |
| Inside the Codex `workspace-write` sandbox, `python --version` returned "No installed Python found!" | The adapter must make Python reachable in the sandbox. The challenges depend on it. |
| MXC shared mode: Claude authenticated and finished in 4 turns. `python` ran, and `Write` worked. Its `init` reported 47 plugins, 327 skills, 54 MCP servers and 393 tools. The trivial task processed about 260k tokens (206k of them cache reads). | Shared mode is not acceptable for eval runs (D51): use `--isolated`. |
| MXC isolated mode: `init` reported only the bundled `cc-plugin-*` plugins (3), 18 skills, 0 MCP servers, the default output style and private memory. Without `CLAUDE_CODE_OAUTH_TOKEN` it fails with "Not logged in". | D51 is met. Auth follows D71. |
| In MXC, the Bash tool failed with exit 66 because Git Bash can't start. The agent fell back to the PowerShell tool, which ran but returned exit 5 because of an unreadable host PowerShell profile config (OneDrive `Documents\PowerShell\powershell.config.json`). | The Claude contestant has no Bash: this is a capability note. The exit-5 noise could inflate validation attempts (D68), so it needs a fix (O18). |
| `python.exe` (3.13.15) starts inside MXC with or without `--allow-win32k`. | The challenges can run in MXC. |
| A hook declared with `"shell": "powershell"` **runs** inside MXC (`--allow-win32k`). The default Git Bash hook does not. The `mxc-sandbox` host passes only `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY` into the container, so env-based switches such as `CLAUDE_CODE_SHELL`, `CODEX_HOME` and `MCP_TIMEOUT` can't be set per run. | Hooks are possible in MXC through PowerShell, but only when declared per hook with `"shell": "powershell"`. The Claude binary rejects any `CLAUDE_CODE_SHELL` that is not a bash/zsh path, so no env switch routes hooks to PowerShell. Per-run env, which Codex's `CODEX_HOME` needs, requires an `--env` pass-through added to `mxc-sandbox` (O18). |
| `geeky_mcp` in MXC: a prebuilt offline venv (`mcp` 2.3.0) imports `server.py` in 2.7 s with `--allow-win32k`. Without it, the `cryptography` DLL load fails. Launched by Claude as a stdio MCP server, it **never connects**: <ul><li>through the venv redirector, `CONNECT_TIMEOUT` (30 s);</li><li>through the base interpreter with `PYTHONPATH`, `CONNECTION_CLOSED` (`pywintypes` missing, because `.pth` files aren't processed);</li><li>through the base interpreter with `site.addsitedir`, `CONNECT_TIMEOUT` (90 s, with `MCP_TIMEOUT` set via settings `env`).</li></ul> | Python stdio MCP servers start but never complete the MCP handshake in MXC. The untested hypothesis is `mcp`'s win32 stdio handle rebinding (via pywin32). |
| Native `codex.exe exec --json --sandbox danger-full-access` runs **inside MXC** (`--allow-win32k --rw ~/.codex`): Python ran, the file was written, the trace was complete, about 109k input tokens. Its user config still loads (unrecognized settings, under-development features). The container blocks `~/.agents/skills` (449 skills, all access denied). | Codex can share Claude's containment. Isolation needs `CODEX_HOME` (an env pass-through) or config flags (O18). |
| The PowerShell warning in MXC reads: "Cannot read the PowerShell configuration file '…OneDrive…\Documents\PowerShell\powershell.config.json': Access … is denied. Falling back to default settings." Claude's PowerShell tool turns it into exit 5; Codex's commands still exit 0. The file (dated 2023-05-18) holds only `{"Microsoft.PowerShell:ExecutionPolicy":"RemoteSigned"}`. Documents is redirected to OneDrive (Known Folder Move), and `LocalMachine` is already `RemoteSigned`. | Renaming the file leaves the effective execution policy unchanged and removes the warning everywhere. The owner performs this change (O18). |
| Codex discovers skills from `.agents/skills` (working directory up to the repo root) and `$HOME/.agents/skills`, not `~/.codex/skills`. `--full-auto` has been removed. | D48: provide skills through a run-scoped `HOME`, never inside the contestant repo (D47). Use `--sandbox workspace-write`. |
