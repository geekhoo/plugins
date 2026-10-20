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
| D47 | Seed workspace | Each run starts from a fresh seed repo created by the eval, outside every repository: `git init`, `brief.md`, `contract.md`, `.gitignore`, no remote. The plugin is not copied into it. |
| D48 | Equivalent plugin access | The adapter exports the plugin at a pinned SHA (D50). Both harnesses get **equivalent context and access** to the full export: skills with their references, agents, templates, scripts, hooks and the `geeky_mcp` server. **Claude Code** loads it with `--plugin-dir`. **Codex** gets the same material through the plugin's cross-harness mechanisms: `sync-agents` projections, the plugin's `AGENTS.md`, skill discovery, the guard hook (D23), and `geeky_mcp` registered in its config. A parity pre-flight lists everything each harness can reach. It fails the run if Codex lacks anything Claude Code has. The plugin SHA is recorded on every run. |
| D50 | Oracle leak prevention | The adapter exports the plugin with `git archive` at the pinned SHA, excluding `evals/`, into a temp directory outside every repo. Contestants load only that export. The seed workspace, oracle and run records live where the contestant cannot reach them. A pre-flight check fails the run if any `oracle_*.py` or `spec.md` is reachable from the contestant's workspace or plugin path. |
| D51 | Clean harness config | Each harness runs under an isolated config profile kept in `evals/adapters/<harness>/profile/`. Claude Code runs under its own `CLAUDE_CONFIG_DIR`: the plugin export only, default output style, no user `CLAUDE.md`, no memory, no other plugins or hooks. Codex runs under its own `CODEX_HOME` containing only the D48 shim. The profile hash is recorded on every run. |
| D52 | Unattended safety | Each harness's own sandbox limits writes to the run's worktree: Codex `--sandbox workspace-write`; Claude Code with sandboxing enabled and a permission allowlist instead of bypassing permissions. Network is allowed only in the spec-research stage. A later hardening step runs contestants under a dedicated low-privilege Windows user with no git credentials. Any file written outside the worktree is a fail-fast event (D37). |
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
| D67 | Tasks: implementation scored, creation not | The agent creates its tasks in `geeky-plan` however it judges best. How it decomposes the work is not scored. Task creation counts only toward the `geeky-plan` stage: whether the planning produced the artifacts that workflow requires. **Task tier:** each task the agent created gets a 0–100 implementation score from three checks: its re-run validation block (D27), its DoD gate, and its task-review verdict. The **task-tier score** is the mean of the per-task scores, normalized across tasks so the number of tasks has no effect on scale. Per-task scores are kept in the breakdown. Component weights and where this score sits in the composite: O16. |
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
| D30 | Runs per case | N = 3 by default, configurable per campaign. |
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
- **Composite** = 0.45 × Quality + 0.35 × Adherence + 0.20 × Consistency.
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
| O2 | Normalized action-event schema across Claude Code and Codex transcripts. Goes to `/spec-research`. |
| O7 | How the ingest-only path supplies a transcript the tracer can read. Goes to `/spec-research`. |
| O13 | Pipeline wall-time ceilings per challenge. Deferred. |
| O16 | Task-tier scoring details (D67): per-task component weights, mean weighting, and placement in the composite. |
| O14 | The owner runs the external baseline implementations and records each run's transcript and total tokens. They are then compared and folded in as baseline solutions, and the token ceilings (D53) are adjusted from them. |
