# Quickstart: run a geeky-orchestration eval in MXC (Claude Code or Codex)

This sheet takes you from a fresh Linux host to a scored run. Each step links to the doc that explains it. For the full procedure and the pitfalls table, read [mxc-litellm-runbook.md](mxc-litellm-runbook.md). The Windows / OAuth path is in [baseline-runs.md](baseline-runs.md).

Commands run from the repository root unless noted. `T=~/repos/.eval-tools` throughout.

For Windows preparation without oracle or contestant execution, use
`run-baseline.ps1 -PrepareOnly` for Claude and omit both `-Launch` and
`-MockAgent` for Codex. Claude's older `-DryRun` executes the seed oracle.
The [Windows claudex-001 preparation record](analyses/c0-claudex-001-preparation-20261025/README.md)
contains the model-specific setup history; qualification was subsequently waived
by the owner. The [Windows claudex-001 results](analyses/c0-claudex-001-win-20261026/README.md)
record Codex's completed run, Claude's same-folder continuation and cumulative
closeout, and the earlier router-fixed timeout.

Both runners accept a positive `-TimeoutSec`, optional `-AuthorizationReference`
and `-CloseoutReserveSec` (default 0, nonnegative and smaller than the wall budget).
The reserve is advisory time **inside** the hard wall; a proposed next-C0 value
is 900 of 5400 seconds, pending separate run authorization. Each authorized
refusal recovery shares the original deadline; `-ResumeOnRefusal` remains 0 by
default. Token ceilings remain informational. Both contestants receive identical
`GEEKY_DEADLINE_UTC`/`GEEKY_CLOSEOUT_RESERVE_S` context. See the
[record and timing contract](mxc-litellm-runbook.md#runner-record-and-timing-contract)
before recovering an interrupted run.

## A. Set up the host (once, ~20 min)

1. **System packages.** Ubuntu 24.04 was verified. MXC's Linux backend is described in [mxc-sandbox/README.md](../../mxc-sandbox/README.md).

   ```bash
   sudo apt install -y bubblewrap slirp4netns iproute2 iptables git
   # Also needed: .NET 10 SDK, PowerShell 7 (pwsh), uv, Node.js 22+
   ```

2. **The contestant CLIs.**

   ```bash
   # Claude Code: on PATH, or at ~/.local/bin/claude
   claude --version
   # Codex 0.164.0: the platform package's two binaries
   mkdir -p $T/codex/0.164.0/bin && cd /tmp && npm pack @openai/codex@0.164.0-linux-x64 --silent
   tar -xzf openai-codex-0.164.0-linux-x64.tgz
   cp package/vendor/x86_64-unknown-linux-musl/bin/{codex,codex-code-mode-host} $T/codex/0.164.0/bin/ && cd -
   mkdir -p $T/codex-home        # Codex state; no sign-in is needed with a LiteLLM provider
   ```

   A copy of that Codex package is also in [archives/session-20261025/](../../archives/session-20261025/README.md) (`installers.zip`).

3. **Sandbox Pythons.** The sandbox cannot `pip install`, so build the venvs on the host ([baseline-runs.md](baseline-runs.md), D75).

   ```bash
   uv venv --python "$(command -v python3)" $T/agent-py   && VIRTUAL_ENV=$T/agent-py   uv pip install pytest
   uv venv --python "$(command -v python3)" $T/geeky-mcp  && VIRTUAL_ENV=$T/geeky-mcp  uv pip install "mcp==2.3.0"
   pwsh -File geeky-orchestration/evals/scripts/install-agent-pythons.ps1     # pytest for every python3.X on PATH
   ```

4. **Telemetry hooks** (pinned and SHA-checked; see [telemetry/README.md](telemetry/README.md)):

   ```bash
   pwsh -File geeky-orchestration/evals/telemetry/install-telemetry-tools.ps1
   ```

## B. Set the environment (every shell)

```bash
export LITELLM_PROXY_URL=https://<your-litellm>     LITELLM_PROXY_API_KEY=<virtual key>
export TRACE_TO_LANGFUSE=true
export LANGFUSE_BASE_URL=https://<your-langfuse>    LANGFUSE_PUBLIC_KEY=pk-lf-...  LANGFUSE_SECRET_KEY=sk-lf-...
# Behind a TLS-inspecting proxy, also: SSL_CERT_FILE / REQUESTS_CA_BUNDLE / NODE_EXTRA_CA_CERTS
```

Never set `ANTHROPIC_AUTH_TOKEN` for LiteLLM. The Claude runner sends the key as `ANTHROPIC_API_KEY` itself (D104). Keys reach the sandbox by name only and are never printed.

## C. Preflight (free, ~2 min; do it before every paid run)

```bash
cd geeky-orchestration
pwsh -NoProfile -File evals/scripts/run-mock-matrix.ps1 -Case c0-wordstat
```

Both rows must say `PASS ... telemetry=delivered`. The checks are listed in [runbook §3](mxc-litellm-runbook.md#3-before-every-paid-run-the-preflight-no-model-calls). Any `FAIL` means the toolchain or tracing is broken; fix it before spending money.

## D. Run (paid; ~60-90 min each for C0; the two can run in parallel)

```bash
pwsh -NoProfile -File evals/scripts/run-codex-baseline.ps1 -Case c0-wordstat -Model <litellm-model> -Litellm -Launch -TimeoutSec 5400
pwsh -NoProfile -File evals/scripts/run-baseline.ps1       -Case c0-wordstat -Model <litellm-model> -Litellm -ResumeOnRefusal 2
```

- **Cases:** `c0-wordstat` (start here), `c1-csvledger`, `c2-linkvault`, `c3-minisql` ([cases](cases/)).
- **Progress:** watch the commit count in `~/repos/eval-<case>-<stamp>`.
- **Output:** each runner ends with `stored: evals/baselines/<case>/<stamp>`.
- **Warning signs:** exit 255, repeated `API Error: 400`, or more than two refusal resumes. See the [pitfalls table](mxc-litellm-runbook.md#7-pitfalls-warning-and-guidance).

## E. Score and publish (~15 min per run)

```bash
P=$T/agent-py/bin/python; RUN=evals/baselines/c0-wordstat/<stamp>; H=claude-code   # or codex
OUT=evals/analyses/<your-analysis>/$H; SID=$(python3 -c "import json;r=json.load(open('$RUN/run.json'));print((r.get('telemetry') or {}).get('session_id') or r['session_id'])")
$P evals/telemetry/langfuse-run.py --session-id $SID --output /tmp/sum.json --full /tmp/obs.json
$P evals/scripts/score-run.py $RUN --harness $H --out $OUT
# Judge the needs_judge items against the workspace and write $OUT/manual-verdicts.json
#   (format: any existing analyses/c0-*/<harness>/manual-verdicts.json)
$P evals/scripts/score-run.py $RUN --harness $H --manual $OUT/manual-verdicts.json --out $OUT
$P evals/scripts/parity-eval.py $RUN --observations /tmp/obs.json --score $OUT/score.json --manual $OUT/manual-verdicts.json --out $OUT
$P evals/telemetry/langfuse-scores.py --run $RUN --parity $OUT/parity.json
```

- **Read `parity.json`** for the comparable composite (D103). score-run's own composite is not comparable across harnesses.
- **Check every failing check** against the run before trusting the number ([runbook §6](mxc-litellm-runbook.md#6-after-the-run)).
- **Commit** the run folder and the analysis folder. Keep `/tmp/obs.json` out of git; it is in Langfuse.

## F. Where to look next

| Need | Doc |
|---|---|
| Every pitfall, with guidance | [mxc-litellm-runbook.md §7](mxc-litellm-runbook.md#7-pitfalls-warning-and-guidance) |
| Why things are the way they are | [lessons-learned.md](lessons-learned.md), [agent-eval-decisions.md](../docs/agent-eval-decisions.md) (D101-D104) |
| Telemetry, coverage, Langfuse scores and evaluators | [telemetry/README.md](telemetry/README.md), [telemetry/langfuse-evaluators/](telemetry/langfuse-evaluators/README.md) |
| Codex adapter internals | [adapters/codex/README.md](adapters/codex/README.md) |
| What the C0 cases check | [cases/c0-wordstat/spec.md](cases/c0-wordstat/spec.md) |
| Results so far | [C0 on ant-claude](analyses/c0-ant-claude-20261025/README.md), [C0 on ant-claudex](analyses/c0-ant-claudex-20261025/README.md) |
| Session evidence and archives | [session-20261025-evidence/](analyses/session-20261025-evidence/README.md), [archives/session-20261025/](../../archives/session-20261025/README.md) |
