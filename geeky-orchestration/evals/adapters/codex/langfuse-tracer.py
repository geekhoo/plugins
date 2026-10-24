"""Run the Langfuse Codex tracer named in langfuse-tracer.json beside this file.

The hook command is then a space-free `python langfuse-tracer.py`, so no shell has to quote a
node path such as C:\\Program Files\\nodejs\\node.exe. The Stop payload passes through on stdin.
"""
import json
from pathlib import Path
import subprocess
import sys

config = json.loads(Path(__file__).with_suffix('.json').read_text(encoding='utf-8'))
sys.exit(subprocess.run([config['node'], config['hook']], stdin=sys.stdin).returncode)
