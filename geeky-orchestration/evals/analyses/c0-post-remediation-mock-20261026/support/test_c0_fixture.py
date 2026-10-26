"""Focused local subprocess checks; no MXC, network, providers or oracle code."""
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

MOCKS = Path(__file__).resolve().parent
PLUGIN = MOCKS.parents[1]
RUNNERS = PLUGIN / 'evals/scripts'


def run(argv, cwd, env):
    return subprocess.run([str(v) for v in argv], cwd=cwd, env=env,
                          capture_output=True, encoding='utf-8', timeout=120)


@pytest.fixture
def candidate(tmp_path):
    workspace = tmp_path / 'candidate'
    workspace.mkdir()
    config = tmp_path / 'config'
    config.mkdir()
    for name in ('brief.md', 'contract.md'):
        shutil.copyfile(PLUGIN / 'evals/cases/c0-wordstat' / name, workspace / name)
    for name in ('mock_claude.py', 'c0_fixture.py'):
        shutil.copyfile(MOCKS / name, config / name)
    shutil.copyfile(PLUGIN / 'evals/adapters/codex/mock_codex.py', config / 'mock_codex.py')
    # Every child Python (including fixture tests and gates) has denied network.
    (config / 'sitecustomize.py').write_text(
        'import socket\n'
        'def denied(*args, **kwargs):\n    raise RuntimeError("test denies network")\n'
        'socket.create_connection = denied\nsocket.socket.connect = denied\n', encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if not any(
        word in k.upper() for word in ('API_KEY', 'OAUTH', 'AUTH_TOKEN', 'LANGFUSE', 'LITELLM'))}
    env.update(PATH=str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', ''),
        PYTHONPATH=str(config), PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        CLAUDE_PLUGIN_ROOT=str(PLUGIN), CLAUDE_CONFIG_DIR=str(config / 'claude'),
        CODEX_HOME=str(config / 'codex'), TMPDIR=str(tmp_path), MOCK_LATENCY_MS='0',
        GEEKY_DEADLINE_UTC=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)).isoformat(),
        GEEKY_CLOSEOUT_RESERVE_S='30', GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory',
        GIT_CONFIG_VALUE_0=str(workspace), GIT_AUTHOR_NAME='scripted mock',
        GIT_AUTHOR_EMAIL='mock@example.invalid', GIT_COMMITTER_NAME='scripted mock',
        GIT_COMMITTER_EMAIL='mock@example.invalid')
    assert run(['git', 'init', '-q'], workspace, env).returncode == 0
    assert run(['git', 'add', '.'], workspace, env).returncode == 0
    assert run(['git', 'commit', '-qm', 'docs: seed public case'], workspace, env).returncode == 0
    return workspace, config, env


@pytest.mark.parametrize('actor', ['claude', 'codex'])
def test_full_scripted_fixture_both_native_shapes(candidate, actor):
    workspace, config, env = candidate
    before = run(['git', 'rev-parse', 'HEAD'], workspace, env).stdout.strip()
    if actor == 'claude':
        argv = [sys.executable, config / 'mock_claude.py', '--plugin-dir', PLUGIN,
                '--mock-scenario', 'c0-full', '--mock-case', 'c0-wordstat',
                '-p', 'Execute docs/spec-001-feature/']
    else:
        argv = [sys.executable, config / 'mock_codex.py', 'exec', '--json', '--cd', workspace,
                '--mock-scenario', 'c0-full', '-c', 'hooks={PreToolUse=[]}',
                'Execute docs/spec-001-feature/']
    result = run(argv, workspace, env)
    (workspace / '.git/actor.stdout.jsonl').write_text(result.stdout, encoding='utf-8')
    (workspace / '.git/actor.stderr.log').write_text(result.stderr, encoding='utf-8')
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    report = json.loads((workspace / '.git/c0-full-summary.json').read_text())
    assert report['label'] == 'SCRIPTED MOCK' and report['model_calls'] == 0
    assert report['deadline_environment'] == {'GEEKY_DEADLINE_UTC': env['GEEKY_DEADLINE_UTC'],
                                             'GEEKY_CLOSEOUT_RESERVE_S': 30}
    assert [s['stage'] for s in report['stages']] == [
        'spec-research', 'geeky-plan', 'plan-review', 'geeky-implement', 'impl-review']
    assert report['tests_passed'] == 17 and len(set(report['commits'])) == 3
    assert report['phase_verdict'] == 'READY TO ADVANCE' and report['final_verdict'] == 'PASS'
    folder = workspace / report['planning_folder']
    assert json.loads((folder / '.heartbeat').read_text())['status'] == 'done'
    assert report['closeout'] == 'done' and (folder / 'run-summary.md').is_file()
    assert len(report['saved_domain_replies']) == 3
    for path in report['saved_domain_replies']:
        reply = (workspace / path).read_text()
        assert 'SCRIPTED MOCK' in reply and 'Verdict: PASS' in reply
        assert report['commits'][1] in reply and '<!-- reviewer-complete:' in reply
    assert (folder / 'review-impl.md').read_text().count('<!-- reviewer-complete:') == 3
    assert (folder / 'review-impl.md').read_text().endswith('Overall: PASS\n')
    assert (folder / 'review-phase-1.md').read_text().count('Phase 1: READY TO ADVANCE') == 1
    commands = json.loads((workspace / '.git/c0-full-commands.json').read_text())
    assert all(c['exit_code'] == 0 for c in commands)
    assert all(Path(c['argv'][0]).name.lower() in ('python.exe', 'python', 'git') for c in commands)
    for gate in ('validate-planning-folder', 'validate-task-schema', 'validate-kanban', 'check-dod', 'check-commit'):
        assert any(c['name'] == gate for c in commands)
    commits = run(['git', 'rev-list', before + '..HEAD'], workspace, env).stdout.splitlines()
    assert len(commits) == 3
    files = run(['git', 'show', '--format=', '--name-only', report['commits'][1]], workspace, env).stdout
    assert 'wordstat/__main__.py' in files and 'tests/test_wordstat.py' in files
    assert run(['git', 'status', '--porcelain'], workspace, env).stdout == ''
    if actor == 'claude':
        summary = next(e for e in events if e.get('subtype') == 'mock_summary')
        assert summary['ok'] and summary['model_calls'] == 0
        assert events[-1]['total_cost_usd'] == 0 and events[-1]['modelUsage'] == {}
        assert '17 tests passed' in events[-1]['result'] and 'Commits:' in events[-1]['result']
        assert all(e['message']['usage']['output_tokens'] == 0 for e in events if e['type'] == 'assistant')
    else:
        summary = next(e for e in events if e.get('type') == 'mock_summary')
        assert summary['ok'] and summary['c0_full'] == report | {'completion_report': summary['c0_full']['completion_report']}
        assert events[-1]['type'] == 'turn.completed'
        rollout = next((config / 'codex/sessions').rglob('*.jsonl'))
        payloads = [json.loads(line)['payload'] for line in rollout.read_text().splitlines()]
        assert any(p.get('type') == 'function_call' for p in payloads)
        assert any(p.get('type') == 'task_complete' for p in payloads)
        final = next(p['message'] for p in payloads if p.get('type') == 'agent_message')
        assert 'SCRIPTED MOCK' in final and '17 tests passed' in final and 'Commits:' in final


@pytest.mark.parametrize('deadline,reserve', [('not-utc', '30'), ('2026-10-26T00:00:00', '30'),
    ('2026-10-26T00:00:00Z', '-1')])
def test_invalid_deadline_environment_fails_before_writes(candidate, deadline, reserve):
    workspace, config, env = candidate
    env.update(GEEKY_DEADLINE_UTC=deadline, GEEKY_CLOSEOUT_RESERVE_S=reserve)
    result = run([sys.executable, config / 'mock_codex.py', '--cd', workspace,
                  '--mock-scenario', 'c0-full'], workspace, env)
    assert result.returncode == 1
    assert not (workspace / 'docs').exists() and not (workspace / 'wordstat').exists()


def test_runner_mock_dispatch_is_explicit():
    claude = (RUNNERS / 'run-baseline.ps1').read_text(encoding='utf-8-sig')
    codex = (RUNNERS / 'run-codex-baseline.ps1').read_text(encoding='utf-8-sig')
    for script in (claude, codex):
        assert "if ($MockAgent -and $MockScenario -eq 'c0-full') { $hostArgs += '--deny-net' }" in script
        assert "c0-full requires c0-wordstat and -NoTelemetry" in script
        assert "evals/mock-agent/c0_fixture.py" in script
    assert "if (-not $MockAgent -and -not $env:CLAUDE_CODE_OAUTH_TOKEN)" in claude


def test_old_claude_happy_and_gate_failure_remain_explicit(candidate):
    workspace, config, env = candidate
    result = run([sys.executable, config / 'mock_claude.py', '--plugin-dir', PLUGIN,
                  '--mock-scenario', 'happy,gate-fail', '--mock-case', 'c0-wordstat'], workspace, env)
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    summary = next(e for e in events if e.get('subtype') == 'mock_summary')
    assert summary['ok'] and 'c0_full' not in summary
    assert any(c['name'] == 'happy.pytest' and c['status'] == 'pass' for c in summary['checks'])
    assert any(c['name'] == 'gate-fail.stopped' and c['status'] == 'pass' for c in summary['checks'])
    assert not (workspace / '.git/c0-full-summary.json').exists()
    assert 'mock-agent stub' in (workspace / 'wordstat/__main__.py').read_text()


def test_codex_crash_and_bounded_slow(candidate):
    workspace, config, env = candidate
    env['MOCK_SLOW_SECONDS'] = '0.01'
    result = run([sys.executable, config / 'mock_codex.py', '--cd', workspace,
                  '--mock-scenario', 'slow'], workspace, env)
    assert result.returncode == 0 and 'turn.completed' in result.stdout
    result = run([sys.executable, config / 'mock_codex.py', '--cd', workspace,
                  '--mock-scenario', 'crash'], workspace, env)
    assert result.returncode == 3 and 'simulated crash' in result.stderr
    assert 'turn.completed' not in result.stdout


@pytest.mark.parametrize('actor', ['claude', 'codex'])
def test_full_fixture_rejects_telemetry_hooks(candidate, actor):
    workspace, config, env = candidate
    if actor == 'claude':
        settings = config / 'settings.json'
        settings.write_text(json.dumps({'hooks': {'Stop': [{'hooks': []}]}}))
        args = [config / 'mock_claude.py', '--settings', settings]
    else:
        args = [config / 'mock_codex.py', '--cd', workspace, '-c', 'hooks={Stop=[]}']
        # Nonempty hook arrays are exactly what the profile emits for telemetry.
        args[-1] = 'hooks={Stop=[{hooks=[]}]}'
    result = run([sys.executable, *args, '--mock-scenario', 'c0-full'], workspace, env)
    assert result.returncode != 0 and 'c0-full must run alone' in result.stderr
    assert not (workspace / 'docs').exists()
