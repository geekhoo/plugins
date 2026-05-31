#!/usr/bin/env python3
"""guard-planning-contract.py

PreToolUse hook for Edit/Write/NotebookEdit. Reads tool input JSON from stdin.
If file_path points at a frozen geeky-plan artifact, emits a warning to stderr
but does NOT block the tool call.

Frozen patterns (inside a planning folder under docs/<feature>/):
  - implementation-plan.md
  - feature-specification.md
  - draft.md
  - references.md
  - tasks/Tx-*.md           (but NOT tasks/Tx-*.notes.md — those are writable)

Exit codes:
  0  -> allow (with or without warning printed to stderr)
  1  -> non-blocking error from hook itself (still allows tool call)
  2  -> block (we never use this — guard is warn-only by design)
"""

from __future__ import annotations

import json
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


def warn(file_path: str, reason: str) -> None:
    msg = (
        f"\n[geeky-orchestration] WARNING: {file_path} {reason}.\n"
        "[geeky-orchestration] Planning artifacts are the contract between "
        "/geeky-plan and /geeky-implement.\n"
        "[geeky-orchestration] If the plan is genuinely wrong, surface the issue "
        "via kanban Blocked + handoff.md\n"
        "[geeky-orchestration] rather than editing the contract mid-run. "
        "Tool call WILL proceed (warn-only).\n"
    )
    sys.stderr.write(msg)
    sys.stderr.flush()


def main() -> int:
    try:
        raw = sys.stdin.read()
    except Exception:
        return 0

    if not raw:
        return 0

    try:
        payload = json.loads(raw)
    except Exception:
        # Malformed input — don't block, just exit clean.
        return 0

    tool = payload.get("tool_name") or payload.get("tool")
    if not tool:
        return 0

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    file_path = (
        tool_input.get("file_path")
        or tool_input.get("notebook_path")
    )
    if not file_path:
        return 0

    # Normalize path separators to forward-slash for matching.
    normalized = file_path.replace("\\", "/")
    leaf = normalized.rsplit("/", 1)[-1]

    if leaf in FROZEN_LEAVES:
        warn(file_path, "is a frozen geeky-plan planning artifact")
        return 0

    if TASK_FILE_RE.search(normalized) and not NOTES_FILE_RE.search(normalized):
        warn(
            file_path,
            "is a frozen task file (per-task notes belong in tasks/Tx-*.notes.md instead)",
        )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
