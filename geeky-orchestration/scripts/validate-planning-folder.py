#!/usr/bin/env python3
"""validate-planning-folder.py

Verify that a folder produced by /geeky-plan contains all artifacts /geeky-implement needs.

Exit codes (match validate-planning-folder.ps1 exactly):
  0  -> OK summary on stdout, folder is valid
  1  -> missing-artifact summary on stdout, folder is invalid

Usage:
  python validate-planning-folder.py --path "/abs/path/to/docs/feature-folder"
  python validate-planning-folder.py "/abs/path/to/docs/feature-folder"   # positional also supported
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


REQUIRED = (
    "implementation-plan.md",
    "kanban.md",
    "references.md",
    "handoff.md",
)

RECOMMENDED = (
    "feature-specification.md",
    "draft.md",
)

# Match the .ps1: tasks/T*-*.md but exclude the *.notes.md siblings.
TASK_INCLUDE = re.compile(r"^T.*\.md$", re.IGNORECASE)
TASK_EXCLUDE = re.compile(r"\.notes\.md$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--path", dest="path", required=False)
    p.add_argument("positional", nargs="?", default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    path_str = args.path or args.positional
    if not path_str:
        print("USAGE: validate-planning-folder.py --path <folder>")
        return 1

    folder = Path(path_str)
    if not folder.is_dir():
        print(f"MISSING_FOLDER: {folder}")
        return 1

    missing: list[str] = []
    for name in REQUIRED:
        if not (folder / name).is_file():
            missing.append(name)

    tasks_dir = folder / "tasks"
    task_count = 0
    if not tasks_dir.is_dir():
        missing.append("tasks/ (directory)")
    else:
        task_files = [
            f for f in tasks_dir.iterdir()
            if f.is_file() and TASK_INCLUDE.match(f.name) and not TASK_EXCLUDE.search(f.name)
        ]
        task_count = len(task_files)
        if task_count == 0:
            missing.append("tasks/Tx-*.md (no task files found)")

    missing_recommended = [
        name for name in RECOMMENDED if not (folder / name).is_file()
    ]

    if missing:
        print(f"INVALID_PLANNING_FOLDER: {folder}")
        print("Missing required artifacts:")
        for m in missing:
            print(f"  - {m}")
        if missing_recommended:
            print("Also missing (recommended):")
            for m in missing_recommended:
                print(f"  - {m}")
        return 1

    warning_part = ""
    if missing_recommended:
        warning_part = f" (warnings: missing {', '.join(missing_recommended)})"

    print(f"OK: planning folder valid. {task_count} task file(s) found.{warning_part}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
