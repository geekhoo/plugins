"""Offline C0 inventory. --mock-test runs only local telemetry fixtures; never authorizes a run.

Optional --output DIRECTORY must be beneath the repository's ignored outputs/ tree.
Every invocation creates a distinct evidence directory. No runner or live mode exists.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
EVAL = 'geeky-orchestration/evals/'
INPUTS = [EVAL + p for p in (
    'cases/c0-wordstat/case.json', 'cases/c0-wordstat/brief.md',
    'cases/c0-wordstat/contract.md', 'prompts/end-to-end.md',
    'scripts/run-baseline.ps1', 'scripts/run-codex-baseline.ps1',
    'scripts/evaluation_scope.py', 'telemetry/langfuse-scores.py',
    'telemetry/telemetry.ps1', 'telemetry/pins.json', 'adapters/codex/profile/mxc-pin.json',
    'telemetry/test_langfuse_scores.py', 'telemetry/test_langfuse_run.py',
    'telemetry/test_langfuse_coverage.py', 'scripts/test_c0_readiness.py',
    'scripts/check-c0-readiness.py')]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def effective_prompt(path):
    return path.read_bytes().decode('utf-8-sig').replace('{{PLANNING_FOLDER}}', 'docs/spec-001-feature/')


def local_env(git_inventory=False):
    # Pass only host execution necessities, never provider/telemetry credentials or plugin settings.
    keep = {'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'TEMP', 'TMP', 'SYSTEMDRIVE'}
    if git_inventory:
        # Preserve normal Git config/global-ignore discovery without passing Git overrides.
        keep.update({'HOME', 'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH', 'XDG_CONFIG_HOME'})
    env = {k: os.environ[k] for k in os.environ if k.upper() in keep}
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    return env


def command(args, cwd):
    try:
        git_inventory = args in (['git', 'rev-parse', 'HEAD'],
                                 ['git', 'status', '--short', '--untracked-files=all'])
        p = subprocess.run(args, cwd=cwd, env=local_env(git_inventory), capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=180)
        return {'command': [str(a) for a in args], 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'command': [str(a) for a in args], 'exit': -1, 'stdout': '', 'stderr': str(exc)}


def inventory(root=ROOT, tools_dir=Path('C:/repos/.eval-tools')):
    head = command(['git', 'rev-parse', 'HEAD'], root)
    dirty = command(['git', 'status', '--short', '--untracked-files=all'], root)
    errors = []
    if head['exit'] or dirty['exit']:
        errors.append('Git inventory failed')
    sources = {}
    for name in INPUTS:
        path = root / name
        sources[name] = {'path': str(path), 'sha256': digest(path.read_bytes()) if path.is_file() else None}
        if not path.is_file():
            errors.append('Missing input: ' + name)
    prompt = root / EVAL / 'prompts/end-to-end.md'
    prompt_sha = digest(effective_prompt(prompt).encode('utf-8')) if prompt.is_file() else None
    paths = {'python_tests': Path('C:/Python314/python.exe'),
             'codex': tools_dir / 'codex/0.164.0/bin/codex.exe',
             'mxc': tools_dir / 'windows-mxc/bin/MxcClaude.exe',
             'langfuse': Path.home() / 'AppData/Roaming/npm/langfuse.cmd'}
    for name in ('node', 'pwsh', 'claude'):
        found = shutil.which(name)
        paths[name] = Path(found) if found else None
    tools = {}
    for name, path in paths.items():
        present = bool(path and path.is_file())
        item = {'path': str(path) if path else None, 'present': present, 'version': None}
        if present:
            item['sha256'] = digest(path.read_bytes())
            # MXC has no safe version probe: hash it without starting the container launcher.
            if name != 'mxc':
                result = command([str(path), '--version'], root)
                item['version_probe'] = result
                item['version'] = result['stdout'].strip() if result['exit'] == 0 else None
                if result['exit']:
                    errors.append('Version probe failed: ' + name)
        else:
            errors.append('Missing tool: ' + name)
        tools[name] = item
    pins = root / EVAL / 'telemetry/pins.json'
    mxc_pin = root / EVAL / 'adapters/codex/profile/mxc-pin.json'
    artifacts = {}
    try:
        pin = json.loads(pins.read_bytes())
        mpin = json.loads(mxc_pin.read_bytes())
        checks = {
            'claude_hook': (tools_dir / ('langfuse/claude-hook/' + pin['claude_hook']['commit'] + '/langfuse_hook.py'), pin['claude_hook']['sha256']),
            'codex_tarball': (tools_dir / ('langfuse/codex-tracing/' + pin['codex_plugin']['version'] + '.tgz'), pin['codex_plugin']['sha256']),
            'mxc_exe': (paths['mxc'], mpin['exe_sha256']),
            'mxc_dll': (paths['mxc'].with_suffix('.dll'), mpin['dll_sha256']),
            'derived_codex_hook': (tools_dir / ('langfuse/codex-tracing/' + pin['codex_plugin']['version'] + '/dist/index.geeky.mjs'), None)}
        for name, (path, expected) in checks.items():
            actual = digest(path.read_bytes()) if path.is_file() else None
            ok = actual is not None and (expected is None or actual == expected.lower())
            artifacts[name] = {'path': str(path), 'sha256': actual, 'expected_sha256': expected, 'ready': ok}
            if not ok:
                errors.append('Missing or stale artifact: ' + name)
    except (OSError, ValueError, KeyError) as exc:
        errors.append('Invalid pins: ' + str(exc))
    return {'schema': 'geeky-eval.c0-readiness/1', 'repo_head': head['stdout'].strip(),
            'dirty_scope': dirty['stdout'].splitlines(), 'commit_only_proof': not bool(dirty['stdout'].strip()),
            'sources': sources, 'effective_prompt_sha256': prompt_sha, 'tools': tools, 'artifacts': artifacts,
            'errors': errors, 'readiness': 'blocked' if errors else 'inventory-ready', 'mock_tests': None,
            'paid_run_authorized': False, 'live_launch': 'held', 'live_telemetry_verified': False,
            'models': {'configured': None, 'observed': None},
            'future_launch_required': ['explicit models and efforts by role', 'reserve', 'waiver', 'authorization reference'],
            'telemetry_preview_arguments': ['--run', '<run-folder>', '--parity', '<parity.json>', '--scope', '<evaluation-inputs.json>', '--dry-run'],
            'limitations': ['Offline inventory and mocks do not establish live provider, MXC, auth, or remote telemetry readiness.',
                            'Derived Codex hook has an observed hash but no expected hash in existing pins.',
                            'Tool presence/version does not establish runtime compatibility; configured and observed models remain unknown.']}


def mock_tests(root, directory, python):
    tests = [EVAL + 'telemetry/test_langfuse_' + name + '.py' for name in ('scores', 'run', 'coverage')]
    tests += [EVAL + 'scripts/test_c0_readiness.py::test_actual_publisher_dry_run']
    result = command([python, '-m', 'pytest', '-q', '-rA', '-p', 'no:cacheprovider',
                      '--basetemp', str(directory / 'pytest-temp'), *tests], root)
    log = directory / 'mock-tests.log'
    log.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return {'command': result['command'], 'exit': result['exit'], 'log': str(log),
            'log_sha256': digest(log.read_bytes()), 'status': 'pass' if result['exit'] == 0 else 'fail'}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mock-test', action='store_true')
    ap.add_argument('--output', type=Path, help='Evidence parent directory beneath ignored outputs/')
    a = ap.parse_args(argv)  # Reject unsupported/live flags before any subprocess or file writes.
    parent = (a.output or ROOT / 'outputs/c0-readiness').resolve()
    if not parent.is_relative_to((ROOT / 'outputs').resolve()):
        ap.error('--output must be beneath repository outputs/')
    report = inventory()
    directory = None
    if a.output or a.mock_test:
        directory = parent / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
        directory.mkdir(parents=True)
    if a.mock_test and not report['errors']:
        report['mock_tests'] = mock_tests(ROOT, directory, report['tools']['python_tests']['path'])
        report['readiness'] = 'mocktested-ready' if report['mock_tests']['exit'] == 0 else 'blocked'
    if directory:
        report['report_path'] = str(directory / 'readiness.json')
        (directory / 'readiness.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 1 if report['readiness'] == 'blocked' else 0


if __name__ == '__main__':
    sys.exit(main())
