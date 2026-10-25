# Eval Runs: Lessons Learned

Final-pair lesson: [automatic extraction](analyses/c1-final-parity-20261024/README.md) now replaces run-2 process annotations for supported shapes. Reject ambiguous task/commit/review mappings, do not count JS/poll wrappers twice, and fail strict scoring when withholding a composite. A pre-override untrusted hook catalog does not establish an untrusted launch.

Measurement lessons: distinguish skill prereads from execution boundaries; merge nested worker ownership; count repeated reviews and polled outcomes; reject documentation-HEAD fallback; reuse exact task-commit validation once. Complete metric coverage does not prove hook execution or model superiority. See D94-D98 and the checkpoint 5 question-by-question disposition.

> Current Codex reference (2026-10-24): [checkpoint 5 closeout](codex-c1-checkpoint5.md). Both C1 runs completed and the saved-trace repair yields 96.3/98.0; original scores remain historical. The frozen six-Claude replay supplements the complete four-run proof. Historical cleanup instructions do not apply to these preserved records. No further paid run is authorized.

This page records what it took to run paid geeky-orchestration evals in the MXC sandbox, first on Windows (C1) and since 2026-10-24 on Linux through LiteLLM (C0): what broke, how each break was fixed, the traps that cost a run, and what is still open. Read it before a new case, a new harness or a new machine. [baseline-runs.md](baseline-runs.md) is the step-by-step procedure, and [agent-eval-decisions.md](../docs/agent-eval-decisions.md) holds the decisions (D-numbers below). This file covers what those two leave out: the reasons, the traps and the order things went wrong.

Written 2026-10-23, after six paid C1 runs on Windows 11 (Claude Code 2.1.304, `claude-sonnet-5-5`); the Linux/LiteLLM sections were added 2026-10-24/25 (Ubuntu 24.04, Claude Code 2.1.310, Codex 0.164.0). The current step-by-step for Linux + LiteLLM + Langfuse is [mxc-litellm-runbook.md](mxc-litellm-runbook.md); the one-page version is [QUICKSTART.md](QUICKSTART.md).

## Where things live

| What | Path |
|---|---|
| Runner | `evals/scripts/run-baseline.ps1` |
| Analyzer (tokens, timings, gate counts) | `evals/scripts/analyze-run.py` |
| Scorer (QACT) | `evals/scripts/score-run.py` |
| Mock agent and dry run | `evals/mock-agent/mock_claude.py`, `evals/mock-agent/dry-run.ps1` |
| Cases and oracles | `evals/cases/<case>/` (`c0-wordstat` harness smoke test, `c1-csvledger`, `c2-linkvault`, `c3-minisql`) |
| Stored runs | `evals/baselines/<case>/<UTC stamp>/` |
| Invalid runs kept as evidence | `evals/baselines/archive/` |
| Scorecard | `evals/baselines/c1-csvledger/comparison-20261022T0800Z.md` |
| Tools the sandbox uses | `C:\repos\.eval-tools\agent-py` (venv with pytest), `C:\repos\.eval-tools\geeky-mcp` |
| Run workspaces | `C:\repos\eval-<case>-<stamp>` |
| Per-run config (plugin export, temp) | `C:\repos\.eval-cfg-<stamp>` |
| Claude session transcripts from MXC | `%USERPROFILE%\.mxc-sandbox\home\projects\<workspace slug>\` |

## One-time machine setup

These steps happen outside the repo. Check each one on a new machine before spending money.

1. **Claude token.** Run `claude setup-token` and store the result as the User environment variable `CLAUDE_CODE_OAUTH_TOKEN`. Never print it or pass it on a command line. To check it exists without reading it: `[bool][Environment]::GetEnvironmentVariable('CLAUDE_CODE_OAUTH_TOKEN','User')`.
2. **Sandbox Python with pytest.** The Python inside MXC has no pytest, and `pip` can't install inside the sandbox. Build the venv on the host instead: `uv venv C:\repos\.eval-tools\agent-py`, then `uv pip install --offline pytest` into it. The runner puts `agent-py\Scripts` first on PATH inside the sandbox.
3. **MCP server venv.** `C:\repos\.eval-tools\geeky-mcp` holds the `mcp` package for the plugin's `geeky_mcp` server. The runner writes an `mcp.json` that boots `mcp/server.py` from the plugin export through this venv.
4. **OneDrive PowerShell config.** A `powershell.config.json` under OneDrive Documents printed a warning on every `pwsh` start, and that warning polluted tool output. The fix was renaming the file. That is a user-owned settings change, so leave it to the machine owner.
5. **Loopback for asyncio.** The MCP server needs `--host-loopback` (mxc#1505), and that needs Windows update KB5127648.

## MXC sandbox: what breaks and the fix in place

Every item below cost at least one failed run or probe. All the fixes now live in `run-baseline.ps1`, and `dry-run.ps1` mirrors its environment.

| Symptom | Cause | Fix in the runner |
|---|---|---|
| Every Bash tool call fails with exit 66. One spec write silently did nothing. | Git Bash cannot start in MXC (microsoft/mxc#1061). | `--disallowedTools Bash`, so the agent goes straight to PowerShell. |
| Plugin hooks never fire. | Hooks default to bash. | Hooks declare `"shell": "powershell"`. |
| Skills don't load. | A read-only grant on the plugin folder breaks Claude's scandir. | The plugin is exported per run and granted read-write. A hash checks it wasn't edited. |
| Every PowerShell tool call reports "Exit code 5", even on success. | Claude's Windows shell launcher inside MXC. | `CLAUDE_CODE_DISABLE_WINDOWS_SHELL_LAUNCHER=1` (D81). |
| `pytest` missing, `pip install` fails. | Sandbox Python has no pytest; the sandbox's temp folder isn't writable. | The `agent-py` venv first on PATH, plus `VIRTUAL_ENV`. |
| Agents commit as "Claude", or commits fail for lack of an identity. | The seed repo has no git identity. | `GIT_AUTHOR_*` and `GIT_COMMITTER_*` set to `geeky-eval-agent <agent@geeky-eval.local>`. |
| git refuses with "dubious ownership". | The workspace is owned by another identity inside the container. | `GIT_CONFIG_COUNT/KEY_0/VALUE_0` sets `safe.directory` for the workspace only. |
| Warnings on every git command. | The host `~/.config/git` can't be read inside the container. | `XDG_CONFIG_HOME` set to the per-run config folder. |
| `mkdtemp`, pytest `tmp_path` and git temp repos fail. | MXC forces TEMP/TMP to the AppContainer's `AC\Temp`, which those can't write to. | `TMPDIR` set to a per-run read-write folder (D84). |
| The MCP server hangs on start. | Asyncio needs loopback. | `--host-loopback`. |
| The run was cut off at 19 minutes; the main agent's last turn said "the implementation run is in the background". | `claude -p` stops background subagents 10 minutes after the main agent's last turn. | `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` (D85). The runner records such runs as `exit_reason = bg_killed`. |
| A clean run was flagged "plugin modified" and lost reference eligibility. | Python wrote `scripts/__pycache__/*.pyc` into the read-write export. | `PYTHONDONTWRITEBYTECODE=1`, and the tamper hash ignores `__pycache__` (D93). |
| The scorer couldn't see half of a run. | Subagents launched by a subagent appear only in the session's `subagents/agent-<id>.jsonl`, not in `stream.jsonl`. | The runner copies `subagents/` into the run folder (D93). |

## Claude Code headless traps

- **A command shadows a skill.** A `commands/geeky-implement.md` wrapper made invoking the skill load the command instead of `SKILL.md`. The `commands/` folder was removed (D78). Don't add same-named commands.
- **Usage repeats in stream-json.** It reports a turn's `usage` once per content block, so naive sums double count. Count each `message.id` once. The run total in the final `result` event (`modelUsage`) is the reliable number.
- **Background agent results are placeholders.** An async Agent call returns "Async agent launched" at once. The real result arrives later as a notification turn, so result-size stats from tool results mean nothing.
- **Delegation is legal and changes the trace.** In run 6 the main agent handed all of `geeky-implement` to the plugin's `geeky-implement-orchestrator` subagent. That cut main-thread cost sharply. But the coders and reviewers it started appear only in `subagents/`. Score from the merged trace (D93).
- **The token cost is the main thread.** In run 4, 64% of 15.5M tokens were main-thread turns during implement. Each turn re-reads a context that grew from 118K to 231K tokens. Fewer dispatches and fewer turns save far more than cheaper subagents do (D90).

## Running a baseline

Do these in this order. Skipping the mock has cost money before.

1. `git status` is clean and HEAD is the plugin you mean to test. **The runner exports the committed HEAD, not the working tree.** Uncommitted skill edits are not in the run.
2. Run the mock through the runner in MXC: `pwsh -File evals\scripts\run-baseline.ps1 -Case c1-csvledger -MockAgent -MockScenario happy`. Then run the dry run: `pwsh -File evals\mock-agent\dry-run.ps1 -InMxc -Case c1-csvledger -Checks all,happy`. Expect 69–71 PASS lines and no FAIL. Delete the mock's run folder, workspace, `.eval-cfg-<stamp>` and session folder afterwards.
3. Put `%SystemRoot%\System32` first on PATH before calling the runner from Git Bash or Python. Otherwise `tar` resolves to MSYS tar, which reads `C:` as a remote host and the plugin export fails.
4. Start the paid run in the background: `pwsh -NoProfile -File evals\scripts\run-baseline.ps1 -Case c1-csvledger`. A C1 run takes 34–41 minutes.
5. Watch it with a monitor that polls the workspace git log, the latest `"skill":` in `stream.jsonl`, `stderr.txt` for "Background tasks still running", and the runner output for `stored:`. Hard-code the workspace path from the runner's `workspace:` line; parsing `C:\...` with grep and sed failed once and the monitor watched the plugin repo instead. Don't count reviewer dispatches by grepping `subagent_type`: the string repeats all over the stream. Monitors expire after 30 minutes, and the runner's own completion notice is enough.
6. When it ends, read `run.json` (`exit_reason`, `reference_eligible`, `over_token_ceiling`, `plugin_modified_during_run`) before trusting anything else.

## Scoring

`python evals\scripts\score-run.py <run-folder> --manual <run-folder>\manual-verdicts.json` writes `score.json` and `score.md`. Without `--manual`, judgement items are listed as `needs_judge`.

- **Write the manual verdicts from evidence.** Re-run the test count the final report claims, check `kanban.md`, and check that reviewer IDs in `handoff.md` match real subagent transcripts. Every run so far has had at least one claim worth checking.
- **Re-runs happen at each task's own commit (D27).** A later task may legitimately change an earlier command's result. In run 4, T8 made T1's `python -m csvledger` exit 2. Re-running at the final HEAD wrongly failed it.
- **`check-dod` only passes for a task already in the Done lane** (`check-dod.py` lines 126–127). "Pass before the Done move" is impossible. The rule is move, check in the same step, and move back on failure (D92, corrected).
- **The scorer reads agent-written helpers.** Agents wrote lane-move helpers twice: `kb.py` in run 4, called `T2 Done`, and `kmove.ps1` in run 5, called `-Task T3 -To Done`. Expect new shapes. When a scorer check fails with "no Done move found", read the trace before believing it.
- **Gate counts come from gate output, not command text.** One command often runs several gates, loops over tasks, or loops over message variables (`foreach($m in $m1,$m2,$m3)`). `| Out-Null` hides verdicts, so those count as `unknown`.
- **After any scorer change, reproduce every stored run.** Runs 1–6 must give their committed composites exactly. That check caught two regressions I introduced myself.
- **Different plugin SHAs are different contestants (D60).** Don't average across them.

## Skill behaviour that moved the scores

| Lesson | Evidence | Decision |
|---|---|---|
| Per-task event logs were never written, whatever the wording. | 0 entries in runs 1–5, even with an `EVENTS:` output field. | Retired (D91). |
| Per-task review dispatches blow the token budget. | Run 4: 15 implement-stage reviewers, 15.5M tokens. | One reviewer per phase, with a separate verdict per task (D90). Run 5: 8.97M. |
| A rule pointing at an agent that doesn't exist gets skipped. | Phase review pointed at a "planning-coordinator" agent, so run 3 self-issued its last phase verdict and then claimed a reviewer verdict. | Phase verdicts come from a `code-reviewer` subagent with its ID recorded (D88). |
| Two rules that can't both be met get resolved by the agent, badly. | "Dependents wait for Done" against "the batch holds until review" made run 3 dispatch dependents early. | Dependents may start once a predecessor is In Review with passing evidence (D90). |
| The orchestrator patched code itself when a fix looked small. | Runs 1–3 all did it. | The orchestrator never edits code; fixes go to `geeky-coder` (D87, D88). |
| Text in the agent definition beats text in the skill. | `geeky-implement-orchestrator.md` said "move to Done and run check-dod". | Fix the agent file and regenerate the projections with `scripts/sync-agents.py`. |
| Token cuts must not cost quality. | The owner's rule for D90. | Evidence and review verdicts are never shortened; failures are read in full; phases over 4 tasks split their review. |

## Repo hygiene traps

- The `.agents`, `.claude`, `.codex`, `.cursor` and `.github` agent projections drift from `agents/*.md`. Run `python geeky-orchestration\scripts\sync-agents.py --project-root . --agents <names>` after any agent edit, and expect it to pick up older unsynced changes too.
- An automated security review flagged the regenerated Codex projection as "fail-open", because it verifies saved evidence instead of always re-running tests. That policy is deliberate (D89).
- `test_sync_agents.py` fails when TEMP is the 8.3 short path (`GERALD~1.KHO`). Run tests with `$env:TEMP=(Get-Item $env:TEMP).FullName; $env:TMP=$env:TEMP` first. The system Python has no pytest; use `C:\repos\.eval-tools\agent-py\Scripts\python.exe`.
- To split one file across two commits without interactive staging, stage a filtered copy with `git hash-object -w --path <repo-relative path>` and `git update-index --cacheinfo`. The path must be repo-relative. A plugin-relative path failed once and both changes landed in the same commit.
- Never amend or force-push to fix grouping after a push. Leave it and say so.

## Results so far (C1)

| Run | Plugin | Tokens | Composite | Note |
|---|---|---|---|---|
| 1 | `24c4e6d` | 10.06M | 77.2 | |
| 2 | `24c4e6d` | 13.32M | 77.0 | Over the 12M ceiling. |
| 3 | `e674b86` | 10.12M | 86.7 | |
| 4 | `e572902` | 15.51M | 97.9 | Over the ceiling, not reference-eligible. |
| 5 | `fd67ca3` | 8.97M | 93.8 | |
| 6 | `8ea2ccc` | 8.13M | 98.3 | Implement delegated to the orchestrator subagent. |

The cut-off run from before the background-wait fix is archived in `evals/baselines/archive/`.

## Telemetry and Linux MXC (2026-10-24)

- **Langfuse telemetry is opt-in by host env** (`TRACE_TO_LANGFUSE=true`) and covers both harnesses through Langfuse's own pinned hooks (D101, [telemetry README](telemetry/README.md)). Install the hooks once with `telemetry/install-telemetry-tools.ps1`.
- **`claude -p` drops thinking text.** It requests `display: "omitted"`, so all 124 thinking blocks in C1 run 6 were empty signatures. `showThinkingSummaries: true` in the run settings restores summaries. Codex runs used `summary: none`; telemetry runs set `model_reasoning_summary = "detailed"`.
- **The Claude hook exits 0 even when an upload fails**, and it defers a turn with pending Agent calls until `SessionEnd`. Judge delivery from the Langfuse readback (`run.json.telemetry.delivered`), not from the hook's exit code. The Codex tracer marks a delivered turn in `<rollout>.langfuse`.
- **Langfuse v4 events-only servers have no `/api/public/traces`.** Read sessions through `/api/public/v2/observations?sessionId=...`.
- **MXC runs on Linux** with Bubblewrap (D102). Install `bubblewrap slirp4netns iproute2 iptables`. The sandbox sees only system folders and gets its own `HOME`, so runtimes under `/opt` or `/usr/local` need grants; the host grants the CLI, its symlink target and the PATH runtimes. A TLS-inspecting proxy's CA must be passed through (`SSL_CERT_FILE` and friends) or the hooks' HTTPS fails inside the sandbox.
- **Linux MXC exit 255 was the SDK's spawn thread dying.** bwrap runs with `--die-with-parent` (PR_SET_PDEATHSIG), which fires when the forking *thread* exits. `MxcContainer.SpawnAsync` forks from a thread-pool worker, so a retired worker SIGKILLed the sandbox: Codex C0 attempts 1-4 at 2-3 min, Claude C0 run 2 at 69 s, `sleep 150` at 21 s. slirp4netns vanishing the same second was a symptom, not the cause, so upgrading it changed nothing. mxc-sandbox 0.2.1 spawns from a dedicated long-lived thread.
- **C0 audit (2026-10-25).** Three more harness defects, all fixed. Bubblewrap set HOME to the workspace, so Claude Code and pwsh wrote `.cache/` into the contestant repo; the host now gives the sandbox a private HOME. A provider content-filter stop (Claude C0 run 3) was logged as `completed`; it is now `provider_refusal`. And the matrix never exercised Claude's toolchain checks (`happy` only simulates the workflow), whose Linux versions failed on `cmd.exe` probes; the matrix now runs `all,happy`, and the Codex mock gained a gates check (.py and pwsh). Two findings first read as model behaviour also had harness causes. The Codex agent tested on the contract's minimum Python (`python3.11`), which had no pytest; `scripts/install-agent-pythons.ps1` now gives every `python3.X` on the sandbox PATH pytest. And it ran `geeky-implement` itself rather than through the orchestrator, which the skill allows, so `nested_subagents` is now informational in the coverage check. For provider content filters, `run-baseline.ps1 -ResumeOnRefusal N` resumes the session and records an intervention.
- **The ant-claude content filter is intermittent, not content-specific.** Claude C0 run 3's final request was replayed 8 times without a refusal: the skill message alone, the prefix and the whole conversation as plain text (max_tokens 8), the whole conversation 3 times with room to generate, and the exact structured request twice (resumed session in MXC). The route is LiteLLM `anthropic` -> `mimo-v2.6-flash`. Use `-ResumeOnRefusal`; Claude C0 run 4 recovered from one refusal that way. LiteLLM takes its virtual key as `ANTHROPIC_API_KEY` (`x-api-key`); the runner no longer sends it as `ANTHROPIC_AUTH_TOKEN`.
- **C0 first.** `c0-wordstat` is a small case that drives every harness point we trace. Run it on a new harness or model before C1-C3, then check `langfuse-coverage.json`.
- **Codex handoffs are provider-encrypted** (`encrypted_content` in `agent_message`), and both Langfuse SDKs time out a large export after 5 s unless `LANGFUSE_TIMEOUT` is raised. The runners pass `300`.
- **Mock matrix:** `scripts/run-mock-matrix.ps1` runs both harnesses on C0-C3 with no model calls (Claude with `all,happy`, so its toolchain checks run too) and fails any run whose mock checks fail or whose session never reached Langfuse.

## C0 parity on LiteLLM (2026-10-25)

- **Compare harnesses with `parity-eval.py`, not score-run composites.** score-run's Codex process parser expects the Windows PowerShell shape. On Linux it scored ~20 checks "not found" (Codex 68.26 vs Claude 55.77, not comparable), and its latency-based task tier exists only for Claude. `parity-eval.py` reads both runs from Langfuse observations, reflog stage bounds and the final artifacts, and takes Quality from score-run (D103).
- **Results.** On `ant-claude`: Codex 98.75, Claude 59.15 (96.93 without the forbidden-git hard gate for a `git reset --soft`). On `ant-claudex`: Codex 97.78, Claude 94.43 (Claude hit the 5400 s ceiling in the final review fix). Oracle 13/13 in all four runs. See [c0-ant-claude](analyses/c0-ant-claude-20261025/README.md) and [c0-ant-claudex](analyses/c0-ant-claudex-20261025/README.md).
- **Audit every check against raw evidence before trusting a score.** That audit found and fixed:
  - in parity-eval: an empty Codex implement window, a wrong phase map, a zero-length Claude plan-review window, and missing run-completed/work-committed checks;
  - in score-run: a missed docs-only critical-fix commit;
  - in codex-trace: refusing interrupted children and rejected spawns.
- **Parity confounds that remain.**
  - Reasoning: Codex runs `high`, while Claude Code requests no thinking for an unrecognised model name.
  - Complexity-router models can send each harness to different backends.
  - One run each.
- **Langfuse scoring.**
  - `telemetry/langfuse-scores.py` posts 10 session scores per run, with score configs.
  - The LLM judge `final_report_complete` exists, pinned to `zen/gpt-6-luna`. Its rule is disabled until calibration.
  - Code evaluators need server-side enablement.

## Open TODOs

- [x] **Codex C1 on `bee7b14` (after `f54747e`).** Three completed runs now exercise the later plugin: 96.3, 98.0, and 99.6 reviewed for run 3 (`20261023T230041Z-2c3b5489`). See [the Claude review](analyses/c1-claude-review-20261024.md). This does not establish a new Claude repeat on that SHA; D92 remains move/check/revert.
- [ ] **Three runs on one SHA**, for a real mean and stability figure (D60).
- [ ] **C2 (`c2-linkvault`) and C3 (`c3-minisql`) baselines.** The kits and oracles exist but neither has run. Do mock runs first; C2 and C3 have larger ceilings (25M, 50M).
- [ ] **The judge (D57) and the expectations files (D34).** A Langfuse LLM judge (`final_report_complete`) exists but is uncalibrated and its rule disabled; `manual-verdicts.json` is still hand-written.
- [ ] **Calibrate `final_report_complete`** on labelled main-thread turns (positive: the three C0 final reports; negative: intermediate turns and the last turns of the refused and timed-out runs) before enabling its rule.
- [ ] **Claude C0 on `ant-claudex` with a higher ceiling**, then three runs per harness on one fixed model with matched reasoning.
- [ ] **Recalibrate the C0 token ceiling** (6M in `case.json`; real runs used 11.7M-21.9M, mostly cached input).
- [x] **Codex adapter and C1 saved-trace scoring.** Built and exercised in three completed calibration runs; checkpoint 5 records complete. Automatic process extraction covers run 2's shape only. Run 3's Python-heredoc kanban writes and collapsed stage detection are unsupported, so a strict raw score of run 3 exits 1. Runtime hook parity remains a separate documented gap.
- [ ] **The `/geeky-eval` skill.** Still a future component; not implemented by the adapter closeout.
- [ ] **O22 leftovers:** the MSYS tar PATH trap is documented but not guarded in the runner, and `model_calls` counts subagent messages.
- [ ] **Historical `analysis.json` in run 5.** Preserve it; any future derived refresh belongs in a new output folder. Frozen historical score reproduction is recorded separately.
- [ ] **A conflicting rule in `agents/geeky-implement-orchestrator.md`:** it prefers the MCP gate tools while `SKILL.md` prefers the scripts. It predates the eval work.
- [ ] **Unmerged side branches:** `claude/reverent-wright-14ac9b` (`618f1bf`, sync-agents test fix) and `claude/exciting-dewdney-adcbb0` (`c1cb0b0`, guard warn-mode). Merge or drop.
- [ ] **Leftover folders:** the run workspaces under `C:\repos\eval-c1-csvledger-*`, their `C:\repos\.eval-cfg-*` folders and `C:\repos\mxc-probe`. Keep each run's workspace until it is scored, then delete it with its `.eval-cfg` and session folder.
