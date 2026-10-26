"""Retain small local-fixture records and bind validation to source file bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PLUGIN = Path(__file__).resolve().parents[6]
EVIDENCE = Path(__file__).parent
fixture_root = Path(sys.argv[1]).resolve()
files = [
    'evals/scripts/run-baseline.ps1', 'evals/scripts/run-codex-baseline.ps1',
    'evals/scripts/run-lifecycle.ps1', 'evals/scripts/test_run_lifecycle.py',
    'evals/QUICKSTART.md', 'evals/mxc-litellm-runbook.md',
    'skills/geeky-implement/SKILL.md', 'skills/geeky-implement/references/execution-protocol.md',
    'evals/scripts/test_codex_run2_prep.py', 'evals/scripts/test_codex_auto_process.py',
    'evals/scripts/analyze-run.py', 'evals/telemetry/telemetry.ps1', 'evals/prompts/end-to-end.md',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


hashes = {name: sha(PLUGIN / name) for name in files}
cases = sorted(path for path in fixture_root.iterdir() if path.is_dir() and (path / 'repo').exists())
for case in cases:
    for name in files[:2]:
        assert sha(case / 'repo/geeky-orchestration' / name) == hashes[name], (case, name)
    sample = EVIDENCE / 'samples' / case.name
    sample.mkdir(parents=True, exist_ok=True)
    for name in ('launches.jsonl', 'observed-prepared.json', 'before-replacement.json'):
        if (case / name).is_file():
            shutil.copy2(case / name, sample / name)
    for record in (case / 'repo/geeky-orchestration/evals/baselines').rglob('run.json'):
        # Exclude the analyzer's separate derived record.
        if record.parent.name == 'derived':
            continue
        for name in ('run.json', 'stream.jsonl', 'stderr.txt'):
            if (record.parent / name).is_file():
                shutil.copy2(record.parent / name, sample / name)
        (sample / 'fixture-input.json').write_text(json.dumps({
            'source': str(case), 'run_record': str(record),
            'synthetic_only': True, 'real_mxc_provider_oracle_telemetry': False,
        }, indent=2), encoding='utf-8')

manifest = {
    'head': subprocess.check_output(['git', '-C', str(PLUGIN), 'rev-parse', 'HEAD'], text=True).strip(),
    'baseline': subprocess.check_output(['git', '-C', str(PLUGIN), 'rev-parse', '8fff98b0f087f148d4f416f512dc9988d61a57aa^{commit}'], text=True).strip(),
    'environment': {'python': sys.version, 'python_executable': sys.executable,
                    'powershell': subprocess.check_output(['pwsh', '-NoProfile', '-Command', '$PSVersionTable.PSVersion.ToString()'], text=True).strip()},
    'sha256': hashes, 'actual_runner_fixture_copies_verified': len(cases) * 2,
    'fixture_root': str(fixture_root), 'samples': len(cases),
    'commands': [
        {'command': '& C:/Python314/python.exe -m pytest -q evals/scripts/test_run_lifecycle.py',
         'exit': 0, 'result': '43 passed in 172.98s (0:02:52)', 'log': 'lifecycle-final.log'},
        {'command': '& C:/Python314/python.exe -m pytest -q evals/scripts/test_codex_run2_prep.py evals/scripts/test_codex_auto_process.py',
         'exit': 0, 'result': '15 passed, 1 skipped in 13.85s', 'log': 'preparation-regressions.log'},
        {'command': '& pwsh -NoProfile -File evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/tasks/T1-evidence/check-prompt.ps1',
         'exit': 0, 'result': 'identical rendered prompt SHA256; no runner entry point executed', 'log': 'prompt-parity.log'},
    ],
}
(EVIDENCE / 'tested-state.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(f'PASS: {len(cases)} actual-runner fixtures retained; {len(cases) * 2} runner copies match final source SHA256')
print(json.dumps(hashes, indent=2))
