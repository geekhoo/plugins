#!/usr/bin/env python3
"""check-commit.py

Validate a commit message against the geeky-implement format: a Conventional
Commits subject plus a task reference (Tasks: T<n> ...). The most natively
portable gate — wire it as a git commit-msg hook, a pre-commit check, or a
Claude PreToolUse matcher on `Bash(git commit *)`.

Rules (violations => ERROR, exit 1):
  - subject matches  type(scope)!: summary  where type is one of
    feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert
    (scope optional; '!' optional)
  - subject length <= 72 chars
  - a task reference exists somewhere in the message: a "Tasks:" line, or a
    bare T<number> token (warn-only if only a bare token, error if neither).

Message source (first that is provided):
  positional FILE  (git commit-msg passes the path to .git/COMMIT_EDITMSG)
  --message "..."
  stdin

Contract: exit 0 = pass / exit 1 = fail, human summary on stdout. --json optional.

Usage:
  python check-commit.py .git/COMMIT_EDITMSG
  python check-commit.py --message "feat(plan): add linter\n\nTasks: T3"
  echo "$msg" | python check-commit.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
SUBJECT_RE = re.compile(rf"^(?:{TYPES})(?:\([^)]+\))?!?: .+")
TASKS_LINE_RE = re.compile(r"^\s*Tasks:\s*.*\bT\d+\b", re.IGNORECASE | re.MULTILINE)
BARE_TASK_RE = re.compile(r"\bT\d+\b")
MAX_SUBJECT = 72


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("file", nargs="?", default=None)
    p.add_argument("--message", dest="message", default=None)
    p.add_argument("--json", dest="as_json", action="store_true")
    return p.parse_args()


def read_message(args: argparse.Namespace) -> str | None:
    if args.message is not None:
        return args.message
    if args.file:
        p = Path(args.file)
        if not p.is_file():
            return None
        return p.read_text(encoding="utf-8", errors="replace")
    data = sys.stdin.read()
    return data if data else None


def check(message: str) -> dict:
    # Ignore comment lines (git strips '#' lines) and blank leading lines.
    lines = [ln for ln in message.splitlines() if not ln.lstrip().startswith("#")]
    subject = next((ln for ln in lines if ln.strip()), "")
    body = "\n".join(lines)

    errors: list[str] = []
    warnings: list[str] = []

    if not SUBJECT_RE.match(subject):
        errors.append(
            f'subject is not Conventional Commits "type(scope): summary": {subject!r}'
        )
    if len(subject) > MAX_SUBJECT:
        errors.append(f"subject exceeds {MAX_SUBJECT} chars ({len(subject)})")

    if TASKS_LINE_RE.search(body):
        pass
    elif BARE_TASK_RE.search(body):
        warnings.append('task referenced but no "Tasks: T<n>" line (recommended)')
    else:
        errors.append("no task reference (expected a Tasks: line with T<n>)")

    ok = not errors
    return {"ok": ok, "subject": subject, "errors": errors, "warnings": warnings}


def main() -> int:
    args = parse_args()
    message = read_message(args)
    if message is None:
        msg = "NO_MESSAGE: provide a file path, --message, or pipe via stdin"
        print(json.dumps({"ok": False, "errors": [msg]}) if args.as_json else msg)
        return 1

    report = check(message)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print("OK: commit message valid." if report["ok"] else "INVALID_COMMIT_MESSAGE:")
        for e in report["errors"]:
            print(f"  ERROR:   {e}")
        for w in report["warnings"]:
            print(f"  WARNING: {w}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
