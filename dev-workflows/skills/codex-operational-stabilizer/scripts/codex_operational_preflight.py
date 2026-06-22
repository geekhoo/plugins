import argparse
import json
import os
from pathlib import Path

from operational_preflight_hooks import (
    hook_command_info,
    hook_command_paths,
    inspect_hooks,
)
from operational_preflight_inventory import (
    DEFAULT_SKILLS,
    build_report,
    command_status,
    count_lines,
    inspect_agents,
    inspect_sessions,
    inspect_skills,
)
from operational_preflight_report import as_markdown
from operational_preflight_shim import inspect_shim


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect local Codex operational readiness.")
    default_root = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    parser.add_argument("--codex-root", default=default_root)
    parser.add_argument("--required-skill", action="append", default=[])
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    required_skills = args.required_skill or DEFAULT_SKILLS
    report = build_report(Path(args.codex_root), required_skills)
    if args.markdown:
        print(as_markdown(report), end="")
        return
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
