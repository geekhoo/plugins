from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "geeky-orchestration"
CANONICAL = PLUGIN_ROOT / "agents" / "geeky-orchestrator.md"
SYNC = PLUGIN_ROOT / "scripts" / "sync-agents.py"


class GeekyOrchestratorContractTests(unittest.TestCase):
    def test_canonical_contract_contains_required_runtime_modes(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")
        required = (
            "name: geeky-orchestrator",
            "## Runtime modes",
            "### Direct mode",
            "### Triage mode",
            "### Administration mode",
            "### End-to-end mode",
            "### Generic fallback mode",
            "read-only examination",
            "Load the selected `SKILL.md` completely",
            "Do not mutate",
            "Never auto-chain",
            "Never push",
            "feature-specification.md",
            "provisional",
        )
        for item in required:
            self.assertIn(item, text)
        self.assertNotIn(
            "pick the earliest stage whose output they don't yet have", text.lower()
        )

    def test_scoped_sync_generates_all_five_projections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC),
                    "--source",
                    str(PLUGIN_ROOT / "agents"),
                    "--project-root",
                    str(output),
                    "--agents",
                    "geeky-orchestrator",
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            expected = (
                Path(".claude/agents/geeky-orchestrator.md"),
                Path(".github/agents/geeky-orchestrator.agent.md"),
                Path(".codex/agents/geeky-orchestrator.toml"),
                Path(".cursor/agents/geeky-orchestrator.md"),
                Path(".agents/geeky-orchestrator.md"),
            )
            for relative in expected:
                self.assertTrue((output / relative).is_file(), relative)
            with (output / ".codex/agents/geeky-orchestrator.toml").open(
                "rb"
            ) as handle:
                codex = tomllib.load(handle)
            self.assertEqual(codex["name"], "geeky-orchestrator")
            self.assertIn("### Triage mode", codex["developer_instructions"])
            self.assertNotIn("model", codex)


if __name__ == "__main__":
    unittest.main()
