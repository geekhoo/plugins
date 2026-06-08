#!/usr/bin/env python3
"""Detect validation command candidates from repository evidence.

This helper is a lightweight candidate detector, not the full validation runner.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validation_common import INSPECTED_CATEGORIES, UNSUPPORTED_CATEGORIES
from validation_node import detect_package_json
from validation_other import detect_dotnet, detect_makefile
from validation_python import detect_python


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect repo-grounded validation command candidates.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root to inspect")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    candidates: list[dict] = []
    detect_package_json(root, candidates)
    detect_python(root, candidates)
    detect_makefile(root, candidates)
    detect_dotnet(root, candidates)

    print(
        json.dumps(
            {
                "repo": str(root),
                "role": "candidate_detector",
                "note": (
                    "This helper suggests command candidates from repo evidence; "
                    "it is not the full validation runner."
                ),
                "inspected_categories": INSPECTED_CATEGORIES,
                "unsupported_categories": UNSUPPORTED_CATEGORIES,
                "candidates": candidates,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
