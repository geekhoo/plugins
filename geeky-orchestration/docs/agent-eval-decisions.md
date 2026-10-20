# Agent Eval — Decision Record

Design decisions for `/geeky-eval`. It is an end-to-end workflow inside geeky-orchestration that:

- runs coding agents (one harness + model per contestant) through the geeky workflow;
- judges and scores their **quality**, **adherence** and **consistency**;
- scores every run against one common, deterministic baseline.

It reports scores and their breakdown. It does not rank contestants as winners or losers.

- Status: decisions settled except the open items at the end. Specced challenge kits are committed; the eval tooling is not yet built.
- Baseline: geeky-orchestration @ `c957a43` (main).
- Next step: `/spec-research` on this record (D15).

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
| D8 | Honesty audit | Claims in the final report are checked automatically against git, test output and artifacts. Each false claim lowers the **adherence** score. |
| D19 | Action-trace source | The primary source is the adapter-normalized transcript (`claude -p --output-format stream-json`, `codex exec --json`). Actions are also derived from artifacts: kanban and handoff diffs, and git log. Self-reported events are only a cross-check, and any mismatch feeds D8. |
| D26 | Quality oracle | Hidden acceptance tests are copied in only at scoring time. Tests written by the agent do not count toward the oracle. |
| D27 | Validation execution | The scorer re-runs every task's validation block and the hidden oracle itself, then compares the results with what the agent claimed. |
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
| D53 | Cost = tokens | Cost is measured only as **total tokens**: input (including cached) plus output, as each harness reports them. How the harness is billed is ignored. Provisional token ceilings per run are best-case values set now: **C1 10M, C2 25M, C3 50M**, held in each `case.json`. They are recalibrated to 2× the baseline implementation run's tokens once O14 lands. **Token efficiency** = min(100, 100 × baseline tokens ÷ run tokens). It is reported in the breakdown, not in the composite. |
| D58 | Scores bound to their evidence | Each dimension is scored only from its own evidence across everything the run did. There are no stage weights and no roll-up across stages. Per-stage figures appear only as breakdown. |
| D59 | Simple quality metrics | Quality uses three key metrics; see [Scoring](#scoring). Until reference solutions land, size is measured against the LOC band in each spec's Quality signals section. |
| D60 | Normalized scores, no ranking | Each run reports a normalized 0–100 composite with the full breakdown: each dimension and each metric inside it, plus token efficiency and wall time. When N > 1, the mean and min–max are reported. There are no winners, losers or significance tests. |
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
| Any false completion claim | Adherence ≤ 50 |
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

**Stability** is the share of decision points where all N runs of a contestant took the same action. It is reported for diagnosis and is not part of the score.

## Task-tier formula

All inputs come from the normalized trace (D19) and the task's artifacts.

**Per task `i`** (each part is 0–1):

| Part | Weight | Definition |
|---|---|---|
| **V** — validation attempts | 0.40 | `a` = the number of times the agent ran the task's validation block (or any of its commands), counted from the task's first code edit up to the first fully passing run. V = max(0, 1 − 0.25 × (a − 1)), so 1 attempt scores 1.0, 2 score 0.75, 3 score 0.5 and 4 score 0.25. V = 0 if the block never passes, including when the scorer's re-run fails (D27). |
| **R** — review rounds | 0.30 | `r` = the number of task-review rounds until PASS. R = 1 for `r` = 1 (first try), 0.5 for `r` = 2, and 0 for `r` ≥ 3 or if the task never passes review. |
| **T** — latency-normalized duration | 0.20 | `d` = wall time from the task's dispatch (In Progress) to Done. The adjusted time is `d_adj` = d × (L_ref ÷ L_run), where `L_run` is the run's median model-response latency per turn and `L_ref` is a fixed reference latency per harness, stored in its adapter. This removes slow-API effects. T = max(0, 1 − d_adj ÷ task timeout) (D37, 20 min by default). |
| **D** — DoD gate | 0.10 | 1 if `check-dod` passes for the task, else 0. |

Per-task score: s_i = 100 × (0.40 V + 0.30 R + 0.20 T + 0.10 D).

**Combining tasks:** the task-tier score is Σ w_i × s_i, with w_i = 0.5 × (LOC_i ÷ Σ LOC) + 0.5 × (a_i ÷ Σ a), where:

- `LOC_i` is the task's non-test lines changed;
- `a_i` is the task's validation attempts.

The weights sum to 1, so the score stays 0–100 however many tasks there are. Larger tasks, and tasks that took more attempts, count for more, so padding the plan with trivial tasks cannot raise the score.

## Placement

| Component | Location |
|---|---|
| Skill + command | `skills/geeky-eval/`, `commands/geeky-eval.md`, with subcommands `run`, `judge`, `score`, `compare`, `report` |
| Deterministic scorers | `scripts/eval-*.py`, following the gate contract (exit 0/1, `--json`) |
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

## Open items

| ID | Item |
|---|---|
| O2 | Mapping each harness's events into ATIF-v1.7 (D69): `steps[]` with `tool_calls`, `observation`, `metrics`, `subagent_trajectories` and `extra`. Goes to `/spec-research`. |
| O7 | Ingest-only runs. **Recommendation:** a per-harness, per-version adapter turns the native session file into ATIF. Imported runs are marked `provenance=imported` and store the SHA-256 of each raw file. Unknown record types fail softly, and a truncated last line is ignored. Usage comes from Codex's cumulative `token_count` events. Existing references: Harbor trajectory loading, `cc-transcript`, `toolpath-codex`. Goes to `/spec-research`. |
| O13 | Run limits. Requirements and their derivation are in [evals/baseline-runs.md](../evals/baseline-runs.md): <ul><li>three layers: hard wall-time ceiling, idle watchdog, native caps;</li><li>a process-tree kill on Windows;</li><li>a recorded `exit_reason`.</li></ul>Values are provisional until O14 lands. |
| O14 | The owner's baseline runs. The procedure, expected outcomes and measures are in [evals/baseline-runs.md](../evals/baseline-runs.md). |
| O18 | MXC parity. **Done:** <ul><li>The OneDrive PowerShell config was renamed by the owner. In MXC pwsh now exits 0, and the effective policy is still `RemoteSigned` from LocalMachine.</li><li>`mxc-sandbox` gained `--env NAME[=VALUE]` (D73).</li><li>The geeky guard hook runs through `"shell": "powershell"` (D74).</li></ul> **Open:** <ul><li>The owner signs Codex in once with `CODEX_HOME=C:\repos\.eval-tools\codex-home` (`codex login`).</li></ul> |
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
