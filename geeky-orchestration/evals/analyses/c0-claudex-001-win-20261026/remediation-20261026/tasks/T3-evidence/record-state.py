import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[5]
files = ['evals/scripts/evaluation_scope.py', 'evals/scripts/parity-eval.py', 'evals/scripts/test_parity_eval.py',
         'evals/telemetry/langfuse-scores.py', 'evals/telemetry/test_langfuse_scores.py',
         'evals/telemetry/telemetry.ps1', 'evals/telemetry/README.md', 'evals/mxc-litellm-runbook.md']
prefix = 'evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/tasks/T3-evidence/'
files += [prefix + 'check-retained.py', prefix + 'check-static.ps1']
commands = [
    ('& C:/Python314/python.exe -m pytest -q test_score_run.py evals/scripts/test_parity_eval.py evals/scripts/test_codex_trace.py evals/scripts/test_process_replay.py evals/telemetry/test_langfuse_run.py evals/telemetry/test_langfuse_coverage.py evals/telemetry/test_langfuse_scores.py', 'required-suite-final'),
    ('& C:/Python314/python.exe ' + prefix + 'check-retained.py', 'retained-invariants-final'),
    ('& pwsh -NoProfile -File ' + prefix + 'check-static.ps1', 'static')]
result = {'head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=PLUGIN, capture_output=True, text=True, check=True).stdout.strip(),
          'state': 'uncommitted T3 source; parent-owned T1/T2 work also present', 'workdir': str(PLUGIN),
          'environment': {'python_executable': sys.executable, 'python': sys.version, 'platform': platform.platform(),
                          'powershell': subprocess.run(['pwsh', '-NoProfile', '-Command', '$PSVersionTable.PSVersion.ToString()'], capture_output=True, text=True, check=True).stdout.strip()},
          'files': {str(PLUGIN / name): hashlib.sha256((PLUGIN / name).read_bytes()).hexdigest() for name in files},
          'validation': [{'command': command, 'exit': int((HERE / (name + '.exit.txt')).read_text().strip()),
                          'log': str(HERE / (name + '.log')), 'result': (HERE / (name + '.log')).read_text(encoding='utf-8').strip()}
                         for command, name in commands]}
(HERE / 'tested-state.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
