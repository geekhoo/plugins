"""Deterministic clock tests; no contestant or provider execution."""
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("workflow_budget", Path(__file__).parent / "scripts/workflow-budget.py")
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)
NOW = datetime(2026, 10, 27, tzinfo=timezone.utc)


def context(elapsed=0):
    return {"GEEKY_DEADLINE_UTC": (NOW + timedelta(seconds=6000 - elapsed)).isoformat(),
            "GEEKY_CLOSEOUT_RESERVE_S": "60", "GEEKY_HARD_WALL_BUDGET_S": "6000"}


def test_unset_does_not_invent_budget():
    result = budget.evaluate("spec-research", {}, NOW)
    assert result["status"] == "unbounded"
    assert result["remaining_s"] is None and not result["acceptance_established"]


def test_cumulative_targets_leave_implementation_time():
    result = budget.evaluate("plan-review", context(), NOW)
    assert result["usable_s"] == 5940
    assert result["stage_target_remaining_s"] == 2376
    assert result["status"] == "active"


def test_replaying_claude_timeline_surfaces_overrun_before_coding():
    research = budget.evaluate("spec-research", context(1800), NOW)
    plan = budget.evaluate("geeky-plan", context(4500), NOW)
    assert research["stage_target_exceeded"] and plan["stage_target_exceeded"]
    assert plan["remaining_s"] == 1500
    assert plan["action"] == "reduce-optional-scope-complete-required-gates"
    assert not plan["acceptance_established"]


@pytest.mark.parametrize("elapsed,status", [(5940, "reserve"), (5999, "reserve"), (6000, "exhausted"), (6001, "exhausted")])
def test_reserve_and_expiry_cannot_authorize_work(elapsed, status):
    result = budget.evaluate("geeky-plan", context(elapsed), NOW)
    assert result["status"] == status
    assert result["action"].startswith("checkpoint")
    assert not result["acceptance_established"]


@pytest.mark.parametrize("patch", [
    {"GEEKY_DEADLINE_UTC": ""}, {"GEEKY_DEADLINE_UTC": "2026-10-27T00:00:00"},
    {"GEEKY_CLOSEOUT_RESERVE_S": "nan"}, {"GEEKY_CLOSEOUT_RESERVE_S": "-1"},
    {"GEEKY_HARD_WALL_BUDGET_S": "0"}, {"GEEKY_HARD_WALL_BUDGET_S": "60"},
    {"GEEKY_HARD_WALL_BUDGET_S": "inf"}, {"GEEKY_HARD_WALL_BUDGET_S": "1e999"},
    {"GEEKY_DEADLINE_UTC": "9999-12-31T23:59:59+00:00"},
])
def test_invalid_context_fails_closed(patch):
    env = context()
    env.update(patch)
    result = budget.evaluate("spec-research", env, NOW)
    assert result["status"] == "invalid" and not result["acceptance_established"]


def test_legacy_context_retains_deadline_without_fabricated_targets():
    env = context()
    del env["GEEKY_HARD_WALL_BUDGET_S"]
    result = budget.evaluate("plan-review", env, NOW)
    assert result["status"] == "active"
    assert result["stage_target_utc"] is None


def test_cli_status_codes(monkeypatch, capsys):
    for name in context():
        monkeypatch.delenv(name, raising=False)
    assert budget.main(["--stage", "spec-research", "--json"]) == 0
    monkeypatch.setenv("GEEKY_DEADLINE_UTC", "bad")
    assert budget.main(["--stage", "spec-research", "--json"]) == 2
    monkeypatch.setenv("GEEKY_DEADLINE_UTC", "2000-01-01T00:00:00Z")
    monkeypatch.setenv("GEEKY_CLOSEOUT_RESERVE_S", "0")
    assert budget.main(["--stage", "spec-research", "--json"]) == 3
