import shutil

from operational_preflight_hooks import inspect_hooks
from operational_preflight_shim import inspect_shim


DEFAULT_SKILLS = [
    "windows-host-preflight",
    "browser-ui-validation-gates",
    "figma-ui-scope-parity",
    "packet-workflow-integrity",
    "subagent-orchestration-hygiene",
    "source-backed-closeout",
    "patch-baseline-safety",
    "codex-operational-stabilizer",
]


def count_lines(path):
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return None


def command_status(name):
    found = shutil.which(name)
    return {"name": name, "path": found or "", "available": bool(found)}


def inspect_skills(codex_root, required_skills):
    skills_root = codex_root / "skills"
    rows = []
    for name in required_skills:
        skill_dir = skills_root / name
        skill_md = skill_dir / "SKILL.md"
        rows.append(
            {
                "name": name,
                "directory": str(skill_dir),
                "exists": skill_dir.exists(),
                "skill_md_exists": skill_md.exists(),
            }
        )
    return rows


def inspect_agents(codex_root):
    agents_root = codex_root / "agents"
    files = list(agents_root.glob("*.toml")) if agents_root.exists() else []
    nonempty = [path for path in files if path.stat().st_size > 0]
    empty = [path for path in files if path.stat().st_size == 0]
    return {
        "directory": str(agents_root),
        "exists": agents_root.exists(),
        "toml_files": len(files),
        "nonempty_toml_files": len(nonempty),
        "empty_toml_files": len(empty),
        "sample_nonempty": [path.name for path in sorted(nonempty)[:12]],
    }


def count_rollouts(root):
    if not root.exists():
        return 0
    return sum(1 for _ in root.rglob("rollout-*.jsonl"))


def inspect_sessions(codex_root):
    sessions_root = codex_root / "sessions"
    archived_root = codex_root / "archived_sessions"
    index_path = codex_root / "session_index.jsonl"
    return {
        "sessions_root": str(sessions_root),
        "rollout_files": count_rollouts(sessions_root),
        "archived_rollout_files": count_rollouts(archived_root),
        "session_index": str(index_path),
        "session_index_exists": index_path.exists(),
        "session_index_lines": count_lines(index_path) if index_path.exists() else None,
    }


def build_report(codex_root, required_skills):
    commands = ["pwsh", "powershell", "rg", "git", "node", "python", "omx", "codex"]
    return {
        "codex_root": str(codex_root),
        "skills": inspect_skills(codex_root, required_skills),
        "hooks": inspect_hooks(codex_root),
        "hook_shim": inspect_shim(codex_root),
        "agents": inspect_agents(codex_root),
        "commands": [command_status(name) for name in commands],
        "sessions": inspect_sessions(codex_root),
    }
