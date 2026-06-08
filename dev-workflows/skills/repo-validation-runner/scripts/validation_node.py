from __future__ import annotations

import json
from pathlib import Path

from validation_common import SCRIPT_CATEGORIES, add, package_runner


def detect_package_json(root: Path, candidates: list[dict]) -> None:
    path = root / "package.json"
    if not path.exists():
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return

    runner = package_runner(root)
    for name in sorted(scripts):
        lowered = name.lower()
        for category, keywords in SCRIPT_CATEGORIES.items():
            if any(keyword in lowered for keyword in keywords):
                add(candidates, category, f"{runner} run {name}", f"package.json scripts.{name}")
                break
