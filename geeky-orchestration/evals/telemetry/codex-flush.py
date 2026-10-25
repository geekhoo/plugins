"""Replay a Codex rollout through the Langfuse tracer after the run.

Usage: <python> codex-flush.py <node> <tracer .mjs> <payload.json>
The tracer reads its Stop payload from stdin; the MXC host closes the workload's stdin, so the payload
travels as a file. Without a turn_id the tracer skips a turn that never completed (a run killed or timed
out mid-turn), so the last started turn is named as the one that stopped. The rollout's .langfuse sidecar
keeps already-delivered turns from being re-sent.
"""
import json
import subprocess
import sys

node, tracer, payload_path = sys.argv[1:4]
with open(payload_path, encoding='utf-8') as f:
    payload = json.load(f)
if not payload.get('turn_id'):
    with open(payload['transcript_path'], encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            item = row.get('payload') or {}
            if row.get('type') == 'event_msg' and item.get('type') == 'task_started' and item.get('turn_id'):
                payload['turn_id'] = item['turn_id']
node_options = ['--preserve-symlinks-main', '--preserve-symlinks'] if sys.platform == 'win32' else []
sys.exit(subprocess.run([node, *node_options, tracer], input=json.dumps(payload).encode()).returncode)
