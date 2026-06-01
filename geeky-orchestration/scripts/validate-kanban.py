#!/usr/bin/env python3
"""validate-kanban.py

Deterministic integrity check for a geeky-plan kanban.md against the tasks/ folder.
Replaces LLM self-report ("I updated the board") with a fail-stop check.

Checks (errors fail the run; warnings do not):
  ERROR   - a task file in tasks/ is not placed in any lane (untracked)
  ERROR   - a task id appears in more than one lane (ambiguous placement)
  WARNING - a task id referenced in the kanban has no matching task file (dangling)
  WARNING - In Progress count exceeds the WIP cap (default 3)
  WARNING - a known lane heading is entirely missing

Recognised lanes (case-insensitive, any heading depth): Backlog, Ready,
In Progress, In Review, Blocked, Done. A heading containing "validation" is
treated as the release-gate checklist, not a task lane.

Contract (matches the other validators):
  argv in, exit 0 = pass / exit 1 = fail, human summary on stdout.
  --json emits a machine-readable object instead of the human summary.

Usage:
  python validate-kanban.py --path "/abs/path/to/docs/feature-folder"
  python validate-kanban.py "/abs/path/to/docs/feature-folder" --wip 3 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Ordered so that more specific "In ..." lanes are tested before short names.
KNOWN_LANES = ("Backlog", "Ready", "In Progress", "In Review", "Blocked", "Done")

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*\S)\s*$")
TASK_ID_RE = re.compile(r"\bT\d+\b", re.IGNORECASE)
TASK_FILE_RE = re.compile(r"^T\d+", re.IGNORECASE)
NOTES_RE = re.compile(r"\.notes\.md$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--path", dest="path", required=False)
    p.add_argument("positional", nargs="?", default=None)
    p.add_argument("--wip", type=int, default=3, help="In Progress WIP cap (default 3)")
    p.add_argument("--json", dest="as_json", action="store_true")
    return p.parse_args()


def lane_for_heading(heading: str) -> str | None:
    """Return the canonical lane name for a heading, or None."""
    norm = heading.strip().lower()
    if "validation" in norm:
        return None
    for lane in KNOWN_LANES:
        if norm == lane.lower() or norm.startswith(lane.lower()):
            return lane
    return None


def task_ids_from_files(tasks_dir: Path) -> set[str]:
    ids: set[str] = set()
    if not tasks_dir.is_dir():
        return ids
    for f in tasks_dir.iterdir():
        if not f.is_file():
            continue
        if NOTES_RE.search(f.name) or not f.name.lower().endswith(".md"):
            continue
        m = TASK_FILE_RE.match(f.name)
        if m:
            ids.add(m.group(0).upper())
    return ids


def parse_kanban(text: str) -> tuple[dict[str, set[str]], set[str]]:
    """Map canonical lane -> set of task ids referenced under it, and the set of
    lane headings actually present in the document."""
    placements: dict[str, set[str]] = {lane: set() for lane in KNOWN_LANES}
    present: set[str] = set()
    current: str | None = None
    for line in text.splitlines():
        hm = HEADING_RE.match(line)
        if hm:
            current = lane_for_heading(hm.group(1))
            if current:
                present.add(current)
            continue
        if current is None:
            continue
        for tid in TASK_ID_RE.findall(line):
            placements[current].add(tid.upper())
    return placements, present


def build_report(folder: Path, wip_cap: int) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    kanban = folder / "kanban.md"
    if not kanban.is_file():
        return {
            "ok": False,
            "errors": [f"MISSING: {kanban}"],
            "warnings": [],
            "lane_counts": {},
            "summary": f"INVALID_KANBAN: {kanban} not found.",
        }

    file_ids = task_ids_from_files(folder / "tasks")
    placements, present_lanes = parse_kanban(
        kanban.read_text(encoding="utf-8", errors="replace")
    )

    # Where does each id live?
    id_lanes: dict[str, list[str]] = {}
    for lane, ids in placements.items():
        for tid in ids:
            id_lanes.setdefault(tid, []).append(lane)

    # Untracked: a real task file not placed anywhere.
    for tid in sorted(file_ids):
        if tid not in id_lanes:
            errors.append(f"{tid} has a task file but is not placed in any kanban lane")

    # Ambiguous: placed in more than one lane.
    for tid, lanes in sorted(id_lanes.items()):
        if len(lanes) > 1:
            errors.append(f"{tid} appears in multiple lanes: {', '.join(sorted(lanes))}")

    # Dangling: referenced in kanban but no task file.
    for tid in sorted(id_lanes):
        if file_ids and tid not in file_ids:
            warnings.append(f"{tid} is referenced in the kanban but has no tasks/{tid}-*.md file")

    # Missing lanes.
    for lane in KNOWN_LANES:
        if lane not in present_lanes:
            warnings.append(f'lane "{lane}" heading not found in kanban.md')

    # WIP cap.
    in_progress = len(placements["In Progress"])
    if in_progress > wip_cap:
        warnings.append(f"In Progress has {in_progress} tasks (WIP cap {wip_cap})")

    lane_counts = {lane: len(ids) for lane, ids in placements.items()}
    tracked = len({tid for ids in placements.values() for tid in ids})

    ok = not errors
    summary = (
        f"{'OK' if ok else 'INVALID_KANBAN'}: {tracked} task(s) tracked, "
        f"{len(file_ids)} task file(s). "
        + ", ".join(f"{k}={v}" for k, v in lane_counts.items())
    )
    return {
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "lane_counts": lane_counts,
        "summary": summary,
    }


def main() -> int:
    args = parse_args()
    path_str = args.path or args.positional
    if not path_str:
        print("USAGE: validate-kanban.py --path <folder> [--wip N] [--json]")
        return 1

    folder = Path(path_str)
    if not folder.is_dir():
        msg = f"MISSING_FOLDER: {folder}"
        print(json.dumps({"ok": False, "errors": [msg]}) if args.as_json else msg)
        return 1

    report = build_report(folder, args.wip)

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(report["summary"])
        for e in report["errors"]:
            print(f"  ERROR:   {e}")
        for w in report["warnings"]:
            print(f"  WARNING: {w}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
