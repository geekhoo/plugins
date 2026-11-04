# macOS MXC eval kit (Claude Code harness)

Scripts and setup notes for running the geeky-orchestration evals with Claude Code inside the MXC sandbox
(Seatbelt backend) on a Mac whose endpoint-security tool, Santa, runs in Lockdown mode. These are the launchers
used for the C0 and C2 runs analysed in [`../analyses/c0-macos-mxc-sonnet-20261030`](../analyses/c0-macos-mxc-sonnet-20261030/README.md)
and [`../analyses/c2-macos-mxc-20261102`](../analyses/c2-macos-mxc-20261102/README.md), with machine paths taken
from the environment. No keys are in this folder; they live in a private file in the eval root.

Runs on such a Mac are not reference results: the only Python Santa allows is the Xcode 3.9.6, and the cases ask
for 3.11 or newer.

| File | What it does |
|---|---|
| `launch-c2.sh` | C2 `c2-linkvault`, any gateway model: `prepare` (free) or `run` (paid). Installs the compat layer for non-Claude models; `BRIDGE=1` starts the Messages-to-Responses bridge for the run |
| `launch-c0.sh` | C0 `c0-wordstat` with `claude-sonnet-5-5` |
| `bin/pwsh` | PowerShell as `dotnet pwsh.dll` (Santa blocks the dotnet-tool apphost, allows dotnet) |
| `langfuse.env.example` | template for `$MXC_EVAL_ROOT/langfuse.env`: Langfuse keys, OTel content and delivery flags |
| `probes/otel-pong.sh` | one-turn Claude Code call in MXC with native OTel export, to check telemetry before a paid run |
| `scoring/make-scope.mjs` | builds the `geeky-eval.inputs/1` scope and the `publish-run/` copy of `run.json` for one run (scoring step 5) |
| `bridge-scout/` | probes used to design `mxc-sandbox/bridge`: a request recorder and an effort sweep ([README](bridge-scout/README.md)) |

## Layout

Two locations, kept apart so that nothing private can be committed by accident:

- this repository checkout (`MXC_EVAL_REPO`, default: the checkout the script is in);
- the eval root (`MXC_EVAL_ROOT`, default `~/mxc-eval`), outside every repository:

  ```
  $MXC_EVAL_ROOT/
    langfuse.env          private, chmod 600 (from langfuse.env.example)
    secret-denylist.txt   optional, private: internal host/org names for the secret scan (one per line)
    tools/agent-py/       Xcode Python 3.9 venv with pytest: the oracle, the contestant's tests, the scorers
    pwsh-tool/            dotnet tool install of PowerShell (bin/pwsh runs it)
    mxc-home/             MXC_SANDBOX_HOME: built host (bin/), the sandbox's Claude config (home/)
    work/                 per-run seed workspaces and runner config
    bridge-logs/          per-run bridge request logs (BRIDGE=1)
  ```

The gateway comes from the operator's shell, never from a file in the repo: `ANTHROPIC_BASE_URL` and
`ANTHROPIC_AUTH_TOKEN`. On the test Mac the gateway is a local TLS proxy on 127.0.0.1, which the sandbox reaches
through MXC's `--host-loopback` (the runner passes it).

## One-time setup

1. Allowed toolchain: dotnet 10 at `/usr/local/share/dotnet`, node 22.18+ (24 used), git, `claude`, and the Xcode
   command-line Python at `/Applications/Xcode.app/Contents/Developer/usr/bin/python3`.
2. `mkdir -p "$MXC_EVAL_ROOT"`; copy `langfuse.env.example` to `$MXC_EVAL_ROOT/langfuse.env`, fill in the two
   Langfuse keys and the host, `chmod 600`.
3. `tools/agent-py`: a venv on the Xcode Python with pytest installed (the runner's error message names the
   expected shape: `uv venv` + `uv pip install --offline pytest`). The launchers put its `bin/` first on PATH so
   the runner never probes a blocked interpreter.
4. PowerShell: `dotnet tool install PowerShell --tool-path "$MXC_EVAL_ROOT/pwsh-tool"`. The kit's `bin/pwsh`
   finds the newest `pwsh.dll` there (`PWSH_DLL` overrides it).
5. Build the MXC host from the committed source:
   `MXC_SANDBOX_HOME="$MXC_EVAL_ROOT/mxc-home" pwsh mxc-sandbox/scripts/mxc.ps1 -Rebuild probe`.
   `run` refuses to start unless `mxc-home/bin/.source-hash` matches the committed host source.
6. Check telemetry once: `bash probes/otel-pong.sh` (one small paid call), then find the printed session id in
   Langfuse.

## Running

```
bash launch-c2.sh prepare <model> <effort>                 # free: materializes the launch, starts nothing
bash launch-c2.sh run <model> <effort> <AUTH_REF>          # paid: 10800 s budget, 900 s reserve, no recovery
BRIDGE=1 bash launch-c2.sh run gpt-6.1-sol high <AUTH_REF> # GPT through mxc-sandbox/bridge + compat layer
```

- Every paid run needs the owner's go and its own authorization reference
  (`owner-macos-mxc-<date>-c2-<model>-<effort>[-aN]`). Run one at a time.
- `run` requires a clean tree under `geeky-orchestration` and `mxc-sandbox` (except `evals/baselines`): the
  runner exports HEAD, and anything outside `geeky-orchestration/evals/` changes the plugin export.
- The Langfuse environment is `mxc-claude-mac` (override with `LF_ENV`) on every channel: native OTel spans,
  the post-run transcript upload and the session scores.

Scoring is the six-step pipeline in the C2 analysis README ("Method"), all on `tools/agent-py/bin/python`.

## Secrets

Three rules, learned the hard way (see the C2 analysis README, "Redaction"):

1. **Never put a secret on a command line.** Santa logs process arguments. Keys reach child processes through the
   environment (`set -a; . langfuse.env`), files with mode 600, or MXC's `--env NAME` (name only).
2. **Contestants can print their environment.** The runner scrubs every stored text file of a run
   (`evals/scripts/scrub-secrets.mjs`) right after capture, before hashing, analysis or upload, and again on the
   exported Langfuse observations, and fails the run if the scrub fails. It redacts the values of this process's
   secret-named variables, the Langfuse Basic-auth value, key-shaped strings and `NAME=value` env-dump lines.
   Live OTel spans leave during the run and cannot be scrubbed first; look for leaks in Langfuse too.
3. **Scan before every commit and push of eval records:**

   ```
   set -a; . "$MXC_EVAL_ROOT/langfuse.env"; set +a
   export GEEKY_SECRET_DENYLIST="$MXC_EVAL_ROOT/secret-denylist.txt"   # optional
   node evals/scripts/secret-scan.mjs --staged                 # before a commit
   node evals/scripts/secret-scan.mjs --git origin/main..HEAD  # before a push: added lines + messages
   ```

   It prints location and rule only, never the value, and exits 1 on any hit. Values that only look like secrets
   (a case app's own test tokens) go in `evals/scripts/secret-allow.txt`, one narrow regex each.

If a secret reaches a pushed commit: rotate it first (a rewrite does not un-publish it), then rewrite only the
affected branch with a `git filter-branch --index-filter` that replaces the value, reading the value from the
environment, scan the rewritten range, and force-push only with the owner's approval. Check Langfuse traces of the
same run.

## Machine notes

- Allowed by Santa: dotnet (Microsoft certificate), node (its team ID), `claude` (signing ID), git, zsh, the
  Xcode Python. Blocked: other Python builds, downloaded interpreters, ad-hoc-signed binaries (dotnet apphosts,
  dotnet-tool launchers; run the MXC host as `dotnet MxcClaude.dll`), `gh`, and the Codex CLI (OpenAI team ID),
  so Codex runs need another host.
- An endpoint control on the test Mac stops processes started with a very long command line. Claude Code takes
  the canonical prompt on argv (`-p`) and stays under the limit; the pi harness does not, so pi runs need another
  host or the control owner's approval of off-argv prompt delivery.
- Hooks inside the sandbox need an absolute node path (`NODE_BIN`); the sandbox's PATH does not include nvm.
- zsh heredocs need a writable `$TMPPREFIX`; the MXC host points it into the run's TMPDIR.

## Status (2026-11-04)

- C2 results (parity-eval/1.2): Sonnet high 95.30, Sonnet medium 96.47, GPT high via the bridge 94.24, GPT high
  without it 79.38 (BLOCKED in phase 2), GPT medium 22.83 (BLOCKED at plan review). Details in the C2 analysis.
- GPT models stop on contract or environment gaps (a year-10000 expiry, no Python 3.11) where Claude decides and
  continues: a model-behaviour finding, not a harness bug. A fair GPT reference needs a host with Python 3.11+,
  such as Linux MXC.
- Open with the gateway owner: whether its LiteLLM build includes the `/v1/messages` usage-mapping and effort
  fixes; the bridge makes this non-blocking.
- Not in this kit: the pi launchers (they drive `run-pi-baseline.ps1`, which lives on the pi branch).
