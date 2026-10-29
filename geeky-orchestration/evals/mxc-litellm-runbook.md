# Runbook: Claude Code and Codex evals in MXC, through LiteLLM, traced to Langfuse

Both evaluations are stopped. The [latest pair](analyses/c0-fresh-sequential-20261027/README.md)
produced no implementation. Its [offline follow-up](analyses/c0-root-causes-20261027/README.md)
adds planning budget checks and explicit rejection of the observed tool-call text;
upstream attribution and live effectiveness remain unresolved. Source changes
are uncommitted, and old prepared commands/pins must not be reused. A later source
commit requires authorization, followed by fresh preparation; launch remains separate.

For historical completed Windows `claudex-001` attempts, see the
[C0 comparison](analyses/c0-claudex-001-win-20261026/README.md). Codex completed
at parity 97.46. Claude completed its same-folder continuation at cumulative
parity 98.33 after the earlier timeout at 90.33. The continuation used additional
time and retained conversation context. These results do not replace native
qualification proof.

This is the process that produced complete C0 runs on both harnesses (2026-10-25). It covers Linux MXC (mxc-sandbox 0.2.1, Bubblewrap), models served by a LiteLLM proxy, full-content Langfuse tracing, and harness-neutral scoring. Windows specifics and the older C1 procedure are in [baseline-runs.md](baseline-runs.md). The reasons behind each step are in [lessons-learned.md](lessons-learned.md) and the D-numbers in [agent-eval-decisions.md](../docs/agent-eval-decisions.md).

Short version: [QUICKSTART.md](QUICKSTART.md). Results so far: [C0 on ant-claude](analyses/c0-ant-claude-20261025/README.md), [C0 on ant-claudex](analyses/c0-ant-claudex-20261025/README.md).

## Current authorization hold

The [2026-10-27 V2 mapping fix](analyses/codex-v2-litellm-mapping-20261027/README.md)
adds an authenticated host-side wire bridge for future Codex `-Litellm -Launch`
invocations. It translates V2 messages/functions before LiteLLM and restores
plaintext collaboration metadata on JSON/SSE responses. Native V2 roles and
effort settings remain in use. One bounded synthetic provider request passed;
it started no Codex/Claude/MXC evaluation and does not supply full workflow or
telemetry qualification. Both evaluations are stopped. Historical launch and
recovery recipes below grant no new authority.

Read [C0 operator readiness](c0-readiness.md) before using the procedures below. Local inventory and mock checks pass; live telemetry compatibility and paid canaries remain held. Launch only the separately authorized attempt with explicit role models/efforts, budget/reserve, recovery limit, waiver and authorization reference. Remote score publication and any judge inference need their own covered scope. Read-only session queries do not prove publisher write/readback.

## Runner record and timing contract

Both runners persist `run.json` before configuration/preflight and contestant
launch, then update it to running before invoking MXC. `execution.schema` is
`geeky-eval.execution/1`. Its `attempt_id`, `segment_id`,
`authorization_reference` (an operator-supplied reference, not a grant of authority),
`allowed_recoveries`, `qualification_waiver`, whitelisted `configuration` and
`configuration_sha256` bind the local record. Existing prompt/plugin/profile/model
fields remain alongside it. Credentials and the full environment are never
fingerprinted. An owner qualification waiver still skips the existing probes and
does not establish runtime qualification; preparation does not start an oracle
or contestant. Claude's legacy `-DryRun` still executes the seed oracle.

`hard_wall_budget_s` is positive. The initial UTC deadline and monotonic elapsed
time begin when the prepared record is created; configuration, seed checks and
authorized refusal recovery consume that same budget. Before **every** contestant
launch, remaining seconds are floored at invocation preparation; below one whole
second no child starts.
MXC never receives zero (unlimited). `allowed_recoveries` defaults to zero;
no generic transient retry is added. Both existing environment argument lists
carry `GEEKY_DEADLINE_UTC` and `GEEKY_CLOSEOUT_RESERVE_S`. The reserve defaults
to zero, must be smaller than the hard budget, and only advises the existing
dispatch/phase boundaries to prioritize required acceptance and closeout. The
proposed next-C0 900-second reserve within 5400 seconds is uncalibrated and needs
separate launch authorization. Reserve/deadline expiry cannot pass an unmet gate.
Case token ceilings are **informational**, without a live token supervisor.

Each `invocations[]` entry retains its ID, kind, supplied timeout, timestamps,
exit code and outcome. `process_outcome` is independent of `capture_status`,
`postprocessing` step statuses and `analysis_status`; `workflow_acceptance` stays
`not-established`. A known timeout/crash retains its top-level exit reason when
parsing, oracle, diagnostics or telemetry fails. A successful child never proves
workflow acceptance. Running capture interrupted by an exception is `unknown`
with `capture_status=incomplete`; later failures identify the active step.
`contestant_time_s` sums measured invocation intervals, each beginning before its
running-record write and ending when the synchronous MXC call returns. It therefore
includes record handling as well as the MXC call. `attempt_elapsed_s` includes budget
consumption between launches, and `finalization_time_s` measures subsequent local
capture/analysis work separately. These measurements do not isolate startup from
termination overhead or prove an upper bound on timeout excess.

Post-processing can exceed the contestant wall. Existing Codex replay MXC timeout
is 900 seconds, sandbox telemetry hooks retain 600 seconds, and telemetry polling
retains its 120-second wait setting. These are separate step settings, **not**
extra contestant allowance. Synchronous seed/result oracles, Claude host flush,
host telemetry/coverage processes and analysis have no enclosing process deadline;
the 120-second poll setting is not a hard process kill. `step_timeouts_s` records
these distinctions with null for unbounded steps. This patch adds no universal
post-processing cancellation or process-tree cleanup guarantee.

Runner JSON writes use a same-directory temporary file and atomic replacement;
the analyzer writes into `derived/`, then its result is merged atomically. Existing
raw stream/stderr and native transcripts are retained, with Git HEAD/status and
available artifact SHA-256 hashes in the final execution record. Failed replacement
leaves the previous valid record. A hard host death can leave prepared/running or
in-progress steps; `finally` cannot guarantee recovery. Before any separately
authorized continuation, explicitly reconcile the last valid metadata, partial
bytes, `writer_host`/`writer_pid`, MXC/contestant descendants and workspace state;
verify **no surviving writer** before changing records. Mark unresolved outcomes
interrupted/unknown, never completed. No automatic continuation is provided. A
later authorized segment needs its own deadline and links to the retained initial
result; do not reinterpret an unfinished record as accepted.

## 1. One-time setup (Linux host)

1. **Sandbox backend:** `apt install bubblewrap slirp4netns iproute2 iptables`. You also need the .NET 10 SDK, `pwsh`, `uv`, Node 22+ and `git`.
2. **Contestant CLIs:**
   - Claude Code on `PATH`. The host uses `~/.local/bin/claude`, else the first `claude` on `PATH`, else `MXC_CLAUDE_EXE`.
   - Codex 0.164.0 at `~/repos/.eval-tools/codex/0.164.0/bin/codex`.
3. **Sandbox Pythons with pytest:**
   - `~/repos/.eval-tools/agent-py`: a uv venv on a system Python, with pytest.
   - `~/repos/.eval-tools/geeky-mcp`: the `mcp` package.
   - Then run `pwsh -File evals/scripts/install-agent-pythons.ps1`, so every `python3.X` on the sandbox `PATH` also has pytest.
4. **Telemetry hooks:** run `pwsh -File evals/telemetry/install-telemetry-tools.ps1`. It installs the pinned Claude hook, the Codex tracer and the `langfuse-py` venv.

## 2. Environment (host shell)

| Variable | Purpose |
|---|---|
| `LITELLM_PROXY_URL`, `LITELLM_PROXY_API_KEY` | The LiteLLM proxy and its virtual key. |
| `TRACE_TO_LANGFUSE=true` | Turns telemetry on for both runners. |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` | Langfuse project. Codex prefers `LANGFUSE_CODEX_*` when set. |
| MXC platform environment | Runners select `mxc-win`, `mxc-linux` or `mxc-mac` and the matching `codex-mxc-*` / `claude-mxc-*` family. Host identity overrides are not used. |
| `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` / `NODE_EXTRA_CA_CERTS` | Only behind a TLS-inspecting proxy. They pass through to the sandbox. |

Keys reach the sandbox only as bare `--env NAME`; the MXC host copies the value and never prints it.

## 3. Before every paid run: the preflight (no model calls)

```bash
pwsh -NoProfile -File evals/scripts/run-mock-matrix.ps1 -Case c0-wordstat
```

Both rows must read `PASS` with `telemetry=delivered`. The Claude row runs `-MockScenario all,happy`, about 74 checks: pwsh, python and pytest on every `python3.X`, git identity, the plugin's .py and .ps1 gates, grants, the MCP handshake, HOME outside the workspace, and the Langfuse hook. The Codex row runs 9 checks, including its gates and its Langfuse Stop hook. Drop `-Case` to cover C0–C3.

## 4. Launch (in parallel is fine)

```bash
cd geeky-orchestration
pwsh -NoProfile -File evals/scripts/run-codex-baseline.ps1 -Case c0-wordstat -Model <litellm-model> -Litellm -Launch -TimeoutSec 5400
pwsh -NoProfile -File evals/scripts/run-baseline.ps1       -Case c0-wordstat -Model <litellm-model> -Litellm -ResumeOnRefusal 2
```

- **Claude** receives the LiteLLM key as `ANTHROPIC_API_KEY`, sent as `x-api-key`. The runner clears `ANTHROPIC_AUTH_TOKEN` and the OAuth token.
- **Codex** gets a `litellm` provider on the Responses wire API, plus a catalog entry that forces classic function tools.
- Both run **runner-default reasoning**: Codex `high`, Claude Code its own default.

## 5. While it runs

- **Progress** is the commit count in the run workspace, `~/repos/eval-<case>-...`. C0 runs commit in this order: spec → plan → plan-review → per task or phase → final review.
- **Normal:** quiet stretches of 10+ minutes while reviewers run, Codex `wait_agent` loops, and one `[claude-code:unrecognized_model]` line in Claude's stderr.
- **Not normal:**
  - exit 255 (a sandbox kill; check that the host is 0.2.1 or later);
  - repeated `API Error: 400` in `stream.jsonl` (LiteLLM routing; see pitfalls);
  - `provider refusal: resuming` more than twice.
- **Watching from a cloud session:** use read-only checks (`/proc`, `git rev-list --count`). Never `pkill -f` or `kill`.

## 6. After the run

1. **Commit the run folder**, `evals/baselines/<case>/<stamp>/`, as evidence. Commit failed runs too.
2. **Telemetry** is already in the folder:
   - `run.json.telemetry`: human-readable `session_id`, `agent_family`, `environment`, `delivered`, `observations`, `coverage_complete`;
   - `langfuse.json`;
   - `langfuse-coverage.json`.

   Codex runs replay their rollout after the run (`host_flush`), so timeouts and kills still reach Langfuse.
3. **Score**, the same way for both harnesses:

   ```bash
   P=~/repos/.eval-tools/agent-py/bin/python
   $P evals/telemetry/langfuse-run.py --session-id <run.json.telemetry.session_id> --output /tmp/sum.json --full /tmp/obs.json   # 50-100 MB; keep it out of git
   $P evals/scripts/score-run.py <run> --harness <claude-code|codex> --out <analysis-dir>                   # Quality (harness-neutral)
   # Judge the needs_judge items by hand against the workspace -> <analysis-dir>/manual-verdicts.json
   $P evals/scripts/score-run.py <run> --harness <h> --manual <analysis-dir>/manual-verdicts.json --out <analysis-dir>
   $P evals/scripts/parity-eval.py <run> --observations /tmp/obs.json --score <analysis-dir>/score.json --manual <analysis-dir>/manual-verdicts.json --out <analysis-dir>
   $P evals/telemetry/langfuse-scores.py --run <run> --parity <analysis-dir>/parity.json --scope <evaluation-inputs.json> --output <analysis-dir>/score-readback.json # explicit scope; exact readback required
   ```

4. **Audit before you trust a number.** Check every failing check, and the sensitive passes (stage windows, orchestrator code edits), against the raw evidence. Every scoring bug found this session was found that way.
5. **Compare harnesses with `parity.json`, not `score.json`.** score-run's Adherence, Consistency and Task tier read each harness's transcript through its own parser and are not comparable across harnesses.

New traces use platform-specific environments and actor-specific user IDs.
All agent traces share the readable run session; parent relationships remain
metadata links. See [agent and run identities](telemetry/README.md#agent-and-run-identities).
Older results below retain their original `mxc` environment and native session IDs.

## 7. Pitfalls: warning and guidance

| Warning | What happens | Guidance |
|---|---|---|
| **Sandbox killed with exit 255 after 20 s to a few minutes** | bwrap's `--die-with-parent` fires when the *thread* that forked it exits; the MXC SDK forked from a thread-pool worker. | Fixed in mxc-sandbox 0.2.1 (dedicated spawn thread). Upgrading slirp4netns does nothing; it dies as a symptom. |
| **Wrong LiteLLM auth** | Sending the key as `ANTHROPIC_AUTH_TOKEN` (bearer) is the wrong path for LiteLLM. | The key goes in `ANTHROPIC_API_KEY`, as with `anthropic.Anthropic(base_url=..., api_key=...)`. The runner does this; do not hand-roll env. |
| **Claude Code on the host gets "Authentication error"** | Direct host calls to LiteLLM failed while the same key worked inside MXC. | Run Claude only through the runner or the MXC host. Do not probe from the host. |
| **LiteLLM router 400: `requires a native Responses target`** | A complexity router (`ant-claudex`) sent a Messages-format request to a Responses-only backend. The Claude run aborted after 2.5 min. | Give the route a Messages-compatible target or fallback in LiteLLM before running Claude on it. Codex is unaffected. |
| **Provider content filter ends a Claude run** | `stop_reason: content_filter`, "considered high risk" (mimo behind `ant-claude`). It is intermittent: 8 replays of the refused request passed. | `-ResumeOnRefusal 2`. Each resume is an intervention, and the run is not reference-eligible. Without the flag the run reads `provider_refusal`. |
| **Same model name, different model** | A complexity router sends differently shaped requests (one harness vs the other) to different backends. | Treat router models as a confound. Prefer a fixed model for parity runs. |
| **Reasoning differs between harnesses** | Codex runs at `high`. Claude Code requests no thinking for a model name it does not recognise (0 thinking tokens). | Record it as a confound, or equalise it deliberately (`claude --effort`). |
| **C0 time ceiling** | Claude on `ant-claudex` hit 5400 s during the final review fix. | For slow routes, raise `-TimeoutSec` (Codex) or `wall_time_ceiling_s` in `case.json` before the run. |
| **C0 token ceiling is stale** | `case.json` says 6M; real C0 runs used 11.7M–21.9M, mostly cached input. | Recalibrate before reading `over_token_ceiling`. |
| **Codex trace refused by score-run** | Its loader rejected interrupted children and rejected spawns (fixed). Its process parser expects Windows PowerShell board edits. | Use parity-eval for cross-harness process scores. score-run is still right for Quality. |
| **Stage boundaries** | Codex pre-reads every SKILL.md up front; Claude commits a stage late; history rewrites move commit times. | parity-eval uses reflog times and ignores batched skill reads. Sanity-check `stage_bounds` against the dispatch timeline. |
| **Forbidden git hidden in a "fix"** | Claude ran `git reset --soft HEAD~1` to unstage a file. That is amend by other means, and the D24 hard gate sets adherence to 0. | Read the reflog. It is a real rule break, not a scorer artefact. |
| **Langfuse readback looks short** | v4 ingests asynchronously (4/10 scores, then 20/20 seconds later). | Poll until counts are stable (`langfuse-run.py --wait`). Reads go through `/api/public/v2/observations` and `/api/public/v3/scores`. |
| **Codex Langfuse upload missing after a kill** | The Stop hook only fires at turn end. Node ignores `HTTPS_PROXY`. | The runner replays the rollout inside MXC (`host_flush`), with `LANGFUSE_TIMEOUT=300`. |
| **Unexpected extra tags** | Host `LANGFUSE_CODEX_TAGS` / `CC_LANGFUSE_TRACE_TAGS` are appended to the mandatory run/actor tags. | Unset them for clean traces. MXC user IDs and environments are generated from source-bound actor identity and the actual platform. |
| **Tracer smoke tests write to real Langfuse** | A local trace-name test uploaded duplicates under `development`. | Point tests at a local OTLP sink, or expect the duplicates. |
| **Live run folders trip the stop hook** | Untracked `evals/baselines/...` while a run writes. | Exclude them in `.git/info/exclude` until the run ends, then remove the line and commit the folder. |
| **Sandbox HOME was the workspace** | Claude Code and pwsh wrote `.cache/` into the contestant repo. | Fixed: the host sets a private HOME. The mock checks `env.home_outside_workspace`. |
| **`python3.11` had no pytest** | Agents test on the contract's minimum Python. | `install-agent-pythons.ps1`. A literal `/usr/bin/python3.11` path still bypasses `PATH`. |
| **`~/.local/bin/claude` disappeared** | An auto-update removed it mid-session. | The host falls back to `claude` on `PATH`. |
| **Code evaluators rejected by Langfuse** | "Code evaluations are not enabled for this deployment." | Set `LANGFUSE_CODE_EVAL_DISPATCHER=insecure-local` and `QUEUE_CONSUMER_CODE_EVAL_EXECUTION_QUEUE_IS_ENABLED=true` on the server. Source is in `telemetry/langfuse-evaluators/`. |
| **LLM judge runs before calibration** | An enabled rule scores every main-thread turn, at one paid call each. | Keep the rule disabled until the judge is calibrated (`telemetry/langfuse-evaluators/README.md`). |
| **Cloud-session safety check gives no verdict** | Transient. Repeated retries slow down and can end the turn. | Stop after two tries, do read-only work, and retry later. |

## 8. Open items

- Calibrate the `final_report_complete` judge (pinned to `zen/gpt-6-luna`, rule disabled) on labelled turns before enabling it.
- Rerun Claude C0 on `ant-claudex` with a higher time ceiling, and run three runs per harness for variance (D60).
- Fix or pin the router route so both harnesses hit the same backend, then rerun with reasoning matched.
- Recalibrate the C0 token ceiling.
