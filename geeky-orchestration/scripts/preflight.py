#!/usr/bin/env python3
"""preflight.py — self-test the geeky-orchestration tooling BEFORE a run starts.

Guards the failure class observed 2026-07-01..05: a gate script crashed at
import time (`import yaml` with PyYAML absent) and every downstream validation
call silently halted a 91-hour orchestration run. This script verifies the
*validators themselves* are runnable, so geeky-implement fails fast and loud
instead of stalling mid-run.

Checks (in order):
  1. Runtime      — Python version >= 3.8, report which interpreter resolved.
  2. Deps         — every sibling scripts/*.py: extract top-level imports,
                    verify each non-stdlib module is importable (find_spec).
                    THIS script uses stdlib only, so it cannot fail the same way.
  3. Compile      — py_compile every sibling scripts/*.py (catches syntax rot).
  4. Doc freshness (with --path) — inside the planning folder: warn if
                    handoff.md is older than kanban.md by > --stale-hours
                    (default 24), or if kanban.md is missing.
  5. Long-run reminder — always prints: if the run may exceed ~1 hour, re-auth
                    (/login) BEFORE starting; OAuth expiry mid-run is a known,
                    unrecoverable-in-session failure.

Contract (matches the other validators):
  argv in, exit 0 = pass / exit 1 = fail (warnings alone do not fail),
  human summary on stdout. --json emits a machine-readable object.

Usage:
  python preflight.py                       # tooling checks only
  python preflight.py --path "docs/pkg"     # + doc freshness for that package
  python preflight.py --path "docs/pkg" --json
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import sys
import time
from importlib.util import find_spec
from pathlib import Path

STALE_HOURS_DEFAULT = 24

# Stdlib names we should never flag (fast path; sys.stdlib_module_names covers 3.10+).
def _is_stdlib(mod: str) -> bool:
    root = mod.split(".")[0]
    names = getattr(sys, "stdlib_module_names", None)
    if names is not None:
        return root in names
    return find_spec(root) is not None and "site-packages" not in str(getattr(find_spec(root), "origin", "") or "")


def check_runtime(results: dict) -> None:
    ok = sys.version_info >= (3, 8)
    results["checks"].append({
        "name": "runtime",
        "ok": ok,
        "detail": f"python {sys.version.split()[0]} at {sys.executable}",
    })


def top_level_imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()  # compile check will report it
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module)
    return mods


def check_deps_and_compile(results: dict) -> None:
    here = Path(__file__).resolve().parent
    for script in sorted(here.glob("*.py")):
        if script.name == Path(__file__).name:
            continue
        missing = []
        for mod in sorted(top_level_imports(script)):
            root = mod.split(".")[0]
            if _is_stdlib(root):
                continue
            if find_spec(root) is None:
                missing.append(root)
        results["checks"].append({
            "name": f"deps:{script.name}",
            "ok": not missing,
            "detail": ("missing third-party module(s): " + ", ".join(missing)) if missing
                      else "all imports resolvable",
        })
        try:
            py_compile.compile(str(script), doraise=True)
            results["checks"].append({"name": f"compile:{script.name}", "ok": True, "detail": "compiles"})
        except py_compile.PyCompileError as e:
            results["checks"].append({"name": f"compile:{script.name}", "ok": False, "detail": str(e)[:200]})


def check_doc_freshness(results: dict, folder: Path, stale_hours: float) -> None:
    kanban = folder / "kanban.md"
    handoff = folder / "handoff.md"
    if not kanban.exists():
        results["checks"].append({"name": "freshness:kanban.md", "ok": False,
                                  "detail": f"missing: {kanban}"})
        return
    results["checks"].append({"name": "freshness:kanban.md", "ok": True, "detail": "present"})
    if not handoff.exists():
        results["warnings"].append(f"handoff.md missing in {folder} — runs cannot checkpoint/resume without it")
        return
    lag_h = (kanban.stat().st_mtime - handoff.stat().st_mtime) / 3600.0
    if lag_h > stale_hours:
        results["warnings"].append(
            f"handoff.md is {lag_h:.1f}h older than kanban.md (> {stale_hours}h) — "
            "the handoff likely does not reflect current board state; reconcile before running "
            "(constitution: kanban is truth, handoff must be reconciled to it)")
    hb = folder / ".heartbeat"
    if hb.exists():
        try:
            data = json.loads(hb.read_text(encoding="utf-8"))
            if data.get("status") == "running":
                age_min = (time.time() - hb.stat().st_mtime) / 60.0
                results["warnings"].append(
                    f".heartbeat says a run is still ACTIVE (task {data.get('task','?')}, "
                    f"file age {age_min:.0f} min) — a prior run may have died; read handoff.md "
                    "before starting a new run over the same package")
        except (json.JSONDecodeError, OSError):
            results["warnings"].append(".heartbeat exists but is unreadable — treat prior run state as unknown")


def main() -> int:
    ap = argparse.ArgumentParser(description="Preflight the geeky-orchestration tooling")
    ap.add_argument("--path", help="planning package folder (enables doc-freshness checks)")
    ap.add_argument("--stale-hours", type=float, default=STALE_HOURS_DEFAULT)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = {"ok": True, "checks": [], "warnings": [], "reminders": []}
    check_runtime(results)
    check_deps_and_compile(results)
    if args.path:
        check_doc_freshness(results, Path(args.path), args.stale_hours)
    results["reminders"].append(
        "If this run may exceed ~1 hour: re-auth NOW (/login) before starting. "
        "OAuth expiry mid-run is a known failure with no in-session recovery "
        "(anthropics/claude-code #12447, #15007); the session dies, only handoff.md survives.")

    results["ok"] = all(c["ok"] for c in results["checks"])

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for c in results["checks"]:
            print(f"[{'PASS' if c['ok'] else 'FAIL'}] {c['name']}: {c['detail']}")
        for w in results["warnings"]:
            print(f"[WARN] {w}")
        for r in results["reminders"]:
            print(f"[REMINDER] {r}")
        print(f"PREFLIGHT {'OK' if results['ok'] else 'FAILED'} "
              f"({sum(1 for c in results['checks'] if c['ok'])}/{len(results['checks'])} checks, "
              f"{len(results['warnings'])} warning(s))")
    return 0 if results["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
