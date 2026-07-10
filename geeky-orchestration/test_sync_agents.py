from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent
PYTHON_SYNC = PLUGIN_ROOT / "scripts" / "sync-agents.py"
NODE_SYNC = PLUGIN_ROOT / "scripts" / "sync-agents.js"
TARGETS = ("claude", "copilot", "codex", "cursor", "generic")
PROJECTIONS = {
    "claude": Path(".claude/agents/{name}.md"),
    "copilot": Path(".github/agents/{name}.agent.md"),
    "codex": Path(".codex/agents/{name}.toml"),
    "cursor": Path(".cursor/agents/{name}.md"),
    "generic": Path(".agents/{name}.md"),
}


AGENT_TEMPLATE = """---
name: {name}
description: {description}
tools: Read, Grep
model: inherit
color: blue
---

# {title}

{body}
"""


class SyncAgentsTests(unittest.TestCase):
    def make_sources(self, root: Path) -> Path:
        source = root / "sources"
        source.mkdir()
        (source / "alpha.md").write_text(
            AGENT_TEMPLATE.format(
                name="alpha",
                description="Alpha agent.",
                title="Alpha",
                body="Alpha instructions.",
            ),
            encoding="utf-8",
        )
        (source / "beta.md").write_text(
            AGENT_TEMPLATE.format(
                name="beta",
                description="Beta agent.",
                title="Beta",
                body="Beta instructions.",
            ),
            encoding="utf-8",
        )
        return source

    def run_sync(
        self,
        runtime: str,
        source: Path,
        project_root: Path,
        agents: str | None = "beta",
    ) -> subprocess.CompletedProcess[str]:
        if runtime == "python":
            command = [sys.executable, str(PYTHON_SYNC)]
        else:
            node = shutil.which("node")
            if node is None:
                self.skipTest("node is not available")
            command = [node, str(NODE_SYNC)]
        arguments = [
            *command,
            "--source",
            str(source),
            "--project-root",
            str(project_root),
            "--targets",
            ",".join(TARGETS),
        ]
        if agents is not None:
            arguments.extend(("--agents", agents))
        return subprocess.run(
            [*arguments, "--json"],
            check=False,
            capture_output=True,
            text=True,
        )

    def assert_scoped_output(self, runtime: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_sources(root)
            output = root / runtime

            result = self.run_sync(runtime, source, output)

            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["discovered_agent_count"], 2)
            self.assertEqual(report["agent_filter"], ["beta"])
            self.assertEqual(report["agent_count"], 1)
            self.assertEqual(report["targets"], list(TARGETS))
            self.assertEqual(report["generated_count"], len(TARGETS))
            for relative_template in PROJECTIONS.values():
                beta = Path(str(relative_template).format(name="beta"))
                alpha = Path(str(relative_template).format(name="alpha"))
                self.assertTrue((output / beta).is_file(), beta)
                self.assertFalse((output / alpha).exists(), alpha)
            generic = (output / ".agents" / "beta.md").read_text(encoding="utf-8")
            self.assertIn("name: beta", generic)
            self.assertIn("Beta instructions.", generic)
            self.assertNotIn("tools:", generic)

    def test_python_generates_only_selected_agent(self) -> None:
        self.assert_scoped_output("python")

    def test_node_generates_only_selected_agent(self) -> None:
        self.assert_scoped_output("node")

    def test_python_and_node_outputs_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_sources(root)
            python_root = root / "python"
            node_root = root / "node"

            python_result = self.run_sync("python", source, python_root)
            node_result = self.run_sync("node", source, node_root)

            self.assertEqual(python_result.returncode, 0, python_result.stderr)
            self.assertEqual(node_result.returncode, 0, node_result.stderr)
            for relative_template in PROJECTIONS.values():
                relative = Path(str(relative_template).format(name="beta"))
                self.assertEqual(
                    (python_root / relative).read_text(encoding="utf-8"),
                    (node_root / relative).read_text(encoding="utf-8"),
                )

    def test_unknown_agent_filter_fails_without_outputs_in_both_runtimes(self) -> None:
        for runtime in ("python", "node"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = self.make_sources(root)
                output = root / "output"

                result = self.run_sync(runtime, source, output, agents="missing")

                self.assertEqual(result.returncode, 1)
                report = json.loads(result.stdout)
                self.assertFalse(report["ok"])
                self.assertIn("unknown agent name(s): missing", report["error"])
                self.assertFalse(output.exists())

    def test_unfiltered_inventory_generates_every_agent_for_both_runtimes(self) -> None:
        for runtime in ("python", "node"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = self.make_sources(root)
                output = root / "output"

                result = self.run_sync(runtime, source, output, agents=None)

                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                report = json.loads(result.stdout)
                self.assertEqual(report["agent_filter"], [])
                self.assertEqual(report["agent_count"], 2)
                self.assertEqual(report["generated_count"], 2 * len(TARGETS))
                for name in ("alpha", "beta"):
                    for relative_template in PROJECTIONS.values():
                        relative = Path(str(relative_template).format(name=name))
                        self.assertTrue((output / relative).is_file(), relative)

    def test_repeat_run_is_reproducible_for_both_runtimes(self) -> None:
        for runtime in ("python", "node"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = self.make_sources(root)
                output = root / "output"

                first = self.run_sync(runtime, source, output)
                self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
                first_contents = {
                    target: (output / Path(str(relative).format(name="beta"))).read_bytes()
                    for target, relative in PROJECTIONS.items()
                }

                second = self.run_sync(runtime, source, output)
                self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
                second_contents = {
                    target: (output / Path(str(relative).format(name="beta"))).read_bytes()
                    for target, relative in PROJECTIONS.items()
                }

                self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
                self.assertEqual(first_contents, second_contents)

    def test_missing_agent_filter_value_reports_deliberate_error(self) -> None:
        for runtime in ("python", "node"):
            with self.subTest(runtime=runtime):
                if runtime == "python":
                    command = [sys.executable, str(PYTHON_SYNC)]
                else:
                    node = shutil.which("node")
                    if node is None:
                        self.skipTest("node is not available")
                    command = [node, str(NODE_SYNC)]

                result = subprocess.run(
                    [*command, "--json", "--agents"],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                self.assertNotEqual(result.returncode, 0)
                if runtime == "node":
                    report = json.loads(result.stdout)
                    self.assertFalse(report["ok"])
                    error = report["error"]
                else:
                    error = result.stderr
                self.assertIn("argument --agents: expected one argument", error)
                self.assertNotIn("undefined", error)


if __name__ == "__main__":
    unittest.main()
