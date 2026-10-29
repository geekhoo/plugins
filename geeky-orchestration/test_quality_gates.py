from __future__ import annotations

import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
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


class CommitGateCliTests(unittest.TestCase):
    def assert_gate_result(self, message: str, expected_errors: list[str]) -> None:
        pwsh = shutil.which("pwsh")
        self.assertIsNotNone(pwsh, "PowerShell 7 is required to verify the paired gate")
        commands = {
            "python": [
                sys.executable, str(SCRIPT_DIR / "check-commit.py"),
                "--json", "--message", message,
            ],
            "pwsh": [
                pwsh, "-NoProfile", "-NonInteractive", "-File",
                str(SCRIPT_DIR / "check-commit.ps1"), "-Json", "-Message", message,
            ],
        }
        for backend, command in commands.items():
            with self.subTest(backend=backend):
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, int(bool(expected_errors)), result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["ok"], not expected_errors)
                self.assertEqual(report["errors"], expected_errors)
                self.assertEqual(report["warnings"], [])

    def test_spec_research_full_commit_message_passes(self) -> None:
        skill = SCRIPT_DIR.parent / "skills" / "spec-research" / "SKILL.md"
        command = next(
            line for line in skill.read_text(encoding="utf-8").splitlines()
            if line.startswith("git commit -m ")
        )
        arguments = shlex.split(command)
        self.assertEqual(arguments[:2], ["git", "commit"])
        self.assertEqual(arguments[2::2], ["-m"] * 4)
        paragraphs = arguments[3::2]
        self.assertEqual(paragraphs, [
            "docs: author feature specification in <feature-folder>",
            "[1-line summary of the spec focus]",
            "Research conducted by: codebase analyst, researcher 2 domain, researcher 3 domain",
            "Tasks: none (pre-planning specification)",
        ])
        self.assert_gate_result("\n\n".join(paragraphs), [])

    def test_feat_with_none_is_rejected(self) -> None:
        self.assert_gate_result(
            "feat(plan): add packet validator\n\nTasks: none",
            ["Tasks: none is allowed only for docs commits"],
        )

    def test_fix_without_task_is_rejected(self) -> None:
        self.assert_gate_result(
            "fix(plan): repair validator",
            ["no task reference (expected a Tasks: line with T<n>)"],
        )

    def test_feat_with_task_passes(self) -> None:
        self.assert_gate_result("feat(plan): add packet validator\n\nTasks: T3", [])

    def test_docs_none_line_is_case_insensitive(self) -> None:
        self.assert_gate_result(
            "docs(plan)!: author specification\n\n  tAsKs: NoNe (pre-planning specification)",
            [],
        )

    def test_non_docs_none_is_rejected_even_with_task_reference(self) -> None:
        self.assert_gate_result(
            "feat(plan): add packet validator\n\nTasks: none\n\nTasks: T3",
            ["Tasks: none is allowed only for docs commits"],
        )


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
