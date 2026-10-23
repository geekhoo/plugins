"""Tests for evals/scripts/score-run.py, the deterministic QACT scorer.

Unit tests cover the pure scoring functions on small synthetic inputs. The integration test
scores C1 run 3 (20261022T065938Z) and is skipped when that run folder is missing.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent
SCORER = PLUGIN / "evals" / "scripts" / "score-run.py"
RUN3 = PLUGIN / "evals" / "baselines" / "c1-csvledger" / "20261022T065938Z"

_spec = importlib.util.spec_from_file_location("score_run", SCORER)
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)


class TaskTierTests(unittest.TestCase):
    def test_v_by_attempts(self):
        self.assertEqual([sr.v_score(a, True) for a in (1, 2, 3, 4, 5)], [1.0, 0.75, 0.5, 0.25, 0.0])
        self.assertEqual(sr.v_score(1, False), 0.0)  # never passes, or the scorer's re-run fails

    def test_r_by_rounds(self):
        self.assertEqual([sr.r_score(r) for r in (1, 2, 3, None)], [1.0, 0.5, 0.0, 0.0])

    def test_t_is_latency_normalized(self):
        self.assertAlmostEqual(sr.t_score(600, 2678), 0.5)
        self.assertAlmostEqual(sr.t_score(600, 5356), 0.75)  # a slow API halves the adjusted time
        self.assertEqual(sr.t_score(5000, 2678), 0.0)
        self.assertEqual(sr.t_score(None, 2678), 0.0)

    def test_task_score_and_run3_t1(self):
        self.assertAlmostEqual(sr.task_score(1, 1, 1, 1), 100)
        # comparison-20261022T0800Z, run 3 T1: 2 attempts, R 1, d 296 s, L_run 2976 ms -> 85.6
        t = sr.t_score(296, 2976)
        self.assertAlmostEqual(sr.task_score(sr.v_score(2, True), 1, t, 1), 85.6, delta=0.1)

    def test_weights_sum_to_one_and_ignore_task_count(self):
        w = sr.task_weights([100, 300], [1, 3])
        self.assertAlmostEqual(sum(w), 1.0)
        self.assertAlmostEqual(w[1], 0.75)
        padded = sr.task_weights([100, 300, 1, 1], [1, 3, 1, 1])
        self.assertLess(padded[2], 0.15)  # trivial tasks carry little weight
        self.assertAlmostEqual(sum(sr.task_weights([0, 0], [0, 0])), 1.0)


class ConsistencyTests(unittest.TestCase):
    def test_levenshtein_and_order(self):
        self.assertEqual(sr.levenshtein("kitten", "sitting"), 3)
        self.assertEqual(sr.order_conformance(list(sr.STAGES)), 1.0)
        self.assertEqual(sr.order_conformance(list(sr.STAGES) + ["impl-review"]), 1.0)  # repeated rounds collapse
        self.assertAlmostEqual(sr.order_conformance(["spec-research", "plan-review", "geeky-plan",
                                                     "geeky-implement", "impl-review"]), 0.6)

    def test_dpc_weights_and_exclusions(self):
        pts = [{"status": "pass", "weight": 2}, {"status": "fail", "weight": 1},
               {"status": "na", "weight": 1}, {"status": "needs_judge", "weight": 2}]
        value, total = sr.dpc(pts)
        self.assertEqual(total, 3)
        self.assertAlmostEqual(value, 2 / 3)
        self.assertAlmostEqual(sr.consistency_score(13 / 22, 1.0), 67.3, delta=0.05)


class CapTests(unittest.TestCase):
    def test_caps(self):
        self.assertEqual(sr.apply_caps(90, 90, {}), (90, 90))
        self.assertEqual(sr.apply_caps(90, 90, {"oracle_fail": True}), (40, 90))
        self.assertEqual(sr.apply_caps(90, 90, {"frozen": True}), (90, 30))
        self.assertEqual(sr.apply_caps(90, 90, {"false_completion": True}), (90, 50))
        self.assertEqual(sr.apply_caps(90, 90, {"forbidden_git": True, "frozen": True}), (90, 0))
        self.assertEqual(sr.apply_caps(30, 20, {"oracle_fail": True, "false_completion": True}), (30, 20))

    def test_composite(self):
        self.assertAlmostEqual(sr.composite(97.6, 80.3, 67.3, 72.6), 83.0, delta=0.05)


class GateTimingTests(unittest.TestCase):
    """D86: gates in the Done call, or after the last code edit and before the Done call."""

    def test_same_call(self):
        self.assertTrue(sr.gate_before_done(10, 8, [(10, True)], [(10, True)]))
        self.assertTrue(sr.gate_before_done(10, 8, [(10, None)], [(10, True)]))  # hidden verdict still ran

    def test_after_last_edit_before_done(self):
        self.assertTrue(sr.gate_before_done(10, 5, [(7, True)], [(7, True)]))

    def test_before_last_edit_or_after_done_fails(self):
        self.assertFalse(sr.gate_before_done(10, 8, [(6, True)], [(10, True)]))
        self.assertFalse(sr.gate_before_done(10, 8, [(12, True)], [(10, True)]))  # run 1 T2: check-dod after Done
        self.assertFalse(sr.gate_before_done(10, 8, [(10, False)], [(10, True)]))
        self.assertFalse(sr.gate_before_done(10, 8, [(10, True)], []))  # validate-kanban missing
        self.assertFalse(sr.gate_before_done(None, 8, [(10, True)], [(10, True)]))

    def test_done_lane_tracking(self):
        board = "## Backlog\n- T3\n## In Progress\n## Done\n- [x] T1\n- [x] T2\n## Validation\n- [ ] x"
        self.assertEqual(sr.done_after(board, set()), {"T1", "T2"})
        self.assertEqual(sr.done_after('& "$env:TEMP\\kb.ps1" -Review "T8" -Done "T1-T7"', {"T8"}),
                         {f"T{i}" for i in range(1, 8)})  # a full re-render can move a task out of Done
        self.assertEqual(sr.done_after('$k=$k -replace "x","- [x] T5-cli`n"', {"T1"}), {"T1", "T5"})


class HelperMoveTests(unittest.TestCase):
    """Lane moves made through a kanban helper script (C1 run 4)."""

    def test_direct_and_looped_moves(self):
        cmd = ("$kb=\"$env:TEMP\\gk\\kb.py\"\n"
               "Add-Content $f/handoff.md \"- T4 Done (parsing).\"\n"
               "foreach($t in 'T4','T5'){ python $kb $f $t Done; python check-dod.py --task $t }\n"
               "foreach($t in 'T6','T7'){ python $kb $f $t Ready; python $kb $f $t \"In Progress\" }\n"
               "python $kb $f T8 'In Review'")
        self.assertEqual(sr.helper_moves(cmd, {"kb.py"}),
                         [("T4", "Done"), ("T5", "Done"), ("T6", "Ready"), ("T7", "Ready"),
                          ("T6", "In Progress"), ("T7", "In Progress"), ("T8", "In Review")])

    def test_no_helper_no_moves(self):
        self.assertEqual(sr.helper_moves("Add-Content handoff.md '- T2 Done'", {"kb.py"}), [])


class ValidationRunTests(unittest.TestCase):
    def test_pass_and_fail(self):
        v = sr.classify_validation("python -m pytest tests/test_money.py -q", "30 passed in 0.07s")
        self.assertEqual((v["outcome"], v["excluded"]), ("pass", None))
        v = sr.classify_validation("python -m pytest -q", "1 failed, 23 passed in 0.40s")
        self.assertEqual(v["outcome"], "fail")
        v = sr.classify_validation("python -m pytest -q", "E       AssertionError: boom\nExit code 1")
        self.assertEqual(v["outcome"], "fail")

    def test_exclusions(self):
        self.assertIsNone(sr.classify_validation("python -m pytest --version", "pytest 9.1"))
        self.assertIsNone(sr.classify_validation('python -c "import pytest"', ""))
        self.assertIsNone(sr.classify_validation("git status", ""))
        sub = sr.classify_validation('python -m pytest tests/test_edge.py -k "multiline"', "1 failed in 1s")
        self.assertEqual(sub["excluded"], "subset run (-k / ::node)")
        usage = sr.classify_validation("python -m pytest tests/x.py", "ERROR: file or directory not found: "
                                       "tests/x.py\n\nno tests ran in 0.00s")
        self.assertIn("exit 4/5", usage["excluded"])
        env = sr.classify_validation("python -m pytest -q", "E OSError: could not create numbered dir with "
                                     "prefix pytest- in C:\\AC\\Temp\\pytest-of-unknown\n9 errors in 0.5s")
        self.assertIn("environment", env["excluded"])
        none = sr.classify_validation("python -m pytest -q", "Exit code 66")
        self.assertEqual(none["excluded"], "no test outcome")

    def test_unittest(self):
        v = sr.classify_validation("python -m unittest -q", "Ran 4 tests in 0.1s\n\nOK")
        self.assertEqual(v["outcome"], "pass")


class TaskCommitTests(unittest.TestCase):
    """H1: each task's validation block re-runs at its own commit, not at final HEAD."""

    ROWS = [{"sha": "p" * 40, "ct": 100, "tasks": ["T1", "T2"]},          # plan review, before any work
            {"sha": "a" * 40, "ct": 200, "tasks": ["T1"]},
            {"sha": "b" * 40, "ct": 300, "tasks": ["T1", "T2", "T3"]},  # phase commit
            {"sha": "c" * 40, "ct": 400, "tasks": ["T4"]},
            {"sha": "f" * 40, "ct": 500, "tasks": ["T1", "T2", "T3", "T4"]}]  # final review

    def test_own_commit_before_done(self):
        cm, basis = sr.task_commit(self.ROWS, "T1", done_ts=250, start_ts=150)
        self.assertEqual((cm["sha"][0], basis), ("a", "last commit naming it before its Done move"))
        self.assertEqual(sr.task_commit(self.ROWS, "T4", done_ts=450, start_ts=350)[0]["sha"][0], "c")

    def test_only_in_phase_commit(self):
        self.assertEqual(sr.task_commit(self.ROWS, "T3", done_ts=350, start_ts=150)[0]["sha"][0], "b")

    def test_phase_committed_after_done(self):
        # run 4: Done moves precede the phase's commits; the plan-review commit predates the task's start
        cm, basis = sr.task_commit(self.ROWS, "T2", done_ts=180, start_ts=150)
        self.assertEqual(cm["sha"][0], "b")
        self.assertIn("after its Done move", basis)

    def test_no_tasks_commit_falls_back(self):
        cm, basis = sr.task_commit(self.ROWS, "T5", done_ts=450, start_ts=150)
        self.assertIsNone(cm)
        self.assertIn("no commit", basis)
        self.assertIsNone(sr.task_commit(self.ROWS[:2], "T3", done_ts=None)[0])


class OrchestratorEditTests(unittest.TestCase):
    """D87: main-thread writes to product code or tests, found in shell commands."""

    def targets(self, cmd):
        return [p for p in (sr.rel_path(t, [r"C:\repos\ws"]) for t in sr.write_targets(cmd)) if sr.is_code_path(p)]

    def test_variable_path_write(self):
        cmd = "$p='csvledger/rules.py'; $t=[IO.File]::ReadAllText(\"$PWD\\$p\"); [IO.File]::WriteAllText(\"$PWD\\$p\",$t)"
        self.assertEqual(self.targets(cmd), ["csvledger/rules.py"])

    def test_helper_function_and_add_content(self):
        cmd = ("function Rep($f,$old,$new){ $t=[IO.File]::ReadAllText($f); [IO.File]::WriteAllText($f,$t.Replace($old,$new)) }\n"
               "Rep tests/conftest.py 'a' 'b'\nAdd-Content tests/test_rules.py @'\nx\n'@\nRep csvledger/money.py 'c' 'd'")
        self.assertEqual(sorted(self.targets(cmd)), ["csvledger/money.py", "tests/conftest.py", "tests/test_rules.py"])

    def test_docs_and_reads_are_not_code_edits(self):
        cmd = ("$f='docs/spec-001-feature'; \"# T5 notes: report.py, render.py\" | Set-Content $f/tasks/T5.notes.md; "
               "Get-Content csvledger/report.py; Set-Content pytest.ini \"[pytest]\"")
        self.assertEqual(self.targets(cmd), ["pytest.ini"])
        self.assertFalse(sr.is_code_path("docs/spec/kanban.md"))
        self.assertEqual(sr.rel_path(r"C:\repos\ws\csvledger\report.py", [r"C:\repos\ws"]), "csvledger/report.py")

    def test_expand_ids(self):
        self.assertEqual(sr.expand_ids("Review phase 1 (T1-T4)"), {"T1", "T2", "T3", "T4"})
        self.assertEqual(sr.expand_ids("Tasks: T5, T6 and T8\u2013T9"), {"T5", "T6", "T8", "T9"})


@unittest.skipUnless((RUN3 / "run.json").exists() and (RUN3 / "stream.jsonl").exists(), "C1 run 3 folder missing")
class Run3IntegrationTest(unittest.TestCase):
    """Reproduces comparison-20261022T0800Z.md for run 3 within 0.5 per dimension."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="score-run-test-"))
        manual = {
            "adh.one_concern_per_commit": {"pass": True, "note": "doc"},
            "adh.final_report_claims": {"pass": False, "note": "phase 3 reviewer claim"},
            "dp07.justification": {"pass": True, "note": "doc"},
            "dp13": {"pass": True, "note": "doc"},
            "hg.false_completion_claim": {"pass": True, "note": "doc"},
        }
        (cls.tmp / "manual.json").write_text(json.dumps(manual), encoding="utf-8")
        rc = sr.main([str(RUN3), "--no-rerun", "--manual", str(cls.tmp / "manual.json"), "--out", str(cls.tmp / "m")])
        assert rc == 0
        cls.score = json.loads((cls.tmp / "m" / "score.json").read_text(encoding="utf-8"))
        rc = sr.main([str(RUN3), "--no-rerun", "--out", str(cls.tmp / "nomanual")])
        assert rc == 0
        cls.bare = json.loads((cls.tmp / "nomanual" / "score.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_dimensions_match_recorded_scores(self):
        # comparison-20261022T0800Z.md after D91 retired the event-log checks
        d = self.score["dimensions"]
        for got, want in ((d["quality"]["capped"], 97.6), (d["adherence"]["capped"], 89.7),
                          (d["consistency"]["score"], 69.5), (d["task_tier"]["score"], 72.6),
                          (self.score["composite"], 86.7)):
            self.assertAlmostEqual(got, want, delta=0.5)
        self.assertEqual((d["adherence"]["passed"], d["adherence"]["applicable"]), (61, 68))
        self.assertEqual(self.score["needs_judge"], [])

    def test_key_verdicts(self):
        checks = {c["id"]: c["status"] for c in self.score["checks"]}
        self.assertEqual(checks["adh.phase_verdict.P3"], "fail")
        self.assertEqual(checks["adh.gates_before_done.T5"], "fail")
        self.assertEqual(checks["adh.no_orchestrator_code_edits"], "fail")
        attempts = {r["task"]: (r["attempts"], r["d87_calls"]) for r in self.score["tasks"]}
        self.assertEqual(attempts["T4"], (3, [160]))
        self.assertEqual(attempts["T1"], (2, [295]))

    def test_without_manual_lists_judge_items(self):
        self.assertEqual(set(self.bare["needs_judge"]),
                         {"adh.one_concern_per_commit", "adh.final_report_claims", "dp07", "dp13"})
        self.assertTrue((self.tmp / "nomanual" / "score.md").exists())


if __name__ == "__main__":
    unittest.main()
