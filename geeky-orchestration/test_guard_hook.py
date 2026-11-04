from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent
HOOKS = PLUGIN_ROOT / "hooks"
_PWSH_DEFAULT = Path(r"C:\Program Files\PowerShell\7\pwsh.exe")
PWSH = shutil.which("pwsh") or (str(_PWSH_DEFAULT) if _PWSH_DEFAULT.is_file() else None)

FROZEN = r"C:\repo\docs\feature\implementation-plan.md"
FROZEN_TASK = "docs/feature/tasks/T1-setup.md"
NON_ASCII = "docs/caf\u00e9/draft.md"
WRITABLE = "docs/feature/tasks/T1-setup.notes.md"


def payload(file_path: str) -> str:
    return json.dumps({"tool_name": "Edit", "tool_input": {"file_path": file_path}})


def run_py(stdin: str, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(HOOKS / "guard-planning-contract.py"), *args],
        input=stdin.encode("utf-8"), capture_output=True, timeout=30,
    )


def run_ps(stdin: str, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(HOOKS / "guard-planning-contract.ps1"), *args],
        input=stdin.encode("utf-8"), capture_output=True, timeout=60,
    )


def lines(raw: bytes) -> str:
    return raw.decode("utf-8").replace("\r\n", "\n")


class PythonGuardTests(unittest.TestCase):
    def test_warn_emits_additional_context_json(self) -> None:
        result = run_py(payload(FROZEN), "--mode", "warn")
        self.assertEqual(result.returncode, 0)
        out = json.loads(lines(result.stdout))
        spec = out["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "PreToolUse")
        self.assertNotIn("permissionDecision", spec)
        self.assertIn("frozen geeky-plan planning artifact", spec["additionalContext"])
        self.assertIn(FROZEN, spec["additionalContext"])
        # stderr keeps the plain message for non-Claude frameworks.
        self.assertEqual(lines(result.stderr).strip(), spec["additionalContext"])

    def test_plan_review_warning_uses_additional_context(self) -> None:
        result = run_py(payload(FROZEN_TASK), "--mode", "block", "--stage", "plan-review")
        self.assertEqual(result.returncode, 0)
        spec = json.loads(lines(result.stdout))["hookSpecificOutput"]
        self.assertNotIn("permissionDecision", spec)
        self.assertIn("may be edited during plan-review", spec["additionalContext"])
        self.assertEqual(lines(result.stderr).strip(), spec["additionalContext"])

    def test_warn_is_default_mode(self) -> None:
        result = run_py(payload(FROZEN_TASK))
        self.assertEqual(result.returncode, 0)
        self.assertIn("additionalContext", json.loads(lines(result.stdout))["hookSpecificOutput"])

    def test_writable_file_is_silent(self) -> None:
        for path in (WRITABLE, "src/app.py"):
            result = run_py(payload(path), "--mode", "warn")
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""), path)

    def test_block_emits_deny_json(self) -> None:
        result = run_py(payload(FROZEN), "--mode", "block")
        self.assertEqual(result.returncode, 0)
        spec = json.loads(lines(result.stdout))["hookSpecificOutput"]
        self.assertEqual(spec["permissionDecision"], "deny")
        self.assertNotIn("additionalContext", spec)

    def test_block_exit_code(self) -> None:
        result = run_py(payload(FROZEN), "--mode", "block", "--exit-code")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"frozen", result.stderr)


@unittest.skipUnless(PWSH, "pwsh not on PATH")
class GuardParityTests(unittest.TestCase):
    def assert_parity(self, path: str, py_args: list[str], ps_args: list[str]) -> None:
        py = run_py(payload(path), *py_args)
        ps = run_ps(payload(path), *ps_args)
        self.assertEqual(py.returncode, ps.returncode, path)
        self.assertEqual(lines(py.stdout), lines(ps.stdout), path)
        # stderr is plain text in each runtime's console code page (cp1252 vs
        # OEM on Windows), so byte parity only holds for ASCII paths.
        if path.isascii():
            self.assertEqual(lines(py.stderr), lines(ps.stderr), path)

    def test_warn_output_identical(self) -> None:
        for path in (FROZEN, FROZEN_TASK, NON_ASCII, WRITABLE):
            self.assert_parity(path, ["--mode", "warn"], ["-Mode", "warn"])

    def test_plan_review_warning_identical(self) -> None:
        self.assert_parity(FROZEN_TASK, ["--stage", "plan-review"], ["-Stage", "plan-review"])

    def test_block_exit_code_identical(self) -> None:
        self.assert_parity(FROZEN, ["--mode", "block", "--exit-code"],
                           ["-Mode", "block", "-ExitCode"])

    def test_block_json_equivalent(self) -> None:
        py = run_py(payload(FROZEN), "--mode", "block")
        ps = run_ps(payload(FROZEN), "-Mode", "block")
        self.assertEqual(json.loads(lines(py.stdout)), json.loads(lines(ps.stdout)))


if __name__ == "__main__":
    unittest.main()
