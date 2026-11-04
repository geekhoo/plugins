"""Behavioral coverage of stage-aware guards and the MCP classifier.

Run with ``uv run --with pytest --with 'mcp>=1.2.0' python -m pytest
geeky-orchestration/test_plan_freeze_stage.py -q``. PowerShell 7 is required;
the paired guard must be exercised rather than skipped.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from pydantic import ValidationError


ROOT = Path(__file__).resolve().parent
FOLDER = "C:/repo/docs/spec-001-feature/"
FROZEN = (
    "implementation-plan.md",
    "feature-specification.md",
    "draft.md",
    "references.md",
    "tasks/T2-x.md",
)
MUTABLE = ("tasks/T2-x.notes.md", "kanban.md", "handoff.md", "README.md")
STAGES = (None, "implement", "unknown", "plan-review")


def legacy_message(path: str) -> str:
    reason = (
        "is a frozen task file (per-task notes belong in tasks/Tx-*.notes.md instead)"
        if "/tasks/" in path.replace("\\", "/")
        else "is a frozen geeky-plan planning artifact"
    )
    return (
        f"[geeky-orchestration] {path} {reason}. "
        "Planning artifacts are the frozen contract between geeky-plan and "
        "geeky-implement. If the plan is genuinely wrong, surface it via kanban "
        "Blocked + handoff.md rather than editing the contract mid-run."
    )


def line_bytes(message: str) -> bytes:
    return (message + os.linesep).encode("utf-8")


def warn_stdout(message: str) -> bytes:
    return line_bytes(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": message,
    }}, separators=(",", ":")))


def review_message(path: str) -> str:
    return (
        f"[geeky-orchestration] {path} may be edited during plan-review. "
        "This edit invalidates the affected review: a bounded mechanical fix needs a "
        "changed-content/reference check; scope, requirement, AC or sequencing edits need a fresh verdict."
    )


def run_guard(backend: str, path: str, *, stage: str | None = None,
              env_stage: str | None = None, mode: str | None = "block",
              exit_code: bool = True) -> subprocess.CompletedProcess[bytes]:
    if backend == "python":
        command = [sys.executable, str(ROOT / "hooks" / "guard-planning-contract.py")]
        if mode is not None:
            command += ["--mode", mode]
        if exit_code:
            command += ["--exit-code"]
        if stage is not None:
            command += ["--stage", stage]
    else:
        pwsh = shutil.which("pwsh")
        assert pwsh is not None, "PowerShell 7 is required to verify the paired guard"
        command = [pwsh, "-NoProfile", "-NonInteractive", "-File",
                   str(ROOT / "hooks" / "guard-planning-contract.ps1")]
        if mode is not None:
            command += ["-Mode", mode]
        if exit_code:
            command += ["-ExitCode"]
        if stage is not None:
            command += ["-Stage", stage]
    env = os.environ.copy()
    env.pop("GEEKY_GUARD_MODE", None)
    env.pop("GEEKY_STAGE", None)
    if env_stage is not None:
        env["GEEKY_STAGE"] = env_stage
    payload = {"tool_name": "Edit", "tool_input": {"file_path": path}}
    return subprocess.run(command, input=json.dumps(payload).encode("utf-8"),
                          capture_output=True, env=env, timeout=30)


def assert_guard_result(result: subprocess.CompletedProcess[bytes], path: str,
                        leaf: str, stage: str | None) -> None:
    editable_review = stage == "plan-review" and leaf in FROZEN and leaf != "feature-specification.md"
    frozen = leaf in FROZEN and not editable_review
    assert result.returncode == (2 if frozen else 0), result.stderr
    assert result.stdout == (warn_stdout(review_message(path)) if editable_review else b"")
    expected = legacy_message(path) if frozen else review_message(path) if editable_review else None
    assert result.stderr == (line_bytes(expected) if expected else b"")


@pytest.mark.parametrize("backend", ("python", "pwsh"))
@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("leaf", FROZEN + MUTABLE)
def test_guard_stage_classification(backend: str, stage: str | None, leaf: str) -> None:
    path = FOLDER + leaf
    assert_guard_result(run_guard(backend, path, stage=stage), path, leaf, stage)


@pytest.mark.parametrize("backend", ("python", "pwsh"))
@pytest.mark.parametrize("leaf", FROZEN)
def test_guard_unset_stage_preserves_default_warn_output(backend: str, leaf: str) -> None:
    path = FOLDER + leaf
    result = run_guard(backend, path, mode=None, exit_code=False)
    assert result.returncode == 0
    assert result.stdout == warn_stdout(legacy_message(path))
    assert result.stderr == line_bytes(legacy_message(path))


@pytest.mark.parametrize("backend", ("python", "pwsh"))
@pytest.mark.parametrize("stage", ("plan-review", "implement", "unknown", "PLAN-REVIEW"))
def test_guard_reads_stage_environment(backend: str, stage: str) -> None:
    leaf = "tasks/T2-x.md"
    path = FOLDER + leaf
    assert_guard_result(run_guard(backend, path, env_stage=stage), path, leaf, stage)


@pytest.mark.parametrize("backend", ("python", "pwsh"))
@pytest.mark.parametrize("stage,env_stage", (
    ("implement", "plan-review"), ("unknown", "plan-review"),
    ("", "plan-review"), ("plan-review", "implement"),
))
def test_guard_cli_stage_overrides_environment(backend: str, stage: str, env_stage: str) -> None:
    leaf = "tasks/T2-x.md"
    path = FOLDER + leaf
    assert_guard_result(run_guard(backend, path, stage=stage, env_stage=env_stage),
                        path, leaf, stage)


@pytest.mark.parametrize("backend", ("python", "pwsh"))
@pytest.mark.parametrize("stage", (None, "plan-review"))
def test_guard_block_json_retains_deny_or_allows_review(backend: str, stage: str | None) -> None:
    path = FOLDER + "tasks/T2-x.md"
    result = run_guard(backend, path, stage=stage, exit_code=False)
    assert result.returncode == 0
    if stage == "plan-review":
        assert result.stdout == warn_stdout(review_message(path))
        assert result.stderr == line_bytes(review_message(path))
    else:
        assert result.stderr == b""
        assert json.loads(result.stdout) == {"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": legacy_message(path),
        }}


@pytest.mark.parametrize("backend", ("python", "pwsh"))
@pytest.mark.parametrize("leaf", ("tasks/T2-x.md", "feature-specification.md"))
def test_guard_review_with_windows_path(backend: str, leaf: str) -> None:
    path = (FOLDER + leaf).replace("/", "\\")
    assert_guard_result(run_guard(backend, path, stage="plan-review"), path, leaf, "plan-review")


@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("plan_freeze_mcp_server", ROOT / "mcp" / "server.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("stage", (None, "implement", "plan-review"))
@pytest.mark.parametrize("leaf", FROZEN + MUTABLE)
def test_mcp_classifier_stage_behavior(server, stage: str | None, leaf: str) -> None:
    path = FOLDER + leaf
    params = server.FrozenInput(file_path=path, stage=stage)
    report = asyncio.run(server.geeky_check_frozen_artifact(params))
    editable_review = stage == "plan-review" and leaf in FROZEN and leaf != "feature-specification.md"
    frozen = leaf in FROZEN and not editable_review
    assert report["file_path"] == path
    assert report["frozen"] is frozen
    assert report["exit_code"] == (2 if frozen else 0)
    expected = legacy_message(path) if frozen else review_message(path) if editable_review else None
    assert report["reason"] == expected


@pytest.mark.parametrize("stage", (None, "implement"))
@pytest.mark.parametrize("leaf", FROZEN)
def test_mcp_omitted_or_implement_stage_ignores_ambient_review(server, monkeypatch,
                                                           stage: str | None, leaf: str) -> None:
    monkeypatch.setenv("GEEKY_STAGE", "plan-review")
    arguments = {"file_path": FOLDER + leaf}
    if stage is not None:
        arguments["stage"] = stage
    params = server.FrozenInput(**arguments)
    assert params.stage == stage
    report = asyncio.run(server.geeky_check_frozen_artifact(params))
    assert report["frozen"] is True
    assert report["exit_code"] == 2
    assert report["reason"] == legacy_message(arguments["file_path"])


@pytest.mark.parametrize("stage", ("unknown", "PLAN-REVIEW", "plan-review; echo bypass"))
def test_mcp_rejects_unknown_stage(server, stage: str) -> None:
    with pytest.raises(ValidationError):
        server.FrozenInput(file_path=FOLDER + "tasks/T2-x.md", stage=stage)
