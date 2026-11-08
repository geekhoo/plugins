# macOS MXC findings

What the macOS MXC work established, kept as a point of reference. None of these runs is a reference baseline: the numbers are for orientation, and each carries its state below.

The runs stay on this repo's remote, on branch `opus/macos-mxc-c0` at `8c3597c`, which is kept and not merged. Their records are under `geeky-orchestration/evals/baselines/<case>/<stamp>/` on that branch:

```bash
git show origin/opus/macos-mxc-c0:geeky-orchestration/evals/baselines/c3-minisql/20261104T083537Z/run.json
```

Eight later scorer commits, `f4c1240` to `4e6fdd8`, and the local `parity-eval/1.3` numbers come from the fork `gkhoo-c-gif/plugins`, branch `opus/macos-mxc-c0`, at `35e40d1`. Code paths below refer to `8c3597c`, except the `parity-eval/1.3` scorer readers, which refer to `35e40d1`.

## Results

All 10 runs used the Claude Code harness in MXC on macOS, through the LiteLLM gateway. Santa allowed only Python 3.9.6, so none is a reference result.

| Case, run | Model, effort | Route | Outcome | Time (s) | Commits | Oracle passed | Tokens | Parity |
|---|---|---|---|---:|---:|---:|---:|---:|
| C0 `20261029T161528Z` | Sonnet 5.5, default | gateway | stopped at the first budget check | 233 | 1 | 0/13, all errors | 0.40M | none |
| C0 `20261030T043030Z` | Sonnet 5.5, default | gateway | 5 stages, PASS | 1261 | 10 | 13/13 | 12.26M | 61.11 |
| C2 `20261101T192141Z` | Sonnet 5.5, high | gateway | 5 stages, PASS | 4354 | 14 | 136/136 | 40.83M | 95.30 |
| C2 `20261101T225826Z` | Sonnet 5.5, medium | gateway | 5 stages, PASS | 1938 | 13 | 136/136 | 13.46M | 96.47 |
| C2 `20261102T053248Z` | GPT-6.1-sol, high | compat, bridge | 5 stages, NEEDS FIXES for Python evidence only | 4487 | 8 | 136/136 | 18.97M | 94.24 |
| C2 `20261101T211028Z` | GPT-6.1-sol, high | gateway | BLOCKED in phase 2 | 3074 | 6 | 136/136 | 9.97M | 79.38 |
| C2 `20261101T222922Z` | GPT-6.1-sol, medium | compat | BLOCKED at plan review, no code | 1151 | 3 | 0/136, all errors | 5.47M | 22.83 |
| C2 `20261101T205532Z` | GPT-6.1-sol, high | gateway | BLOCKED during research | 288 | 0 | 0/136, all errors | 1.60M | none |
| C3 `20261104T083537Z` | Opus 5.5, high | gateway | 5 stages, PASS in round 3 | 7652 | 20 | 181/183 | 38.96M | 36.84, unpublished |
| C3 `20261104T104418Z` | GPT-6.1-sol, high | compat, bridge | 5 stages, PASS | 6716 | 10 | 181/183 | 22.36M | 76.67, unpublished |

Process trace coverage for these runs is in [process-trace.md](process-trace.md#results-on-retained-runs).

### State of the parity numbers

| Runs | State |
|---|---|
| C0 `20261030T043030Z` | Published under `parity-eval/1` |
| The five scored C2 runs | Published under `parity-eval/1.2`, with judge verdicts from Sonnet 5.5 |
| C3, both runs | Local `parity-eval/1.3` only, never published, with judge verdicts from Sonnet 5.5 |
| C0 `20261029T161528Z`, C2 `20261101T205532Z` | Not scored |

- Stored files were redacted after scoring, so the 6 published scores can't be re-verified from the repo alone. The scopes bind originals kept outside it.
- Under `parity-eval/1.3` the C2 bridge run reads 97.03 locally. Its published value stays 94.24.
- `parity-eval/1.3` redefines `a.commit_gate`, so its numbers aren't directly comparable with 1.2, and it has the false-credit defect described below.
- C2 `20261101T211028Z` has `reference_eligible: true` in `run.json`, although its analysis says none of these runs can serve as a reference. The analysis is right.

## C3 reference

Use these when running C3. They show roughly what a full run costs and how it behaves. They aren't a baseline to score against: [the provisional ceilings](baseline-runs.md#limits-derived-from-the-baselines-o13-requirements) stay in force until a reference-eligible run exists. The C3 contract requires Python 3.11+, which these runs didn't have.

| Measure | C3 `20261104T083537Z` | C3 `20261104T104418Z` |
|---|---|---|
| Model, effort | Opus 5.5, high | GPT-6.1-sol, high |
| Route | gateway | gateway, compat layer, bridge |
| Wall time, of a 21,600 s budget | 7,652 s | 6,716 s |
| Tokens, against the 50M ceiling | 38.96M | 22.36M |
| Input from cache | 90.1% | 92.9% |
| Model calls | 115 | 119 |
| Subagents | 31 | 23 |
| Tasks, phases | 11, 4 | 6, 3 |
| Commits | 20 | 10 |
| Final review | NEEDS FIXES, PASS in round 3 | PASS in round 1 |
| Oracle, stable over 3 | 181 passed, 1 failed, 1 skipped | 181 passed, 1 failed, 1 skipped |
| Run's own test suite | 673 passed, 2 skipped | 1,600 passed, 2 skipped |
| Local `parity-eval/1.3` | 36.84 | 76.67 |
| Quality / Adherence / Consistency, our rerun without judge verdicts | 40 / 0 / 95.29, composite 36.73 | 40 / 100 / 100, composite 76.67 |

On frozen QACT without judge verdicts (`score-run.py`, 300-line reference), Opus scores 37.1 and Sol 60.2. With the oracle and forbidden-git gates removed, both score 77.1. The rescore and the comparison with Windows Codex run `463d8062` are in [the 8 November C3 Windows analysis](analyses/c3-codex-sol-win-20261108/README.md#against-the-macos-c3-pair).

Both ran Claude Code 2.1.318 with plugin `52160ef`, prompt `124eba9b`, a 900 s closeout reserve, no recoveries and Python 3.9.6. Their Langfuse sessions begin `2b944b7c` and `4df94188`, environment `mxc-claude-mac`.

When comparing a new C3 run with these:

- **Oracle:** expect 182 passed and 1 skipped on Windows. The Mac's failure is `test_ac1_import_scan`, which needs Python 3.10+. The Mac's skip comes from its case-insensitive filesystem.
- **Parity:** don't compare composites directly. Both Quality scores are capped at 40 by that failure, and Opus Adherence is 0 from the forbidden-git gate.
- **Plugin:** `52160ef` isn't `main`. A run from `main` has a different budget split and other contestant-visible differences.
- **Sample:** there is one run per configuration, and each plan differs in size.

## What the runs support

- GPT through the bridge can complete all five stages, on C2 and C3.
- Blocking behaved as designed. No blocked or bridge report made a false PASS claim.
- Review loops found real defects, such as large-integer handling in the C3 GPT run.

There is one run per configuration, and route, compat layer, plugin version and plan size all vary. These runs do not rank models or isolate the bridge's effect, and they say nothing about Python 3.11+ behaviour. Sonnet's two efforts alone differ by 1.17 parity points.

## Reading the low scores

- **C3 Quality is capped from about 88 to 40 on both runs.** The one failing oracle test, `test_ac1_import_scan`, calls `sys.stdlib_module_names`, which needs Python 3.10+. The cap comes from the host, not the work.
- **C3 Opus Adherence is 0.** It ran `git worktree remove --force` five times to delete its own throwaway worktrees. The owner ruled that this stays forbidden. Without the gate its Adherence would be 93.59.
- **C0 r1 stopped on the runner, not the model.** A 7-digit deadline fraction meets Python 3.9's parser, the budget helper returned `invalid`, and the prompt requires a stop there.
- **Why GPT blocked:**
  - a1: it reported no wait or receive tool, although the reports had arrived.
  - a2: its reviewer returned BLOCKED on conflicting expiry requirements and a Python 3.11 defect.
  - Medium: it could not establish Python 3.11+.

## Interventions on non-Claude routes

A comparison between models has to account for these. The Claude runs had neither layer, and the kit has no bridged-Claude control.

**Compat layer** (`evals/adapters/claude-code-litellm-compat/`):
- Coaches the model: "Do not stop or checkpoint for lack of a wait tool" (`compat-hook.mjs:73`). Stopping there is the behaviour a run would otherwise measure.
- Forces `run_in_background: false` on subagents (`compat-hook.mjs:65`).
- Adds a preamble with stage order and skill names (`make-shim.mjs:25-29`).

**Bridge** (`mxc-sandbox/bridge/bridge.mjs`):
- Drops `temperature`, `top_p`, `top_k`, `stop_sequences` and `context_management` (`:28`).
- Drops server tools (`:108`).
- Sends medium effort when none is given, and maps `max` to `xhigh` (`:91`, `:15`).
- Maps only `content_filter` to `refusal` (`:216`).

**Not recorded on these runs:** the branch's `run-baseline.ps1:465` writes `Interventions: none` on every run, and that script never mentions either layer. On `main`, `run.json.route_interventions` records these once declared with `-DeclaredIntervention`. The score scope doesn't carry them yet.

## Readers real runs needed

A scorer has to read these shapes, or it marks completed work as failed. Parity results moved on the C2 bridge run and both C3 runs when they were added.

- Lane moves through a heredoc-written helper called by variable or in a loop, and through inline Python.
- Commits through a shell function that wraps `check-commit`.
- Qualified headings such as `## Implementation Run Summary`.
- The prescribed fix-commit wording with "required" as well as "critical".
- `git stash push` is not a push. Check that the subcommand follows `git`.
- Count gate runs and commits over the same stage window. Counting them over different windows failed a run that gated every commit.

Traps in those fixes:
- **False credit:** the new `commit_gate_runs` gives 3 passes for a helper whose gate fails three times with nothing committed, and 2 for a helper called only inside `if false`. Run on both commits; at `8c3597c` each gives 1. Hidden passes need proof that the gate ran.
- **Missed pushes:** the forbidden-git regex should now miss `git -C "a b" push` and `git --git-dir x push`. Read from the regex, not run.
- **Labels:** `c75c4d0` changed logic while keeping the 1.3 label, and 1.2 cannot be reproduced from the tip. Each logic change needs its own version.
- **Portability:** `score-run.py:827` raises `OSError: [Errno 22]` on Windows for near-epoch timestamps.

## Evaluation practice

- **Check the judge's model in the transcript.** `CLAUDE_CODE_SUBAGENT_MODEL` overrode an agent call with no explicit model, so the C3 judges and eval agents ran on Sonnet, not the Opus requested. The C2 judges were Sonnet too.
- **Contestants can print their environment.** One run's `printenv` carried a gateway key into transcripts and traces. Both runners on `main` now scrub stored files before hashing, but they can't reach spans the hook already sent from inside the sandbox. A telemetry run with any redaction records `telemetry_exposure: possible`.
- **Redaction breaks hash bindings.** `raw_sha256` no longer matches the stored transcripts on 4 runs, and redacted scope sources no longer match their recorded hashes. Keep originals, and hash after scrubbing.
- **A shared telemetry label needs one meaning.** `exit_reason` is `completed` on blocked runs, so it reports the process, not the workflow.

## Workflow findings

- Commit gate friction: both C2 Sonnet runs hit the 72-character limit with a 73-character subject.
- A failed commit gate followed by another `git add` bundled two tasks' files into one commit. The branch adds a rule to the implement skill: stage nothing else until that commit exists.
- Reviewers often had no shell, so their reviews were static.
- Sonnet C2 reports note that no PM agent type exists.

## Host facts

Read from source, not run:
- macOS: zsh heredocs need a writable temp prefix (`Program.cs:199,302`), and Santa kills the .NET apphost, so `mxc.ps1:63` and `macos-mxc/bin/pwsh` avoid it.
- macOS: `--host-loopback` also sets ingress default to Allow (`Program.cs:218`), and the runner always passes it.
- Linux: `Program.cs:218-219` sets HostLoopback Allow with default Deny, which its own comment at `:214-215` says the SDK rejects. A Linux reference host may hit this.

## Code worth porting

The branch stays as it is and nothing here is merged. Port by need.

| Item | Path | Before using it |
|---|---|---|
| Bridge | `mxc-sandbox/bridge/` | Record it as an intervention. Stream failures log `status:200`, so "all 200" does not prove success |
| Compat layer | `evals/adapters/claude-code-litellm-compat/` | Decide first whether coaching is acceptable in a scored run |
| Node gates and MCP | `scripts/*.mts`, `mcp/server.mts` | Needed only on Python-restricted hosts. It lacks `geeky_workflow_budget`, its implement target is 0.90 against 0.75 here, and its guard has no `GEEKY_STAGE` |
| Scorer readers | `evals/scripts/analyze-run.py` | Fix the false credit first, and use a new evaluator version |
| macOS host fixes | `mxc-sandbox/scripts/` | Needed for any macOS host |
