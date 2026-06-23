from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent / "scripts"


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


check_commit = load_script("check_commit", "check-commit.py")
validate_kanban = load_script("validate_kanban", "validate-kanban.py")


class QualityGateTests(unittest.TestCase):
    def test_check_commit_accepts_conventional_message_with_tasks_line(self) -> None:
        report = check_commit.check("feat(plan): add packet validator\n\nTasks: T3")

        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["warnings"], [])

    def test_check_commit_rejects_missing_task_reference(self) -> None:
        report = check_commit.check("fix(plan): repair validator")

        self.assertFalse(report["ok"])
        self.assertIn("no task reference", report["errors"][0])

    def test_validate_kanban_reports_untracked_task_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            tasks = folder / "tasks"
            tasks.mkdir()
            (tasks / "T1-example.md").write_text("# T1\n", encoding="utf-8")
            (folder / "kanban.md").write_text(
                "\n".join(
                    [
                        "# Kanban",
                        "## Backlog",
                        "## Ready",
                        "## In Progress",
                        "## In Review",
                        "## Blocked",
                        "## Done",
                    ]
                ),
                encoding="utf-8",
            )

            report = validate_kanban.build_report(folder, wip_cap=3)

        self.assertFalse(report["ok"])
        self.assertIn("T1 has a task file but is not placed", report["errors"][0])

    def test_validate_kanban_accepts_single_tracked_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            tasks = folder / "tasks"
            tasks.mkdir()
            (tasks / "T1-example.md").write_text("# T1\n", encoding="utf-8")
            (folder / "kanban.md").write_text(
                "\n".join(
                    [
                        "# Kanban",
                        "## Backlog",
                        "- T1 example",
                        "## Ready",
                        "## In Progress",
                        "## In Review",
                        "## Blocked",
                        "## Done",
                    ]
                ),
                encoding="utf-8",
            )

            report = validate_kanban.build_report(folder, wip_cap=3)

        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])


if __name__ == "__main__":
    unittest.main()
