from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent / "scripts"
PREFLIGHT = SCRIPT_DIR / "preflight.py"


def run_preflight(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PREFLIGHT), *args],
        capture_output=True, text=True, timeout=120,
    )


class PreflightTests(unittest.TestCase):
    def test_tooling_checks_pass_on_shipped_scripts(self) -> None:
        proc = run_preflight("--json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        self.assertTrue(report["ok"])
        # every shipped sibling script must have a deps + compile entry
        names = {c["name"] for c in report["checks"]}
        for script in SCRIPT_DIR.glob("*.py"):
            if script.name == "preflight.py":
                continue
            self.assertIn(f"deps:{script.name}", names)
            self.assertIn(f"compile:{script.name}", names)

    def test_missing_kanban_fails_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_preflight("--path", tmp)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("freshness:kanban.md", proc.stdout)

    def test_active_heartbeat_produces_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "kanban.md").write_text("# Kanban\n## Done\n- T1\n", encoding="utf-8")
            (folder / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
            (folder / ".heartbeat").write_text(
                json.dumps({"ts": "2026-07-13T00:00:00Z", "task": "T1", "status": "running"}),
                encoding="utf-8",
            )
            proc = run_preflight("--path", str(folder), "--json")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(proc.stdout)
            self.assertTrue(any("ACTIVE" in w for w in report["warnings"]), report["warnings"])

    def test_preflight_itself_is_stdlib_only(self) -> None:
        spec = importlib.util.spec_from_file_location("preflight", PREFLIGHT)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        # import must succeed on a bare interpreter (no third-party deps)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "main"))


if __name__ == "__main__":
    unittest.main()
