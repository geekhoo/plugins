#!/usr/bin/env python3
"""check-dod.py

Definition-of-Done checker for a single geeky-implement task. Embodies "verify,
don't trust": instead of believing the agent that a task is finished, assert the
durable signals on disk before the task may move to Done.

Lifecycle: move the task to **In Review** -> run validation + this gate -> move to
**Done** only on success. Both `In Review` and `Done` are therefore accepted
placements: `In Review` is the normal pre-Done state this gate is run from, and
`Done` stays acceptable so re-running the gate after the move is not an error.

Checks for task <ID> in <folder> (missing => ERROR unless noted):
  - a per-task notes file tasks/<ID>-*.notes.md exists
  - <ID> is placed in the In Review or Done lane of kanban.md
  - handoff.md mentions <ID>
  - WARNING if <ID> also appears in another lane (Backlog / In Progress / Blocked / ...)

It also extracts and prints the task's "Tests/Validation Before Next Task" block
so the orchestrator can re-run those commands itself (this script does not execute
them — running is the caller's job, kept framework- and shell-agnostic).

Contract: argv in, exit 0 = pass / exit 1 = fail, human summary on stdout.
  --json emits a machine-readable object.

Usage:
  python check-dod.py --path "/abs/docs/feature" --task T3
  python check-dod.py "/abs/docs/feature" T3 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KNOWN_LANES = ("Backlog", "Ready", "In Progress", "In Review", "Blocked", "Done")
# Lanes from which the DoD gate may legitimately pass. "In Review" is the state the
# gate is run from; "Done" keeps a post-move re-run from failing.
ACCEPTED_LANES = ("In Review", "Done")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*\S)\s*$")

# --- Lane placement (keep in sync with validate-kanban.py and hooks/guard-planning-contract.py) ---
# Only a markdown list item whose LEADING token is the task id places that task
# in a lane. A trailing cross-reference or an HTML comment merely mentions it.
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
PLACEMENT_RE = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])\s+"   # markdown bullet or ordered-list marker
    r"(?:\[[ xX]\]\s*)?"          # optional task-list checkbox
    r"[*_`~]*\s*"                 # optional emphasis / code marks
    r"(T\d+)\b",                  # the task id, and it must lead
    re.IGNORECASE,
)


def strip_comments(text: str) -> str:
    """Remove HTML comments (possibly multi-line) before lane parsing."""
    return COMMENT_RE.sub("", text)


def placement_id(line: str) -> str | None:
    """The task id this line PLACES in the current lane, or None."""
    m = PLACEMENT_RE.match(line)
    return m.group(1).upper() if m else None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--path", dest="path")
    p.add_argument("--task", dest="task")
    p.add_argument("pos_path", nargs="?", default=None)
    p.add_argument("pos_task", nargs="?", default=None)
    p.add_argument("--json", dest="as_json", action="store_true")
    return p.parse_args()


def lane_for_heading(heading: str) -> str | None:
    norm = heading.strip().lower()
    if "validation" in norm:
        return None
    for lane in KNOWN_LANES:
        if norm == lane.lower() or norm.startswith(lane.lower()):
            return lane
    return None


def lanes_for_task(kanban_text: str, task_id: str) -> list[str]:
    """Lanes in which task_id is PLACED (not merely mentioned).

    Placement rule kept in sync with scripts/validate-kanban.py and
    hooks/guard-planning-contract.py: only a markdown list item whose leading
    token is the id counts. A trailing cross-reference ("- T1 (unblocks T4)")
    or an HTML comment mentions the id without placing it.
    """
    found: list[str] = []
    current: str | None = None
    want = task_id.upper()
    for line in strip_comments(kanban_text).splitlines():
        hm = HEADING_RE.match(line)
        if hm:
            current = lane_for_heading(hm.group(1))
            continue
        if current and placement_id(line) == want and current not in found:
            found.append(current)
    return found


def extract_validation_block(task_text: str) -> str:
    lines = task_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.search(r"Tests\s*/\s*Validation", line, re.IGNORECASE):
            start = i + 1
            break
    if start is None:
        return ""
    out: list[str] = []
    for line in lines[start:]:
        # Stop at the next section label (Estimate:/Priority:/heading).
        if re.match(r"^\s*[#*\s]*(Estimate|Priority)\b", line, re.IGNORECASE):
            break
        if re.match(r"^\s{0,3}#{1,6}\s+\S", line):
            break
        out.append(line)
    return "\n".join(out).strip()


def main() -> int:
    args = parse_args()
    path_str = args.path or args.pos_path
    task_id = (args.task or args.pos_task or "").upper()
    if not path_str or not task_id:
        print("USAGE: check-dod.py --path <folder> --task <ID> [--json]")
        return 1

    folder = Path(path_str)
    if not folder.is_dir():
        msg = f"MISSING_FOLDER: {folder}"
        print(json.dumps({"ok": False, "errors": [msg]}) if args.as_json else msg)
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    # 1. notes file
    tasks_dir = folder / "tasks"
    notes = []
    if tasks_dir.is_dir():
        notes = [f.name for f in tasks_dir.iterdir()
                 if f.is_file() and re.match(rf"^{re.escape(task_id)}\b", f.name, re.IGNORECASE)
                 and f.name.lower().endswith(".notes.md")]
    if not notes:
        errors.append(f"no per-task notes file tasks/{task_id}-*.notes.md")

    # 2/4. kanban placement
    kanban = folder / "kanban.md"
    lanes: list[str] = []
    if not kanban.is_file():
        errors.append("kanban.md not found")
    else:
        lanes = lanes_for_task(kanban.read_text(encoding="utf-8", errors="replace"), task_id)
        if not any(l in lanes for l in ACCEPTED_LANES):
            errors.append(
                f"{task_id} is not in the In Review or Done lane "
                f"(found in: {', '.join(lanes) or 'no lane'})"
            )
        extra = [l for l in lanes if l not in ACCEPTED_LANES]
        if extra:
            warnings.append(f"{task_id} also appears in: {', '.join(extra)}")
        if "In Review" in lanes and "Done" in lanes:
            warnings.append(f"{task_id} appears in both In Review and Done")

    # 3. handoff mention
    handoff = folder / "handoff.md"
    if not handoff.is_file():
        warnings.append("handoff.md not found")
    elif not re.search(rf"\b{re.escape(task_id)}\b", handoff.read_text(encoding="utf-8", errors="replace"), re.IGNORECASE):
        warnings.append(f"handoff.md does not mention {task_id}")

    # validation block (informational)
    validation = ""
    if tasks_dir.is_dir():
        for f in tasks_dir.iterdir():
            if (f.is_file() and re.match(rf"^{re.escape(task_id)}\b", f.name, re.IGNORECASE)
                    and f.name.lower().endswith(".md") and not f.name.lower().endswith(".notes.md")):
                validation = extract_validation_block(f.read_text(encoding="utf-8", errors="replace"))
                break

    ok = not errors
    summary = f"{'DOD_OK' if ok else 'DOD_INCOMPLETE'}: {task_id}"

    if args.as_json:
        print(json.dumps({
            "ok": ok, "task": task_id, "errors": errors, "warnings": warnings,
            "lanes": lanes, "validation_block": validation,
            "accepted_lanes": list(ACCEPTED_LANES),
        }, indent=2))
    else:
        print(summary)
        for e in errors:
            print(f"  ERROR:   {e}")
        for w in warnings:
            print(f"  WARNING: {w}")
        if validation:
            print("  Re-run this task's validation block (verify, don't trust):")
            for line in validation.splitlines():
                print(f"    | {line}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
