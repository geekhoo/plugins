def as_markdown(report):
    lines = ["# Codex Operational Preflight", ""]
    append_root(lines, report)
    append_skills(lines, report["skills"])
    append_hooks(lines, report["hooks"], report["hook_shim"])
    append_agents(lines, report["agents"])
    append_commands(lines, report["commands"])
    append_sessions(lines, report["sessions"])
    return "\n".join(lines) + "\n"


def append_root(lines, report):
    lines.append(f"- Codex root: `{report['codex_root']}`")
    lines.append("")


def append_skills(lines, skills):
    lines.append("## Skills")
    for row in skills:
        status = "ok" if row["exists"] and row["skill_md_exists"] else "missing"
        lines.append(f"- `{row['name']}`: {status}")
    lines.append("")


def append_hooks(lines, hooks, shim):
    lines.append("## Hooks")
    hooks_state = "valid" if hooks["json_valid"] else "invalid or missing"
    event_names = ", ".join(sorted(hooks["events"].keys())) if hooks["events"] else "(none)"
    shim_state = "ok" if not shim["issues"] else "issues found"
    lines.append(f"- `hooks.json`: {hooks_state}")
    lines.append(f"- Events: {event_names}")
    lines.append(f"- Windows shim: {shim_state}")
    for issue in hooks["issues"] + shim["issues"]:
        lines.append(f"- Issue: {issue}")
    lines.append("")


def append_agents(lines, agents):
    lines.append("## Agents")
    lines.append(
        f"- TOML files: {agents['toml_files']}; "
        f"nonempty: {agents['nonempty_toml_files']}; "
        f"empty placeholders: {agents['empty_toml_files']}"
    )
    lines.append("")


def append_commands(lines, commands):
    lines.append("## Commands")
    for row in commands:
        status = "ok" if row["available"] else "missing"
        lines.append(f"- `{row['name']}`: {status} {row['path']}")
    lines.append("")


def append_sessions(lines, sessions):
    lines.append("## Sessions")
    lines.append(f"- Rollout files: {sessions['rollout_files']}")
    lines.append(f"- Archived rollout files: {sessions['archived_rollout_files']}")
    lines.append(f"- Session index lines: {sessions['session_index_lines']}")
