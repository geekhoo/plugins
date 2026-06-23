#!/usr/bin/env python3
"""
Scan ~/.claude/projects for Claude Code session transcripts and report them
grouped by project/repo, separating real conversations from background
housekeeping jobs (memory-consolidation agents, daily-log summarizers).
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

DEFAULT_BACKGROUND_PATTERNS = [
    "you are a memory consolidation agent",
    "summarizing a claude code session for a daily memory log",
    "apply maximum non-destructive compression",
    "you are summarizing a claude code session",
]

SAMPLE_LINES = 40  # lines to JSON-parse looking for metadata; rest just get counted


def extract_text(content) -> str:
    """message.content can be a plain string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(p for p in parts if p)
    return ""


def scan_jsonl(path: Path) -> dict:
    first_prompt = cwd = git_branch = created = None
    message_count = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for i, raw_line in enumerate(f):
            line = raw_line.strip()
            if not line:
                continue
            message_count += 1
            if i >= SAMPLE_LINES:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            cwd = cwd or obj.get("cwd")
            git_branch = git_branch or obj.get("gitBranch")
            created = created or obj.get("timestamp")
            if first_prompt is None and obj.get("type") == "user":
                msg = obj.get("message")
                content = msg.get("content") if isinstance(msg, dict) else None
                text = extract_text(content).strip()
                if text:
                    first_prompt = text

    stat = path.stat()
    return {
        "sessionId": path.stem,
        "fullPath": str(path),
        "firstPrompt": first_prompt or "No prompt",
        "cwd": cwd,
        "gitBranch": git_branch,
        "created": created,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "messageCount": message_count,
        "isSidechain": False,
        "source": "jsonl",
    }


def load_index(index_path: Path) -> list:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    entries = data if isinstance(data, list) else data.get("entries", [])
    return [{
        "sessionId": e.get("sessionId"),
        "fullPath": e.get("fullPath"),
        "firstPrompt": e.get("firstPrompt") or "No prompt",
        "cwd": e.get("projectPath"),
        "gitBranch": e.get("gitBranch"),
        "created": e.get("created"),
        "modified": e.get("modified"),
        "messageCount": e.get("messageCount"),
        "isSidechain": e.get("isSidechain", False),
        "source": "index",
    } for e in entries]


def collect_groups(claude_dir: Path) -> list:
    projects_dir = claude_dir / "projects"
    groups = []
    for project_dir in sorted(p for p in projects_dir.iterdir() if p.is_dir()):
        sessions = []
        seen_ids = set()

        index_path = project_dir / "sessions-index.json"
        if index_path.exists():
            for entry in load_index(index_path):
                if entry["sessionId"]:
                    seen_ids.add(entry["sessionId"])
                sessions.append(entry)

        for jsonl_path in sorted(project_dir.glob("*.jsonl")):
            if jsonl_path.stem in seen_ids:
                continue
            try:
                sessions.append(scan_jsonl(jsonl_path))
            except OSError:
                continue

        if not sessions:
            continue

        resolved = next((s["cwd"] for s in sessions if s.get("cwd")), None)
        groups.append({
            "dirName": project_dir.name,
            "displayPath": resolved or project_dir.name,
            "pathIsGuess": resolved is None,
            "sessions": sessions,
        })
    return groups


def is_background(first_prompt: str, patterns: list) -> bool:
    fp = (first_prompt or "").lower()
    return any(p in fp for p in patterns)


def process(groups, patterns, project_filter, since, show_background):
    out_groups = []
    totals = {"files": 0, "real": 0, "background": 0, "projects": 0}

    for group in groups:
        if project_filter and project_filter.lower() not in group["displayPath"].lower():
            continue

        real, background = [], []
        for s in group["sessions"]:
            if s.get("isSidechain"):
                continue
            if since and (s.get("created") or "") < since:
                continue
            (background if is_background(s.get("firstPrompt"), patterns) else real).append(s)

        if not real and not background:
            continue

        real.sort(key=lambda s: s.get("created") or "")
        background.sort(key=lambda s: s.get("created") or "")

        totals["files"] += len(real) + len(background)
        totals["real"] += len(real)
        totals["background"] += len(background)
        totals["projects"] += 1

        out_groups.append({
            "displayPath": group["displayPath"],
            "pathIsGuess": group["pathIsGuess"],
            "real": real,
            "background": background if show_background else [],
            "backgroundCount": len(background),
        })

    return out_groups, totals


def render_markdown(out_groups, totals) -> str:
    lines = []
    for group in out_groups:
        label = group["displayPath"] + (
            " (path inferred from dir name)" if group["pathIsGuess"] else "")
        lines.append(f"## {label}")
        lines.append("")
        if group["real"]:
            lines.append("| Created | Messages | First prompt |")
            lines.append("|---|---|---|")
            for s in group["real"]:
                prompt = (s.get("firstPrompt") or "").replace("\n", " ").strip()
                if len(prompt) > 90:
                    prompt = prompt[:87] + "..."
                prompt = prompt.replace("|", "\\|")
                lines.append(
                    f"| {s.get('created') or '?'} | {s.get('messageCount', '?')} | {prompt} |")
        else:
            lines.append("_No real conversations in this window._")
        lines.append("")

        if group["backgroundCount"]:
            if group["background"]:
                lines.append("**Background jobs:**")
                for s in group["background"]:
                    prompt = (s.get("firstPrompt") or "").replace("\n", " ").strip()[:70]
                    lines.append(f"- {s.get('created') or '?'} — {prompt}")
            else:
                lines.append(
                    f"_{group['backgroundCount']} background housekeeping session(s) hidden "
                    f"— pass --show-background to list them._"
                )
            lines.append("")

    lines.append("---")
    lines.append(
        f"**Totals:** {totals['files']} session files · {totals['real']} real conversations · "
        f"{totals['background']} background jobs · {totals['projects']} project paths"
    )
    return "\n".join(lines)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        # Windows consoles default to a lossy codepage otherwise.
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude-dir", default="~/.claude")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--project", default=None,
                        help="Only show groups whose path contains this substring")
    parser.add_argument("--since", default=None,
                        help="Only include sessions created on/after this ISO timestamp/date")
    parser.add_argument("--show-background", action="store_true",
                        help="List background sessions individually instead of just a count")
    parser.add_argument("--background-pattern", action="append", default=[],
                        help="Extra substring(s) (case-insensitive) that mark "
                             "a session as background")
    args = parser.parse_args()

    claude_dir = Path(args.claude_dir).expanduser().resolve()
    patterns = [p.lower() for p in DEFAULT_BACKGROUND_PATTERNS + args.background_pattern]

    groups = collect_groups(claude_dir)
    out_groups, totals = process(groups, patterns, args.project, args.since, args.show_background)

    if args.format == "json":
        print(json.dumps({"groups": out_groups, "totals": totals}, indent=2, default=str))
    else:
        print(render_markdown(out_groups, totals))


if __name__ == "__main__":
    main()
