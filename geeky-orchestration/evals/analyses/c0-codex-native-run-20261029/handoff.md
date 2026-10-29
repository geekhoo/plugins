# Codex kickoff: fix the commit gate, then prepare and launch the native Codex C0 MXC run

## Target
- Machine: the Windows 11 host that holds `C:\Users\gerald.khoo\geekhoo-plugins`. Shell: PowerShell 7.
- Workdir: `C:\Users\gerald.khoo\geekhoo-plugins`. Plugin root: `geeky-orchestration\`.
- Word budget for your final report: 300 words.

## Verify before acting
1. Run `git fetch origin` and check out `main` at `origin/main`. `git merge-base --is-ancestor 76c40b62e731c9a0663edb3e648f4f33574f9f06 HEAD` must exit 0. That commit adds the native-run captures; the commit after it adds this file. Stop and report if the check fails.
2. `git status --short` must be empty. If it isn't, the changes belong to the owner: stop and report, and do not stage, revert or rewrite them.
3. `git log -1 --format=%H 0b1f5fbc0e84b110ea0f9fa59ddfa711b46cf53a` must resolve. That is the plugin SHA of both earlier Luna runs.
4. `git log --format=%h -1 -- geeky-orchestration/scripts/check-commit.py` must not be newer than `76c40b6`. If it is, someone has already changed the gate: read that commit and skip whichever parts of W1–W3 it covers.

## Read in this order
1. `geeky-orchestration/evals/analyses/c0-codex-native-run-20261029/README.md`
2. `geeky-orchestration/evals/baselines/c0-wordstat/20261029T043904Z-28148c1d/stream.jsonl`: read the last 6 lines only.
3. `geeky-orchestration/scripts/check-commit.py` and `geeky-orchestration/scripts/check-commit.ps1`
4. `geeky-orchestration/skills/spec-research/SKILL.md`, Phase 5
5. `geeky-orchestration/AGENTS.md`, the "Deterministic quality gates" table
6. `geeky-orchestration/test_quality_gates.py`
7. `geeky-orchestration/mcp/server.py`, `geeky_check_commit`
8. `geeky-orchestration/evals/analyses/c0-codex-native-preparation-20261029/README.md`
9. `geeky-orchestration/evals/analyses/c0-luna-overtime-20261028/README.md`: the Claude reference setup.

## Verified state
- Run `20261029T043904Z-28148c1d` uses native LiteLLM wire, Luna/high on every role, and a 6000 s budget. It stopped after 354 s with process exit 0. No stage was accepted, nothing was committed, and the oracle passed 0/13. The native transport worked: three research workers ran and their waits completed, with no protocol errors.
- The blocker is a rule conflict:
  - `AGENTS.md` requires `check-commit` before each commit.
  - `check-commit` rejects any message without a `Tasks: T<n>` line.
  - spec-research prescribes `docs: author feature specification in <folder>` with no task line, and no task IDs exist at that stage.
  - Codex refused to invent an ID and stopped, which is the correct behaviour.
  - Claude run `20261028T115941Z` hit the same gate and committed under a self-declared exception.
  - Codex run `20261028T114114Z-eb4361e5` invented `Tasks: T1`.
- Preparation exports the committed plugin HEAD and nothing from the working tree, so a fix the contestant can see must be committed.

## Work

### W1. Pre-planning commit rule
- `check-commit.py` and `check-commit.ps1` must behave identically. Accept a body line matching `^\s*Tasks:\s*none\b` (case-insensitive) only when the subject type is `docs`.
- If the type is anything else and the message has `Tasks: none`, raise this error: `Tasks: none is allowed only for docs commits`.
- Leave every other rule unchanged. Update both header comments.
- Spec-research Phase 5: add `-m "Tasks: none (pre-planning specification)"` to the prescribed `git commit` command.
- `AGENTS.md` commit-gate row: add one clause saying that pre-planning `docs` commits use `Tasks: none`.
- In `mcp/server.py`, update the `geeky_check_commit` docstring to match. Make no logic change.

### W2. Regression proof
Add to `test_quality_gates.py`, covering the Python gate and the PowerShell twin through `pwsh -File`:

| Message | Expected |
|---|---|
| The exact new spec-research message, all three `-m` paragraphs joined by blank lines | Pass |
| `feat(x): y` + `Tasks: none` | Fail |
| `fix(x): y` with no task line | Fail |
| `feat(plan): add packet validator` + `Tasks: T3` | Pass |

Run `python -m pytest geeky-orchestration/test_quality_gates.py -q`, then `python geeky-orchestration/evals/scripts/check-c0-readiness.py`. Both must exit 0. If readiness pins the changed sources, refresh only those pins.

### W3. Commits
Make these commits, staging explicit paths only. Run the new gate on each message first.
1. `fix(gates): allow Tasks: none for pre-planning docs commits`. Includes both gates, the SKILL, `AGENTS.md`, the MCP docstring and the tests.
2. `docs(evals): record native Codex C0 commit-gate fix`. Create `geeky-orchestration/evals/analyses/c0-commit-gate-fix-20261029/` with `README.md`, `kanban.md`, `handoff.md` and `references.md`. Append a one-line "resolved by `<sha>`" note to `c0-codex-native-run-20261029/README.md`.

Do not push.

### W4. Fresh preparation
- Re-prepare the native candidate using `outputs/c0-codex-native-preparation-20261029/prepare-held.ps1` and `launch-command.ps1.txt` as templates, pinned to the new HEAD.
- Settings must match the Claude reference:
  - Case `c0-wordstat` on Windows MXC.
  - LiteLLM `vercel/gpt-6-luna` at high on all eight roles. Read the roles back and confirm.
  - `-Litellm -LitellmWireMode native`.
  - 6000 s hard budget, 60 s reserve, one attempt, zero recoveries.
  - Langfuse hooks from startup with the `LANGFUSE_CODEX_*` keys.
  - Prompt SHA-256 `124eba9b416324a052c8e25031f1660200f52a05a74c9a1d9ce13527b270ddde`, unchanged.
- Load credentials by dot-sourcing `outputs/c0-luna-live-20261028/credential-env.ps1` in its own process, before you set any harness variable. Never print values.
- Record the plugin SHA difference from `0b1f5fb`. It is a scoped change to the gate. The model, prompt and budget are unchanged.
- Write outputs to `outputs/c0-codex-native-fix-20261029/` and generate a fresh deadline at launch time. The deadline in any older record has expired, so never reuse it.

### W5. Launch
The owner authorizes exactly one native Codex C0 attempt, and only after W1–W4 pass. If any W1–W4 gate fails, stop and report; do not launch.
- Run exactly one attempt. Do not retry, resume or probe the provider.
- On a provider or protocol error, or on a timeout, preserve the capture, stop and report. Overtime continuation, as the owner granted Claude, needs separate written authorization.
- After the run:
  - Run the oracle 3 times.
  - Read Langfuse back with `evals/telemetry/langfuse-run.py --public-key-env LANGFUSE_CODEX_PUBLIC_KEY --secret-key-env LANGFUSE_CODEX_SECRET_KEY --base-url-env LANGFUSE_CODEX_BASE_URL`.
  - Run `parity-eval.py`.
  - Record the analysis under a new dated `evals/analyses/` folder with README, kanban, handoff and references.
- Process exit 0 is not acceptance.

## Constraints
- Never push, force, amend or use `--no-verify`.
- Do not edit historical captures, scores or earlier analyses beyond the one-line resolution note.
- Known friction, which you record but do not fix: Codex on Windows sometimes pipes a heredoc into `apply_patch` and gets `--codex-run-as-apply-patch requires a UTF-8 PATCH argument`. Codex researchers have no WebSearch or WebFetch and fetch docs over shell HTTP.

## Done
- W1–W3 are committed, the tests and readiness check exit 0, and the gate rejects `Tasks: none` outside `docs`.
- W4 prepared, with pins at the new HEAD.
- W5 launched one attempt, then the oracle ×3, Langfuse readback, parity eval, and analysis records were completed.
- The report lists commit SHAs, test counts, the preparation path and anything left undone.
