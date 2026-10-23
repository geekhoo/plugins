# Kickoff: C1 Baselines with Codex as the Contestant

Paste this whole file into a fresh Codex session. It is the full brief, so you don't need any earlier chat.

## Your role

You are the **operator**. You prepare, launch, watch and score C1 eval runs in which **Codex CLI is the contestant**. The contestant runs the geeky-orchestration workflow end to end inside the Microsoft MXC sandbox:

> spec-research → geeky-plan → plan-review → geeky-implement → impl-review

Six C1 baselines already exist with Claude Code as the contestant. Your job is the Codex equivalent, scored on the same rubric so the two harnesses can be compared. You work with the owner in this session. Stop at each checkpoint below and wait for a go-ahead.

## Machine and paths

- Machine: the owner's Windows 11 workstation. Shell: PowerShell 7 (`pwsh`). Git Bash exists on the host but **cannot run inside MXC**.
- Repo: `C:\Users\gerald.khoo\geekhoo-plugins`, branch `main`. The plugin is in `geeky-orchestration\`.
- Codex on the host: `codex-cli 0.163.0` (check with `codex --version`).
- Sandbox tools: `C:\repos\.eval-tools\agent-py` (a venv with pytest) and `C:\repos\.eval-tools\geeky-mcp` (a venv for the MCP server). An isolated Codex home is planned at `C:\repos\.eval-tools\codex-home`; check whether it exists.
- MXC wrapper: the `mxc-sandbox` plugin's `scripts\mxc.ps1`, in this repo at `mxc-sandbox\scripts\mxc.ps1`. Swap the workload exe with `MXC_CLAUDE_EXE`.

## Verify before acting

Run these first and report the output. Don't trust this brief over `git`.

```powershell
cd C:\Users\gerald.khoo\geekhoo-plugins
git status --short
git log -1 --oneline        # expect 60dc3fc or later
git fetch origin; git rev-list --left-right --count origin/main...HEAD
codex --version
Test-Path C:\repos\.eval-tools\agent-py\Scripts\python.exe, C:\repos\.eval-tools\geeky-mcp, C:\repos\.eval-tools\codex-home
```

If HEAD is not `60dc3fc` or a descendant of it, stop and ask.

## Read in this order

1. `geeky-orchestration\evals\lessons-learned.md`: every MXC trap found so far and the fix for each. Most of them apply to Codex too.
2. `geeky-orchestration\evals\baseline-runs.md`: the run procedure, the run-folder layout and the `run.json` fields, including the existing Codex notes.
3. `geeky-orchestration\docs\agent-eval-decisions.md`. Read these entries:
   - D14 (v1 scope), D19 (trace source), D23 (guard hook for Codex);
   - D47, D48, D50 and D51 (plugin access, isolated `CODEX_HOME`);
   - D52 (sandboxing), D53 (tokens), D54 (sync-agents test), D60 (no mixing of contestants);
   - D72–D74 (MXC);
   - D27, D86–D93 (scoring);
   - O7 (Codex trace ingest), O18 (Codex sign-in);
   - the "Verified harness facts" table, which records the Codex probes.
4. `geeky-orchestration\evals\scripts\run-baseline.ps1`: the Claude runner. Its `--env` list is the sandbox recipe.
5. `geeky-orchestration\evals\scripts\analyze-run.py` and `evals\scripts\score-run.py`: they parse **Claude** stream-json today.
6. `geeky-orchestration\evals\prompts\end-to-end.md`: the canonical contestant prompt. Use it unchanged.
7. `geeky-orchestration\evals\baselines\c1-csvledger\comparison-20261022T0800Z.md`: the Claude results you are comparing against.

## Current verified state (2026-10-23)

- The Claude path works end to end. The runner, mock agent, dry run, analyzer and scorer are built and tested. C1 runs 1–6 scored 77.2, 77.0, 86.7, 97.9, 93.8 and 98.3. The latest two used 8–9M tokens.
- **The Codex path is not built.** `run-baseline.ps1` launches `claude -p` only. The analyzer and scorer read Claude stream-json only. There is no `evals\adapters\codex\` profile yet.
- These facts about Codex were checked by probes on 2026-10-20 with codex-cli 0.163.0:
  - `codex.exe exec --json --sandbox danger-full-access` runs inside MXC with `--allow-win32k` and a read-write grant on its home.
  - `MXC_CLAUDE_EXE=codex.exe` with `--env CODEX_HOME=<dir>` gives a fresh home, which needs a one-time `codex login` (otherwise 401).
  - Codex finds skills in `.agents/skills`, searched from the working directory up to the repo root, and in `$HOME/.agents/skills`. It does not use `~/.codex/skills`.
  - `--full-auto` has been removed, and `--ephemeral` suppresses the session file.
  - `codex exec --json` events carry **no timestamps**. Timings and cumulative `token_count` come from the rollout file `%CODEX_HOME%\sessions\YYYY\MM\DD\rollout-*-<thread_id>.jsonl`.
  - Codex's own `workspace-write` sandbox once reported "No installed Python found!", so Python must be reachable on PATH.
  - A trivial prompt costs about 110–150K input tokens of fixed overhead.
- The C1 token ceiling is 12M, which was calibrated for Claude. Record Codex's usage; don't fail a run on that number until there is a Codex baseline (D53).

## Constraints

- **Never print, log or pass on a command line** `CLAUDE_CODE_OAUTH_TOKEN`, the Codex auth file, or any API key. The owner does all sign-ins, including `codex login` into the isolated home.
- **Don't change system or security settings.** Ask the owner instead.
- **Commit only when the owner asks.** Use small, logical commits that end with a co-author line naming the model. **Never push unasked, never force, never amend, never `--no-verify`.**
- **Keep the plugin export isolated (D47, D48, D51).** Skills reach Codex through a run-scoped `HOME` or `CODEX_HOME`, never by copying them into the contestant workspace. The user's `~/.codex` config and `~/.agents/skills` must not leak into a run.
- **Give both harnesses the same context (D48).** If Codex can't reach something Claude can (skills, references, agents, scripts, the guard hook, `geeky_mcp`), the parity pre-flight fails the run.
- **No paid run before both of these pass:** a mock run through your Codex runner path, and the MXC dry-run checks.
- **Add Codex support next to the Claude path.** Runs 1–6 must keep scoring exactly 77.2, 77.0, 86.7, 97.9, 93.8 and 98.3. Re-check that after every analyzer or scorer change.
- **Scope:** the Codex runner path, the Codex trace adapter, the C1 runs and their scoring. Don't edit the plugin's skills or agents. If a skill problem shows up, write it down for the owner.
- **Reply length:** 200 words or less at each checkpoint, with a numbered list of any decisions you need.

## Work plan and checkpoints

**Checkpoint 0. Prerequisites.**
1. Confirm D54. Run `geeky-orchestration\test_sync_agents.py` with the agent-py Python, after setting `$env:TEMP=(Get-Item $env:TEMP).FullName`. A short 8.3 TEMP path makes one test fail for a reason unrelated to the plugin.
2. Have the owner run `codex login` with `CODEX_HOME=C:\repos\.eval-tools\codex-home`. This is the open item O18.
3. Ask which model and reasoning level the Codex runs should use.

**Checkpoint 1. Codex runner path.**
1. Build a Codex profile under `evals\adapters\codex\profile\` (D51). It holds:
   - the `config.toml`;
   - `geeky_mcp` registered as an MCP server;
   - the guard hook (D23);
   - the `sync-agents` projections and plugin skills reachable through a run-scoped `HOME/.agents/skills`.
2. Add `-Harness codex` to `run-baseline.ps1`, or write a sibling script. Keep the Claude sandbox settings that still apply: `TMPDIR`, `PYTHONDONTWRITEBYTECODE`, agent-py first on PATH, git identity, `safe.directory`, `XDG_CONFIG_HOME` and `--host-loopback`.
3. Launch with `codex exec --json --sandbox danger-full-access`. MXC is the containment, as D52 and the MXC probe found.
4. Store `stream.jsonl`, the rollout file and `run.json` in the same layout as the Claude runs.
5. Write the parity pre-flight that lists what each harness can reach.

**Checkpoint 2. Mock and dry run.** Run the mock agent through the Codex path in MXC and fix every failure. The mock currently emulates Claude, so extend it for Codex, or add a minimal Codex smoke prompt that exercises:
- skills;
- an MCP call;
- `pwsh`, `python` and `pytest`;
- a `git` commit.

Then clean up the run folder, the workspace, `.eval-cfg-<stamp>` and the session folder.

**Checkpoint 3. Trace adapter.** Make `analyze-run.py` and `score-run.py` read Codex traces (O7):
- `command_execution`, `file_change` and `agent_message` items;
- subagent or delegation records, if Codex has any;
- timestamps and `token_count` from the rollout file.

Re-check that runs 1–6 still score exactly as recorded.

**Checkpoint 4. One paid C1 run.** Only on the owner's go-ahead.
1. Run it in the background and watch the commits, the current skill stage and the token total.
2. Write `manual-verdicts.json` from evidence. Re-run the test count the final report claims, and check the reviewer IDs against the transcripts.
3. Score the run.
4. Add a Codex column to the scorecard. It is a separate contestant, so keep it out of the Claude means (D60).

**Checkpoint 5. Records.** Update these, then report what changed and what is still open:
- `baseline-runs.md` (the Codex procedure);
- `lessons-learned.md` (new traps);
- the decision doc, with new D-numbers after the highest existing one.

## Done when

- [ ] A Codex C1 run is stored under `evals\baselines\c1-csvledger\<stamp>\` with `run.json`, `stream.jsonl`, the rollout file, `analysis.json`, `score.json`, `score.md` and `manual-verdicts.json`.
- [ ] The parity pre-flight for that run passes, and its output is saved in the run folder.
- [ ] The scorecard has a Codex column, scored with the same rubric and the same `score-run.py`.
- [ ] Runs 1–6 still reproduce their committed composites exactly.
- [ ] `lessons-learned.md`, `baseline-runs.md` and the decision doc describe the Codex path as it now works.
- [ ] Everything is committed only on the owner's say-so, and nothing is pushed unasked.
