#!/usr/bin/env bash
# py-run.sh — run a Python hook with whatever Python 3 interpreter is available.
#
# Why: hooks.json previously invoked `python` directly. On Windows + Git Bash,
# neither `python` nor `python3` is necessarily on PATH (the Python launcher `py`
# may be the only entry point), so the hook silently failed with exit 127 and the
# planning-contract guard never ran. This shim probes interpreters in order and
# execs the first working Python 3, so the same hooks.json line works on Windows,
# macOS, and Linux without assuming a specific interpreter name.
#
# Usage (from hooks.json):
#   bash "${CLAUDE_PLUGIN_ROOT}/hooks/py-run.sh" \
#        "${CLAUDE_PLUGIN_ROOT}/hooks/guard-planning-contract.py" --mode warn
set -e

# Force UTF-8 so Windows Python doesn't default to cp1252 and choke on non-ASCII
# paths/filenames. No-op on macOS/Linux. Must be set before Python starts.
export PYTHONUTF8=1

# Git Bash hands paths in POSIX form (/c/Users/...). A native Windows python.exe
# (which `py` launches) reads the leading slash as a drive root and fails ENOENT.
# Convert absolute args to native Windows form when cygpath is present (Git Bash
# only; a no-op elsewhere).
if command -v cygpath >/dev/null 2>&1; then
  conv=()
  for a in "$@"; do
    case "$a" in
      /*) conv+=("$(cygpath -w "$a" 2>/dev/null || printf '%s' "$a")") ;;
      *)  conv+=("$a") ;;
    esac
  done
  set -- "${conv[@]}"
fi

# Probe interpreters in order; exec the first that is a working Python 3.
# `py -3` is the Windows Python launcher; python3/python cover macOS/Linux.
for cmd in "python3" "python" "py -3"; do
  # shellcheck disable=SC2086
  if $cmd -c 'import sys; raise SystemExit(0 if sys.version_info[0] >= 3 else 1)' >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    exec $cmd "$@"
  fi
done

echo "geeky-orchestration: no working Python 3 interpreter found (tried python3, python, py -3)." >&2
echo "  Install Python 3 from https://python.org, or ensure the 'py' launcher is on PATH (Windows)." >&2
exit 1
