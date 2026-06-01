#!/usr/bin/env python3
"""validate-task-schema.py

Validate that geeky-plan task files (tasks/Tx-*.md) carry the sections the
template defines and that geeky-implement relies on. This is the plan->implement
boundary gate: run it at the end of geeky-plan and the start of geeky-implement.

Required sections (missing => ERROR, file fails):
  Task Name, Scope / In scope, Dependencies, Acceptance Criteria,
  Tests/Validation Before Next Task, Priority
Recommended sections (missing => WARNING):
  Context, Module/System, Technical Notes, Definition of Done, Estimate

Matching is tolerant: a label counts as present if any line, after stripping
leading '#'/'*' markers and whitespace, begins with the label (case-insensitive).

Contract (matches the other validators):
  argv in, exit 0 = pass / exit 1 = fail, human summary on stdout.
  --json emits a machine-readable object.

Usage:
  python validate-task-schema.py --path "/abs/path/to/docs/feature-folder"
  python validate-task-schema.py --file "/abs/path/to/tasks/T1-foo.md" --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = (
    ("Task Name", r"Task\s*Name"),
    ("In scope", r"In\s*scope"),
    ("Dependencies", r"Dependencies"),
    ("Acceptance Criteria", r"Acceptance\s*Criteria"),
    ("Tests/Validation", r"Tests\s*/\s*Validation"),
    ("Priority", r"Priority"),
)
RECOMMENDED = (
    ("Context", r"Context"),
    ("Module/System", r"Module\s*/\s*System"),
    ("Technical Notes", r"Technical\s*Notes"),
    ("Definition of Done", r"Definition\s+of\s+Done"),
    ("Estimate", r"Estimate"),
)

NOTES_RE = re.compile(r"\.notes\.md$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--path", dest="path", required=False)
    p.add_argument("positional", nargs="?", default=None)
    p.add_argument("--file", dest="file", required=False)
    p.add_argument("--json", dest="as_json", action="store_true")
    return p.parse_args()


def label_present(text: str, pattern: str) -> bool:
    rx = re.compile(rf"^\s*[#*\s]*{pattern}\b", re.IGNORECASE | re.MULTILINE)
    return rx.search(text) is not None


def check_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    missing_required = [name for name, pat in REQUIRED if not label_present(text, pat)]
    missing_recommended = [name for name, pat in RECOMMENDED if not label_present(text, pat)]
    return {
        "file": path.name,
        "ok": not missing_required,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
    }


def collect_task_files(folder: Path) -> list[Path]:
    tasks_dir = folder / "tasks"
    if not tasks_dir.is_dir():
        return []
    return sorted(
        f for f in tasks_dir.iterdir()
        if f.is_file() and f.name.lower().endswith(".md") and not NOTES_RE.search(f.name)
        and f.name[:1].upper() == "T"
    )


def main() -> int:
    args = parse_args()

    files: list[Path] = []
    if args.file:
        files = [Path(args.file)]
    else:
        path_str = args.path or args.positional
        if not path_str:
            print("USAGE: validate-task-schema.py (--path <folder> | --file <task.md>) [--json]")
            return 1
        folder = Path(path_str)
        if not folder.is_dir():
            msg = f"MISSING_FOLDER: {folder}"
            print(json.dumps({"ok": False, "errors": [msg]}) if args.as_json else msg)
            return 1
        files = collect_task_files(folder)

    if not files:
        msg = "NO_TASK_FILES: nothing to validate (expected tasks/Tx-*.md)"
        print(json.dumps({"ok": False, "errors": [msg]}) if args.as_json else msg)
        return 1

    results = []
    for f in files:
        if not f.is_file():
            results.append({"file": str(f), "ok": False,
                            "missing_required": ["<file not found>"], "missing_recommended": []})
            continue
        results.append(check_file(f))

    ok = all(r["ok"] for r in results)
    failed = sum(1 for r in results if not r["ok"])

    if args.as_json:
        print(json.dumps({"ok": ok, "results": results}, indent=2))
    else:
        prefix = "OK" if ok else "INVALID_TASK_SCHEMA"
        print(f"{prefix}: {len(results)} task file(s) checked, {failed} failing.")
        for r in results:
            if r["missing_required"]:
                print(f"  {r['file']}:")
                for m in r["missing_required"]:
                    print(f"    ERROR:   missing required section: {m}")
            for m in r["missing_recommended"]:
                print(f"    WARNING: {r['file']} missing recommended section: {m}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
