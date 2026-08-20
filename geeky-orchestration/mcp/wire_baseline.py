#!/usr/bin/env python3
"""wire_baseline.py - A/B wire harness for the geeky_mcp stdio server.

Migration instrument, not a unit test. It drives the real server.py in this
directory over stdio against a throwaway planning folder and dumps a
*normalised* transcript of `initialize`, `tools/list`, and one `tools/call` per
tool, so the same document can be captured under two different `mcp` SDK majors
and diffed byte for byte.

The transcript is deliberately stripped of everything that legitimately varies:

  * `serverInfo` is excluded - the version reported there is the one field the
    migration is *expected* to change (spec D3). It is printed to stderr
    instead, so a human can still check it.
  * the fixture folder path is rewritten to the literal `<FIXTURE>` - the temp
    directory name is random, so leaving it in would make the baseline
    irreproducible on the very next run.
  * keys are sorted recursively.

What it does *not* normalise is the tool descriptions, which come straight from
the handler docstrings -- and CPython 3.13 changed the compiler to strip leading
indentation from docstrings, so the same server emits differently formatted
descriptions on 3.12 and on 3.14. The baseline is therefore only reproducible on
one side of that change; `.python-version` pins this project to 3.14 so `uv`
cannot quietly build the venv on an older interpreter, and MIN_PYTHON below
fails loudly rather than writing a baseline that will not diff.

Run (from this directory):

  uv run --with "mcp>=1.2.0" python wire_baseline.py --out wire_baseline.json

Deliberately not wired into pytest: every run pays a `uv` resolve. The stdio
invariant it used to be the only check for -- that no validator inherits the
host's transport -- is guarded cheaply in ../test_mcp_server.py.
"""

from __future__ import annotations

import argparse
import json
import queue
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
SERVER = HERE / "server.py"

FIXTURE = "<FIXTURE>"
PROTOCOL_VERSION = "2025-11-25"
READ_TIMEOUT_S = 120.0

# CPython 3.13 strips docstring indentation at compile time; 3.10-3.12 do not.
# Tool descriptions are docstrings, so a capture below this floor differs from
# the committed baseline in all six of them for a reason that has nothing to do
# with the server or the SDK.
MIN_PYTHON = (3, 13)

# Fixed order: the transcript must not depend on dict iteration order.
TOOL_CALLS: list[tuple[str, dict[str, Any]]] = [
    ("geeky_check_commit",
     {"message": "feat(mcp): capture wire baseline\n\nTasks: T1"}),
    ("geeky_check_dod", {"folder": None, "task": "T1"}),
    ("geeky_check_frozen_artifact", {"file_path": None}),
    ("geeky_validate_kanban", {"folder": None, "wip": 3}),
    ("geeky_validate_planning_folder", {"folder": None}),
    ("geeky_validate_task_schema", {"folder": None}),
]


# --------------------------------------------------------------------------- #
# Fixture                                                                     #
# --------------------------------------------------------------------------- #
TASK_BODY = """# T1 - Example task

## Task Name
Example task

## Context
Fixture task used by the wire baseline harness.

## Module/System
geeky_mcp

## In scope
- Exercise the validators with a well-formed task file.

## Dependencies
None.

## Acceptance Criteria
- The validators return a clean report.

## Technical Notes
Nothing noteworthy.

## Tests/Validation Before Next Task
- python -m pytest -q

## Definition of Done
- Acceptance criteria met.

## Estimate
S

## Priority
P2
"""

KANBAN_BODY = """# Kanban

## Backlog

## Ready

## In Progress

## In Review

## Blocked

## Done
- T1 example task
"""


def build_fixture(root: Path) -> None:
    """Write the smallest planning folder that makes all six validators pass.

    Mirrors the layout test_quality_gates.py builds, extended with the files
    validate-planning-folder.py and check-dod.py require.
    """
    tasks = root / "tasks"
    tasks.mkdir()
    (tasks / "T1-example.md").write_text(TASK_BODY, encoding="utf-8")
    (tasks / "T1-example.notes.md").write_text(
        "# T1 notes\n\nDone.\n", encoding="utf-8")
    (root / "kanban.md").write_text(KANBAN_BODY, encoding="utf-8")
    (root / "implementation-plan.md").write_text(
        "# Plan\n\n- T1\n", encoding="utf-8")
    (root / "references.md").write_text("# References\n", encoding="utf-8")
    (root / "handoff.md").write_text("# Handoff\n\nT1 is done.\n", encoding="utf-8")
    (root / "feature-specification.md").write_text("# Spec\n", encoding="utf-8")
    (root / "draft.md").write_text("# Draft\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Normalisation                                                               #
# --------------------------------------------------------------------------- #
def path_variants(root: Path) -> list[str]:
    """Every spelling of the fixture path a validator might echo back.

    On Windows `tempfile` can hand out an 8.3 short path while `Path.resolve()`
    expands it, and separators differ between what we pass in and what pathlib
    prints - so all of them have to be substitutable.
    """
    spellings: set[str] = set()
    for base in {str(root), str(root.resolve())}:
        native = base.replace("/", "\\")
        spellings.add(base)
        spellings.add(base.replace("\\", "/"))
        spellings.add(native)
        # `content[].text` carries the result re-serialised as JSON *inside* a
        # string, so every separator in it is a doubled backslash.
        spellings.add(native.replace("\\", "\\\\"))
    # Longest first: the doubled-backslash spelling must win over the single.
    return sorted(spellings, key=len, reverse=True)


def normalize(obj: Any, variants: list[str]) -> Any:
    if isinstance(obj, dict):
        return {k: normalize(v, variants) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize(v, variants) for v in obj]
    if isinstance(obj, str):
        text = obj
        for spelling in variants:
            text = re.sub(re.escape(spelling), FIXTURE, text, flags=re.IGNORECASE)
        if FIXTURE in text:
            # Only inside rewritten paths - elsewhere a backslash may be content.
            text = text.replace("\\", "/")
        return text
    return obj


LEAK_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]"),           # C:\ or C:/
    re.compile(r"/tmp/"),
    re.compile(r"geekywire[A-Za-z0-9_]*"),   # the temp directory prefix
)


def assert_no_leaks(obj: Any, where: str = "$") -> None:
    """Walk the normalised document and refuse to write a leaky baseline.

    Deliberately walks the object rather than the serialised text: in JSON,
    `Args:\\n` inside a docstring reads as a colon followed by a backslash, and
    a text-level scan flags every tool description as an absolute path.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            assert_no_leaks(value, where + "." + str(key))
        return
    if isinstance(obj, list):
        for index, value in enumerate(obj):
            assert_no_leaks(value, where + "[" + str(index) + "]")
        return
    if not isinstance(obj, str):
        return
    for pattern in LEAK_PATTERNS:
        found = pattern.search(obj)
        if found:
            raise SystemExit(
                "wire_baseline: absolute or temporary path leaked into the "
                "baseline at " + where + " near " + repr(found.group(0))
                + "; fix normalisation rather than committing a document that "
                "cannot reproduce."
            )


# --------------------------------------------------------------------------- #
# stdio client                                                                #
# --------------------------------------------------------------------------- #
class StdioClient:
    """Minimal line-delimited JSON-RPC client - no SDK, on purpose.

    Using the SDK's own client would make the harness agree with whichever SDK
    is installed; the point is to observe the bytes on the wire.
    """

    def __init__(self, argv: list[str]) -> None:
        self.proc = subprocess.Popen(
            argv,
            cwd=str(HERE),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._lines: "queue.Queue[Optional[str]]" = queue.Queue()
        self.stderr: list[str] = []
        threading.Thread(target=self._pump_stdout, daemon=True).start()
        threading.Thread(target=self._pump_stderr, daemon=True).start()

    def _pump_stdout(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self._lines.put(line)
        self._lines.put(None)

    def _pump_stderr(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self.stderr.append(line.rstrip("\n"))

    def send(self, payload: dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

    def request(self, req_id: int, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        while True:
            try:
                line = self._lines.get(timeout=READ_TIMEOUT_S)
            except queue.Empty:
                raise SystemExit(
                    "wire_baseline: timed out waiting for " + method
                    + "; server stderr:\n" + "\n".join(self.stderr)
                )
            if line is None:
                raise SystemExit(
                    "wire_baseline: server exited before answering " + method
                    + "; server stderr:\n" + "\n".join(self.stderr)
                )
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue          # log noise on stdout is not our business
            if message.get("id") != req_id:
                continue          # notification or an out-of-band message
            if "error" in message:
                raise SystemExit(
                    "wire_baseline: " + method + " returned an error: "
                    + json.dumps(message["error"], sort_keys=True)
                )
            return message.get("result", {})

    def close(self) -> None:
        try:
            if self.proc.stdin is not None:
                self.proc.stdin.close()
            self.proc.wait(timeout=30)
        except Exception:
            self.proc.kill()


# --------------------------------------------------------------------------- #
# Transcript                                                                  #
# --------------------------------------------------------------------------- #
def capture(root: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Drive the server once; return (raw transcript, serverInfo, server stderr)."""
    client = StdioClient([sys.executable, str(SERVER)])
    try:
        init = client.request(1, "initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "wire_baseline", "version": "1"},
        })
        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        transcript: dict[str, Any] = {
            "schema": "geeky_mcp.wire_baseline/1",
            "initialize": {k: v for k, v in init.items() if k != "serverInfo"},
            "tools_list": client.request(2, "tools/list", {}),
            "tools_call": {},
        }

        folder = str(root)
        frozen_target = str(root / "tasks" / "T1-example.md")
        for offset, (tool, template) in enumerate(TOOL_CALLS):
            arguments = dict(template)
            if "folder" in arguments:
                arguments["folder"] = folder
            if "file_path" in arguments:
                arguments["file_path"] = frozen_target
            transcript["tools_call"][tool] = client.request(
                3 + offset, "tools/call",
                {"name": tool, "arguments": {"params": arguments}},
            )
        return transcript, init.get("serverInfo", {}), client.stderr
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a geeky_mcp wire baseline.")
    parser.add_argument("--out", required=True,
                        help="path to write the normalised transcript to")
    args = parser.parse_args()

    if sys.version_info[:2] < MIN_PYTHON:
        raise SystemExit(
            "wire_baseline: refusing to capture on Python %d.%d. Tool descriptions "
            "are docstrings, and CPython %d.%d+ strips their indentation while older "
            "versions keep it, so this capture would differ from the committed "
            "baseline in every description for reasons unrelated to the server. "
            "Run it on the interpreter named in .python-version."
            % (sys.version_info[0], sys.version_info[1], MIN_PYTHON[0], MIN_PYTHON[1])
        )

    with tempfile.TemporaryDirectory(prefix="geekywire") as temp_dir:
        root = Path(temp_dir)
        build_fixture(root)
        transcript, server_info, stderr = capture(root)
        document = normalize(transcript, path_variants(root))

    assert_no_leaks(document)
    text = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    out = Path(args.out)
    if out.parent:
        out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    tools = [t["name"] for t in document["tools_list"].get("tools", [])]
    print("wire_baseline: wrote " + str(out), file=sys.stderr)
    print("wire_baseline: serverInfo = " + json.dumps(server_info, sort_keys=True),
          file=sys.stderr)
    print("wire_baseline: " + str(len(tools)) + " tools: " + ", ".join(sorted(tools)),
          file=sys.stderr)
    if stderr:
        print("wire_baseline: server stderr:", file=sys.stderr)
        for line in stderr:
            print("  " + line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
