#!/bin/bash
# otel-pong.sh: one-turn Claude Code call inside MXC with native OTel export to Langfuse, to check the telemetry
# path before a paid eval (one small paid call). Prints the session id to look up in Langfuse.
# Secrets reach the sandbox by name (`--env NAME`), so their values never appear on any argv.
set -uo pipefail
ROOT=${MXC_EVAL_ROOT:-$HOME/mxc-eval}; T="$ROOT/work/otelcheck"; mkdir -p "$T"
set -a; . "$ROOT/langfuse.env"; set +a
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic $(printf '%s:%s' "$LANGFUSE_PUBLIC_KEY" "$LANGFUSE_SECRET_KEY" | base64)"
SID=$(uuidgen | tr 'A-Z' 'a-z'); export OTEL_RESOURCE_ATTRIBUTES="$OTEL_RESOURCE_ATTRIBUTES,geeky.case=otel-check,langfuse.session.id=$SID"
# short export intervals so a 1-turn run flushes before exit
export OTEL_METRIC_EXPORT_INTERVAL=2000 OTEL_LOGS_EXPORT_INTERVAL=1000 OTEL_BSP_SCHEDULE_DELAY=500
ENVS=(); for n in ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_USE_BEDROCK CLAUDE_CODE_ENABLE_TELEMETRY CLAUDE_CODE_ENHANCED_TELEMETRY_BETA \
  OTEL_EXPORTER_OTLP_ENDPOINT OTEL_EXPORTER_OTLP_PROTOCOL OTEL_EXPORTER_OTLP_HEADERS OTEL_LOGS_EXPORTER OTEL_METRICS_EXPORTER OTEL_TRACES_EXPORTER \
  OTEL_RESOURCE_ATTRIBUTES OTEL_SERVICE_NAME OTEL_METRIC_EXPORT_INTERVAL OTEL_LOGS_EXPORT_INTERVAL OTEL_BSP_SCHEDULE_DELAY; do [ -n "${!n+x}" ] && ENVS+=(--env "$n"); done
cd "$T"; MXC_SANDBOX_HOME="$ROOT/mxc-home" /usr/local/share/dotnet/dotnet "$ROOT/mxc-home/bin/MxcClaude.dll" run --isolated --workspace "$T" --host-loopback "${ENVS[@]}" --timeout 150 \
  -- -p "Reply with exactly: OTEL-PONG" --model "${MODEL:-claude-sonnet-5-5}" --max-turns 1 > "$T/out.txt" 2> "$T/err.txt"; rc=$?
echo "rc=$rc stdout=$(head -c 60 "$T/out.txt") session=$SID"; grep -viE "settings.local.json|did not load" "$T/err.txt" | sed -E 's/(Basic |sk-lf-|pk-lf-)[A-Za-z0-9+/=-]+/\1<redacted>/g' | head -5
echo "$SID" > "$T/sid"
