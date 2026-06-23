#!/usr/bin/env python3
"""scan_friction.py - quantify recurring friction across Claude Code session transcripts.

Sibling to list-sessions/scan_sessions.py. Where scan_sessions answers "what conversations
happened", this answers "where are we wasting rounds": per session it counts environment /
command failures, *silent* (non-blocking) hook failures, and sharp user corrections - so the
recurring "analyse all our sessions for conflicts / confusions / wasted rounds" request becomes
a one-command delta instead of a from-scratch grep investigation each time.

Why this exists: that analysis was requested 3x (2026-06-09, -16, -22) and re-derived by hand
each time. The single biggest finding each time was hook stderr ("python3: command not found",
"Failed with non-blocking status code") that is invisible in normal use because the hooks are
non-blocking. This script makes that visible on demand.

Dates come from the transcript's own timestamps (last-activity), NOT file mtime - old
transcripts get touched by background jobs, so mtime is not a reliable session date.

Usage:
    py scan_friction.py [--since YYYY-MM-DD] [--claude-dir PATH] [--format md|json] [--top N]

Plain stdlib only; runs the same from PowerShell or Bash. On Windows invoke via `py`.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# label -> (regex, human description). Counts are transcript-LINE match counts, which is the
# point for hook stderr: one line per failed hook event (Pre/Post/UserPromptSubmit).
SIGNATURES = [
    ("hook_silent_fail", re.compile(r"Failed with non-blocking status code"),
     "silent (non-blocking) hook failures - the dangerous, invisible kind"),
    ("python_not_found",
     re.compile(r"python3?: command not found|'python3?' is not recognized", re.I),
     "python/python3 not resolving (breaks plugin hooks + scripts)"),
    ("cmd_not_found", re.compile(r"[\w.\-/]+: command not found|is not recognized as", re.I),
     "command failures (Unix-on-Windows reflexes, missing tools)"),
    ("user_correction", re.compile(
        r"that'?s not what|you keep|didn'?t ask|not what i (?:asked|meant|wanted)|"
        r"no,? i (?:said|meant|just)|going in circles|stop doing", re.I),
     "sharp user corrections (genuine misunderstandings)"),
    ("apology", re.compile(r"you'?re absolutely right|i apologi[sz]e|my mistake|i was wrong", re.I),
     "assistant concessions (often a wasted-round tail)"),
]
_CMD_RE = re.compile(r"([\w.\-/]+): command not found")
_TS_RE = re.compile(r'"timestamp"\s*:\s*"(\d{4}-\d{2}-\d{2}T[^"]+)"')
_SKIP_DIR_HINTS = ("AppData-Local-Temp", "-Temp")


def resolve_claude_dir(arg):
    return Path(arg) if arg else Path(os.path.expanduser("~")) / ".claude"


def first_field(path, field, max_lines=40):
    """Cheap scan of the first N lines for a top-level JSON field (cwd, gitBranch)."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh):
                if i >= max_lines:
                    break
                if f'"{field}"' not in line:
                    continue
                try:
                    val = json.loads(line).get(field)
                    if val:
                        return val
                except Exception:
                    m = re.search(rf'"{field}"\s*:\s*"([^"]+)"', line)
                    if m:
                        return m.group(1)
    except Exception:
        pass
    return None


def short_project(cwd, fallback_dir):
    if cwd:
        return Path(cwd).name or cwd
    return fallback_dir.name.split("-")[-1] or fallback_dir.name


def scan_file(path):
    """Single pass: count friction signatures AND track first/last transcript timestamp."""
    counts = defaultdict(int)
    failing_cmds = defaultdict(int)
    first_ts = last_ts = None
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                for label, rx, _ in SIGNATURES:
                    n = len(rx.findall(line))
                    if n:
                        counts[label] += n
                for m in _CMD_RE.finditer(line):
                    failing_cmds[m.group(1)] += 1
                tm = _TS_RE.search(line)
                if tm:
                    ts = tm.group(1)
                    if first_ts is None or ts < first_ts:
                        first_ts = ts
                    if last_ts is None or ts > last_ts:
                        last_ts = ts
    except Exception:
        counts["_read_error"] = 1
    return counts, failing_cmds, first_ts, last_ts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scan session transcripts for recurring friction.")
    ap.add_argument("--since",
                    help="only sessions with activity on/after this ISO date (YYYY-MM-DD)")
    ap.add_argument("--claude-dir", help="path to a .claude dir (default: ~/.claude)")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--top", type=int, default=0, help="show only the N highest-friction sessions")
    ap.add_argument("--include-temp", action="store_true",
                    help="include AppData/Temp background dirs")
    args = ap.parse_args(argv)

    since = datetime.fromisoformat(args.since).date() if args.since else None

    projects = resolve_claude_dir(args.claude_dir) / "projects"
    if not projects.is_dir():
        print(f"no projects dir at {projects}", file=sys.stderr)
        return 1

    rows = []
    for proj in sorted(projects.iterdir()):
        if not proj.is_dir():
            continue
        if not args.include_temp and any(h in proj.name for h in _SKIP_DIR_HINTS):
            continue
        for f in sorted(proj.glob("*.jsonl")):  # non-recursive => skips subagents/
            counts, failing, first_ts, last_ts = scan_file(f)
            total = sum(v for k, v in counts.items() if not k.startswith("_"))
            if total == 0:
                continue
            # date = transcript last-activity; fall back to mtime only if no timestamp parsed
            if last_ts:
                last_date = last_ts[:10]
            else:
                last_date = datetime.fromtimestamp(
                    f.stat().st_mtime, tz=timezone.utc).date().isoformat()
            if since and datetime.fromisoformat(last_date).date() < since:
                continue
            cwd = first_field(f, "cwd")
            top_cmd = max(failing.items(), key=lambda kv: kv[1])[0] if failing else ""
            rows.append({
                "date": last_date,
                "created": (first_ts or "")[:10],
                "project": short_project(cwd, proj),
                "session": f.stem[:8],
                "total": total,
                "silent_hook": counts.get("hook_silent_fail", 0),
                "python": counts.get("python_not_found", 0),
                "cmd": counts.get("cmd_not_found", 0),
                "correction": counts.get("user_correction", 0),
                "apology": counts.get("apology", 0),
                "top_failing_cmd": top_cmd,
            })

    rows.sort(key=lambda r: r["total"], reverse=True)
    if args.top:
        rows = rows[:args.top]

    if args.format == "json":
        print(json.dumps(rows, indent=2))
        return 0

    scope = f" (activity since {args.since})" if args.since else ""
    print(f"# Session friction scan{scope}\n")
    if not rows:
        print("_No friction signatures found in scope. Clean._")
        return 0
    print("| LastActive | Project | Session | Total | SilentHook | Python | "
          "Cmd | Corrections | Apologies | Top failing cmd |")
    print("|---|---|---|---:|---:|---:|---:|---:|---:|---|")
    agg = defaultdict(int)
    for r in rows:
        print(f"| {r['date']} | {r['project']} | {r['session']} | {r['total']} | "
              f"{r['silent_hook']} | {r['python']} | {r['cmd']} | {r['correction']} | "
              f"{r['apology']} | {r['top_failing_cmd']} |")
        for k in ("total", "silent_hook", "python", "cmd", "correction", "apology"):
            agg[k] += r[k]
    print(f"\n**Totals across {len(rows)} session(s):** {agg['total']} friction hits "
          f"-- silent-hook {agg['silent_hook']}, python {agg['python']}, cmd {agg['cmd']}, "
          f"corrections {agg['correction']}, apologies {agg['apology']}.")
    print("\n**Legend:**")
    for label, _, desc in SIGNATURES:
        print(f"- `{label}` - {desc}")
    print("\n_Counts are transcript-line hits. 'SilentHook' + 'Python' dominating a recent "
          "session = the dead-hook pattern resurfacing (check ~/bin is on PATH). NB: a "
          "meta-analysis session (one that itself greps for these phrases) self-inflates "
          "'Corrections'/'Apologies' - read it in context before trusting it._")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
