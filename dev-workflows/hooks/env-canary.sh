#!/usr/bin/env bash
# SessionStart canary.
#
# The security-guidance and geeky-orchestration plugin hooks shell out to python and fail
# *non-blocking* (silently) when no interpreter resolves. That once degraded an entire plugin
# safety layer for ~a week with nothing surfacing it (1,040 invisible failures; see
# analysis/collaboration-friction-analysis-2026-06-22.md). This canary turns that invisible
# failure into a visible startup notice.
#
# Design: uses ONLY bash builtins (`command -v`, `printf`) so it cannot share the failure mode
# it guards against (a broken PATH that hides python would also hide `cat`/external tools).
# Emits nothing when healthy (no noise). Always exits 0 (never blocks startup).
if command -v python3 >/dev/null 2>&1 || command -v py >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
    exit 0
fi

# No interpreter resolved -> inject a loud, actionable notice into the session context.
printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[ENV CANARY FAILED] No python / python3 / py on PATH. The security-guidance and geeky-orchestration plugin hooks shell out to python and will now SILENTLY no-op (schema guards + security reminders disabled). FIX: re-add ~/bin (which holds the python/python3 shims) to PATH, then restart the session. Diagnose with: pwsh -File ~/.claude/scripts/env-healthcheck.ps1"}}'
exit 0
