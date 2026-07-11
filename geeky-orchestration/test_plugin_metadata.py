from __future__ import annotations

import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PLUGIN_ROOT.parent


class PluginMetadataTests(unittest.TestCase):
    def test_package_versions_are_aligned(self) -> None:
        claude = json.loads(
            (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        codex = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        entry = next(
            plugin for plugin in marketplace["plugins"]
            if plugin["name"] == "geeky-orchestration"
        )
        self.assertEqual(claude["version"], "0.2.6")
        self.assertEqual(codex["version"], "0.2.6")
        self.assertEqual(entry["version"], "0.2.6")

    def test_quality_gate_manifest_version_is_independent(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / "geeky.manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["version"], "0.1.0")

    def test_codex_default_prompts_include_router_within_limit(self) -> None:
        codex = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        prompts = codex["interface"]["defaultPrompt"]
        self.assertIn(
            "Examine this repository and recommend the appropriate Geeky Orchestration workflow.",
            prompts,
        )
        self.assertLessEqual(len(prompts), 3)

    def test_public_docs_describe_router_and_generic_fallback(self) -> None:
        agents = (PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
        registration = (
            PLUGIN_ROOT / "docs" / "cross-harness-agent-registration.md"
        ).read_text(encoding="utf-8")
        self.assertIn("geeky-orchestrator", agents)
        self.assertIn("read-only", agents)
        self.assertIn("geeky-orchestrator", readme)
        self.assertIn(".agents/<name>.md", readme)
        self.assertIn("--agents geeky-orchestrator", readme)
        self.assertNotIn("writes SPEC-NNNN.md", readme)
        self.assertIn(".agents/<name>.md", registration)
        self.assertIn("--agents geeky-orchestrator", registration)


if __name__ == "__main__":
    unittest.main()
