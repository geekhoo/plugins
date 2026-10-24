import importlib.util
import json
from pathlib import Path
import queue

import pytest

spec = importlib.util.spec_from_file_location('mock_codex', Path(__file__).with_name('mock_codex.py'))
mock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock)


def test_actual_cli_overrides_and_nested_merge(tmp_path):
    args = mock.parse_args(['--no-daemon', 'exec', '--json', '--cd', str(tmp_path),
        '--model', 'gpt-6.1-sol', '-c', 'agents={enabled=true}',
        '-c', 'agents.worker={config_file="role.toml"}', '--mock-scenario', 'env,guard'])
    assert args.cd == tmp_path
    assert args.config['agents'] == {'enabled': True, 'worker': {'config_file': 'role.toml'}}
    assert args.scenarios == ['env', 'guard']


def test_bad_toml_fails():
    with pytest.raises(Exception):
        mock.parse_args(['-c', 'broken={'])


def test_unknown_scenario_fails():
    with pytest.raises(SystemExit):
        mock.parse_args(['--mock-scenario', 'fictional'])


@pytest.mark.parametrize('passed', [True, False])
def test_trace_correlates_timestamped_rollout_and_zero_usage(tmp_path, capsys, passed):
    trace = mock.Trace(tmp_path, tmp_path)
    summary = trace.finish([{'name': 'unit', 'passed': passed}])
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[0]['thread_id'] == summary['thread_id']
    assert summary['tokens'] == 0 and summary['model_calls'] == 0
    assert summary['ok'] is passed
    assert events[-1]['type'] == ('turn.completed' if passed else 'turn.failed')
    entries = [json.loads(line) for line in trace.path.read_text().splitlines()]
    assert all(entry['timestamp'].endswith('Z') for entry in entries)
    assert entries[0]['payload']['id'] == summary['thread_id']
    assert trace.path.name.endswith(summary['thread_id'] + '.jsonl')
    usage = next(x for x in entries if x['payload'].get('type') == 'token_count')
    assert usage['payload']['info']['total_token_usage']['total_tokens'] == 0


def test_mcp_response_skips_notifications_and_rejects_error():
    messages = queue.Queue()
    for value in ['log line', '{"method":"notification"}', '{"id":3,"result":{"ok":true}}']:
        messages.put(value)
    assert mock.request_response(messages, 3) == {'ok': True}
    messages.put('{"id":4,"error":{"code":-1}}')
    with pytest.raises(RuntimeError, match='JSON-RPC error'):
        mock.request_response(messages, 4)


def test_main_reports_check_failure_without_claiming_completion(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'codex'))
    monkeypatch.setenv('TMPDIR', str(tmp_path))
    monkeypatch.setattr(mock, 'perform', lambda *args: (_ for _ in ()).throw(RuntimeError('deliberate failure')))
    report = tmp_path / 'report.json'
    previous = Path.cwd()
    try:
        assert mock.main(['--cd', str(tmp_path), '--mock-scenario', 'env', '--mock-report', str(report)]) == 1
    finally:
        monkeypatch.chdir(previous)
    data = json.loads(report.read_text())
    assert not data['passed'] and data['checks'][0]['detail'] == 'RuntimeError: deliberate failure'
    assert json.loads(capsys.readouterr().out.splitlines()[-1])['type'] == 'turn.failed'


def test_negative_control_is_an_explicit_failure():
    args = mock.parse_args(['--mock-scenario', 'fail'])
    assert args.scenarios == ['fail']
    with pytest.raises(RuntimeError, match='negative-control'):
        mock.perform('fail', args, Path('.'))


def test_skills_reads_unicode_role_as_utf8_with_optional_bom(tmp_path, monkeypatch):
    plugin = tmp_path / 'plugin'
    home = tmp_path / 'home'
    source = plugin / 'skills/unicode'
    target = home / '.agents/skills/unicode'
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    content = '# Unicode “role” → 测试\n'.encode('utf-8')
    (source / 'SKILL.md').write_bytes(content)
    (target / 'SKILL.md').write_bytes(content)
    (plugin / 'agents').mkdir()
    (plugin / 'agents/unicode.md').write_bytes(content)
    role = home / 'role.toml'
    role.write_text('developer_instructions="Unicode “role” → 测试"\n', encoding='utf-8-sig')
    args = mock.parse_args(['-c', 'agents={worker={config_file=' + json.dumps(str(role)) + '}}'])
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('CLAUDE_PLUGIN_ROOT', str(plugin))
    assert '1 registered roles readable' in mock.perform('skills', args, tmp_path)


def _telemetry_args(tmp_path, hook_body):
    hook = tmp_path / 'fake_tracer.py'
    hook.write_text(hook_body, encoding='utf-8')
    command = mock.shlex.join([mock.sys.executable, str(hook)]) if mock.os.name != 'nt' else \
        mock.subprocess.list2cmdline([mock.sys.executable, str(hook)])
    return mock.parse_args(['--cd', str(tmp_path), '-c', 'model_reasoning_summary="detailed"',
        '-c', 'hooks={Stop=[{hooks=[{type="command",command=' + json.dumps(command) + ',timeout=30}]}]}', 'prompt text'])


def test_telemetry_requires_the_tracer_to_record_the_turn(tmp_path, capsys):
    # A stand-in for the Langfuse tracer: reads the Stop payload and marks the turn delivered.
    args = _telemetry_args(tmp_path, 'import json,sys\np=json.load(sys.stdin)\n'
        'open(p["transcript_path"]+".langfuse","a").write(p["turn_id"]+"\\n")\n')
    trace = mock.Trace(tmp_path / 'codex', tmp_path, 'gpt-x', args.prompt)
    trace.complete_turn('done')
    assert 'delivered turn' in mock.check_telemetry(args, trace)
    kinds = [json.loads(line)['payload'].get('type') for line in trace.path.read_text().splitlines()]
    assert kinds.index('task_started') < kinds.index('user_message') and kinds[-1] == 'task_complete'


def test_telemetry_fails_when_nothing_is_delivered(tmp_path):
    args = _telemetry_args(tmp_path, 'import sys\nsys.stdin.read()\n')
    trace = mock.Trace(tmp_path / 'codex', tmp_path)
    trace.complete_turn('done')
    with pytest.raises(RuntimeError, match='not recorded'):
        mock.check_telemetry(args, trace)
