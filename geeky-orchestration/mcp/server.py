#!/usr/bin/env python3
"""geeky_mcp — MCP server exposing the geeky-orchestration deterministic quality gates.

This is a thin adapter, not a reimplementation: each tool shells out to the same
portable validator script under ../scripts (or ../hooks) with its --json flag and
returns the parsed report. The scripts stay the single source of truth, so MCP
output is identical to the CLI/hook output. Any MCP-capable agent (Claude Code,
Cursor, OpenAI Agents SDK, LangGraph, ...) can call these gates with no
per-framework hook configuration.

All tools are read-only: they inspect a planning folder / message / path and never
modify anything. A non-zero exit from a validator is a *validation failure* (a
normal result with ok=false), not a server error.

Run (stdio):
  uv run --with mcp python server.py
  # or, with mcp installed:  python server.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from mcp.server.fastmcp import FastMCP

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN_ROOT / "scripts"
HOOKS = PLUGIN_ROOT / "hooks"

READONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

mcp = FastMCP("geeky_mcp")


# --------------------------------------------------------------------------- #
# Shared subprocess helper                                                    #
# --------------------------------------------------------------------------- #
async def _run(script: Path, args: list[str], stdin_text: Optional[str] = None) -> dict[str, Any]:
    """Run a validator script with the current interpreter; return its parsed report.

    Returns a dict that always contains 'exit_code'. If the script emitted JSON on
    stdout (the --json contract) those fields are merged in; otherwise the raw text
    is returned under 'output'. A missing script or interpreter failure surfaces as
    {'error': ...}.
    """
    if not script.is_file():
        return {"ok": False, "error": f"validator not found: {script}", "exit_code": 127}

    cmd = [sys.executable, str(script), *args]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if stdin_text is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdin_bytes = stdin_text.encode("utf-8") if stdin_text is not None else None
        out_b, err_b = await proc.communicate(input=stdin_bytes)
        rc = proc.returncode
    except Exception as exc:  # pragma: no cover - defensive
        return {"ok": False, "error": f"failed to run {script.name}: {exc!r}", "exit_code": 1}

    out = out_b.decode("utf-8", errors="replace").strip()
    err = err_b.decode("utf-8", errors="replace").strip()

    result: dict[str, Any] = {"exit_code": rc}
    parsed: Any = None
    if out:
        try:
            parsed = json.loads(out)
        except json.JSONDecodeError:
            parsed = None
    if isinstance(parsed, dict):
        result.update(parsed)
    elif out:
        result["output"] = out
    if err:
        result["stderr"] = err
    result.setdefault("ok", rc == 0)
    return result


def _require_dir(folder: str) -> Optional[dict[str, Any]]:
    if not Path(folder).is_dir():
        return {"ok": False, "error": f"folder not found: {folder}", "exit_code": 1}
    return None


# --------------------------------------------------------------------------- #
# Input models                                                                #
# --------------------------------------------------------------------------- #
class FolderInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    folder: str = Field(..., description="Absolute path to the geeky-plan planning folder (contains kanban.md, tasks/, etc.)", min_length=1)


class TaskSchemaInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    folder: Optional[str] = Field(default=None, description="Planning folder; validates every tasks/Tx-*.md in it")
    file: Optional[str] = Field(default=None, description="A single task .md file to validate instead of a whole folder")

    @model_validator(mode="after")
    def _one_of(self) -> "TaskSchemaInput":
        if not self.folder and not self.file:
            raise ValueError("provide either 'folder' or 'file'")
        return self


class KanbanInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    folder: str = Field(..., description="Planning folder containing kanban.md and tasks/", min_length=1)
    wip: int = Field(default=3, description="In Progress WIP cap before a warning is raised", ge=1, le=50)


class DodInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    folder: str = Field(..., description="Planning folder", min_length=1)
    task: str = Field(..., description="Task id to check, e.g. 'T3'", min_length=2)


class CommitInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    message: str = Field(..., description="The full commit message text to validate", min_length=1)


class FrozenInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    file_path: str = Field(..., description="Path an agent intends to edit; checks whether it is a frozen planning artifact", min_length=1)


# --------------------------------------------------------------------------- #
# Tools                                                                       #
# --------------------------------------------------------------------------- #
@mcp.tool(name="geeky_validate_planning_folder", annotations={"title": "Validate planning folder", **READONLY})
async def geeky_validate_planning_folder(params: FolderInput) -> dict[str, Any]:
    """Verify a geeky-plan folder contains the artifacts geeky-implement needs.

    Checks for implementation-plan.md, kanban.md, references.md, handoff.md, and a
    non-empty tasks/ folder; reports missing recommended files (feature-specification.md,
    draft.md) as warnings.

    Args:
        params (FolderInput): folder = absolute path to the planning folder.

    Returns:
        dict: { ok: bool, task_count: int, missing_required: [str],
                missing_recommended: [str], summary: str, exit_code: int }.
        ok=false with exit_code=1 means the folder is incomplete (a validation
        failure, not a server error).
    """
    if (err := _require_dir(params.folder)):
        return err
    return await _run(SCRIPTS / "validate-planning-folder.py", ["--path", params.folder, "--json"])


@mcp.tool(name="geeky_validate_task_schema", annotations={"title": "Validate task-file schema", **READONLY})
async def geeky_validate_task_schema(params: TaskSchemaInput) -> dict[str, Any]:
    """Validate that task files carry the required template sections.

    The plan->implement boundary gate. Required sections: Task Name, In scope,
    Dependencies, Acceptance Criteria, Tests/Validation, Priority. Missing
    recommended sections (Context, Module/System, Technical Notes, Definition of
    Done, Estimate) are warnings.

    Args:
        params (TaskSchemaInput): provide 'folder' (validate all tasks/Tx-*.md) OR
            'file' (validate one task .md).

    Returns:
        dict: { ok: bool, results: [ { file, ok, missing_required, missing_recommended } ],
                exit_code: int }.
    """
    args: list[str]
    if params.file:
        args = ["--file", params.file, "--json"]
    else:
        if (err := _require_dir(params.folder or "")):
            return err
        args = ["--path", params.folder, "--json"]
    return await _run(SCRIPTS / "validate-task-schema.py", args)


@mcp.tool(name="geeky_validate_kanban", annotations={"title": "Validate kanban integrity", **READONLY})
async def geeky_validate_kanban(params: KanbanInput) -> dict[str, Any]:
    """Check kanban.md integrity against the tasks/ folder.

    Errors (ok=false): a task file placed in no lane (untracked); a task in more
    than one lane (ambiguous). Warnings: dangling references, WIP cap exceeded,
    missing lane headings.

    Args:
        params (KanbanInput): folder = planning folder; wip = In Progress cap (default 3).

    Returns:
        dict: { ok: bool, errors: [str], warnings: [str], lane_counts: {lane:int},
                summary: str, exit_code: int }.
    """
    if (err := _require_dir(params.folder)):
        return err
    return await _run(SCRIPTS / "validate-kanban.py", ["--path", params.folder, "--wip", str(params.wip), "--json"])


@mcp.tool(name="geeky_check_dod", annotations={"title": "Check Definition of Done", **READONLY})
async def geeky_check_dod(params: DodInput) -> dict[str, Any]:
    """Verify a task's Definition of Done before it moves to Done.

    Asserts: a per-task notes file tasks/<ID>-*.notes.md exists; <ID> is in the Done
    lane; handoff.md mentions <ID>. Also returns the task's Tests/Validation block so
    the caller can re-run it ("verify, don't trust").

    Args:
        params (DodInput): folder = planning folder; task = task id (e.g. 'T3').

    Returns:
        dict: { ok: bool, task: str, errors: [str], warnings: [str], lanes: [str],
                validation_block: str, exit_code: int }.
    """
    if (err := _require_dir(params.folder)):
        return err
    return await _run(SCRIPTS / "check-dod.py", ["--path", params.folder, "--task", params.task, "--json"])


@mcp.tool(name="geeky_check_commit", annotations={"title": "Check commit message", **READONLY})
async def geeky_check_commit(params: CommitInput) -> dict[str, Any]:
    """Validate a commit message: Conventional Commits subject + a task reference.

    Errors (ok=false): subject not 'type(scope): summary'; subject > 72 chars; no
    task reference. A bare T<n> without a 'Tasks:' line is a warning, not an error.

    Args:
        params (CommitInput): message = full commit message text.

    Returns:
        dict: { ok: bool, subject: str, errors: [str], warnings: [str], exit_code: int }.
    """
    return await _run(SCRIPTS / "check-commit.py", ["--json"], stdin_text=params.message)


@mcp.tool(name="geeky_check_frozen_artifact", annotations={"title": "Check if a path is a frozen artifact", **READONLY})
async def geeky_check_frozen_artifact(params: FrozenInput) -> dict[str, Any]:
    """Check whether a file path is a frozen geeky-plan planning artifact.

    Use this as a pre-edit guardrail (the in-process equivalent of the PreToolUse
    guard hook): call it before editing a file inside a planning folder. Frozen:
    implementation-plan.md, feature-specification.md, draft.md, references.md, and
    tasks/Tx-*.md bodies (but NOT tasks/Tx-*.notes.md).

    Args:
        params (FrozenInput): file_path = the path an agent intends to edit.

    Returns:
        dict: { frozen: bool, file_path: str, reason: str|None, exit_code: int }.
        frozen=true means do not edit — surface plan issues via kanban Blocked + handoff.md.
    """
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": params.file_path}})
    res = await _run(HOOKS / "guard-planning-contract.py", ["--mode", "block", "--exit-code"], stdin_text=payload)
    frozen = res.get("exit_code") == 2
    return {
        "frozen": frozen,
        "file_path": params.file_path,
        "reason": res.get("stderr") if frozen else None,
        "exit_code": res.get("exit_code"),
    }


if __name__ == "__main__":
    mcp.run()
