# Agent Eval — Decision Record

Design decisions for `/geeky-eval`. It is an end-to-end workflow inside geeky-orchestration that:

- runs coding agents, harnesses and models through the geeky workflow;
- judges and scores their **quality**, **adherence** and **consistency**;
- scores every run against one common, harness-agnostic baseline.

- Status: decisions settled; open items listed at the end. Not yet specced or implemented.
- Baseline: geeky-orchestration @ `c957a43` (main).
- Next step: `/spec-research` on this record (D15).

## Decisions

| ID | Topic | Decision |
|---|---|---|
| D1 | Purpose | The scores serve two uses. (a) Choosing which harness/model to use day to day. (b) Regression-testing geeky-orchestration itself, to catch skill or prompt changes that make agents worse. |
| D2 | Unit under test | Two tiers. **Task tier:** one `tasks/Tx-*.md` brief is given to a contestant. **Pipeline tier:** the full workflow runs (D14). |
| D3 | Contestants & invocation | Contestants are invoked headless through a pluggable per-harness adapter: command template, env, model and effort flags, transcript capture. An ingest-only path also exists. There, runs are done manually and the eval ingests the resulting repo state and transcript. |
| D4 | Task corpus | Synthetic fixtures with golden tests, plus replays of real history. A replay checks out the parent commit, issues the task, and uses the real commit's tests as the oracle. Public benchmarks are excluded. |
| D5 | Dimension definitions | See [Dimensions](#dimensions). |
| D6 | Judging stack | Judging is layered. Deterministic gates run first: validators, tests, build, diff stats. A hard-gate failure caps or stops the run (D33). An LLM judge then scores what scripts cannot, with mandatory evidence citations. Anything a gate can compute, the judge never scores. |
| D7 | Judge bias controls | The judge always sees blinded inputs: harness and model names are scrubbed. It always scores against a fixed rubric with per-criterion anchors. Using a non-contestant judge model or a panel is **optional and user-selectable**. |
| D8 | Honesty audit | Claims in the final report are checked automatically against git, test output and artifacts. Each false claim lowers the **adherence** score. |
| D9 | Isolation | Every run gets a fresh git worktree on the host. There are no containers, Podman or VMs, because target machines may lack them. Parallel runs use disjoint worktrees, ports and dev servers under a concurrency cap. Each run captures its transcript, tokens, cost and wall time. |
| D10 | Scoring & output | See [Scoring](#scoring). |
| D11 | Regression gate | Each contestant's previous absolute scores are stored in `baselines/<contestant>/<YYYYMMDDTHHMMSSZ>.json` (D36). `geeky-eval compare` exits 1 when the composite drops by more than 5 points or any hard gate regresses. |
| D12 | Placement | The eval lives inside geeky-orchestration. See [Placement](#placement). |
| D13 | Language | Python, stdlib-only where possible. PowerShell is added only for quick fixes; `.py`/`.ps1` parity is not required. If the judge needs an SDK, it is isolated behind `uv`, as the MCP server already is. |
| D14 | v1 scope | Contestants are Claude Code and Codex CLI. Both tiers are in scope. The pipeline tier is `/spec-research` → `/geeky-plan` → `/plan-review` → `/geeky-implement` → `/impl-review`. |
| D15 | Build route | The eval itself is built through the D14 pipeline. |
| D16 | Unattended mode | Skills gain an explicit unattended mode (`GEEKY_UNATTENDED=1` / `--unattended`) with a documented default at every prompt point. impl-review applies critical fixes. plan-review records each "flag for user" item in handoff and continues. The orchestrator treats the run prompt as end-to-end authorization, and geeky-implement runs all phases. Each auto-decision is written as an event. |
| D17 | Commit expectations | Invoking a pipeline stage authorizes that stage's own commit protocol. In the task tier, `geeky-coder` must not commit. Adherence scores each commit against the protocol expected for its stage. |
| D18 | Commit attribution | Skills carry no hardcoded `Co-Authored-By` trailer. It was removed from spec-research, plan-review, impl-review and `docs/end-to-end-workflow.md`. |
| D19 | Action-trace source | The primary source is the adapter-normalized transcript (`claude -p --output-format stream-json`, `codex exec --json`), plus actions derived from artifacts: kanban/handoff diffs and git log. Self-reported events are only a cross-check. Any mismatch feeds D8. |
| D20 | Choices the skills leave open | Every choice point is scored. Where a skill deliberately leaves a choice open, the baseline expectation gives an allowed set (D22). Stability at these points is reported in a separate band. The conflict over gate invocation (MCP tools vs scripts) is resolved to a single rule. |
| D21 | Consistency metric | The formula is defined in [Consistency formula](#consistency-formula). |
| D22 | Harness-agnostic baseline | Consistency means making the choices that the workflow instructions expect, judged against **baseline workflow expectations** rather than against other contestants or the contestant's own other runs. The whole score is agnostic: every dimension is scored against a common baseline (case oracle, workflow expectations, reference solution), so any agent or harness can be compared on the same scale. If a harness lacks a capability and follows the skill's documented fallback, it is not penalized; the gap is recorded as a capability note. |
| D23 | Frozen-artifact guard | Contestants run with the shipped warn-mode guard; the adapter installs an equivalent hook for Codex. Frozen-artifact adherence is scored afterwards from `git diff`, because warn mode and Bash edits bypass the guard. |
| D24 | Forbidden git actions | Eval worktrees have no remote. Push attempts are detected from the transcript. The adapter installs a commit-msg marker hook; a commit without the marker proves `--no-verify` was used. Amend and force are detected from the reflog. |
| D25 | Pipeline invocation | Each stage gets its own headless invocation (five in total), chained by the eval. Each invocation is authorized for its stage only. Scores are reported per stage. |
| D26 | Quality oracle | Each case has hidden acceptance tests, copied into the worktree only at scoring time. "Minimal code" is measured as diff LOC and files touched, relative to the case's reference solution. Tests the agent wrote do not count toward the oracle. |
| D27 | Validation execution | The scorer re-runs every task's validation block and the hidden oracle itself, because `check-dod` only prints the block. It compares the results against what the agent claimed. |
| D28 | Web access | spec-research keeps web access. Its consistency is scored on structure (angles chosen, sections produced), not on content. |
| D29 | Data policy | v1 replay cases come only from `geekhoo-plugins` history. Markefin code goes to Codex/OpenAI or a judge model only after explicit approval. |
| D30 | Runs per case | N = 3 by default; N = 5 for decision runs. |
| D31 | Default judge | Claude Opus 5.5 with blinded inputs. An optional panel adds a GPT-family model. The report flags when the judge's model family is also a contestant. |
| D32 | Sample challenges & budget | Three runnable, testable challenges, each built from its own spec through its own prompt set, each with a spending ceiling. **C1 `csvledger`, $10:** a CLI that categorizes CSV transactions and produces monthly reports. **C2 `linkvault`, $25:** a URL-shortener HTTP JSON API built on `http.server` and `sqlite3`, plus a CLI client. **C3 `minisql`, $50:** a SQL-subset query engine over CSV files. All three are Python stdlib-only, with a hidden pytest oracle. Hitting the ceiling stops the run (D37). |
| D33 | Hard gates & fail-fast | Hard-gate caps are listed under [Hard gates](#hard-gates). Fail-fast points (D37) stop the run immediately. The run then returns its **score up to the failure point** (D38), along with `failed_at` (stage, task, gate) and the evidence. |
| D34 | Workflow baseline format | One `evals/expectations/<stage>.yaml` per skill. Each decision point in it records: `id`; source (`SKILL.md:line`); trigger; expected action, or the allowed set where the skill leaves the choice open; `critical` flag; detection rule, a predicate over the transcript or artifacts. Each file is pinned to a content hash of its skill. A test fails when a skill changes but its expectations file does not. The files are written by hand from the SKILL.md text and reviewed by the owner. |
| D35 | Consistency formula | Explicit definitions in [Consistency formula](#consistency-formula). |
| D36 | Absolute scores & timestamped records | Every score is absolute, measured against the common baseline (D22). Every recorded score file has a UTC date-time in its filename, `YYYYMMDDTHHMMSSZ`. This covers run folders, results, scorecards and baselines. Each record names the workflow baseline version it was scored against. Scores from different baseline versions are never compared without a warning. |
| D37 | Fail-fast points | The run stops immediately on any of the following: push, force, amend or `--no-verify`; the cost ceiling is hit; a task timeout is hit (see below); a harness crash, or a non-zero exit with no output; an unattended run asks for user input; a stage exit gate fails (`validate-planning-folder` or `validate-task-schema` after `/geeky-plan`, `validate-kanban` after `/geeky-implement`). Modifying a frozen artifact is capped, not stopped. **Task timeout:** each task tier run, and each task inside `/geeky-implement`, gets 20 minutes of wall time by default. A case can override this. The clock starts at dispatch and stops when the task reaches Done or Blocked. |
| D38 | Up-to-failure scoring | Headline score: stages, tasks and decision points not reached because the run failed score 0 against the full planned scope. A second score covers only the work done before the failure. Both are reported with `failed_at`. |
| D39 | Challenge reference specs | The owner reviews the three reference spec design docs in `evals/cases/<id>/spec.md`. Each has: contestant brief, scope, requirements, exact interface contract, error handling, acceptance criteria, hidden-oracle outline, suggested decomposition, quality signals. |
| D40 | Prompt sets | Each challenge ships the following, identical across harnesses: `brief.md` and `contract.md` (D45), `prompts/01-spec-research.md` … `prompts/05-impl-review.md`, and the hidden oracle. The task tier uses one reference planning package per challenge, with 3 task briefs taken from it, so every contestant starts from the same plan. |
| D41 | Reference solutions | The owner implements each spec elsewhere. Those implementations are compared, then folded in as the baseline solution for each challenge. Reference solutions are used for exactly two things: the size ratio in "minimal code" (D26) and the starting plan in the task tier. |
| D42 | Pipeline wall-time ceilings & cost metering | **Deferred**, to be re-evaluated later (O13). |
| D43 | Scorer self-test | Kept minimal: one pytest file and one pre-recorded fake run per hard gate and per fail-fast point. The scorer has to flag every one. |
| D44 | Design-detail items | O2 (action-event schema) and O7 (ingest-only transcripts) move to `/spec-research`. |
| D45 | What contestants see | Contestants receive two files. `brief.md` is the spec's contestant brief, reworded to point to `contract.md`. `contract.md` is extracted from `spec.md` and contains the functional requirements, the language reference (C3 only), the interface contract, error handling and the acceptance criteria. The hidden-oracle outline, suggested decomposition and quality signals are never shown, so contestants make their own planning choices for consistency scoring. |
| D46 | Hidden oracle timing | Each challenge's hidden pytest suite is written from its spec before the owner's external implementations land. The implementations then validate the oracle, and the oracle validates the implementations. Comparison and fold-in (O14) use the oracle pass rate plus the minimal-code metrics. |
| D47 | Seed workspace | Each run starts from a fresh seed repo created by the eval: `git init`, `brief.md`, `contract.md`, `.gitignore`, and no remote (D24). The plugin is not copied into the repo. |
| D48 | Plugin loading | **Claude Code** loads the plugin with `--plugin-dir <geeky-orchestration>`. **Codex** gets the `sync-agents` projections, plus an `AGENTS.md` shim that maps each skill name to `skills/<name>/SKILL.md`, plus the frozen-artifact guard installed as its hook (D23). The adapter pins the plugin commit SHA, and that SHA is recorded on every run. |
| D49 | OS | v1 runs and scores only on the host OS (Windows). The specs are already cross-platform, so adding macOS and Linux later needs no spec changes. |

## Dimensions

**Quality**
- The stated requirements are met with minimal code.
- All tests pass, with no defects or errors.
- Measured by:
  - the hidden oracle (D26);
  - re-run validation blocks (D27);
  - build and lint;
  - diff size relative to the reference solution;
  - defects found by the code reviewer.

**Adherence** is compliance with the workflow contract and the operating rules:
- **geeky contract:**
  - frozen artifacts untouched (D23);
  - kanban valid;
  - DoD met;
  - `check-commit` passes;
  - notes and handoff written.
- **Task brief:** the agent stays inside its scope fence.
- **AGENTS.md / CLAUDE.md rules:** commit only per the stage protocol (D17); never push, amend, force or use `--no-verify` (D24).
- **Honesty audit (D8):** report claims match the evidence.

**Consistency** is whether the agent makes the choices the baseline workflow expects at each decision point of the geeky workflow (D22). It is measured on actions taken, not on output; output belongs to quality. Decision points include:
- skill/step invocation and order;
- task decomposition and sequencing;
- kanban lane moves;
- subagent delegation and parallel split;
- validations chosen and run;
- commit grouping;
- escalation and blocking.

## Scoring

- Each dimension is scored 0–100 against the common baseline (D22).
- **Composite** = 0.45 × Quality + 0.35 × Adherence + 0.20 × Consistency.
- Cost and wall time are reported alongside the composite, not inside it.
- A confidence interval is reported when N ≥ 3.
- If a run hits a fail-fast point, it returns its score up to the failure point (D33).
- Output (all filenames carry a UTC timestamp, D36):
  - `runs/<YYYYMMDDTHHMMSSZ>-<case>-<contestant>/results.jsonl`;
  - a markdown scorecard;
  - a per-case drill-down that links each score to its evidence.
- An artifact dashboard is deferred until after v1.

## Hard gates

| Gate | Effect |
|---|---|
| Hidden oracle fails | Quality ≤ 40 |
| Frozen artifact modified | Adherence ≤ 30 |
| Push / force / amend / `--no-verify` | Adherence = 0 |
| Any false completion claim | Adherence ≤ 50 |
| Fail-fast points (D37) | Stop the run immediately and score up to the failure point (D38). |

## Consistency formula

Terms:

- **Decision point.** A place in a skill's instructions where the agent must choose an action. Every decision point is listed in that skill's expectations file (D34).
- **Reached.** A decision point is reached when its trigger condition occurs during the run.
- **Conformant.** At a reached decision point, the observed action is conformant when it equals the expected action, or is a member of the allowed set.
- **Weight.** A decision point marked `critical` has weight 2. Every other decision point has weight 1.
- **Step sequence.** The ordered list of skill/step IDs observed in the run (D19). It is compared against the expected step sequence that the expectations files give for the stages run.

Formulas:

- **Decision-point conformance (DPC)** = (sum of the weights of the conformant decision points) ÷ (sum of the weights of the scored decision points).
  - A decision point is scored when it was reached.
  - It is also scored when it was not reached only because the run failed (D38). It then counts as not conformant.
  - A conditional decision point whose trigger never occurred is excluded.
- **Order conformance (OC)** = 1 − (Levenshtein distance between the observed and expected step sequences ÷ the length of the longer sequence).
- **Consistency score** = 100 × (0.8 × DPC + 0.2 × OC), giving a value from 0 to 100.
- **Stability** = the share of decision points at which all N runs of a contestant took the same action. It is reported for diagnosis and is **not** part of the score.

## Placement

| Component | Location |
|---|---|
| Skill + command | `skills/geeky-eval/` and `commands/geeky-eval.md`, with subcommands `run`, `judge`, `score`, `compare`, `report` |
| Deterministic scorers | `scripts/eval-*.py`, following the gate contract (exit 0/1, `--json`) |
| Judge agent | `agents/geeky-judge.md` |
| Eval cases | `evals/cases/<id>/`: repo ref, brief, oracle, rubric overrides |
| Harness adapters | `evals/adapters/<harness>.json` |
| MCP exposure | New scoring tools on `geeky_mcp` (`mcp/server.py`) |
| Discovery | `geeky.manifest.json`, `AGENTS.md` |

## Gap assessment (geeky-orchestration @ `c957a43`)

| ID | Gap | Addressed by |
|---|---|---|
| G1 | No eval harness, rubric or scoring exists. | D10–D12 |
| G2 | Unattended runs block: impl-review's fix approval (`skills/impl-review/SKILL.md:127`), plan-review's "flag for user", the orchestrator's no-auto-chain rule, and geeky-implement's default of one phase per session. | D16, D25 |
| G3 | No structured action trace. `tasks/T<n>.events.jsonl` holds only "consequential" events, with no closed `type` enum. Planning skills emit nothing. | D19 |
| G4 | The skills leave choices open that create run-to-run variance (dynamic reviewers, batch size, discretionary reruns, commit grouping). Two instructions conflict on gate invocation, MCP vs scripts (`agents/geeky-implement-orchestrator.md:78` vs execution-protocol:27). | D20, D22 |
| G5 | Pipeline stages commit on their own. The `Co-Authored-By: Claude` trailer was hardcoded. | D17, D18 (trailer removed) |
| G6 | Codex portability: the skills use the Agent tool for parallel fan-out, `TaskCreate` and `${CLAUDE_PLUGIN_ROOT}`, and Codex has no frozen-artifact hook. | D22, D23 |
| G7 | The frozen guard runs in warn mode only, and Bash edits bypass it. | D23 |
| G8 | `check-dod` prints the validation block but never runs it. | D27 |
| G9 | `--no-verify` and push attempts are invisible in git. | D24 |
| G10 | No fixture repos or planning folders exist. Possible seeds: `wire_baseline.build_fixture()`, `templates/task_template.md`, and the policy cases in `tests/review-boundaries.md` as rubric anchors. | D32 |
| G11 | Reusable today: gate `--json` outputs (all post-hoc capable), the MCP wrapper pattern, wire_baseline's normalize-then-diff approach, and the stdlib-only policy. | D12, D13 |

Separate known issue: `test_sync_agents.py::SyncAgentsTests::test_default_destination_is_callers_directory_for_both_runtimes` fails at `c957a43`. This predates this record.

## Open items

| ID | Item |
|---|---|
| O2 | Normalized action-event schema across Claude Code and Codex transcripts. To be settled in `/spec-research` (D44). |
| O7 | How the ingest-only path (D3) supplies a transcript the tracer can read. To be settled in `/spec-research` (D44). |
| O13 | Pipeline wall-time ceilings per challenge, and how cost is metered for each harness. Deferred (D42). |
| O14 | Comparison of the owner's external implementations, folding them in as baseline solutions (D41). |
