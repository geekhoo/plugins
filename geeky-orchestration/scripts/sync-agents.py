#!/usr/bin/env python3
"""sync-agents.py

Project utility for projecting canonical plugin agents (agents/*.md) into
harness-specific locations/formats so they can be discovered/registered by
multiple coding harnesses.

Canonical source (this plugin):
  <plugin-root>/agents/*.md

Generated projections:
  Claude Code: <project-root>/.claude/agents/*.md
  Copilot/VS Code: <project-root>/.github/agents/*.agent.md
  Codex CLI: <project-root>/.codex/agents/*.toml
  Cursor (experimental): <project-root>/.cursor/agents/*.md

Notes:
- This script intentionally uses compatibility-safe output for non-Claude
  harnesses. It keeps name/description/instructions and avoids tool/model fields
  where schema/tool-name mismatches may prevent registration.
- Cursor file-based custom agent loading has changed across versions; projection
  is generated as an optional best-effort artifact.

Contract:
- Exit 0 on success, 1 on validation or write failures.
- Human summary on stdout.
- Optional --json for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_TARGETS = ("claude", "copilot", "codex", "cursor")


@dataclass
class AgentDef:
    source_file: Path
    name: str
    description: str
    model: str | None
    color: str | None
    tools: list[str]
    body: str


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    plugin_root = here.parent

    p = argparse.ArgumentParser(add_help=True)
    p.add_argument(
        "--source",
        default=str(plugin_root / "agents"),
        help="Path to canonical agent markdown files (default: <plugin-root>/agents)",
    )
    p.add_argument(
        "--project-root",
        default=str(plugin_root.parent),
        help="Project root where .claude/.github/.codex/.cursor folders will be created",
    )
    p.add_argument(
        "--targets",
        default=",".join(SUPPORTED_TARGETS),
        help="Comma-separated targets: claude,copilot,codex,cursor (default: all)",
    )
    p.add_argument("--dry-run", action="store_true", help="Preview only; do not write files")
    p.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON summary")
    return p.parse_args()


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if ((value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))):
        return value[1:-1]
    return value


def parse_frontmatter(md_text: str) -> tuple[dict[str, str], str]:
    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter opening '---'")

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("missing YAML frontmatter closing '---'")

    fm_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1:]).lstrip("\n")

    fm: dict[str, str] = {}
    i = 0
    while i < len(fm_lines):
        raw = fm_lines[i]
        if not raw.strip() or raw.strip().startswith("#"):
            i += 1
            continue

        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", raw)
        if not m:
            i += 1
            continue

        key, value = m.group(1).strip(), m.group(2).rstrip()
        if value in ("|", "|-", ">", ">-"):
            i += 1
            block: list[str] = []
            while i < len(fm_lines):
                nxt = fm_lines[i]
                if nxt.startswith(" ") or nxt.startswith("\t") or not nxt.strip():
                    block.append(nxt[1:] if nxt.startswith(" ") else nxt)
                    i += 1
                    continue
                break
            joined = "\n".join(block).strip("\n")
            if value.startswith(">"):
                # Fold newlines into spaces for simple scalar use-cases.
                joined = " ".join(part.strip() for part in joined.splitlines() if part.strip())
            fm[key] = joined
            continue

        fm[key] = _strip_quotes(value.strip())
        i += 1

    return fm, body


def parse_tools(raw_tools: str | None) -> list[str]:
    if not raw_tools:
        return []

    raw = raw_tools.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]

    parts = [p.strip() for p in raw.split(",")]
    cleaned: list[str] = []
    for part in parts:
        part = _strip_quotes(part)
        if part:
            cleaned.append(part)
    return cleaned


def load_agent(path: Path) -> AgentDef:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)

    name = (fm.get("name") or "").strip()
    desc = (fm.get("description") or "").strip()
    if not name:
        raise ValueError(f"{path.name}: missing 'name' in frontmatter")
    if not desc:
        raise ValueError(f"{path.name}: missing 'description' in frontmatter")
    if not body.strip():
        raise ValueError(f"{path.name}: empty agent prompt body")

    return AgentDef(
        source_file=path,
        name=name,
        description=desc,
        model=(fm.get("model") or "").strip() or None,
        color=(fm.get("color") or "").strip() or None,
        tools=parse_tools(fm.get("tools")),
        body=body.rstrip() + "\n",
    )


def yaml_block(key: str, value: str) -> str:
    safe = value.replace("\r\n", "\n").strip("\n")
    return f"{key}: >-\n  " + "\n  ".join(safe.split("\n"))


def render_claude(agent: AgentDef) -> str:
    lines = [
        "---",
        f"name: {agent.name}",
        yaml_block("description", agent.description),
    ]
    if agent.tools:
        lines.append("tools: " + ", ".join(agent.tools))
    if agent.model:
        lines.append(f"model: {agent.model}")
    if agent.color:
        lines.append(f"color: {agent.color}")
    lines.extend(["---", "", agent.body.rstrip(), ""])
    return "\n".join(lines)


def render_copilot(agent: AgentDef) -> str:
    # Compatibility-safe: keep the persona and instructions; avoid strict tool
    # field mapping since Copilot tool IDs differ by version.
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


def _toml_escape(value: str) -> str:
    return value.replace('"""', '\\"\\"\\"')


def render_codex(agent: AgentDef) -> str:
    # Required fields per Codex subagent schema.
    escaped_description = agent.description.replace('"', '\\"')
    return (
        f'name = "{agent.name}"\n'
        f'description = "{escaped_description}"\n'
        "developer_instructions = \"\"\"\n"
        f"{_toml_escape(agent.body.rstrip())}\n"
        "\"\"\"\n"
    )


def render_cursor(agent: AgentDef) -> str:
    # Experimental best-effort projection based on markdown+frontmatter pattern.
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


def ensure_targets(raw_targets: str) -> list[str]:
    targets = [t.strip().lower() for t in raw_targets.split(",") if t.strip()]
    bad = [t for t in targets if t not in SUPPORTED_TARGETS]
    if bad:
        raise ValueError(f"unsupported target(s): {', '.join(bad)}")
    if not targets:
        raise ValueError("no targets specified")
    return targets


def write_file(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def discover_agents(source_dir: Path) -> list[Path]:
    if not source_dir.is_dir():
        raise ValueError(f"missing source directory: {source_dir}")
    files = sorted(p for p in source_dir.glob("*.md") if p.is_file())
    if not files:
        raise ValueError(f"no *.md agent files found in {source_dir}")
    return files


def unique_names(agents: Iterable[AgentDef]) -> None:
    seen: dict[str, Path] = {}
    for agent in agents:
        if agent.name in seen:
            raise ValueError(
                f"duplicate agent name '{agent.name}' in "
                f"{seen[agent.name].name} and {agent.source_file.name}"
            )
        seen[agent.name] = agent.source_file


def main() -> int:
    args = parse_args()

    try:
        targets = ensure_targets(args.targets)
        source_dir = Path(args.source).resolve()
        project_root = Path(args.project_root).resolve()

        source_files = discover_agents(source_dir)
        agents = [load_agent(f) for f in source_files]
        unique_names(agents)

        generated: list[dict[str, str]] = []

        for agent in agents:
            if "claude" in targets:
                out = project_root / ".claude" / "agents" / f"{agent.name}.md"
                write_file(out, render_claude(agent), args.dry_run)
                generated.append(
                    {"target": "claude", "source": str(agent.source_file), "output": str(out)})

            if "copilot" in targets:
                out = project_root / ".github" / "agents" / f"{agent.name}.agent.md"
                write_file(out, render_copilot(agent), args.dry_run)
                generated.append(
                    {"target": "copilot", "source": str(agent.source_file), "output": str(out)})

            if "codex" in targets:
                out = project_root / ".codex" / "agents" / f"{agent.name}.toml"
                write_file(out, render_codex(agent), args.dry_run)
                generated.append(
                    {"target": "codex", "source": str(agent.source_file), "output": str(out)})

            if "cursor" in targets:
                out = project_root / ".cursor" / "agents" / f"{agent.name}.md"
                write_file(out, render_cursor(agent), args.dry_run)
                generated.append(
                    {"target": "cursor", "source": str(agent.source_file), "output": str(out)})

        summary = {
            "ok": True,
            "dry_run": bool(args.dry_run),
            "source_dir": str(source_dir),
            "project_root": str(project_root),
            "targets": targets,
            "agent_count": len(agents),
            "generated_count": len(generated),
            "generated": generated,
            "notes": [
                "Claude projection preserves tools/model/color.",
                "Copilot projection uses compatibility-safe frontmatter "
                "without explicit tool mapping.",
                "Codex projection emits required TOML fields: name, "
                "description, developer_instructions.",
                "Cursor projection is best-effort and should be validated "
                "against installed Cursor version.",
            ],
        }

        if args.as_json:
            print(json.dumps(summary, indent=2))
        else:
            mode = "DRY-RUN" if args.dry_run else "WROTE"
            print(f"{mode}: {len(generated)} projection file(s) "
                  f"from {len(agents)} canonical agent(s).")
            for item in generated:
                print(f"  - [{item['target']}] {item['output']}")

        return 0

    except Exception as exc:  # pragma: no cover
        payload = {"ok": False, "error": str(exc)}
        if args.as_json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
