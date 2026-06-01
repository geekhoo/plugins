#!/usr/bin/env python3
"""guard-planning-contract.py

PreToolUse-style guard for Edit/Write/NotebookEdit. Reads tool-call JSON from
stdin. If file_path points at a frozen geeky-plan artifact, it surfaces a message
through a PORTABLE channel so it is visible across agent frameworks, not just on
Claude Code stderr.

Frozen patterns (inside a planning folder under docs/<feature>/):
  - implementation-plan.md
  - feature-specification.md
  - draft.md
  - references.md
  - tasks/Tx-*.md           (but NOT tasks/Tx-*.notes.md — those are writable)

Modes (default warn) via --mode or $GEEKY_GUARD_MODE:
  warn   -> advisory only. Writes the message to BOTH stdout (plain text) and
            stderr, then exit 0. On exit 0, Claude Code treats non-JSON stdout as
            added context; OpenAI Codex treats stdout as developer context. So the
            warning actually reaches the model, unlike stderr-on-exit-0 alone.
  block  -> emits Claude/Codex-style deny JSON on stdout and exits 0 so the host
            parses the decision and blocks the edit. (Frameworks that gate purely
            on exit code: re-run with --exit-code so a block returns exit 2.)

Exit codes:
  0  -> normal (warn, or block-via-JSON which the host parses)
  2  -> hard block via exit code (only when --exit-code is passed in block mode)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

FROZEN_LEAVES = {
    "implementation-plan.md",
    "feature-specification.md",
    "draft.md",
    "references.md",
}

TASK_FILE_RE = re.compile(r"/tasks/T[^/]+\.md$", re.IGNORECASE)
NOTES_FILE_RE = re.compile(r"\.notes\.md$", re.IGNORECASE)


def message(file_path: str, reason: str) -> str:
    return (
        f"[geeky-orchestration] {file_path} {reason}. "
        "Planning artifacts are the frozen contract between geeky-plan and "
        "geeky-implement. If the plan is genuinely wrong, surface it via kanban "
        "Blocked + handoff.md rather than editing the contract mid-run."
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--mode", choices=("warn", "block"),
                   default=os.environ.get("GEEKY_GUARD_MODE", "warn"))
    p.add_argument("--exit-code", dest="exit_code", action="store_true",
                   help="in block mode, return exit 2 instead of deny JSON")
    return p.parse_args()


def emit_warn(msg: str) -> int:
    # stdout: portable context channel (Claude adds non-JSON stdout as context;
    # Codex treats stdout as developer context). stderr: log visibility.
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()
    return 0


def emit_block(msg: str, exit_code: bool) -> int:
    if exit_code:
        sys.stderr.write(msg + "\n")
        sys.stderr.flush()
        return 2
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": msg,
        }
    }
    sys.stdout.write(json.dumps(decision) + "\n")
    sys.stdout.flush()
    return 0


def main() -> int:
    args = parse_args()

    try:
        raw = sys.stdin.read()
    except Exception:
        return 0
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except Exception:
        return 0

    tool = payload.get("tool_name") or payload.get("tool")
    if not tool:
        return 0

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not file_path:
        return 0

    normalized = file_path.replace("\\", "/")
    leaf = normalized.rsplit("/", 1)[-1]

    reason = None
    if leaf in FROZEN_LEAVES:
        reason = "is a frozen geeky-plan planning artifact"
    elif TASK_FILE_RE.search(normalized) and not NOTES_FILE_RE.search(normalized):
        reason = "is a frozen task file (per-task notes belong in tasks/Tx-*.notes.md instead)"

    if reason is None:
        return 0

    msg = message(file_path, reason)
    if args.mode == "block":
        return emit_block(msg, args.exit_code)
    return emit_warn(msg)


if __name__ == "__main__":
    sys.exit(main())
