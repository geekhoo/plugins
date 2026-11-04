#!/bin/bash
# launch-c0.sh: C0 c0-wordstat, Claude Code + claude-sonnet-5-5, in MXC (Seatbelt) on macOS, with full-content
# Langfuse telemetry. Non-reference on a Mac whose only allowed Python is Xcode 3.9.6 (C0 asks for 3.11+).
# Paths and gateway variables as in launch-c2.sh; setup: README.md in this folder.
#
#   bash launch-c0.sh prepare            # materialize the launch only (no oracle, MXC or model calls)
#   bash launch-c0.sh run <AUTH_REF>     # the paid run: 5400 s budget, 900 s reserve, zero recovery
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=${MXC_EVAL_ROOT:-$HOME/mxc-eval}
REPO=${MXC_EVAL_REPO:-$(git -C "$HERE" rev-parse --show-toplevel)}
mode=${1:-}; auth=${2:-}
[ -f "$ROOT/langfuse.env" ] || { echo "missing $ROOT/langfuse.env (copy langfuse.env.example, chmod 600)" >&2; exit 2; }
[ -n "${ANTHROPIC_BASE_URL:-}" ] && [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ] || { echo "ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN not set" >&2; exit 2; }

set -a; . "$ROOT/langfuse.env"; set +a          # Langfuse keys + OTel content/delivery flags (private)
export PATH="$ROOT/tools/agent-py/bin:$HERE/bin:/usr/local/share/dotnet:$PATH"   # bin/pwsh: PowerShell on dotnet
export MXC_EVAL_ROOT="$ROOT" MXC_SANDBOX_HOME="$ROOT/mxc-home"
export GEEKY_EVAL_MCP_RUNTIME=node               # geeky_mcp from server.mts (mcp needs Python 3.10+)
export GEEKY_EVAL_OTEL=1                         # native OTel spans + post-run transcript upload
export GEEKY_EVAL_EXTRA_RO="/Applications/Xcode.app/Contents:$ROOT/pwsh-tool:/usr/local/share/dotnet"
export LITELLM_PROXY_URL="$ANTHROPIC_BASE_URL" LITELLM_PROXY_API_KEY="$ANTHROPIC_AUTH_TOKEN"

args=(-Case c0-wordstat -Model claude-sonnet-5-5 -Litellm -TimeoutSec 5400 -CloseoutReserveSec 900 -ResumeOnRefusal 0
      -NoTelemetry -ToolsDir "$ROOT/tools" -WorkRoot "$ROOT/work")
cd "$REPO/geeky-orchestration"
case "$mode" in
  prepare) exec pwsh -NoProfile -File evals/scripts/run-baseline.ps1 "${args[@]}" -AuthorizationReference prepare-check -PrepareOnly ;;
  run)
    [ -n "$auth" ] || { echo "usage: launch-c0.sh run <AUTH_REF>" >&2; exit 2; }
    # mxc-sandbox is included: mxc.ps1 builds the host from the working tree, so an uncommitted host change would run unrecorded.
    [ -z "$(git -C "$REPO" status --porcelain -- geeky-orchestration mxc-sandbox ':!geeky-orchestration/evals/baselines')" ] \
      || { echo "uncommitted plugin or host changes: the runner exports HEAD; commit or stash first" >&2; exit 2; }
    hostdir="$REPO/mxc-sandbox/scripts/host/MxcClaude"
    want=$(for f in MxcClaude.csproj Program.cs; do shasum -a 256 "$hostdir/$f" | awk '{print toupper($1)}'; done | tr -d '\n')
    [ "$(cat "$MXC_SANDBOX_HOME/bin/.source-hash" 2>/dev/null)" = "$want" ] \
      || { echo "host not built from the committed source: run mxc.ps1 -Rebuild probe first" >&2; exit 2; }
    exec pwsh -NoProfile -File evals/scripts/run-baseline.ps1 "${args[@]}" -AuthorizationReference "$auth" ;;
  *) echo "usage: launch-c0.sh prepare | run <AUTH_REF>" >&2; exit 2 ;;
esac
