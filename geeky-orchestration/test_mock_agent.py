"""Tests for evals/mock-agent/mock_claude.py, the model-free dry-run agent.

Unit tests run the mock directly in temporary git repos (no MXC). The integration test runs
run-baseline.ps1 -MockAgent in MXC and is skipped unless GEEKY_EVAL_MXC=1.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent
MOCK = PLUGIN / "evals" / "mock-agent" / "mock_claude.py"
ANALYZE = PLUGIN / "evals" / "scripts" / "analyze-run.py"
CASE = PLUGIN / "evals" / "cases" / "c1-csvledger"
STAGES = ["spec-research", "geeky-plan", "plan-review", "geeky-implement", "impl-review"]
TOOLS_DIR = Path(r"C:\repos\.eval-tools")


def rmtree(path) -> None:
    """Delete a tree, including git's read-only object files."""
    def unlock(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if Path(path).exists():
        shutil.rmtree(path, onexc=unlock) if sys.version_info >= (3, 12) else shutil.rmtree(path, onerror=unlock)


def find_pwsh() -> str | None:
    found = shutil.which("pwsh")
    if found:
        return found
    default = Path(r"C:\Program Files\PowerShell\7\pwsh.exe")
    return str(default) if default.exists() else None


class MockRun:
    """One mock invocation in a fresh git workspace with an isolated config dir."""

    def __init__(self, scenario: str, case: str | None = "c1-csvledger", seed: bool = True,
                 extra_args: list[str] | None = None, extra_env: dict | None = None):
        self.root = Path(tempfile.mkdtemp(prefix="mock-agent-test-"))
        self.ws = self.root / "ws"
        self.cfg = self.root / "cfg"
        self.ws.mkdir()
        if seed:
            shutil.copy(CASE / "brief.md", self.ws)
            shutil.copy(CASE / "contract.md", self.ws)
        (self.ws / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        self.env = dict(os.environ)
        self.env.update({
            "CLAUDE_CONFIG_DIR": str(self.cfg), "MOCK_LATENCY_MS": "2", "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
            "GIT_AUTHOR_NAME": "mock-test", "GIT_AUTHOR_EMAIL": "mock@test.local",
            "GIT_COMMITTER_NAME": "mock-test", "GIT_COMMITTER_EMAIL": "mock@test.local",
            # the mock runs python/pytest from PATH: make it this interpreter (it has pytest)
            "PATH": os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""),
        })
        self.env.pop("MOCK_SCENARIO", None)
        self.env.update(extra_env or {})
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "seed")
        self.sid = str(uuid.uuid4())
        args = [sys.executable, str(MOCK), "-p", "Run it on docs/spec-001-feature/", "--session-id", self.sid,
                "--plugin-dir", str(PLUGIN), "--permission-mode", "bypassPermissions",
                "--output-format", "stream-json", "--verbose", "--mock-scenario", scenario]
        if case:
            args += ["--mock-case", case]
        args += extra_args or []
        p = subprocess.run(args, cwd=self.ws, env=self.env, capture_output=True, timeout=600)
        self.rc = p.returncode
        self.stdout = p.stdout.decode("utf-8")
        self.stderr = p.stderr.decode("utf-8", "replace")
        self.events = [json.loads(line) for line in self.stdout.splitlines() if line.strip()]

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.ws, env=self.env, capture_output=True,
                              text=True, check=True).stdout

    @property
    def init(self) -> dict:
        return next(e for e in self.events if e.get("subtype") == "init")

    @property
    def result(self) -> dict | None:
        return next((e for e in self.events if e.get("type") == "result"), None)

    @property
    def checks(self) -> dict[str, dict]:
        return {e["name"]: e for e in self.events if e.get("subtype") == "mock_check"}

    @property
    def session_file(self) -> Path:
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(self.ws))
        return self.cfg / "projects" / slug / f"{self.sid}.jsonl"

    def cleanup(self) -> None:
        rmtree(self.root)


class HappyScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.run_ = MockRun("happy")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.run_.cleanup()

    def test_stream_parses_and_init_lists_plugin_skills(self) -> None:
        r = self.run_
        self.assertEqual(r.rc, 0, r.stderr)
        self.assertTrue(r.events)
        geeky = [s for s in r.init["skills"] if s.startswith("geeky-orchestration:")]
        self.assertEqual(len(geeky), 8, geeky)
        self.assertIn("geeky-orchestration:geeky-implement", geeky)
        self.assertEqual(r.init["session_id"], r.sid)
        self.assertTrue(any(a.startswith("geeky-orchestration:") for a in r.init["agents"]))
        # run-baseline.ps1 finds these lines with compact-JSON regexes
        self.assertRegex(r.stdout, r'"subtype":"init"')
        self.assertRegex(r.stdout, r'"type":"result"')

    def test_result_has_model_usage_and_no_failed_checks(self) -> None:
        res = self.run_.result
        self.assertIsNotNone(res)
        self.assertFalse(res["is_error"], [c for c in self.run_.checks.values() if c["status"] == "fail"])
        for usage in res["modelUsage"].values():
            for key in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens", "costUSD"):
                self.assertIn(key, usage)
        self.assertGreater(res["num_turns"], 0)

    def test_skills_stages_and_subagents_in_stream(self) -> None:
        skills = [c["input"]["skill"].split(":")[-1] for e in self.run_.events if e.get("type") == "assistant"
                  for c in e["message"]["content"] if c.get("type") == "tool_use" and c["name"] == "Skill"]
        self.assertEqual(skills, STAGES)
        self.assertTrue(any(e.get("parent_tool_use_id") for e in self.run_.events if e.get("type") == "assistant"))

    def test_session_file_written_with_timestamps(self) -> None:
        path = self.run_.session_file
        self.assertTrue(path.is_file(), path)
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(all("timestamp" in e for e in entries))
        self.assertTrue(any(e.get("isSidechain") for e in entries))
        self.assertTrue(any((e.get("message") or {}).get("id") for e in entries if e["type"] == "assistant"))

    def test_planning_package_passes_plugin_validators(self) -> None:
        folder = self.run_.ws / "docs" / "spec-001-feature"
        for gate in ("validate-planning-folder", "validate-task-schema", "validate-kanban"):
            p = subprocess.run([sys.executable, str(PLUGIN / "scripts" / f"{gate}.py"), "--path", str(folder)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, f"{gate}: {p.stdout}")
        for tid in ("T1", "T2"):
            p = subprocess.run([sys.executable, str(PLUGIN / "scripts" / "check-dod.py"), "--path", str(folder),
                                "--task", tid], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout)

    def test_code_committed_and_workspace_clean(self) -> None:
        log = self.run_.git("log", "--format=%s").splitlines()
        self.assertEqual(len(log), 4, log)
        self.assertTrue((self.run_.ws / "csvledger" / "__main__.py").is_file())
        self.assertEqual(self.run_.git("status", "--porcelain").strip(), "")
        summary = json.loads((self.run_.ws / ".git" / "mock-summary.json").read_text(encoding="utf-8"))
        self.assertTrue(summary["ok"])

    def test_analyze_run_consumes_mock_output(self) -> None:
        run_dir = self.run_.root / "run"
        run_dir.mkdir()
        (run_dir / "stream.jsonl").write_text(self.run_.stdout, encoding="utf-8")
        shutil.copy(self.run_.session_file, run_dir / "session.jsonl")
        (run_dir / "run.json").write_text(json.dumps({"tokens": {"reasoning": 50}}), encoding="utf-8")
        p = subprocess.run([sys.executable, str(ANALYZE), str(run_dir), "--token-ceiling", "12000000"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        analysis = json.loads((run_dir / "analysis.json").read_text(encoding="utf-8"))
        self.assertGreater(run["tokens"]["total"], 0)
        self.assertEqual([s["name"] for s in run["stages"]], STAGES)
        self.assertIsNotNone(run["latency_median_ms"])
        self.assertIsNotNone(run["max_idle_gap_s"])
        self.assertGreater(run["model_calls"], 0)
        self.assertEqual(run["impl_review_rounds"], 1)
        self.assertFalse(run["over_token_ceiling"])
        self.assertIn("geeky-orchestration:geeky-coder", analysis["subagent_dispatches"])
        self.assertIn("validate-kanban", analysis["gate_invocations"])
        self.assertTrue(analysis["validation_runs"])


class ScenarioTests(unittest.TestCase):
    def run_mock(self, *args, **kwargs) -> MockRun:
        r = MockRun(*args, **kwargs)
        self.addCleanup(r.cleanup)
        return r

    def test_crash_exits_nonzero_without_result(self) -> None:
        r = self.run_mock("crash")
        self.assertEqual(r.rc, 3)
        self.assertIsNone(r.result)
        self.assertTrue(r.session_file.is_file())

    def test_gate_fail_leaves_kanban_error(self) -> None:
        r = self.run_mock("gate-fail")
        self.assertEqual(r.rc, 0)
        self.assertIsNotNone(r.result)
        self.assertEqual(r.checks["gate-fail.validate-kanban.rejects"]["status"], "pass")
        folder = r.ws / "docs" / "spec-001-feature"
        p = subprocess.run([sys.executable, str(PLUGIN / "scripts" / "validate-kanban.py"), "--path", str(folder)],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("multiple lanes", p.stdout)
        skills = [c["input"]["skill"] for e in r.events if e.get("type") == "assistant"
                  for c in e["message"]["content"] if c.get("type") == "tool_use" and c["name"] == "Skill"]
        self.assertNotIn("geeky-orchestration:geeky-implement", skills)

    def test_slow_sleeps_then_finishes(self) -> None:
        r = self.run_mock("slow", extra_env={"MOCK_SLOW_SECONDS": "0.2"})
        self.assertEqual(r.rc, 0)
        self.assertIsNotNone(r.result)

    def test_bg_wait_resumes_when_ceiling_is_zero(self) -> None:
        r = self.run_mock("bg-wait")
        self.assertEqual(r.rc, 0)
        self.assertEqual(r.checks["bg-wait.resumed"]["status"], "pass")
        self.assertNotIn("stopping them", r.stderr)

    def test_bg_wait_stops_background_without_ceiling(self) -> None:
        r = self.run_mock("bg-wait", extra_env={"CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": ""})
        self.assertIsNotNone(r.result)
        # the runner's bg_killed pattern
        self.assertRegex(r.stderr, r"Background tasks still running .* stopping them")
        self.assertIn("bg-wait.stopped", r.checks)

    def test_composable_checks_report_lines_and_summary(self) -> None:
        r = self.run_mock("env-probe,grants,python,git,gates")
        self.assertIsNotNone(r.result)
        for name in ("env.python", "env.pytest", "env.git_identity", "env.bg_wait_ceiling", "grants.workspace_rw",
                     "grants.plugin_scandir.skills", "python.pytest_run", "git.commit_workspace",
                     "gate.validate-kanban.py", "gate.validate-kanban.py.rejects_bad", "gate.check-commit.py"):
            self.assertEqual(r.checks[name]["status"], "pass", r.checks.get(name))
        summary = next(e for e in r.events if e.get("subtype") == "mock_summary")
        self.assertEqual(summary["scenarios"], ["env-probe", "grants", "python", "git", "gates"])
        self.assertEqual(set(summary["counts"]), {"pass", "fail", "warn", "info"})
        self.assertTrue(all(c["status"] in {"pass", "fail", "warn", "info"} for c in summary["checks"]))

    @unittest.skipUnless(find_pwsh(), "pwsh not installed")
    def test_pwsh_checks(self) -> None:
        r = self.run_mock("pwsh,gates")
        for name in ("pwsh.exit_7", "pwsh.native_exit_3", "pwsh.cmdlet_error", "gate.validate-kanban.ps1",
                     "gate.check-dod.ps1", "gate.validate-kanban.ps1.rejects_bad"):
            self.assertEqual(r.checks[name]["status"], "pass", r.checks.get(name))

    def test_case_agnostic_arbitrary_workspace(self) -> None:
        r = self.run_mock("happy", case=None, seed=False, extra_args=["--some-future-flag", "x", "--strict-mcp-config"])
        self.assertEqual(r.rc, 0, r.stderr)
        self.assertFalse(r.result["is_error"], [c for c in r.checks.values() if c["status"] == "fail"])
        self.assertTrue((r.ws / "mockpkg" / "__init__.py").is_file())
        self.assertIn("--some-future-flag", r.init["mock_unknown_args"])

    def test_unknown_scenario_is_a_failed_check(self) -> None:
        r = self.run_mock("nope")
        self.assertEqual(r.checks["scenario.nope"]["status"], "fail")
        self.assertTrue(r.result["is_error"])

    def test_token_usage_is_deterministic_per_scenario(self) -> None:
        a = self.run_mock("python").result["modelUsage"]
        b = self.run_mock("python").result["modelUsage"]
        c = self.run_mock("git").result["modelUsage"]
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    @unittest.skipUnless((TOOLS_DIR / "geeky-mcp" / "pyvenv.cfg").is_file(), "geeky-mcp venv not present")
    def test_mcp_handshake_with_runner_config(self) -> None:
        cfg_text = (TOOLS_DIR / "geeky-mcp" / "pyvenv.cfg").read_text(encoding="utf-8")
        home = re.search(r"^home\s*=\s*(.+)$", cfg_text, re.M).group(1).strip()
        boot = (f"import site,runpy,sys; site.addsitedir(r'{TOOLS_DIR}\\geeky-mcp\\Lib\\site-packages'); "
                f"sys.path.insert(0, r'{PLUGIN}\\mcp'); sys.argv=[r'{PLUGIN}\\mcp\\server.py']; "
                "runpy.run_path(sys.argv[0], run_name='__main__')")
        tmp = Path(tempfile.mkdtemp(prefix="mock-mcp-cfg-"))
        self.addCleanup(rmtree, tmp)
        mcp = tmp / "mcp.json"
        mcp.write_text(json.dumps({"mcpServers": {"geeky": {"command": str(Path(home) / "python.exe"),
                                                            "args": ["-u", "-c", boot]}}}), encoding="utf-8")
        r = self.run_mock("mcp", extra_args=["--strict-mcp-config", "--mcp-config", str(mcp)])
        check = r.checks["mcp.geeky.handshake"]
        self.assertEqual(check["status"], "pass", check)
        self.assertIn("geeky_validate_kanban", check["detail"])


@unittest.skipUnless(os.environ.get("GEEKY_EVAL_MXC") == "1", "set GEEKY_EVAL_MXC=1 to run the MXC integration test")
class MxcIntegrationTests(unittest.TestCase):
    def test_run_baseline_mock_agent_happy(self) -> None:
        run, out = self._run_baseline("happy")
        self.assertTrue((out / "analysis.json").is_file())
        self.assertEqual(run["exit_reason"], "completed", run)
        self.assertEqual(run["geeky_skills_loaded"], 8)
        self.assertEqual([s["name"] for s in run["stages"]], STAGES)
        summary = json.loads((out / "mock-summary.json").read_text(encoding="utf-8-sig"))
        self.assertTrue(summary["ok"], summary["failed"])

    def test_run_baseline_waits_for_background_subagent(self) -> None:
        run, out = self._run_baseline("bg-wait")
        self.assertEqual(run["exit_reason"], "completed", run)
        summary = json.loads((out / "mock-summary.json").read_text(encoding="utf-8-sig"))
        self.assertIn("bg-wait.resumed", [c["name"] for c in summary["checks"] if c["status"] == "pass"])

    def _run_baseline(self, scenario: str) -> tuple[dict, Path]:
        pwsh = find_pwsh()
        self.assertIsNotNone(pwsh)
        script = PLUGIN / "evals" / "scripts" / "run-baseline.ps1"
        # The runner pipes `git archive` into `tar -x -C C:\...`; under a Git Bash PATH `tar` is MSYS tar,
        # which reads "C:" as a remote host. Put the Windows tar first.
        env = dict(os.environ)
        system32 = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32")
        env["PATH"] = system32 + os.pathsep + env.get("PATH", "")
        p = subprocess.run([pwsh, "-NoProfile", "-File", str(script), "-Case", "c1-csvledger", "-MockAgent",
                            "-MockScenario", scenario], capture_output=True, text=True, timeout=1800, env=env)
        m = re.search(r"stored: (.+)", p.stdout)
        self.assertIsNotNone(m, p.stdout + p.stderr)
        out = Path(m.group(1).strip())
        ws = Path(re.search(r"workspace: (\S+)", p.stdout).group(1))
        stamp = out.name
        self.addCleanup(self._cleanup, out, ws, Path(r"C:\repos") / f".eval-cfg-{stamp}")
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads((out / "run.json").read_text(encoding="utf-8-sig")), out

    @staticmethod
    def _cleanup(out: Path, ws: Path, cfg: Path) -> None:
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(ws))
        for d in (out, ws, cfg, Path.home() / ".mxc-sandbox" / "home" / "projects" / slug):
            rmtree(d)
        try:
            out.parent.rmdir()  # the case folder, only if this run created it and it is now empty
        except OSError:
            pass


if __name__ == "__main__":
    unittest.main()
