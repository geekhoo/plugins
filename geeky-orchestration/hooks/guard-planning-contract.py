#!/usr/bin/env python3
"""guard-planning-contract.py

PreToolUse-style guard for Edit/Write/NotebookEdit. Reads tool-call JSON from
stdin. If file_path points at a frozen geeky-plan artifact *and* the planning
package is past its freeze point, it surfaces a message through a PORTABLE
channel so it is visible across agent frameworks, not just on Claude Code stderr.

Frozen patterns (inside a planning folder under docs/<feature>/):
  - implementation-plan.md
  - feature-specification.md
  - draft.md
  - references.md
  - tasks/Tx-*.md           (but NOT tasks/Tx-*.notes.md -- those are writable)

Path handling: the incoming file_path is normalized (separators collapsed to
"/", "./" segments dropped, duplicate and trailing separators removed) BEFORE
matching, so relative POSIX, absolute POSIX, Windows backslash, mixed, UNC and
Git-Bash/MSYS (/c/Users/...) forms all match identically. Normalization is
purely lexical -- the file is never resolved against the filesystem for
matching, because it may not exist yet and the hook must stay fast.

Stage awareness: the freeze starts when the first task leaves the Backlog lane.
The guard infers the planning folder from the edited path, reads kanban.md, and
stays SILENT for a pre-freeze package (planning and plan-review edits are
legitimate then). If kanban.md cannot be located the package cannot be proven
pre-freeze, so the guard defaults to the protective behavior and says so.
Override the pre-freeze lane set with $GEEKY_PREFREEZE_LANES (comma separated,
default "Backlog"; e.g. "Backlog,Ready" if your packages rest in Ready between
geeky-plan and geeky-implement).

Fail-closed: a payload the guard cannot interpret (unreadable/empty stdin,
invalid JSON, no tool_name, or no file_path on a guarded tool) is NOT treated as
"fine". In block mode it denies; in warn mode it emits a visible warning. A
payload that is simply not a protected operation still exits 0 silently.

Modes (default warn) via --mode or $GEEKY_GUARD_MODE:
  warn   -> advisory only. Writes the message to BOTH stdout (plain text) and
            stderr, then exit 0. On exit 0, Claude Code treats non-JSON stdout as
            added context; OpenAI Codex treats stdout as developer context. So the
            warning actually reaches the model, unlike stderr-on-exit-0 alone.
  block  -> emits Claude/Codex-style deny JSON on stdout and exits 0 so the host
            parses the decision and blocks the edit. (Frameworks that gate purely
            on exit code: re-run with --exit-code so a block returns exit 2.)

Exit codes:
  0  -> normal (warn, or block-via-JSON which the host parses)
  2  -> hard block via exit code (only when --exit-code is passed in block mode)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

FROZEN_LEAVES = {
    "implementation-plan.md",
    "feature-specification.md",
    "draft.md",
    "references.md",
}

# Tools whose payloads are expected to carry a file_path. A payload for any
# other tool is not a protected operation and exits 0 silently.
GUARDED_TOOLS = {
    "edit",
    "write",
    "multiedit",
    "notebookedit",
    "notebook_edit",
}

TASK_FILE_RE = re.compile(r"(^|/)tasks/T[^/]+\.md$", re.IGNORECASE)
NOTES_FILE_RE = re.compile(r"\.notes\.md$", re.IGNORECASE)
TASK_TOKEN_RE = re.compile(r"\bT\d+\b")

# --- Lane placement (keep in sync with scripts/validate-kanban.py and check-dod.py) ---
# Only a markdown list item whose LEADING token is a task id places that task in
# a lane. Without this, a planning note under Ready such as
# "<!-- none yet; T1 will go here first -->" would read as a promotion and
# falsely freeze a package that has not started.
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
PLACEMENT_RE = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])\s+"   # markdown bullet or ordered-list marker
    r"(?:\[[ xX]\]\s*)?"          # optional task-list checkbox
    r"[*_`~]*\s*"                 # optional emphasis / code marks
    r"(T\d+)\b",                  # the task id, and it must lead
    re.IGNORECASE,
)

# Lane vocabulary duplicated from scripts/check-dod.py (KNOWN_LANES /
# lane_for_heading). Deliberately duplicated rather than imported: this hook must
# run standalone from any cwd, with stdlib only, and must stay byte-identical to
# its PowerShell twin, which has no equivalent import. Keep the two in sync.
KNOWN_LANES = ("Backlog", "Ready", "In Progress", "In Review", "Blocked", "Done")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*\S)\s*$")

TAIL = (
    "Planning artifacts are the frozen contract between geeky-plan and "
    "geeky-implement. If the plan is genuinely wrong, surface it via kanban "
    "Blocked + handoff.md rather than editing the contract mid-run."
)


def message(file_path: str, reason: str, stage_note: str) -> str:
    return f"[geeky-orchestration] {file_path} {reason}. {stage_note} {TAIL}"


def malformed_message(detail: str) -> str:
    return (
        f"[geeky-orchestration] guard could not interpret the hook payload "
        f"({detail}). Failing closed: the guard cannot prove this edit is safe, "
        f"so it is treated as an edit to a frozen planning artifact. " + TAIL
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--mode", choices=("warn", "block"),
                   default=os.environ.get("GEEKY_GUARD_MODE", "warn"))
    p.add_argument("--exit-code", dest="exit_code", action="store_true",
                   help="in block mode, return exit 2 instead of deny JSON")
    return p.parse_args()


def emit_warn(msg: str) -> int:
    # stdout: portable context channel (Claude adds non-JSON stdout as context;
    # Codex treats stdout as developer context). stderr: log visibility.
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()
    return 0


def emit_block(msg: str, exit_code: bool) -> int:
    if exit_code:
        sys.stderr.write(msg + "\n")
        sys.stderr.flush()
        return 2
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": msg,
        }
    }
    sys.stdout.write(json.dumps(decision) + "\n")
    sys.stdout.flush()
    return 0


def emit(msg: str, mode: str, exit_code: bool) -> int:
    if mode == "block":
        return emit_block(msg, exit_code)
    return emit_warn(msg)


def normalize(path: str) -> str:
    """Lexical normalization only -- never touches the filesystem.

    Collapses \\ to /, squeezes duplicate separators, drops "./" segments and
    trailing separators. UNC (\\\\server\\share\\...) collapses to /server/share/...
    which is fine: matching only ever looks at the tail.
    """
    s = path.strip().strip('"').strip("'").replace("\\", "/")
    while "//" in s:
        s = s.replace("//", "/")
    s = re.sub(r"(?:^|(?<=/))\./", "", s)
    if len(s) > 1:
        s = s.rstrip("/")
    return s


def classify(normalized: str) -> str | None:
    leaf = normalized.rsplit("/", 1)[-1].lower()
    if leaf in FROZEN_LEAVES:
        return "is a frozen geeky-plan planning artifact"
    if TASK_FILE_RE.search(normalized) and not NOTES_FILE_RE.search(normalized):
        return ("is a frozen task file (per-task notes belong in "
                "tasks/Tx-*.notes.md instead)")
    return None


def planning_folder(normalized: str) -> str:
    """Folder that should contain kanban.md, inferred lexically."""
    m = re.search(r"(^|/)tasks/[^/]+$", normalized, re.IGNORECASE)
    if m:
        head = normalized[:m.start()] if m.start() > 0 else ""
        return head or "."
    if "/" in normalized:
        return normalized.rsplit("/", 1)[0] or "/"
    return "."


def to_fs_path(candidate: str, base: str) -> Path:
    s = candidate.replace("\\", "/")
    if os.name == "nt":
        # Git Bash / MSYS drive form: /c/Users/... -> C:/Users/...
        m = re.match(r"^/([A-Za-z])(/.*)?$", s)
        if m:
            s = m.group(1).upper() + ":" + (m.group(2) or "/")
    p = Path(s)
    if not p.is_absolute():
        p = Path(base) / s
    return p


def find_kanban(folder: Path) -> Path | None:
    cur = folder
    for _ in range(2):
        try:
            k = cur / "kanban.md"
            if k.is_file():
                return k
        except OSError:
            return None
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def prefreeze_lanes() -> set[str]:
    raw = os.environ.get("GEEKY_PREFREEZE_LANES", "Backlog")
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def lane_for_heading(heading: str) -> str | None:
    # Mirrors scripts/check-dod.py::lane_for_heading -- keep in sync.
    norm = heading.strip().lower()
    if "validation" in norm:
        return None
    for lane in KNOWN_LANES:
        if norm == lane.lower() or norm.startswith(lane.lower()):
            return lane
    return None


def package_is_frozen(kanban_text: str) -> bool:
    """True once any task sits in a lane outside the pre-freeze set."""
    pre = prefreeze_lanes()
    current: str | None = None
    for line in COMMENT_RE.sub("", kanban_text).splitlines():
        hm = HEADING_RE.match(line)
        if hm:
            current = lane_for_heading(hm.group(1))
            continue
        if current and current.lower() not in pre and PLACEMENT_RE.match(line):
            return True
    return False


def stage_note(normalized: str, base: str) -> str | None:
    """None => pre-freeze (stay silent). Otherwise the note to include.

    The note names the inferred planning folder in its NORMALIZED (lexical, "/")
    form rather than a resolved filesystem path, so the message is identical in
    the PowerShell twin regardless of platform path canonicalization.
    """
    folder_rel = planning_folder(normalized)
    kanban = find_kanban(to_fs_path(folder_rel, base))
    if kanban is None:
        return (f"No kanban.md was found for {folder_rel}, so this package "
                "cannot be proven pre-freeze and is treated as frozen.")
    try:
        text = kanban.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return (f"kanban.md for {folder_rel} could not be read, so this package "
                "cannot be proven pre-freeze and is treated as frozen.")
    if package_is_frozen(text):
        return (f"kanban.md for {folder_rel} shows at least one task past the "
                "Backlog lane, so this package is frozen.")
    return None


def main() -> int:
    args = parse_args()

    try:
        raw = sys.stdin.read()
    except Exception:
        return emit(malformed_message("stdin could not be read"),
                    args.mode, args.exit_code)
    if not raw or not raw.strip():
        return emit(malformed_message("stdin was empty"),
                    args.mode, args.exit_code)
    try:
        payload = json.loads(raw)
    except Exception:
        return emit(malformed_message("stdin was not valid JSON"),
                    args.mode, args.exit_code)
    if not isinstance(payload, dict):
        return emit(malformed_message("payload was not a JSON object"),
                    args.mode, args.exit_code)

    tool = payload.get("tool_name") or payload.get("tool")
    if not tool or not isinstance(tool, str):
        return emit(malformed_message("payload carried no tool_name"),
                    args.mode, args.exit_code)

    if tool.strip().lower() not in GUARDED_TOOLS:
        return 0

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not file_path or not isinstance(file_path, str):
        return emit(malformed_message(f"{tool} payload carried no file_path"),
                    args.mode, args.exit_code)

    normalized = normalize(file_path)
    reason = classify(normalized)
    if reason is None:
        return 0

    base = payload.get("cwd") or payload.get("workspace") or os.getcwd()
    if not isinstance(base, str) or not base:
        base = os.getcwd()

    note = stage_note(normalized, base)
    if note is None:
        return 0

    return emit(message(file_path, reason, note), args.mode, args.exit_code)


if __name__ == "__main__":
    sys.exit(main())
