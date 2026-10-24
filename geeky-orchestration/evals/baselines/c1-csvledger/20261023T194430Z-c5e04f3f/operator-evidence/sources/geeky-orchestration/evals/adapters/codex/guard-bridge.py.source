"""Translate Codex patch inputs to the shipped warn-mode guard's file inputs."""
import argparse
import json
import re
import subprocess
import sys


def paths(payload):
    inp = payload.get('tool_input') or {}
    direct = inp.get('file_path') or inp.get('notebook_path')
    if direct:
        return [direct]
    # Include move destinations as well as the source of update/delete operations.
    return list(dict.fromkeys(re.findall(
        r'^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$',
        inp.get('command', ''), re.MULTILINE)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--guard', required=True)
    args = parser.parse_args()
    payload = json.load(sys.stdin)
    warnings = []
    for path in paths(payload):
        result = subprocess.run(
            [sys.executable, args.guard, '--mode', 'warn'],
            input=json.dumps({'tool_name': 'Edit', 'tool_input': {'file_path': path}}),
            text=True, capture_output=True, check=True)
        if result.stdout.strip():
            warnings.append(result.stdout.strip())
    if warnings:
        print(json.dumps({'hookSpecificOutput': {
            'hookEventName': 'PreToolUse', 'additionalContext': '\n'.join(warnings)}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
