# Session evidence, 2026-10-24/25 (Linux MXC, LiteLLM, Langfuse)

These are working files from the cloud session that built the Linux MXC + LiteLLM + Langfuse eval path. They are checked in because the session's machine is ephemeral. The conclusions are in [lessons-learned.md](../../lessons-learned.md), [the runbook](../../mxc-litellm-runbook.md) and the two C0 analyses ([ant-claude](../c0-ant-claude-20261025/README.md), [ant-claudex](../c0-ant-claudex-20261025/README.md)). Every file was scanned for credential values before commit.

| Folder | What it shows |
|---|---|
| `runner-logs/` | Runner output for every paid C0 attempt: Codex attempts 3-5, Codex run 6, Codex on ant-claudex; Claude runs 2-4, both Claude ant-claudex attempts. Also the mock matrices and the refusal-resume mock tests. `backfill-codex5.ps1` replayed Codex attempt 5's rollout to Langfuse after its kill. |
| `mxc-spawn-ab/` | The A/B test behind mxc-sandbox 0.2.1. A `sleep 150` workload on the old host was SIGKILLed (exit 255) at 21 s; the fixed host completed 4/4. `stab.txt` holds three overlapping 300 s sandboxes on the fixed host, all exit 0. The `exit 134` lines are a first draft and a test-only config-copy race. |
| `slirp-watch/` | The liveness watcher that showed slirp4netns dying in the same second as bwrap, a symptom of the sandbox kill rather than its cause. |
| `content-filter-bisect/` | `probe.py` replays Claude C0 run 3's refused request against ant-claude. In `replay-1..4`, Claude Code run on the host returned "Authentication error". `replay-5/6` is the exact structured request resumed inside MXC: no refusal, the model continued with tool calls. |
| `codex-handoff-probe/` | A model-free probe of whether Codex `spawn_agent` handoffs reach rollouts in plaintext across multi-agent v1/v2 and catalog overrides (scripted loopback Responses server). |
| `judge-calibration/` | `candidate-root-turns.json`: every main-thread turn (`Codex Turn`, `Conversational Turn`) with its output, across environments `mxc`, `smoke` and `development`. These are the candidate examples for calibrating the `final_report_complete` judge; they are not labelled yet. |
| `preflight-claudex/` | The model-free preflight (both harnesses, C0, telemetry on) that passed before the ant-claudex runs. |

Not included here:
- The raw Langfuse observation dumps (about 100 MB per run). They are in the Langfuse project under the session ids in the analyses; refetch with `telemetry/langfuse-run.py --full`.
- The decompiled MXC SDK, the installers, the build output and the venvs. They are zipped at the repository root in [archives/session-20261025/](../../../../archives/session-20261025/README.md), outside the plugin folder.

The timed-out Claude ant-claudex run left uncommitted work. It is preserved in [its run folder](../../baselines/c0-wordstat/20261025T061414Z/uncommitted-at-timeout/): the untracked `review-impl.md` and the `handoff.md` diff.
