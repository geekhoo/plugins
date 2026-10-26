"""Offline readiness behavior; synthetic publication is never a contestant result."""
import importlib.util
import json
from pathlib import Path
import socket
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('readiness', HERE / 'check-c0-readiness.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def test_live_flag_rejected_before_actions(monkeypatch):
    monkeypatch.setattr(r, 'inventory', lambda: pytest.fail('inventory must not start'))
    for flag in ('--launch', '--live', '--live-telemetry'):
        with pytest.raises(SystemExit) as exc:
            r.main([flag])
        assert exc.value.code == 2


def test_prompt_preserves_crlf_and_bom(tmp_path):
    path = tmp_path / 'prompt.md'
    path.write_bytes(b'\xef\xbb\xbfstart\r\n{{PLANNING_FOLDER}}\r\n')
    assert r.effective_prompt(path).encode() == b'start\r\ndocs/spec-001-feature/\r\n'
    actual = r.ROOT / r.EVAL / 'prompts/end-to-end.md'
    assert r.effective_prompt(actual) == actual.read_bytes().decode('utf-8-sig').replace(
        '{{PLANNING_FOLDER}}', 'docs/spec-001-feature/')


def test_default_inventory_never_tests_launches_or_networks(monkeypatch, capsys):
    calls = []
    original = r.command

    def guarded(args, cwd):
        calls.append(args)
        assert args[:2] in (['git', 'rev-parse'], ['git', 'status']) or args[1:] == ['--version']
        return original(args, cwd)

    monkeypatch.setattr(r, 'command', guarded)
    monkeypatch.setattr(r, 'mock_tests', lambda *a: pytest.fail('no tests by default'))
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: pytest.fail('network forbidden'))
    assert r.main([]) in (0, 1)  # Tool absence is reported, never converted to a success.
    report = json.loads(capsys.readouterr().out)
    assert calls and report['mock_tests'] is None
    assert report['paid_run_authorized'] is False
    assert report['live_telemetry_verified'] is False and report['live_launch'] == 'held'


def test_missing_inputs_and_tools_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(r.shutil, 'which', lambda _: None)
    monkeypatch.setattr(r, 'command', lambda *a: {'exit': 0, 'stdout': 'fixture\n', 'stderr': ''})
    report = r.inventory(tmp_path, tmp_path / 'missing-tools')
    assert report['readiness'] == 'blocked'
    assert any(e.startswith('Missing input:') for e in report['errors'])
    assert 'Missing tool: mxc' in report['errors']


def test_stale_pins_and_dirty_scope_truthful(tmp_path, monkeypatch):
    pin = tmp_path / r.EVAL / 'telemetry/pins.json'
    pin.parent.mkdir(parents=True)
    pin.write_text(json.dumps({'claude_hook': {'commit': 'fixture', 'sha256': '0' * 64},
                              'codex_plugin': {'version': 'fixture', 'sha256': '0' * 64}}))
    mpin = tmp_path / r.EVAL / 'adapters/codex/profile/mxc-pin.json'
    mpin.parent.mkdir(parents=True)
    mpin.write_text(json.dumps({'exe_sha256': '0' * 64, 'dll_sha256': '0' * 64}))
    artifact = tmp_path / 'tools/langfuse/claude-hook/fixture/langfuse_hook.py'
    artifact.parent.mkdir(parents=True)
    artifact.write_text('stale')
    monkeypatch.setattr(r, 'command', lambda args, cwd: {'exit': 0, 'stdout': ' M changed.py\n', 'stderr': ''})
    report = r.inventory(tmp_path, tmp_path / 'tools')
    assert not report['artifacts']['claude_hook']['ready']
    assert report['dirty_scope'] == [' M changed.py'] and not report['commit_only_proof']


@pytest.mark.parametrize('exit_code,readiness', [(0, 'mocktested-ready'), (1, 'blocked')])
def test_mock_outcome_never_grants_live_authorization(monkeypatch, capsys, tmp_path, exit_code, readiness):
    report = {'errors': [], 'tools': {'python_tests': {'path': sys.executable}},
              'paid_run_authorized': False, 'live_launch': 'held', 'live_telemetry_verified': False}
    monkeypatch.setattr(r, 'ROOT', tmp_path)
    monkeypatch.setattr(r, 'inventory', lambda: report.copy())
    monkeypatch.setattr(r, 'mock_tests', lambda *a: {'exit': exit_code})
    assert r.main(['--mock-test']) == exit_code
    result = json.loads(capsys.readouterr().out)
    assert result['readiness'] == readiness and result['paid_run_authorized'] is False
    assert result['live_launch'] == 'held' and result['live_telemetry_verified'] is False


def test_child_environment_drops_provider_and_telemetry_values(monkeypatch):
    for name in ('OPENAI_API_KEY', 'LANGFUSE_SECRET_KEY', 'TRACE_TO_LANGFUSE', 'ANTHROPIC_API_KEY', 'PYTHONPATH'):
        monkeypatch.setenv(name, 'fixture')
    assert all(name not in r.local_env() for name in (
        'OPENAI_API_KEY', 'LANGFUSE_SECRET_KEY', 'TRACE_TO_LANGFUSE', 'ANTHROPIC_API_KEY', 'PYTHONPATH'))


def test_only_known_git_inventory_retains_config_locations(monkeypatch, tmp_path):
    locations = ('HOME', 'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH', 'XDG_CONFIG_HOME')
    secrets = ('OPENAI_API_KEY', 'LANGFUSE_SECRET_KEY', 'TRACE_TO_LANGFUSE',
               'ANTHROPIC_API_KEY', 'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_COUNT')
    for name in locations + secrets:
        monkeypatch.setenv(name, 'fixture-' + name)
    captured = []

    def child(args, **kwargs):
        captured.append(kwargs['env'])
        return type('Result', (), {'returncode': 0, 'stdout': '', 'stderr': ''})()

    monkeypatch.setattr(r.subprocess, 'run', child)
    for args in (['git', 'rev-parse', 'HEAD'], ['git', 'status', '--short', '--untracked-files=all'],
                 ['python', '--version'], ['git', 'other']):
        assert r.command(args, tmp_path)['exit'] == 0
    for env in captured[:2]:
        assert all(env[name] == 'fixture-' + name for name in locations)
    for env in captured[2:]:
        assert all(name not in env for name in locations)
    assert all(name not in env for env in captured for name in secrets)


def test_actual_publisher_dry_run(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location('c0_dry_publisher', HERE.parent / 'telemetry/langfuse-scores.py')
    publisher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publisher)
    monkeypatch.setattr(publisher, 'Client', lambda *a: pytest.fail('dry-run created client'))
    monkeypatch.setattr(publisher.urllib.request, 'urlopen', lambda *a, **k: pytest.fail('dry-run network'))
    run = {'session_id': 'offline-synthetic-c0', 'case': 'c0-wordstat', 'plugin_sha': None, 'prompt_sha256': None}
    run_path = tmp_path / 'run.json'
    run_path.write_text(json.dumps(run))
    parity = {'harness': 'offline-synthetic', 'composite': 0, 'quality': 0, 'adherence': 0,
              'adherence_uncapped': 0, 'consistency': 0, 'adherence_fraction': '0/1',
              'checks': [{'id': 'a.no_forbidden_git', 'status': 'pass', 'evidence': 'synthetic fixture'}]}
    parity_path = tmp_path / 'parity.json'
    parity_path.write_text(json.dumps(parity))
    scope = {'schema': 'geeky-eval.inputs/1', 'scope_id': 'offline-synthetic', 'kind': 'initial',
             'parent_scope_id': None, 'configuration': {'plugin_sha': None, 'prompt_sha256': None},
             'sources': [{'id': name, 'path': str(path), 'sha256': r.digest(path.read_bytes()), 'ancestry': []}
                         for name, path in [('run', run_path), ('parity', parity_path)]],
             'segments': [{'segment_id': 'fixture', 'authorization_reference': 'offline-fixture-only',
                           'start': '2026-01-01T00:00:00Z', 'end': '2026-01-01T00:00:01Z'}],
             'ownership': {'method': 'native', 'rule': 'synthetic fixture only'},
             'metric_default': {'scope_id': 'offline-synthetic', 'population': 'synthetic',
                                'source_ids': ['run', 'parity'], 'additive': False, 'complete': True}}
    scope_path = tmp_path / 'scope.json'
    scope_path.write_text(json.dumps(scope))
    assert publisher.main(['--run', str(tmp_path), '--parity', str(parity_path),
                           '--scope', str(scope_path), '--dry-run']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'preview' and result['scores_verified'] is False
    assert result['metadata']['input_sha256'] == r.digest(scope_path.read_bytes())
    assert result['expected'] and all(row['sessionId'] == 'offline-synthetic-c0' for row in result['expected'])
