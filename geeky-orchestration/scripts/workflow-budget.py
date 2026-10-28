#!/usr/bin/env python3
"""Read-only workflow clock; no process control, network, or acceptance decisions.

Stage targets are cumulative advisory allocations, not measured completion
estimates. Required gates remain required when a target or deadline expires.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
import os

STAGE_TARGETS = {
    "spec-research": .15, "geeky-plan": .30, "plan-review": .40,
    "geeky-implement": .90, "impl-review": 1.0,
}


def utc(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("Deadline must have an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def number(value, name):
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def evaluate(stage, env, now=None):
    now = now if now is not None else datetime.now(timezone.utc)
    if stage not in STAGE_TARGETS:
        raise ValueError("Unknown workflow stage")
    deadline = env.get("GEEKY_DEADLINE_UTC", "")
    reserve = env.get("GEEKY_CLOSEOUT_RESERVE_S", "")
    budget = env.get("GEEKY_HARD_WALL_BUDGET_S", "")
    report = {"schema": "geeky.workflow-budget/1", "stage": stage,
              "now_utc": now.isoformat(), "status": "unbounded",
              "hard_deadline_utc": None, "closeout_reserve_s": None,
              "hard_wall_budget_s": None, "remaining_s": None,
              "usable_s": None, "stage_target_utc": None,
              "stage_target_remaining_s": None, "stage_target_exceeded": False,
              "stage_target_policy": "cumulative-advisory-v1",
              "action": "ordinary-workflow", "acceptance_established": False}
    if not any((deadline, reserve, budget)):
        return report
    try:
        if not deadline or reserve == "":
            raise ValueError("Deadline and reserve must both be supplied")
        end = utc(deadline)
        reserve_s = number(reserve, "Reserve")
        total = number(budget, "Budget") if budget != "" else None
        if total is not None and (total <= 0 or reserve_s >= total):
            raise ValueError("Budget must be positive and larger than reserve")
        remaining = (end - now).total_seconds()
        report.update(hard_deadline_utc=end.isoformat(), closeout_reserve_s=reserve_s,
                      hard_wall_budget_s=total, remaining_s=round(max(0, remaining), 3),
                      usable_s=round(max(0, remaining - reserve_s), 3))
        if total is not None:
            start = end - timedelta(seconds=total)
            if start > now + timedelta(seconds=1):
                raise ValueError("Budget and deadline imply a future start")
            target = start + timedelta(seconds=(total - reserve_s) * STAGE_TARGETS[stage])
            delta = (target - now).total_seconds()
            report.update(stage_target_utc=target.isoformat(),
                          stage_target_remaining_s=round(delta, 3),
                          stage_target_exceeded=delta <= 0)
        if remaining <= 0:
            report.update(status="exhausted", action="checkpoint-and-stop")
        elif remaining <= reserve_s:
            report.update(status="reserve", action="checkpoint-no-new-stage-or-dispatch")
        else:
            report.update(status="active", action=(
                "reduce-optional-scope-complete-required-gates" if report["stage_target_exceeded"]
                else "bounded-required-work"))
    except (ValueError, TypeError, OverflowError) as error:
        report.update(status="invalid", action="checkpoint-and-stop", error=str(error))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=STAGE_TARGETS, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = evaluate(args.stage, os.environ)
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(f"{report['stage']}: {report['status']}; {report['action']}; "
              f"remaining={report['remaining_s']}s; usable={report['usable_s']}s")
    return {"invalid": 2, "exhausted": 3}.get(report["status"], 0)


if __name__ == "__main__":
    raise SystemExit(main())
