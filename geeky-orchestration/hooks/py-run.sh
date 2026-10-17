#!/usr/bin/env bash
# py-run.sh — run a Python entry point, or its Node twin when Python can't run.
#
# Usage:
#   bash py-run.sh [--uv-with SPEC] <script.py> [args...]
#
# Why: hooks.json previously invoked `python` directly. On Windows + Git Bash,
# neither `python` nor `python3` is necessarily on PATH (the Python launcher `py`
# may be the only entry point), so the hook silently failed with exit 127 and the
# planning-contract guard never ran. This shim probes interpreters in order and
# execs the first working Python 3, so the same hooks.json line works on Windows,
# macOS, and Linux without assuming a specific interpreter name.
#
# Redirect: every entry point has a Node twin beside it (<script>.mts, Node
# 22.18+). When no working Python is found, the twin runs instead, with the
# same arguments, stdin, stdout and exit codes. Some machines have a Python
# that hangs or is killed rather than failing fast, so each probe is killed
# after $GEEKY_PY_PROBE_TIMEOUT seconds (default 2), all probing fits in
# $GEEKY_PROBE_BUDGET seconds (default 3, or 8 with --uv-with), and probes
# never touch stdin: it carries the hook payload or the MCP stdio transport.
# Without a usable Node twin nothing is probed: the Python route runs as before.
#
#   --uv-with SPEC  the script needs a package (the MCP server: "mcp>=1.2.0").
#                   The Python route is then `uv run --with SPEC python`, or a
#                   Python whose installed package meets SPEC's ">=" floor.
#
# The decision is cached for $GEEKY_RUNTIME_TTL_MIN minutes (default 1440) in
# $CLAUDE_PLUGIN_DATA, else ${XDG_CACHE_HOME:-~/.cache}/geeky-orchestration, so
# a machine with a hanging Python pays the probe once, not on every edit.
# GEEKY_RUNTIME=python|node forces a route and skips probing.
#
# Usage (from hooks.json):
#   bash "${CLAUDE_PLUGIN_ROOT}/hooks/py-run.sh" \
#        "${CLAUDE_PLUGIN_ROOT}/hooks/guard-planning-contract.py" --mode warn

usage() { echo "usage: py-run.sh [--uv-with SPEC] <script.py> [args...]" >&2; exit 2; }

uv_with=""
if [ "${1:-}" = "--uv-with" ]; then
  [ $# -ge 3 ] || usage
  uv_with="$2"
  shift 2
fi
script="${1:-}"
[ -n "$script" ] || usage
shift

# Force UTF-8 so Windows Python doesn't default to cp1252 and choke on non-ASCII
# paths/filenames. No-op on macOS/Linux. Must be set before Python starts.
export PYTHONUTF8=1

# Git Bash hands paths in POSIX form (/c/Users/...). A native Windows python.exe
# or node.exe reads the leading slash as a drive root and fails ENOENT. Convert
# absolute paths to native Windows form when cygpath is present (Git Bash only;
# a no-op elsewhere).
native() {
  if command -v cygpath >/dev/null 2>&1; then
    case "$1" in
      /*) cygpath -w "$1" 2>/dev/null || printf '%s' "$1"; return ;;
    esac
  fi
  printf '%s' "$1"
}
args=()
for a in "$@"; do args+=("$(native "$a")"); done

PYTHONS=("python3" "python" "py -3")   # py -3 is the Windows Python launcher
twin="${script%.py}.mts"
pkg="${uv_with%%[<>=!~ ;[]*}"
min_version=$(printf '%s' "$uv_with" | sed -n 's/.*>=[[:space:]]*\([0-9][0-9.]*\).*/\1/p')
min_version="${min_version%.}"   # a one-part floor such as mcp>=2 counts too

# What a Python must pass to be usable. With --uv-with, the package's installed
# distribution must meet SPEC's ">=" floor. This asks importlib.metadata rather
# than running "import pkg": a bare import also finds the plugin's own mcp/
# folder as a namespace package, and would pass on a Python without the package.
if [ -n "$pkg" ]; then
  CHECK="import re
from importlib.metadata import version
have = tuple(int(x) for x in re.findall(r'\d+', version('$pkg'))[:3])
raise SystemExit(0 if have >= tuple(int(x) for x in '${min_version:-0}'.split('.')) else 1)"
else
  CHECK='import sys; raise SystemExit(0 if sys.version_info[0] >= 3 else 1)'
fi

run_python() {   # exec a Python route: "uv", or a python command such as "py -3"
  if [ "$1" = "uv" ]; then
    exec uv run --with "$uv_with" python "$(native "$script")" "${args[@]}"
  fi
  # shellcheck disable=SC2086
  exec $1 "$(native "$script")" "${args[@]}"
}

run_node() {
  # --disable-warning: Node 22.18-23.x print an ExperimentalWarning for type stripping.
  exec node --disable-warning=ExperimentalWarning "$(native "$twin")" "${args[@]}"
}

node_twin_ok() {
  [ -f "$twin" ] && command -v node >/dev/null 2>&1 \
    && node -e 'process.exit(process.features.typescript ? 0 : 1)' </dev/null >/dev/null 2>&1
}

# Without a Node twin to fall back on there is nothing to decide: behave exactly
# as before the redirector (uv for --uv-with, else the first Python that starts).
legacy() {
  if [ -n "$uv_with" ] && command -v uv >/dev/null 2>&1; then run_python uv; fi
  for cmd in "${PYTHONS[@]}"; do
    # shellcheck disable=SC2086
    if $cmd -c 'import sys; raise SystemExit(0 if sys.version_info[0] >= 3 else 1)' </dev/null >/dev/null 2>&1; then
      run_python "$cmd"
    fi
  done
  echo "geeky-orchestration: no working Python 3 interpreter (tried python3, python, py -3)," >&2
  echo "  and no Node 22.18+ to run $twin. Install either one." >&2
  exit 1
}

case "${GEEKY_RUNTIME:-auto}" in
  node)
    if ! node_twin_ok; then
      echo "geeky-orchestration: GEEKY_RUNTIME=node, but there is no Node 22.18+ or no $twin." >&2
      exit 1
    fi
    run_node ;;
  python)
    if [ -n "$uv_with" ] && command -v uv >/dev/null 2>&1; then run_python uv; fi
    for cmd in "${PYTHONS[@]}"; do
      command -v "${cmd%% *}" >/dev/null 2>&1 && run_python "$cmd"
    done
    echo "geeky-orchestration: GEEKY_RUNTIME=python, but no Python was found (tried python3, python, py -3)." >&2
    exit 1 ;;
esac

# --- auto: probe within a budget, cache the decision ------------------------ #

# kill_tree PID : SIGKILL a process and its descendants, such as the interpreter
# `uv run` starts. Each process is frozen (SIGSTOP) before its children are
# listed, so nothing forks or is re-parented mid-walk. A process group would be
# simpler, but `set -m` is a no-op without a controlling terminal, which is
# exactly how hosts start hooks and MCP servers.
kill_tree() {
  local child
  kill -STOP "$1" 2>/dev/null
  for child in $(pgrep -P "$1" 2>/dev/null); do kill_tree "$child"; done
  kill -9 "$1" 2>/dev/null
}

# probe SECONDS CMD... : true if CMD exits 0 within SECONDS, run in
# $PROBE_DIR (default: here). It gets no stdin and its output goes nowhere, so a
# hung probe cannot hold the caller's pipes.
probe() {
  local secs=$1 pid watcher rc=0
  shift
  ( cd "${PROBE_DIR:-.}" && exec "$@" ) </dev/null >/dev/null 2>&1 &
  pid=$!
  ( sleep "$secs"; kill_tree "$pid" ) </dev/null >/dev/null 2>&1 &
  watcher=$!
  wait "$pid" 2>/dev/null || rc=$?
  kill "$watcher" 2>/dev/null
  wait "$watcher" 2>/dev/null
  return "$rc"
}

# The budget keeps a first launch inside the host's timeouts: hooks.json allows
# 5 s, and Codex waits 10 s for an MCP server to start.
# seconds VALUE DEFAULT : whole seconds from a setting. A fraction rounds up, so
# a timeout is never shorter than asked; anything unparsable is the default.
seconds() {
  case "$1" in
    ''|.|*[!0-9.]*|*.*.*) echo "$2" ;;
    *.*)
      local whole="${1%%.*}" frac="${1#*.}"
      case "$frac" in
        *[1-9]*) echo $(( 10#${whole:-0} + 1 )) ;;
        *) echo $(( 10#${whole:-0} )) ;;
      esac ;;
    *) echo $(( 10#$1 )) ;;
  esac
}
if [ -n "$uv_with" ]; then budget=$(seconds "${GEEKY_PROBE_BUDGET:-}" 8); else budget=$(seconds "${GEEKY_PROBE_BUDGET:-}" 3); fi
probe_timeout=$(seconds "${GEEKY_PY_PROBE_TIMEOUT:-}" 2)
deadline=$(( $(date +%s) + budget ))

# within SECONDS CMD... : probe, with SECONDS clipped to what the budget has left.
within() {
  local secs=$1 left
  shift
  left=$(( deadline - $(date +%s) ))
  [ "$left" -lt "$secs" ] && secs=$left
  [ "$secs" -gt 0 ] || return 1
  probe "$secs" "$@"
}

# decide: set $route to "uv", "python:<cmd>", or "node".
decide() {
  local cmd
  if [ -n "$uv_with" ] && command -v uv >/dev/null 2>&1 \
     && within "$budget" uv run --with "$uv_with" python -c "$CHECK"; then
    route="uv"; return 0
  fi
  for cmd in "${PYTHONS[@]}"; do
    command -v "${cmd%% *}" >/dev/null 2>&1 || continue
    # Twice, so one lucky start of a Python that usually hangs or is killed does
    # not pin it for a day. From /, so the caller's directory is not on sys.path.
    # shellcheck disable=SC2086
    if PROBE_DIR=/ within "$probe_timeout" $cmd -c "$CHECK" \
       && PROBE_DIR=/ within "$probe_timeout" $cmd -c "$CHECK"; then
      route="python:$cmd"; return 0
    fi
  done
  route="node"
}

cache_dir="${CLAUDE_PLUGIN_DATA:-${XDG_CACHE_HOME:-$HOME/.cache}/geeky-orchestration}"
cache="$cache_dir/runtime-${pkg:-python}"
ttl="${GEEKY_RUNTIME_TTL_MIN:-1440}"

remember() {   # atomic, so concurrent first launches race safely: last writer wins
  mkdir -p "$cache_dir" 2>/dev/null || return 0
  printf '%s\n' "$1" >"$cache.$$" 2>/dev/null && mv -f "$cache.$$" "$cache" 2>/dev/null
  rm -f "$cache.$$" 2>/dev/null
}

route=""
if [ -f "$cache" ] && [ -n "$(find "$cache" -mmin "-$ttl" 2>/dev/null)" ]; then
  route=$(cat "$cache" 2>/dev/null)
  case "$route" in
    uv) command -v uv >/dev/null 2>&1 || route="" ;;
    python:*) cmd="${route#python:}"; command -v "${cmd%% *}" >/dev/null 2>&1 || route="" ;;
    node) { [ -f "$twin" ] && command -v node >/dev/null 2>&1; } || route="" ;;
    *) route="" ;;
  esac
fi
if [ -z "$route" ]; then
  node_twin_ok || legacy   # nothing to fall back on: no probing, the old behaviour
  # Provisionally Node: if the host kills this launch mid-probe, the next one
  # starts on Node at once instead of probing into the same timeout forever.
  remember node
  decide
  remember "$route"
fi

case "$route" in
  uv) run_python uv ;;
  python:*) run_python "${route#python:}" ;;
  *) run_node ;;
esac
