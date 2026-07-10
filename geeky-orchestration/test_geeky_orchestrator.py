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

ROUTING_SCENARIOS = (
    (
        "clear direct route",
        "A clear request with one workflow and one target routes directly after "
        "prerequisite checks.",
    ),
    (
        "ambiguous read-only recommendation",
        "Ambiguous intent receives a read-only, evidence-backed workflow "
        "recommendation and no mutation.",
    ),
    (
        "multiple targets clarification",
        "Multiple plausible targets require one focused clarification question "
        "before target selection or mutation.",
    ),
    (
        "explicit implementation",
        "An explicit request to implement a reviewed packet routes to "
        "`geeky-implement`.",
    ),
    (
        "recommendation without write authority",
        "A workflow recommendation does not grant write authority; wait for "
        "explicit authorization before mutation.",
    ),
    (
        "blocker stop",
        "A documented blocker or stop condition stops the run and is reported "
        "rather than routed onward.",
    ),
    (
        "Done routes to review",
        "A packet whose implementation tasks are Done routes to `impl-review`, "
        "not `archive`, unless delivered-code review is already evidenced.",
    ),
    (
        "inferred archive confirmation",
        "An inferred `archive` route requires confirmation of the archive target "
        "and explicit approval before files move.",
    ),
    (
        "explicit end-to-end chaining",
        "Explicit end-to-end authority permits stage chaining, with every gate "
        "and stop condition preserved.",
    ),
    (
        "generic capability-gap stop",
        "A required generic-harness capability gap is reported and stops the "
        "run before unsafe mutation.",
    ),
)


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

    def test_canonical_contract_defines_approved_routing_scenarios(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")
        normalized_text = " ".join(text.split())
        for scenario, exact_policy in ROUTING_SCENARIOS:
            with self.subTest(scenario=scenario):
                self.assertIn(exact_policy, normalized_text)

    def test_new_feature_needing_researched_requirements_routes_to_spec_research(
        self,
    ) -> None:
        text = CANONICAL.read_text(encoding="utf-8")
        self.assertIn(
            "New feature needing researched requirements: `spec-research`.", text
        )
        self.assertNotIn("New researched requirements: `spec-research`.", text)

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
