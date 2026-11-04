from pathlib import Path
import re

from operational_preflight_json import load_json_file


def hook_command_paths(command):
    paths = []
    marker = '-File "'
    powershell_command = re.match(
        r'\s*(?:(?:powershell|pwsh)(?:\.exe)?|"[^"\r\n]*[\\/](?:powershell|pwsh)\.exe")\s+',
        command,
        re.IGNORECASE,
    )
    if marker not in command or not powershell_command:
        # Only direct Node invocations with one literal operand are supported.
        # Full matching deliberately excludes options, wrappers and compound commands.
        executable = r"(?:[A-Za-z]:[\\/]|\\\\)(?:[^\r\n\"']*[\\/])?node\.exe"
        match = re.fullmatch(
            rf"\s*(?:node(?:\.exe)?|\"{executable}\"|'{executable}')\s+"
            r"(?:\"([^\"\r\n]+)\"|'([^'\r\n]+)'|([^\s\"']+))\s*",
            command,
            re.IGNORECASE,
        )
        if match:
            path = next(value for value in match.groups() if value is not None)
            if not path.startswith('-') and not any(char in path for char in '$%`;&|<>()'):
                paths.append(path)
        return paths
    start = command.find(marker) + len(marker)
    end = command.find('"', start)
    if end > start:
        paths.append(command[start:end])
    return paths


def hook_command_info(hook):
    command = hook.get("command", "")
    paths = hook_command_paths(command)
    return {
        "type": hook.get("type", ""),
        "command": command,
        "timeout": hook.get("timeout"),
        "referenced_paths": paths,
        "missing_paths": [path for path in paths if not Path(path).exists()],
    }


def empty_hook_result(hooks_json):
    return {
        "hooks_json": str(hooks_json),
        "exists": hooks_json.exists(),
        "json_valid": False,
        "events": {},
        "issues": [],
    }


def load_hooks_json(hooks_json, result):
    data = load_json_file(hooks_json, result["issues"], "hooks.json")
    if data is None:
        return None
    result["json_valid"] = True
    return data


def inspect_hook_event(event, entries):
    event_info = {"entries": len(entries), "commands": []}
    issues = []
    for entry in entries:
        for hook in entry.get("hooks", []):
            command_info = hook_command_info(hook)
            event_info["commands"].append(command_info)
            issues.extend(f"{event} references missing path: {path}" for path in command_info["missing_paths"])
    return event_info, issues


def inspect_hooks(codex_root):
    hooks_json = codex_root / "hooks.json"
    result = empty_hook_result(hooks_json)
    data = load_hooks_json(hooks_json, result)
    if data is None:
        return result
    for event, entries in (data.get("hooks") or {}).items():
        event_info, issues = inspect_hook_event(event, entries)
        result["events"][event] = event_info
        result["issues"].extend(issues)
    return result
