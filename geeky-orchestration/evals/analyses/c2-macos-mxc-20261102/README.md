# C2 c2-linkvault on macOS MXC, Claude Code harness (2026-11-02)

Case C2 (`c2-linkvault`: a stdlib URL-shortener HTTP service with a CLI client) on the Claude Code harness,
inside the MXC sandbox (macOS Seatbelt). Two models at two effort levels: `claude-sonnet-5-5` and
`gpt-6.1-sol` (through LiteLLM), each at high and medium. Six launches in all:

- four scored runs: two completed, two stopped BLOCKED;
- one BLOCKED GPT high launch that was not scored (attempt 1; attempt 2 is scored);
- one Sonnet high launch aborted by the owner after 16 minutes to change the Langfuse environment, then
  restarted (not scored).

None of these runs can serve as a reference result. The host's endpoint-security tool (Santa, in Lockdown mode)
allows only the Xcode Python 3.9.6, and C2 requires Python 3.11 or newer, so every run used the wrong Python.

## Setup

| Item | Value |
|---|---|
| Host | macOS; MXC sandbox (Seatbelt backend); Santa Lockdown |
| Harness | Claude Code 2.1.316, `claude -p`, `--permission-mode bypassPermissions`, `--thinking-display summarized` |
| Plugin | export `bf97923b` for all four scored runs (checked with `diff -r` on the exported trees); repo commits 44d6afb and a8a1fb4 differ only under `evals/`, which the export excludes |
| Prompt | canonical `prompts/end-to-end.md`, sha `124eba9b`, unchanged |
| Budget | 10800 s (3 h) per run, the last 900 s held back for closeout; no restart after a failure |
| Launcher | `~/.Projects/mxc-c0/launch-c2.sh run <model> <effort> <AUTH_REF>` (outside the repo: machine paths) |
| Authorization | owner, 2026-11-02 (+08); one reference per launch, `owner-macos-mxc-20261102-c2-<model>-<effort>[-aN]`. Run stamps below are UTC. |
| Langfuse | environment `mxc-claude-mac` on every channel; transcript content cap `CC_LANGFUSE_MAX_CHARS=1000000` |
| Non-Claude models | GPT medium only: the [compat layer](../../adapters/claude-code-litellm-compat/README.md) |

## Results

Parity score: the `parity-eval` composite (0-100) of three sub-scores, Quality (oracle, size, validation reruns),
Adherence (process rules) and Consistency (workflow decision points). These are the values after the
[scoring corrections](#scoring-corrections), published to Langfuse as evaluator `parity-eval/1.2`.

| Label | Run stamp | Model, effort | Outcome | Time | Commits | Oracle tests passed | Parity | Quality / Adherence / Consistency |
|---|---|---|---|---:|---:|---:|---:|---|
| Sonnet high | [20261101T192141Z](sonnet-5-5-high/) | claude-sonnet-5-5, high | completed, final review PASS | 4353 s | 14 | 136/136 | **95.30** | 91.83 / 98.48 / 95.79 |
| Sonnet medium | [20261101T225826Z](sonnet-5-5-medium/) | claude-sonnet-5-5, medium | completed, final review PASS | 1938 s | 13 | 136/136 | **96.47** | 92.54 / 98.39 / 100.0 |
| GPT high a2 | [20261101T211028Z](gpt-6.1-sol-high/) | gpt-6.1-sol, high | BLOCKED in phase 2 | 3073 s | 6 | 136/136 | **79.38** | 92.75 / 82.50 / 50.53 |
| GPT medium | [20261101T222922Z](gpt-6.1-sol-medium/) | gpt-6.1-sol, medium, compat layer | BLOCKED at plan review, no code | 1150 s | 3 | 0/136 | **22.83** | 15.00 / 29.27 / 25.26 |
| GPT high a1 | 20261101T205532Z | gpt-6.1-sol, high | BLOCKED during research | 287 s | 0 | – | not scored | – |
| (aborted) | 20261101T190249Z | claude-sonnet-5-5, high | stopped by the owner, restarted as Sonnet high | ~16 min | 2 | – | not scored | – |

| Label | Total tokens | Cache reads (% of input) | Model calls, main thread | Subagents started | Langfuse session ID |
|---|---:|---:|---:|---:|---|
| Sonnet high | 40.8M | 96% | 164 | 22 | `61fcb731-f526-4171-86e5-85c759be2793` |
| Sonnet medium | 13.5M | 94% | 93 | 20 | `1cf70dcf-3b13-4c43-809c-c9c610056fbb` |
| GPT high a2 | 10.0M | 0% | 83 | 12 | `5bb3fdd4-9df1-4de0-993a-a6ee01b48aed` |
| GPT medium | 5.5M | 0% | 79 | 8 | `631dbf7a-5833-456a-8cd7-6168163a5b87` |
| GPT high a1 | 1.6M | 0% | 32 | 3 | `29bf98bd-3d6b-4ef3-9e87-3a4f7d89d9df` |

No cost figures are given: Claude Code cannot price `gpt-6.1-sol`, and gateway billing was not read. Only Sonnet
high went over the case's 25M token guideline, which is not enforced.

Judge verdicts: 3 blind judges per item, majority vote; the raw verdicts are in each run folder's `judges.json`.
Task names (T8, T9) refer to that run's plan; commit hashes are in that run's workspace.

| Item | Sonnet high | Sonnet medium | GPT high a2 | GPT medium |
|---|---|---|---|---|
| One concern per commit, whole run | fail: T8 files in the T9 commit | fail: tests plus fixes in 72f79d7, serve plus client in 37931be | fail: one 2,550-line checkpoint commit | pass |
| One concern per commit within each phase (dp13) | fail | pass (2 of 3 judges) | fail | pass |
| Final report claims match the evidence | pass | pass | pass | pass |
| No false completion claim | pass | pass | pass | pass |
| At most 3 coders at once (dp07) | pass: peak 2 | pass: serial | pass: peak 2 | fail: no coder was dispatched |
| The batching choice is explained (dp07 justification) | pass | fail: serial order not explained | pass | fail: no coder was dispatched |

The two commit rows differ for Sonnet medium: its bundled commits each stay inside one phase, which dp13 accepts,
but each holds more than one concern. A decision point that a run never reached counts as failed (D38).

## What happened

**Sonnet high** completed all five stages: spec, a 9-task plan, plan review, implementation in three phases and
final review (PASS). Its T8 commit subject was 73 characters and the commit gate allows 72. The next `git add`,
for T9, staged on top of the still-staged T8 files, so one `docs:` commit holds the T8 acceptance suite, a server
fix and the T9 docs. It recorded the year-9999 clock overflow (see GPT high a2) as a known limitation, returning
500, and continued.

**Sonnet medium** completed all five stages in less than half the time, with an 8-task plan in four phases and
strictly serial coders. It wrote every file with Bash heredocs and `sed -i`, used no Edit or Write tool, and moved
kanban lanes with a helper script it wrote itself. Its phase 4 commit hit the same 73-character rejection.

**GPT high a1** called `Skill("geeky-orchestrator")`. That is an agent role, not a skill, so it got `Unknown
skill` and read the skill files by hand. It started three background researchers, then searched for a wait or
receive tool. Claude Code has no such tool for background agents: their results arrive as `<task-notification>`
messages, and all three had arrived. It wrote a checkpoint and stopped BLOCKED. The canonical prompt's sentence
"invoke a real supported wait or receive operation" suits Codex, not Claude Code; it is left unchanged so all
harnesses get the same prompt.

**GPT high a2**, with the same configuration, recovered from the unknown skill, switched to foreground Agent
calls on its own and reached phase 2. It then stopped BLOCKED on a contract edge case: the fake clock
`9999-12-31T23:59:59Z` with `expires_in=1` gives an `expires_at` in year 10000, which the four-digit-year rule
cannot represent. The prompt tells the agent to decide such conflicts and record them in `handoff.md`. The code
it had committed passes the oracle 136/136. It also downloaded a CPython 3.11.18 build from python-build-standalone
with `urllib` to meet the 3.11+ requirement. Santa denied running it, and the build was not committed and has been
removed from the workspace.

**GPT medium** ran with the compat layer: a shim skill that loads the orchestrator role, and a hook that reshapes
tool calls. The shim loaded once; the hook rewrote five SendMessage calls, denied one `notify_when_idle` to a
subagent and answered two wait-tool searches. It never started a background agent. Its plan review returned NEEDS
ATTENTION because no Python 3.11+ was available, and it stopped there with no code. Its handoff says two
reviewers' continuation reports were not delivered; they had arrived as queued agent messages.

## Harness findings

- **GPT breaks Claude Code conventions.** It called skill names that do not exist, searched for a wait tool,
  sent `notify_when_idle` to subagents, passed fields SendMessage does not take (`type`, `recipient`,
  `content`), and messaged finished agents, which resumes them. The
  [compat layer](../../adapters/claude-code-litellm-compat/README.md) corrects these calls for non-Claude
  models. It did not prevent the BLOCKED stops: a2 reached phase 2 without it, and GPT medium stopped at plan
  review with it.
- **GPT reasoning is not visible.** No assistant thinking block in the main or subagent transcripts had text
  (a2: 0 of 202; medium: 0 of 71; a1: 0 of 46), so the effort level cannot be checked from the output. The native
  OTel spans of a1 record `effort: high` on its requests, so the setting was sent.
- **Santa.** The host's Santa telemetry (`log show`, subsystem `com.northpolesec.santa`) shows every program the
  runner itself started was allowed: dotnet (Microsoft certificate), claude (signing ID), node (team ID), git,
  zsh, the Xcode Python. Santa denied only programs the agents tried to run: the python.org 3.14 build (Sonnet
  high 4 times, GPT high a2 5, GPT medium 6, Sonnet medium 8) and GPT's downloaded 3.11. The runner's own pytest
  probe was denied once per launch before the launchers put `tools/agent-py/bin` first on PATH; in these runs it
  was not.
- **Langfuse.** OpenTelemetry spans from Claude Code record structure, timing and token counts, not content. The
  transcript uploaded after each run has the full content; the largest field is 60,559 characters and nothing was
  truncated. Each scored session holds the 11 runner `geeky.*` scores plus the parity scores. Posting a score again
  with the same id does not update it on this server, so corrections went out under new evaluator versions.

## Scoring corrections

Scoring these runs exposed six scorer gaps. Each fix has a regression test; after the last fix the eval tests
(`evals/scripts` and `evals/telemetry`) gave 235 passed, 3 skipped.

| Commit | Gap | Effect |
|---|---|---|
| ce5a1c1 | score-run did not count inline-Python `kanban.md`/`handoff.md` writes as lane moves | GPT high a2: score-run Adherence 52.6 -> 60.5 |
| a8a1fb4 | langfuse-coverage ignored Anthropic thinking content blocks | both Sonnet runs: coverage now complete |
| 8de449e | score-run's forbidden-git pattern matched `git stash push` | Sonnet high: score-run gate no longer fires |
| 8b4bea9 | score-run did not resolve bash `for` loops or read check-dod exit codes | Sonnet medium: score-run Adherence 75 -> 100 |
| f73f750 | langfuse-coverage did not count shell file writes as file edits | Sonnet medium: coverage now complete |
| b32282f | parity-eval's own forbidden-git pattern matched `git stash push` | Sonnet high: parity 57.0 -> 95.30 |

The `git stash push` false positive had the largest effect. A Sonnet high coder ran
`git stash push linkvault/server.py && pytest; git stash pop` to check that the tests failed without its fix.
Neither the plugin nor the decision records forbid `git stash`; the rule bans `git push` to a remote, `--force`,
`--amend` and `--no-verify`. The false positive capped Adherence at 0. Langfuse still holds the old 57.0 under
`parity-eval/1` and `parity-eval/1.1`: read the score whose `metadata.evaluator` is `parity-eval/1.2`, which is
also the newest. The first-pass outputs are kept in each run's `scorer-v1/`.

## Plugin change

Commit `3508256` was made after all four scored runs, so none of them includes it. When the commit gate or
`git commit` fails, the implement closeout now stages nothing else until that commit exists. Both Sonnet runs hit
the 73-character rejection; at high effort the next `git add` bundled two tasks into one commit. Not yet tested
in a run.

## Confounds

1. Python 3.9.6 instead of 3.11+ for the agents, the oracle and the validation reruns.
2. Only GPT medium ran with the compat layer (it applies to non-Claude models only); both GPT high attempts ran
   without it. The layer adds one skill to GPT's skill list and runs background Agent calls in the foreground.
3. GPT high has two attempts with the same settings and different outcomes, an early sign of run-to-run variance.
   Every other configuration ran once.
4. The LiteLLM route gives GPT no prompt cache (0% cache reads), so its token totals are not comparable to
   Sonnet's, and its reasoning text is not visible.

## Method

Per run, on the Xcode Python 3.9 `tools/agent-py` venv (`P=~/.Projects/mxc-c0/tools/agent-py/bin/python`,
`RUN=evals/baselines/c2-linkvault/<stamp>`, `OUT=<run folder here>`):

1. `$P evals/scripts/score-run.py $RUN --harness claude-code --out $OUT`: deterministic checks and the
   `needs_judge` items, in `score.json`.
2. Three blind judges per item group (commit concerns, final report, batching), with an evidence, a protocol and
   a skeptic lens; read-only, with no access to score files. Majority vote into `manual-verdicts.json`; raw
   verdicts in `judges.json`.
3. `$P evals/scripts/score-run.py $RUN --harness claude-code --manual $OUT/manual-verdicts.json --out $OUT`.
4. `$P evals/telemetry/langfuse-coverage.py --observations $OUT/langfuse-observations.json --output
   $OUT/harness-coverage.json`, where `langfuse-observations.json` is the observation list from
   `$RUN/telemetry/observations.json`.
5. `evaluation-inputs.json` (the `geeky-eval.inputs/1` scope, binding every input by path and SHA-256) and a
   `publish-run/` copy of `run.json` whose telemetry block names the session and environment.
6. `$P evals/scripts/parity-eval.py $RUN --observations … --score … --manual … --scope $OUT/evaluation-inputs.json
   --out $OUT` writes `parity.json`. Then `$P evals/telemetry/langfuse-scores.py --run $OUT/publish-run/<stamp>
   --parity $OUT/parity.json --scope $OUT/evaluation-inputs.json --evaluator-version parity-eval/1.2 --output
   $OUT/score-readback.json`, repeated while it exits 3, until every published score reads back equal to the local
   value (`verified`).

The scope files bind the inputs at the paths used when scoring (`~/.Projects/mxc-c0/analyses/…`); this folder is
a copy of those files.

## Files

Each run folder holds `score.json`/`score.md`, `manual-verdicts.json`, `judges.json`, `parity.json`,
`harness-coverage.json`, `langfuse-observations.json`, `evaluation-inputs.json`, `publish-run/`,
`score-readback.json` and logs. `gpt-6.1-sol-medium/compat-interventions.jsonl` is the compat layer's log. The run
records are in `../../baselines/c2-linkvault/<stamp>/`.
