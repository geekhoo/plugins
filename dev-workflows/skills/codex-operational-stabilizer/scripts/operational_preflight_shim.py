from pathlib import Path


def quoted_assignment_value(text, variable_name):
    line = next((line for line in text.splitlines() if variable_name in line), "")
    parts = line.split("'")
    if len(parts) < 3:
        return ""
    return parts[1]


def check_optional_path(result, key, path_value, missing_message):
    if not path_value:
        result[f"{key}_exists"] = None
        return
    exists = Path(path_value).exists()
    result[key] = path_value
    result[f"{key}_exists"] = exists
    if not exists:
        result["issues"].append(missing_message.format(path=path_value))


def empty_shim_result(shim):
    return {
        "path": str(shim),
        "exists": shim.exists(),
        "uses_shell_execute_false": False,
        "reads_stdin": False,
        "node_path_exists": None,
        "guard_path_exists": None,
        "issues": [],
    }


def inspect_shim(codex_root):
    shim = codex_root / "hooks" / "omx-native-hook-windows-shim.ps1"
    result = empty_shim_result(shim)
    if not shim.exists():
        result["issues"].append("Windows hook shim is missing")
        return result
    text = shim.read_text(encoding="utf-8", errors="replace")
    result["uses_shell_execute_false"] = "UseShellExecute = $false" in text
    result["reads_stdin"] = "In.ReadToEnd()" in text
    node_path = quoted_assignment_value(text, "$startInfo.FileName")
    guard_path = quoted_assignment_value(text, "$guardPath")
    check_optional_path(result, "node_path", node_path, "shim node path is missing: {path}")
    check_optional_path(result, "guard_path", guard_path, "shim guard path is missing: {path}")
    if not result["uses_shell_execute_false"]:
        result["issues"].append("shim does not set UseShellExecute = $false")
    if not result["reads_stdin"]:
        result["issues"].append("shim does not read hook payload from stdin")
    return result
