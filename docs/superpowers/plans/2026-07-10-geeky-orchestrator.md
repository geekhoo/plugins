# Geeky Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable, evidence-gated `geeky-orchestrator` agent with a native Codex projection and a generic fallback definition, while preserving unrelated in-progress work.

**Architecture:** Keep one canonical Markdown agent under `geeky-orchestration/agents/`. Extend the existing Python and Node projection utilities with a `generic` target and a scoped `--agents` filter, then generate five harness projections from that source. The agent performs direct routing for explicit requests and read-only examination plus recommendation for ambiguous requests; stage details stay in the existing workflow skills.

**Tech Stack:** Markdown agent definitions, Python 3.8+ standard library, Node.js standard library, Python `unittest`, JSON, TOML, PowerShell validation commands.

## Global Constraints

- Treat `docs/superpowers/specs/2026-07-10-geeky-orchestrator-design.md` as the approved behavior contract.
- Preserve the existing fix in `geeky-orchestration/scripts/sync-agents.py` that computes `escaped_description` before the Codex f-string.
- Do not modify or commit `geeky-orchestration/agents/geeky-implement-orchestrator.md` or `.github/agents/geeky-implement-orchestrator.agent.md`.
- Do not modify or commit `dev-workflows/skills/codex-work-cleaner/`, `dev-workflows/skills/podman-containers/`, or `outputs/`.
- Generate only `geeky-orchestrator` during this implementation by passing `--agents geeky-orchestrator`.
- Codex inherits the active model; do not add a version-pinned model to `.codex/agents/geeky-orchestrator.toml`.
- The generic `.agents/geeky-orchestrator.md` file is a manual import surface, not a claimed universal discovery standard.
- Never push, force, amend, bypass hooks, or use `--no-verify`.
- Stage only the exact files listed for each task and inspect the staged name list before committing.

---

## File structure

| File | Responsibility |
|---|---|
| `geeky-orchestration/scripts/sync-agents.py` | Canonical Python projection CLI; add generic rendering and scoped agent selection. |
| `geeky-orchestration/scripts/sync-agents.js` | Dependency-free Node projection CLI with behavior identical to Python. |
| `geeky-orchestration/test_sync_agents.py` | Cross-runtime tests for generic output, filtering, error behavior, and parity. |
| `geeky-orchestration/agents/geeky-orchestrator.md` | Canonical hybrid routing and administration contract. |
| `geeky-orchestration/test_geeky_orchestrator.py` | Static contract and generated-projection tests for the new agent. |
| `.claude/agents/geeky-orchestrator.md` | Generated Claude projection. |
| `.github/agents/geeky-orchestrator.agent.md` | Generated Copilot projection, replacing the approved draft. |
| `.codex/agents/geeky-orchestrator.toml` | Generated project-local Codex definition. |
| `.cursor/agents/geeky-orchestrator.md` | Generated Cursor projection. |
| `.agents/geeky-orchestrator.md` | Generated harness-neutral fallback. |
| `geeky-orchestration/AGENTS.md` | General lifecycle, triage, and safety guidance. |
| `geeky-orchestration/README.md` | Public agent inventory and lifecycle documentation. |
| `geeky-orchestration/docs/cross-harness-agent-registration.md` | Generic target and `--agents` usage documentation. |
| `geeky-orchestration/test_plugin_metadata.py` | Version and documentation alignment tests. |
| `geeky-orchestration/.claude-plugin/plugin.json` | Claude package metadata, version `0.2.6`. |
| `geeky-orchestration/.codex-plugin/plugin.json` | Codex package metadata and default prompts, version `0.2.6`. |
| `.claude-plugin/marketplace.json` | Marketplace metadata aligned to version `0.2.6`. |

---

### Task 1: Add scoped generic projection support

**Files:**
- Create: `geeky-orchestration/test_sync_agents.py`
- Modify: `geeky-orchestration/scripts/sync-agents.py`
- Modify: `geeky-orchestration/scripts/sync-agents.js`
- Modify: `geeky-orchestration/docs/cross-harness-agent-registration.md`

**Interfaces:**
- Consumes: canonical `agents/*.md` files parsed into existing `AgentDef` objects.
- Produces: CLI option `--agents <comma-separated-names>`, target name `generic`, generic output `.agents/<name>.md`, JSON fields `discovered_agent_count`, `agent_filter`, `agent_count`, and the existing `generated` list.

- [ ] **Step 1: Write failing cross-runtime projection tests**

Create `geeky-orchestration/test_sync_agents.py` with this complete test module:

```python
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
        agents: str = "beta",
    ) -> subprocess.CompletedProcess[str]:
        if runtime == "python":
            command = [sys.executable, str(PYTHON_SYNC)]
        else:
            node = shutil.which("node")
            if node is None:
                self.skipTest("node is not available")
            command = [node, str(NODE_SYNC)]
        return subprocess.run(
            [
                *command,
                "--source",
                str(source),
                "--project-root",
                str(project_root),
                "--targets",
                "codex,generic",
                "--agents",
                agents,
                "--json",
            ],
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
            self.assertEqual(report["generated_count"], 2)
            self.assertTrue((output / ".codex" / "agents" / "beta.toml").is_file())
            self.assertTrue((output / ".agents" / "beta.md").is_file())
            self.assertFalse((output / ".codex" / "agents" / "alpha.toml").exists())
            self.assertFalse((output / ".agents" / "alpha.md").exists())
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
            for relative in (
                Path(".codex/agents/beta.toml"),
                Path(".agents/beta.md"),
            ):
                self.assertEqual(
                    (python_root / relative).read_text(encoding="utf-8"),
                    (node_root / relative).read_text(encoding="utf-8"),
                )

    def test_unknown_agent_filter_fails_without_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_sources(root)
            output = root / "output"

            result = self.run_sync("python", source, output, agents="missing")

            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertFalse(report["ok"])
            self.assertIn("unknown agent name(s): missing", report["error"])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```powershell
python -B -m unittest discover -s geeky-orchestration -p 'test_sync_agents.py' -v
```

Expected: FAIL because `generic` is not a supported target and `--agents` is not implemented.

- [ ] **Step 3: Implement Python target and filter support**

In `sync-agents.py`:

1. Change the target tuple and add the CLI argument:

```python
SUPPORTED_TARGETS = ("claude", "copilot", "codex", "cursor", "generic")

# Inside parse_args(), after --targets:
p.add_argument(
    "--agents",
    default="",
    help="Comma-separated canonical agent names to project (default: all)",
)
```

2. Add these complete helpers after `render_cursor` and `ensure_targets`:

```python
def render_generic(agent: AgentDef) -> str:
    lines = [
        "---",
        f"name: {agent.name}",
        yaml_block("description", agent.description),
        "---",
        "",
        agent.body.rstrip(),
        "",
    ]
    return "\n".join(lines)


def ensure_agent_filter(raw_agents: str) -> list[str]:
    names = [name.strip() for name in raw_agents.split(",") if name.strip()]
    if len(names) != len(set(names)):
        raise ValueError("duplicate agent name in --agents filter")
    return names


def select_agents(agents: list[AgentDef], names: list[str]) -> list[AgentDef]:
    if not names:
        return agents
    requested = set(names)
    available = {agent.name for agent in agents}
    missing = sorted(requested - available)
    if missing:
        raise ValueError(f"unknown agent name(s): {', '.join(missing)}")
    return [agent for agent in agents if agent.name in requested]
```

3. In `main()`, keep both discovered and selected lists and render generic files:

```python
agent_filter = ensure_agent_filter(args.agents)
source_files = discover_agents(source_dir)
discovered_agents = [load_agent(f) for f in source_files]
unique_names(discovered_agents)
agents = select_agents(discovered_agents, agent_filter)

# Inside the per-agent render loop:
if "generic" in targets:
    out = project_root / ".agents" / f"{agent.name}.md"
    write_file(out, render_generic(agent), args.dry_run)
    generated.append(
        {"target": "generic", "source": str(agent.source_file), "output": str(out)}
    )

# Add to summary before agent_count:
"discovered_agent_count": len(discovered_agents),
"agent_filter": agent_filter,
"agent_count": len(agents),
```

Update the docstring, CLI help, project-root help, and summary notes so they list `.agents` and `generic`.

- [ ] **Step 4: Implement equivalent Node support**

In `sync-agents.js`:

```javascript
const SUPPORTED_TARGETS = ["claude", "copilot", "codex", "cursor", "generic"];

// Add to defaults:
agents: "",

// Add to parseArgs loop:
else if (a === "--agents")                { args.agents = raw[++i]; }
else if (a.startsWith("--agents="))       { args.agents = a.slice("--agents=".length); }
```

Add these helpers:

```javascript
function renderGeneric(agent) {
  return [
    "---",
    `name: ${agent.name}`,
    yamlBlock("description", agent.description),
    "---",
    "",
    agent.body.trimEnd(),
    "",
  ].join("\n");
}

function ensureAgentFilter(rawAgents) {
  const names = rawAgents.split(",").map(name => name.trim()).filter(Boolean);
  if (names.length !== new Set(names).size) {
    throw new Error("duplicate agent name in --agents filter");
  }
  return names;
}

function selectAgents(agents, names) {
  if (!names.length) return agents;
  const requested = new Set(names);
  const available = new Set(agents.map(agent => agent.name));
  const missing = [...requested].filter(name => !available.has(name)).sort();
  if (missing.length) throw new Error(`unknown agent name(s): ${missing.join(", ")}`);
  return agents.filter(agent => requested.has(agent.name));
}
```

Use the selected list and emit generic files:

```javascript
const agentFilter      = ensureAgentFilter(args.agents);
const sourceFiles      = discoverAgents(sourceDir);
const discoveredAgents = sourceFiles.map(loadAgent);
ensureUniqueNames(discoveredAgents);
const agents = selectAgents(discoveredAgents, agentFilter);

if (targets.includes("generic")) {
  const out = path.join(projectRoot, ".agents", `${agent.name}.md`);
  writeFile(out, renderGeneric(agent), args.dryRun);
  generated.push({ target: "generic", source: agent.sourceFile, output: out });
}

// Summary fields:
discovered_agent_count: discoveredAgents.length,
agent_filter: agentFilter,
agent_count: agents.length,
```

Update the JS header, usage output, and notes to match Python.

- [ ] **Step 5: Document the new target and filter**

Update `docs/cross-harness-agent-registration.md` with:

```markdown
# scoped projection
python scripts/sync-agents.py --agents geeky-orchestrator
node   scripts/sync-agents.js --agents geeky-orchestrator

# harness-neutral fallback
python scripts/sync-agents.py --targets generic --agents geeky-orchestrator
node   scripts/sync-agents.js --targets generic --agents geeky-orchestrator
```

Add `.agents/<name>.md` to generated outputs and explain that generic Markdown is for manual import or future adapters, with no promise of automatic discovery.

- [ ] **Step 6: Run focused and existing tests**

Run:

```powershell
python -B -m unittest discover -s geeky-orchestration -p 'test_sync_agents.py' -v
python -B -m unittest discover -s geeky-orchestration -p 'test*.py' -v
node --check geeky-orchestration/scripts/sync-agents.js
```

Expected: all tests PASS and Node syntax check exits 0.

- [ ] **Step 7: Commit only projection tooling files**

```powershell
git add -- geeky-orchestration/test_sync_agents.py geeky-orchestration/scripts/sync-agents.py geeky-orchestration/scripts/sync-agents.js geeky-orchestration/docs/cross-harness-agent-registration.md
git diff --cached --name-only
git diff --cached --check
git commit -m "feat(plugin): add generic agent projection"
```

Expected staged names: exactly the four paths above. This commit intentionally includes the pre-existing `escaped_description` Python fix because it is required for the Python renderer to execute.

---

### Task 2: Create the hybrid orchestrator and projections

**Files:**
- Create: `geeky-orchestration/test_geeky_orchestrator.py`
- Create: `geeky-orchestration/agents/geeky-orchestrator.md`
- Create: `.claude/agents/geeky-orchestrator.md`
- Modify: `.github/agents/geeky-orchestrator.agent.md`
- Create: `.codex/agents/geeky-orchestrator.toml`
- Create: `.cursor/agents/geeky-orchestrator.md`
- Create: `.agents/geeky-orchestrator.md`

**Interfaces:**
- Consumes: explicit user intent, repository evidence, applicable repository instructions, selected workflow skill and references, validator results, available harness capabilities.
- Produces: a direct authorized workflow run or a read-only evidence-backed workflow recommendation with focused clarification.

- [ ] **Step 1: Write the failing agent-contract tests**

Create `geeky-orchestration/test_geeky_orchestrator.py`:

```python
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
        self.assertNotIn("pick the earliest stage whose output they don't yet have", text.lower())

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
            with (output / ".codex/agents/geeky-orchestrator.toml").open("rb") as handle:
                codex = tomllib.load(handle)
            self.assertEqual(codex["name"], "geeky-orchestrator")
            self.assertIn("### Triage mode", codex["developer_instructions"])
            self.assertNotIn("model", codex)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract tests and verify they fail**

```powershell
python -B -m unittest discover -s geeky-orchestration -p 'test_geeky_orchestrator.py' -v
```

Expected: FAIL because the canonical `geeky-orchestrator.md` does not exist.

- [ ] **Step 3: Create the canonical hybrid agent**

Create `geeky-orchestration/agents/geeky-orchestrator.md` with this structure and exact behavioral clauses:

```markdown
---
name: geeky-orchestrator
description: >-
  Use as the intelligent control plane for any geeky-orchestration entry point. Examines repository context, routes explicit requests to the best workflow, recommends a workflow when instructions are unclear, administers lifecycle state, and asks focused clarification questions when evidence cannot resolve a material choice.
tools: Glob, Grep, LS, Read, Edit, Write, Bash, PowerShell, TaskCreate, TaskUpdate, TaskList, Agent, TodoWrite, WebSearch, WebFetch
model: inherit
color: purple
---

You are the **Geeky Orchestrator**, the control plane for the complete
`geeky-orchestration` lifecycle. You route and administer work; current workflow
skills remain authoritative for stage-specific execution.

## Operating contract

- Clear, explicit user instructions win. Examine prerequisites, decide the best
  course within the authorized scope, load the workflow instructions, and act.
- Unclear instructions trigger read-only examination of the codebase, repository
  guidance, Git state, planning packets, and validator availability. Recommend
  the best workflow and target with evidence. Do not mutate from an inferred
  recommendation alone.
- Ask one focused question when workflow, target, scope, authority, or a material
  trade-off remains unresolved.
- Distinguish confirmed evidence, inference, missing information, and blockers.
- Never auto-chain into another lifecycle stage unless the user explicitly
  authorized an end-to-end run.

## Authoritative sources

Use this precedence: explicit user boundaries; applicable `AGENTS.md` and
`CLAUDE.md`; the selected `SKILL.md` and its references; current validators and
`geeky.manifest.json`; command wrappers; README/runbook prose. If material
authoritative sources still conflict, surface the contradiction and ask instead
of guessing.

Locate the plugin from current workspace evidence or installed capability
metadata. Never invent a stale versioned cache path. Load the selected
`SKILL.md` completely and load every reference it marks as required before
executing that stage.

## Runtime modes

### Direct mode

For a clear request, validate the target and prerequisites, select the best
matching workflow, state the route and execution authority, then execute its
complete procedure until its documented completion or stop condition.

### Triage mode

For an unclear request, perform read-only examination first. Report the
recommended workflow, target, supporting evidence, missing information, and
blockers. Do not mutate. Ask for the smallest decision still required.

### Administration mode

For explicit operational administration, inspect status, validate packets,
diagnose blockers, reconcile mutable tracking artifacts, and recommend safe
resumption. For explicit plugin administration, maintain canonical agents,
projections, manifests, hooks, MCP registration, tests, and evaluation evidence.

### End-to-end mode

Chain stages only under explicit end-to-end authority. Re-load each stage's
skill, run its gates, and preserve its stop conditions. Pause on blockers,
missing external authority, gate failures, or required user decisions.

### Generic fallback mode

Map conceptual read, search, edit, command, planning, and delegation operations
to the current harness. If the harness cannot enforce a required guard, run a
validator, preserve frozen artifacts, or provide required delegation semantics,
report the capability gap and stop before unsafe mutation.

## Workflow routing

- New researched requirements: `spec-research`.
- Requirements or a specification needing a packet: `geeky-plan`.
- Packet readiness review: `plan-review`.
- Status, orientation, or resume diagnosis: `geeky-status`.
- Explicit implementation of a reviewed packet: `geeky-implement`.
- Delivered-code review: `impl-review`.
- Explicit archival of a complete, reviewed, signed-off package: `archive`.

Artifact state supports a recommendation but does not independently authorize a
write workflow. Explicit stage, target, flags, and permission boundaries must be
preserved.

## Known reconciliations

- `feature-specification.md` is canonical; `SPEC-NNNN-*.md` is legacy.
- `handoff.md` is mutable during implementation.
- A Done lane move is provisional until `check-dod` and kanban validation pass.
- Validator warnings and policy-level requirements remain visible even on exit 0.
- Planning PM review does not prove `plan-review` or `impl-review` completion.
- Archive target discovery is read-only; confirm a missing explicit target before
  file moves.

## Delegation and validation

Delegate only when the selected skill permits it. Use no more than three workers,
and parallelize only independent, non-overlapping work. The orchestrator owns
integration and re-runs required gates; never trust worker validation claims.

## Hard rules

Never edit frozen planning artifacts during implementation. Never push, force,
amend, bypass hooks, or use `--no-verify`. Preserve unrelated worktree changes.
Stop on a Blocked implementation task after finalizing allowed mutable state.
Treat `geeky-status` as strictly read-only. Require explicit approval for
external installation, publication, critical-review fixes, and archive moves
when the target was inferred.

## Reporting

State the selected or recommended workflow, target, evidence, authority,
validation results, changes, blockers, and one recommended next stage. Once a
workflow runs, follow its stage-specific output contract.
```

Keep the final canonical prompt compact, but preserve every clause above. Improve prose only when the behavior remains identical to the approved design.

- [ ] **Step 4: Generate only the new agent's projections**

Run both implementations into temporary roots first and compare them through the tests. Then generate repository outputs with Python:

```powershell
python geeky-orchestration/scripts/sync-agents.py --agents geeky-orchestrator --targets claude,copilot,codex,cursor,generic
```

Expected: exactly five files reported, one per target. Confirm `geeky-implement-orchestrator` files were not changed.

- [ ] **Step 5: Run focused and full validation**

```powershell
python -B -m unittest discover -s geeky-orchestration -p 'test_geeky_orchestrator.py' -v
python -B -m unittest discover -s geeky-orchestration -p 'test*.py' -v
python -c "import pathlib,tomllib; tomllib.loads(pathlib.Path('.codex/agents/geeky-orchestrator.toml').read_text(encoding='utf-8')); print('Codex TOML: PASS')"
git diff --check
```

Expected: all tests PASS, TOML prints `Codex TOML: PASS`, and diff check exits 0.

- [ ] **Step 6: Commit only the canonical agent, test, and five projections**

```powershell
git add -- geeky-orchestration/test_geeky_orchestrator.py geeky-orchestration/agents/geeky-orchestrator.md .claude/agents/geeky-orchestrator.md .github/agents/geeky-orchestrator.agent.md .codex/agents/geeky-orchestrator.toml .cursor/agents/geeky-orchestrator.md .agents/geeky-orchestrator.md
git diff --cached --name-only
git diff --cached --check
git commit -m "feat(plugin): add geeky orchestrator agent"
```

Expected staged names: exactly the seven paths above.

---

### Task 3: Align workflow guidance and package metadata

**Files:**
- Create: `geeky-orchestration/test_plugin_metadata.py`
- Modify: `geeky-orchestration/AGENTS.md`
- Modify: `geeky-orchestration/README.md`
- Modify: `geeky-orchestration/.claude-plugin/plugin.json`
- Modify: `geeky-orchestration/.codex-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: the canonical orchestrator behavior and plugin version `0.2.5`.
- Produces: aligned package version `0.2.6`, discoverable orchestrator descriptions, full lifecycle guidance, and metadata regression tests. `geeky.manifest.json` remains at `0.1.0` because it is the quality-gate manifest version.

- [ ] **Step 1: Write failing metadata and documentation tests**

Create `geeky-orchestration/test_plugin_metadata.py`:

```python
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

    def test_public_docs_describe_router_and_generic_fallback(self) -> None:
        agents = (PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
        registration = (
            PLUGIN_ROOT / "docs" / "cross-harness-agent-registration.md"
        ).read_text(encoding="utf-8")
        self.assertIn("geeky-orchestrator", agents)
        self.assertIn("read-only", agents)
        self.assertIn("geeky-orchestrator", readme)
        self.assertIn(".agents/<name>.md", registration)
        self.assertIn("--agents geeky-orchestrator", registration)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the metadata tests and verify they fail**

```powershell
python -B -m unittest discover -s geeky-orchestration -p 'test_plugin_metadata.py' -v
```

Expected: FAIL because versions remain `0.2.5` and general guidance does not yet name the router.

- [ ] **Step 3: Update general workflow guidance**

In `geeky-orchestration/AGENTS.md`, replace the three-stage overview with the full lifecycle:

```markdown
## The workflow

1. **spec-research** — research and write `feature-specification.md`.
2. **geeky-plan** — create the frozen planning package.
3. **plan-review** — validate alignment, coverage, sequencing, and readiness.
4. **geeky-status** — read-only status and resumption orientation at any packet stage.
5. **geeky-implement** — execute Ready tasks with validation and review gates.
6. **impl-review** — review delivered code through three domain-specific lanes.
7. **archive** — move completed planning artifacts into the archive structure.

Use **geeky-orchestrator** when the requested entry point is unclear or when one
agent should administer the lifecycle. It examines repository evidence read-only
and recommends a workflow before mutation. Clear, explicit requests route to the
best matching skill after prerequisite checks. Material ambiguity is clarified;
stages are not auto-chained without end-to-end authorization.
```

Keep all existing planning-folder and deterministic-gate rules below this section.

In `README.md`:

- Correct the `spec-research` row to say it writes `feature-specification.md` and `README.md`.
- Add a `geeky-orchestrator` agent row describing direct routing, read-only triage, workflow administration, and focused clarification.
- In the cross-harness section, list the generic output and scoped command.

- [ ] **Step 4: Align package metadata at version 0.2.6**

Apply these exact version changes:

```json
"version": "0.2.6"
```

to:

- `geeky-orchestration/.claude-plugin/plugin.json`
- `geeky-orchestration/.codex-plugin/plugin.json`
- the `geeky-orchestration` entry in `.claude-plugin/marketplace.json`

Update descriptions to mention the intelligent `geeky-orchestrator` and portable agent projections. Add this Codex default prompt:

```json
"Examine this repository and recommend the appropriate Geeky Orchestration workflow."
```

Do not change `geeky-orchestration/geeky.manifest.json` version `0.1.0`.

- [ ] **Step 5: Run all repository validation and plugin evaluation**

```powershell
python -B -m unittest discover -s geeky-orchestration -p 'test*.py' -v
python geeky-orchestration/scripts/sync-agents.py --agents geeky-orchestrator --dry-run --json
node geeky-orchestration/scripts/sync-agents.js --agents geeky-orchestrator --dry-run --json
node --check geeky-orchestration/scripts/sync-agents.js
python -c "import json,pathlib,tomllib; json.loads(pathlib.Path('geeky-orchestration/.claude-plugin/plugin.json').read_text()); json.loads(pathlib.Path('geeky-orchestration/.codex-plugin/plugin.json').read_text()); json.loads(pathlib.Path('.claude-plugin/marketplace.json').read_text()); tomllib.loads(pathlib.Path('.codex/agents/geeky-orchestrator.toml').read_text()); print('metadata parse: PASS')"
git diff --check
node 'C:\Users\gerald.khoo\.codex\plugins\cache\openai-curated\plugin-eval\d6169bef\scripts\plugin-eval.js' analyze '.\geeky-orchestration' --format markdown
```

Expected:

- all unit tests PASS;
- Python and Node dry-runs each report one selected agent and five targets;
- syntax and parse commands exit 0;
- `git diff --check` exits 0;
- plugin evaluation has zero failures and no new agent-specific warning compared with the recorded baseline of `73/C`, 0 failures, 6 warnings, and 2 informational findings. If the evaluator version or scoring changes, report the new output rather than forcing the old score.

- [ ] **Step 6: Inspect final scope before commit**

```powershell
git status --short
git diff -- geeky-orchestration/AGENTS.md geeky-orchestration/README.md geeky-orchestration/.claude-plugin/plugin.json geeky-orchestration/.codex-plugin/plugin.json .claude-plugin/marketplace.json geeky-orchestration/test_plugin_metadata.py
```

Expected: only intended Task 3 changes in the displayed diff; separate untracked work remains unmodified.

- [ ] **Step 7: Commit documentation and metadata alignment**

```powershell
git add -- geeky-orchestration/test_plugin_metadata.py geeky-orchestration/AGENTS.md geeky-orchestration/README.md geeky-orchestration/.claude-plugin/plugin.json geeky-orchestration/.codex-plugin/plugin.json .claude-plugin/marketplace.json
git diff --cached --name-only
git diff --cached --check
git commit -m "docs(plugin): document geeky orchestrator"
```

Expected staged names: exactly the six paths above.

---

## Final verification

After all three task commits:

```powershell
python -B -m unittest discover -s geeky-orchestration -p 'test*.py' -v
python geeky-orchestration/scripts/sync-agents.py --agents geeky-orchestrator --targets claude,copilot,codex,cursor,generic --dry-run --json
node geeky-orchestration/scripts/sync-agents.js --agents geeky-orchestrator --targets claude,copilot,codex,cursor,generic --dry-run --json
python -c "import pathlib,tomllib; data=tomllib.loads(pathlib.Path('.codex/agents/geeky-orchestrator.toml').read_text(encoding='utf-8')); assert data['name']=='geeky-orchestrator'; assert '### Triage mode' in data['developer_instructions']; assert 'model' not in data; print('Codex agent: PASS')"
git diff --check
git status --short --branch
git log -4 --oneline --decorate
```

Final acceptance evidence must include:

- exact unit-test count and pass result;
- Python/Node selected agent and generated target counts;
- Codex TOML parse result;
- plugin-eval score and warning delta from baseline;
- the three implementation commit SHAs plus the design and plan commits;
- explicit confirmation that no push occurred;
- remaining unrelated worktree paths listed separately;
- global Codex installation listed as not performed unless separately authorized.
