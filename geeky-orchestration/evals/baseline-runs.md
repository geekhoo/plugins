# Baseline Runs (O14) and Run Limits (O13)

Latest Codex C1: [run3 completed report](baselines/c1-csvledger/20261023T230041Z-2c3b5489/report.md) — reviewed QACT99.6, oracle118/118 stable3, final110tests,1410s,18.116799M tokens. Main Sol/high, task/default Sol/medium, reviewers Sol/xhigh. Complete operator-reviewed scoring; automatic extraction unsupported for this shape. Token ceiling exceeded under informational calibration policy; reference eligibility remains false. Previous records below remain preserved.

Final-pair update: [Codex 2 automatic process extraction](analyses/c1-final-parity-20261024/README.md) now works without operator process mappings. Use a fresh output directory, existing judgments/validation cache and `--require-complete`; a withheld strict composite exits nonzero. The prior six-run proof is tied to its saved source version.

For saved-evidence scoring, use a separate `--out` directory. Bind reused validation to task, full commit SHA, exact command and source/output hashes with `--no-rerun --validation-cache`; use `--require-complete` for comparable repaired results and source-backed manual judgments for judge checks. Do not regenerate original baseline files. Historical `--no-rerun` score reproduction alone is not a fresh own-commit validation proof. Preserve retained workspaces and configs; the historical cleanup instructions below do not authorize deletion.

> Current status, 2026-10-24: two Codex C1 calibration runs completed; corrected composites are 96.3 and 98.0. [Checkpoint 5 records and decisions](codex-c1-checkpoint5.md) link the frozen six-Claude reproduction and complete four-run derivation. The Codex runner is `scripts/run-codex-baseline.ps1`; its retained launch relies on outer MXC with explicit isolated configuration. The direct CLI/no-hooks examples below are historical, not current launch instructions. No further paid run is authorized.

These are the baseline implementation runs for the three eval challenges: what to do, what each run must produce, and which measures to collect. The results set the reference solutions, token budgets and time limits that every contestant run is scored against.

Decisions referenced: D41 (reference solutions), D53 (tokens as cost), D57 (judge baseline), D68 (task tier, `L_ref`), D37 (fail-fast), and O13 (run time limits). They are recorded in [docs/agent-eval-decisions.md](../docs/agent-eval-decisions.md).

## What the baselines are used for

| Use | Taken from the baseline |
|---|---|
| Reference solution for the judge and the size score `S` | the final code snapshot and its non-test LOC |
| Token ceiling and token efficiency (D53) | total tokens |
| Run wall-time ceiling, idle watchdog and task timeout (O13) | wall time, longest idle gap, per-task durations |
| Reference latency `L_ref` for the task tier (D68) | median model-response latency |
| Checking the oracle (D46) | the oracle pass rate against the baseline |

## Scope

- **Cases:** `c1-csvledger`, `c2-linkvault`, `c3-minisql`, each under `geeky-orchestration/evals/cases/<case>/`.
- **Runs:** at least one per case. If you can, run three per case on the same harness. Repeat runs give the variance; the best one becomes the reference solution.
- **Harness and model:** your choice, recorded in `run.json`. Use the same harness for all three cases so the ceilings are comparable.

## Runner

`evals/scripts/run-baseline.ps1 -Case <case> [-Model <id>] [-DryRun]` performs steps 1–4 below for one run.

Before starting, it needs:
- model access (D101): with the default `-Gateway litellm`, `LITELLM_PROXY_URL` and `LITELLM_PROXY_API_KEY` in the process or User environment; with `-Gateway direct`, `CLAUDE_CODE_OAUTH_TOKEN` (D71);
- a Python with pytest;
- the `geeky-mcp` venv in `C:\repos\.eval-tools`.

### Model gateway and Langfuse (D101)

Both runners send every model call through the owner's LiteLLM proxy by default:

| | Claude (`run-baseline.ps1`) | Codex (`run-codex-baseline.ps1`) |
|---|---|---|
| Default model | `claude-sonnet-5-5` (LiteLLM serves no Opus) | `zen/gpt-6.1-sol` (workers inherit unless `-WorkerModel`) |
| Wiring | `ANTHROPIC_BASE_URL=<proxy>` and `ANTHROPIC_AUTH_TOKEN`, copied into the workload by name. The forwarded OAuth/API-key variables are blanked. The opus/sonnet aliases map to the run model and haiku maps to `-SmallModel` (`claude-haiku-5-5`) | `model_provider="litellm"` (`<proxy>/v1`, Responses API, `env_key=LITELLM_PROXY_API_KEY`) in the generated profile, so subagent threads use it too. The key is copied in by name and excluded from the agent's shell |
| Opt out | `-Gateway direct` | `-Gateway direct` (signed-in `CODEX_HOME`) |

`run.json` records `gateway` and `gateway_url`. Keys never appear on a command line or in evidence. The Claude agent's PowerShell tool can still read `ANTHROPIC_AUTH_TOKEN`, as it could read the OAuth token before. A paid Codex launch needs a native proof prepared with the same gateway and model, because the model matrix must match (`paid-diagnostic-audit.py`).

With `TRACE_TO_LANGFUSE=true` and `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` (and `LANGFUSE_BASE_URL`) set, each stored run is uploaded afterwards by `evals/scripts/langfuse-upload.py` on the host. The uploader stages copies of `session.jsonl` and `subagents/` and runs the official Langfuse converters on them (the Claude Code hook script, pinned by commit, and `@langfuse/codex-observability-plugin`). The contestant never runs anything Langfuse-related. Trace ids are seeded from `<case>/<run folder>`, so re-uploading a run, or backfilling an older one, overwrites its traces instead of duplicating them. Traces are tagged `geeky-eval`, `<case>`, `<harness>` and `gateway:<name>`; Codex traces also carry run metadata. The outcome is written to `langfuse.json`, and a failed upload never fails the run. One-time setup on the host (needs uv and Node 22+):

```powershell
python geeky-orchestration\evals\scripts\langfuse-upload.py --install --tools-dir C:\repos\.eval-tools\langfuse
python geeky-orchestration\evals\scripts\langfuse-upload.py geeky-orchestration\evals\baselines\c1-csvledger\<stamp>   # backfill
```

What it does:
- Exports the plugin at the committed `HEAD`, without `evals/`, into a read-write folder for that run only, and records whether the run modified it. Under a read-only grant, Claude can't list the plugin's folders and loads none of its skills.
- Sets git's `safe.directory` through environment variables, because inside the container git reports the workspace as having "dubious ownership".
- Records `geeky_skills_loaded`. A run in which no geeky skill loaded is never reference-eligible.
- Sets `CLAUDE_CODE_DISABLE_WINDOWS_SHELL_LAUNCHER=1`. Without it, every PowerShell tool call in MXC reports `Exit code 5` even when it succeeds.
- Copies every subagent transcript into `subagents/` in the run folder: `agent-<id>.jsonl`, plus a `meta.json` naming the tool call that spawned it. When a subagent dispatches its own subagents, as `geeky-implement-orchestrator` did in C1 run 6, their calls appear only there and not in `stream.jsonl`.
- Sets `PYTHONDONTWRITEBYTECODE=1`, and the plugin tamper check ignores `__pycache__`. C1 run 6 was flagged as tampered only because the gate scripts' bytecode was written into the read-write export.
- Passes `--disallowedTools Bash`. Git Bash cannot start in MXC (microsoft/mxc#1061), so every Bash call fails with exit 66. In C1 run 3 that wasted 8 calls, and one write silently did nothing. With Bash hidden, the agent uses PowerShell from the start.
- Sets `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`. Headless `claude -p` otherwise stops background subagents still running 10 minutes after the main agent's last turn, which cut C1 run 3 off mid-implementation. The main agent is resumed when the subagents finish. The MXC `--timeout` still bounds the run. A run whose background work was stopped is recorded with `exit_reason = bg_killed`.
- Puts `C:\repos\.eval-tools\agent-py`, a venv with pytest built offline, first on the sandbox `PATH`. The sandbox Python has no pytest, and `pip` can't install inside MXC.
- Sets `TMPDIR` to a per-run writable folder. MXC forces `TEMP` and `TMP` to the AppContainer's own temp folder, where pytest `tmp_path` and other `mkdtemp()` folders can't be written.
- Sets a neutral commit identity, `geeky-eval-agent <agent@geeky-eval.local>`, through the `GIT_AUTHOR_*` and `GIT_COMMITTER_*` environment variables.
- Reads its limits from `evals/cases/<case>/case.json`. After each run it calls `evals/scripts/analyze-run.py`, which writes `analysis.json` and fills the derived `run.json` fields.
- **Scoring is a separate step.** Run `python evals/scripts/score-run.py <run-folder> --manual <verdicts.json>`. It writes `score.json` and `score.md` into the run folder. Without `--manual`, judgement items are listed as `needs_judge` and left out of their denominators. To re-analyse a stored run without touching `run.json`, use `analyze-run.py --analysis-only`.

Run it once per repeat, from a fresh shell.

Before any paid run, check the toolchain with the mock agent (D83). It costs no tokens:

```powershell
pwsh -File evals\mock-agent\dry-run.ps1 -InMxc -Checks all
```

To run the whole pipeline with the mock agent instead of Claude:

```powershell
pwsh -File evals\scripts\run-baseline.ps1 -Case <case> -MockAgent -MockScenario happy
```

## Procedure, per run

### 1. Prepare the workspace

1. Note the geekhoo-plugins commit you are running from (`git rev-parse HEAD`). It goes into `run.json` as `plugin_sha`.
2. Create an empty folder outside every repository, for example `C:\eval-baselines\<case>-<YYYYMMDDTHHMMSSZ>\`. Inside it, run `git init` and create a `.gitignore` containing `__pycache__/`. Do not add a remote.
3. Copy **only** `brief.md` and `contract.md` from `evals/cases/<case>/` into the workspace root. Never copy `spec.md` or `oracle/`.
4. Check that `python --version` works in the shell the harness will use. The probe on 2026-10-20 showed the Codex sandbox reporting "No installed Python found!" when the host Python was on PATH. Fix this in the harness environment before you start.
5. Sign the harness in before the run. On 2026-10-20 the headless Claude CLI failed with "OAuth session expired". Run an interactive sign-in first, then check with a one-line `-p` prompt. Note that Claude reports an auth failure as `result.subtype = success` with `is_error = true`, so always check `is_error`.
6. Run the hidden oracle against this empty workspace (step 3 commands). **Every test must fail.** That proves the oracle doesn't pass on an empty repo.

### 2. Run

Recommended: the canonical prompt, `evals/prompts/end-to-end.md`, with `{{PLANNING_FOLDER}}` replaced by `docs/spec-001-feature/`. Send it as a single headless session. That makes the baseline directly comparable to contestant runs.

Any other approach is allowed, provided steps 3 and 4 are completed. Record the approach in `notes.md`.

Record the UTC start time immediately before launching and the UTC end time immediately after the process exits.

**Claude Code** (PowerShell; run from the workspace):

```powershell
$p = (Get-Content <repo>\geeky-orchestration\evals\prompts\end-to-end.md -Raw) -replace '\{\{PLANNING_FOLDER\}\}','docs/spec-001-feature/'
$sid = [guid]::NewGuid().ToString()
$mxc = "$env:USERPROFILE\.claude\plugins\cache\geekhoo-plugins\mxc-sandbox\0.1.0\scripts\mxc.ps1"
Set-Content <workspace>\..\no-hooks.json '{"disableAllHooks": true}'
& $mxc run --workspace <workspace> --isolated --allow-win32k --ro <plugin dir> --timeout <wall-time ceiling s> -- `
  -p $p --session-id $sid --plugin-dir <plugin dir> --settings <workspace>\..\no-hooks.json `
  --output-format stream-json --verbose > stream.jsonl 2> stderr.txt
```

This runs Claude in the MXC sandbox (D72). The workspace must be a shallow path such as `C:\repos\<case>-<timestamp>`. Set `CLAUDE_CODE_OAUTH_TOKEN` in the host shell first (D71); `--isolated` won't sign in without it. Keep `no-hooks.json` outside the workspace so the agent never sees it. Hooks can't run in the sandbox, and the Bash tool is unavailable (the agent uses PowerShell). In isolated mode the session file is under `%USERPROFILE%\.mxc-sandbox\home\projects\...`, not `~/.claude`.

**Codex CLI:**

```powershell
codex exec --json --sandbox workspace-write -o last-message.txt $p < NUL > stream.jsonl 2> stderr.txt
```

Do not use `--full-auto`; current Codex no longer supports it. Do not use `--ephemeral`, because it suppresses the session file.

Keep the live stream (`stream.jsonl`). After the run, also copy the harness's own **session file**, because it carries per-event timestamps:

| Harness | Session file |
|---|---|
| Claude Code | `%USERPROFILE%\.claude\projects\<workspace path with non-alphanumerics replaced by '-'>\<$sid>.jsonl`. Copy it right away: Claude deletes transcripts after 30 days by default. |
| Codex CLI | `%USERPROFILE%\.codex\sessions\YYYY\MM\DD\rollout-*-<thread_id>.jsonl`. The `thread_id` is in the first `thread.started` event. Skip any `.langfuse` sidecar. |

**Interventions:** don't intervene mid-run. If you have to, log each intervention in `notes.md` with its time, what you did, and why. Such a run is still useful, but it is flagged.

### 3. Validate against the hidden oracle

From `geeky-orchestration/evals/cases/<case>/oracle/`:

```powershell
$env:ORACLE_TARGET = '<workspace>'
python -m pytest -q -rA | Tee-Object oracle-output.txt
```

**Expected outcome:** all tests pass. In C3, one ambiguous-table-file test is skipped on Windows.

| Collected | Expected |
|---|---|
| C1: 118 | 118 passed |
| C2: 136 | 136 passed |
| C3: 183 | 182 passed, 1 skipped |

**For every failure**, check it against `spec.md` and record a verdict in `notes.md`:

- **Implementation wrong:** fix it in a new run, or flag the run as "not reference-eligible".
- **Oracle wrong:** the spec contradicts the test. Raise it, and the oracle is fixed in the repo.
- **Spec ambiguous:** raise it. The spec, the contract and the oracle are all updated, as for the earlier ambiguity rulings.

Run the oracle **3 times** against the final workspace. Any result that differs between the three runs is a flaky test. Record it and raise it as "oracle wrong".

A run can become the reference solution only when its oracle result is clean and stable.

For the traps behind each runner setting and the open TODOs, see [lessons-learned.md](lessons-learned.md).

### 4. Store the baseline

Store everything in `geeky-orchestration/evals/baselines/<case>/<YYYYMMDDTHHMMSSZ>/`. Contestants never see this folder, because D50 excludes `evals/` from the plugin export.

A run that is invalid for an environment reason, rather than for the contestant's own behaviour, moves to `evals/baselines/archive/<case>-<stamp>-<exit_reason>/` so that `<case>/` holds only real baselines. Keep `run.json`, `analysis.json`, `notes.md`, `stderr.txt`, `stream.jsonl` and `solution.bundle`. Drop the duplicate `session.jsonl` and an oracle log that adds nothing. Delete the run's workspace, its `.eval-cfg-<stamp>` folder and its `~/.mxc-sandbox/home/projects` entry.

| File | Content |
|---|---|
| `solution.bundle` | `git bundle create solution.bundle --all`, taken in the workspace: the full repo, including the agent's planning folder and commits |
| `stream.jsonl`, `session.jsonl`, `stderr.txt` | the raw transcripts |
| `run.json` | the measures below |
| `oracle-output.txt` | the step 3 output |
| `notes.md` | the approach, any interventions, oracle verdicts, environment notes |

## Measures to collect (`run.json`)

`schema` is `geeky-eval.baseline/1`. Fields marked *derived* can be computed later from the transcripts by the ingest tool (O7). Record them by hand only if that tool is not ready yet.

| Field | Meaning | Source |
|---|---|---|
| `case` | `c1-csvledger`, `c2-linkvault` or `c3-minisql` | you |
| `harness`, `harness_version` | e.g. `claude-code` / `2.1.293`, `codex-cli` / `0.163.0` | `--version` |
| `model`, `reasoning` | model ID; reasoning setting, or `default` | Claude `init.model`; Codex `turn_context` in its session file |
| `approach` | `canonical-prompt`, or a short description | you |
| `plugin_sha`, `prompt_sha256` | the repo commit and the hash of the filled prompt | step 1, step 2 |
| `started_utc`, `ended_utc`, `wall_time_s` | process start, end and duration | you |
| `tokens.input`, `tokens.cached_input`, `tokens.output`, `tokens.reasoning`, `tokens.total` | totals. `total` is input including cached, plus output. | Claude `result.usage` / `modelUsage`; Codex last `turn.completed.usage` |
| `model_calls` | the number of model requests | *derived*: Claude `result.num_turns` and session; Codex `token_count` events |
| `latency_median_ms` | median model-response latency per call. Sets `L_ref` (D68). | *derived* from session timestamps |
| `max_idle_gap_s` | the longest gap between consecutive session events | *derived* |
| `stages[]` | per workflow: `name`, `started_utc`, `ended_utc` | *derived* from skill invocations |
| `tasks[]` | per task: `id`, `dispatched_utc`, `done_utc`, `duration_s`, `validation_attempts`, `review_rounds`, `loc_changed` | *derived* from the session, kanban and git |
| `impl_review_rounds` | `impl-review` runs until PASS | *derived* |
| `oracle` | `collected`, `passed`, `failed`, `skipped` | step 3 |
| `loc.source_non_test`, `loc.test`, `files_changed` | final code size | `git` in the workspace |
| `commits` | the number of commits | `git rev-list --count HEAD` |
| `exit_reason` | `completed`, `timeout`, `idle`, `budget`, `bg_killed`, `crash` or `aborted` | you / process exit |
| `raw_sha256` | SHA-256 of `stream.jsonl` and `session.jsonl` | computed when stored |
| `interventions` | the count of human interventions, with reasons in `notes.md` | you |
| `reference_eligible` | `true` only if the oracle result is clean and there were no interventions | you |

## Limits derived from the baselines (O13 requirements)

Once each case has a reference-eligible baseline, set these values in `evals/cases/<case>/case.json` (D66). With several baselines, use the median of the eligible runs.

| Limit | Rule | Until then (provisional) |
|---|---|---|
| **Token ceiling** (D53) | 2 × baseline `tokens.total` | C1 10M, C2 25M, C3 50M |
| **Run wall-time ceiling** | 2 × baseline `wall_time_s`, rounded up to 5 minutes | C1 90 min, C2 3 h, C3 6 h |
| **Idle watchdog**: no trace event for N seconds means the run is treated as hung and fails fast | N = max(600, 1.5 × baseline `max_idle_gap_s`) | 10 min |
| **Task timeout** (D37) | max(20 min, 2 × the slowest baseline task's `duration_s`) | 20 min |
| **`L_ref`** (D68), per harness | baseline `latency_median_ms` for that harness | none; the duration part `T` uses an unadjusted `d` |
| **Size reference** (score `S`) | the reference solution's `loc.source_non_test` | the upper bound of the spec's Quality signals band |

How the limits are enforced (O13):

- **Three layers.** The hard wall-time ceiling, the idle watchdog on the live stream, and each harness's native caps. Native caps are Claude `--max-turns`, and for Codex a token check on each `turn.completed`.
- **Graceful stop, then a forced one.** On Windows, the eval first stops the run gracefully. If the process tree is still alive after 30 s, it kills the whole tree with `taskkill /T /F`.
- **Every stop is recorded.** Each stop records its `exit_reason`. A timeout counts as a failure (D38), never as missing data.

With 3 or more eligible baselines, use the p95 instead of the median as the basis for these ceilings.

O13 is complete when every case's `case.json` holds the derived values, and the decision record replaces the provisional numbers with the values that were applied.

## Done criteria

- For every case, the oracle failed entirely against the empty workspace (step 1.6).
- Every case has at least one baseline folder holding all the files listed in step 4.
- In at least one baseline per case, `reference_eligible` is `true`.
- Every oracle failure seen during baselining has a recorded verdict. Any resulting change to the oracle, spec or contract is committed.
- Every `case.json` holds the derived limits from the table above.
