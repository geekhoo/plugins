from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "detect_validation_commands.py"

spec = importlib.util.spec_from_file_location("detect_validation_commands", SCRIPT)
detector = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(detector)


class DetectValidationCommandsTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        for relative_path, content in files.items():
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root

    def detect(self, files: dict[str, str]) -> list[dict]:
        root = self.make_repo(files)
        candidates: list[dict] = []
        detector.detect_package_json(root, candidates)
        detector.detect_python(root, candidates)
        detector.detect_makefile(root, candidates)
        detector.detect_dotnet(root, candidates)
        return candidates

    def commands(self, files: dict[str, str]) -> list[str]:
        return [candidate["command"] for candidate in self.detect(files)]

    def test_node_repo_with_tests_folder_does_not_emit_pytest(self) -> None:
        commands = self.commands(
            {
                "package.json": json.dumps({"scripts": {"test": "vitest"}}),
                "tests/example.test.js": "test('works', () => {});",
            }
        )

        self.assertIn("npm run test", commands)
        self.assertNotIn("python -m pytest", commands)

    def test_python_repo_emits_pytest_from_python_evidence(self) -> None:
        commands = self.commands(
            {
                "pyproject.toml": "[project]\nname = 'example'\n",
                "tests/test_sample.py": "def test_sample():\n    assert True\n",
            }
        )

        self.assertIn("python -m pytest", commands)

    def test_dotnet_repo_emits_build_and_test(self) -> None:
        commands = self.commands(
            {
                "Example.sln": "",
                "src/App/App.csproj": (
                    "<Project Sdk=\"Microsoft.NET.Sdk\" />"
                ),
                "tests/App.Tests/App.Tests.csproj": (
                    "<Project Sdk=\"Microsoft.NET.Sdk\" />"
                ),
            }
        )

        self.assertIn("dotnet build", commands)
        self.assertIn("dotnet test", commands)

    def test_makefile_repo_emits_declared_targets(self) -> None:
        commands = self.commands(
            {
                "Makefile": "lint:\n\tflake8 .\n\ntest:\n\tpytest\n\nbuild:\n\techo build\n",
            }
        )

        self.assertIn("make lint", commands)
        self.assertIn("make test", commands)
        self.assertIn("make build", commands)

    def test_no_manifest_repo_has_no_candidates(self) -> None:
        self.assertEqual([], self.commands({"README.md": "# Empty\n"}))

    def test_mixed_language_repo_keeps_node_and_python_candidates(self) -> None:
        commands = self.commands(
            {
                "package.json": json.dumps({"scripts": {"test": "vitest", "build": "vite build"}}),
                "pyproject.toml": "[project]\nname = 'example'\n",
                "src/example/__init__.py": "",
            }
        )

        self.assertIn("npm run test", commands)
        self.assertIn("npm run build", commands)
        self.assertIn("python -m pytest", commands)

    def test_cli_output_identifies_candidate_detector_scope(self) -> None:
        root = self.make_repo({"README.md": "# Empty\n"})

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(root)],
            check=True,
            capture_output=True,
            text=True,
        )
        output = json.loads(result.stdout)

        self.assertEqual("candidate_detector", output["role"])
        self.assertIn("node", output["inspected_categories"])
        self.assertIn("browser", output["unsupported_categories"])


if __name__ == "__main__":
    unittest.main()
