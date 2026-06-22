import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import codex_operational_preflight as preflight  # noqa: E402


class OperationalPreflightTests(unittest.TestCase):
    def test_hook_command_paths_extracts_file_argument(self):
        command = r'powershell.exe -NoProfile -File "C:\Temp\guard.ps1"'

        self.assertEqual(preflight.hook_command_paths(command), [r"C:\Temp\guard.ps1"])

    def test_inspect_hooks_reports_missing_hook_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing = root / "missing.ps1"
            hooks = {
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": f'powershell.exe -NoProfile -File "{missing}"',
                                }
                            ]
                        }
                    ]
                }
            }
            (root / "hooks.json").write_text(json.dumps(hooks), encoding="utf-8")

            result = preflight.inspect_hooks(root)

            self.assertTrue(result["json_valid"])
            command = result["events"]["UserPromptSubmit"]["commands"][0]
            self.assertEqual(command["missing_paths"], [str(missing)])
            self.assertEqual(result["issues"], [f"UserPromptSubmit references missing path: {missing}"])

    def test_inspect_shim_accepts_stdin_and_no_shell_execute(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            hooks_dir = root / "hooks"
            hooks_dir.mkdir()
            node = root / "node.exe"
            guard = hooks_dir / "guard.ps1"
            node.write_text("", encoding="utf-8")
            guard.write_text("", encoding="utf-8")
            shim = hooks_dir / "omx-native-hook-windows-shim.ps1"
            shim.write_text(
                "\n".join(
                    [
                        "$inputText = [Console]::In.ReadToEnd()",
                        f"$guardPath = '{guard}'",
                        "$startInfo = [System.Diagnostics.ProcessStartInfo]::new()",
                        f"$startInfo.FileName = '{node}'",
                        "$startInfo.UseShellExecute = $false",
                    ]
                ),
                encoding="utf-8",
            )

            result = preflight.inspect_shim(root)

            self.assertEqual(result["issues"], [])
            self.assertTrue(result["reads_stdin"])
            self.assertTrue(result["uses_shell_execute_false"])
            self.assertTrue(result["node_path_exists"])
            self.assertTrue(result["guard_path_exists"])

    def test_as_markdown_includes_core_sections(self):
        report = {
            "codex_root": "C:/Codex",
            "skills": [{"name": "windows-host-preflight", "exists": True, "skill_md_exists": True}],
            "hooks": {"json_valid": True, "events": {"Stop": {}}, "issues": []},
            "hook_shim": {"issues": []},
            "agents": {"toml_files": 1, "nonempty_toml_files": 1, "empty_toml_files": 0},
            "commands": [{"name": "git", "available": True, "path": "git.exe"}],
            "sessions": {"rollout_files": 2, "archived_rollout_files": 1, "session_index_lines": 3},
        }

        markdown = preflight.as_markdown(report)

        self.assertIn("# Codex Operational Preflight", markdown)
        self.assertIn("`windows-host-preflight`: ok", markdown)
        self.assertIn("`hooks.json`: valid", markdown)


if __name__ == "__main__":
    unittest.main()
