"""Offline protocol tests: never bind a server or launch a Codex process."""
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tomllib

import pytest

spec = importlib.util.spec_from_file_location('native_probe', Path(__file__).with_name('native-probe.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_function_call_preserves_namespace_and_json_arguments():
    arguments = {'agent_type': 'geeky-coder', 'message': 'Unicode “测试”'}
    result = probe.item('spawn_agent', arguments, 'call-1', 'collaboration')
    assert result['type'] == 'function_call'
    assert result['namespace'] == 'collaboration'
    assert result['name'] == 'spawn_agent' and result['call_id'] == 'call-1'
    assert isinstance(result['arguments'], str)
    assert json.loads(result['arguments']) == arguments
    assert 'input' not in result


@pytest.mark.parametrize(('name', 'namespace', 'raw'), [
    ('apply_patch', None, '*** Begin Patch\n*** Add File: fixture.txt\n+测试\n*** End Patch'),
    ('exec', 'functions', 'const result = await tools.geeky_check_commit({params:{message:"Tasks: T1"}}); text(result);'),
])
def test_custom_tool_uses_verbatim_raw_input(name, namespace, raw):
    result = probe.item(name, raw, 'custom-1', namespace)
    assert result['type'] == 'custom_tool_call'
    assert result['input'] == raw
    assert result['name'] == name and result['call_id'] == 'custom-1'
    assert 'arguments' not in result
    if namespace is None:
        assert 'namespace' not in result
    else:
        assert result['namespace'] == namespace
    assert json.loads(json.dumps(result))['input'] == raw


def test_final_assistant_message_is_responses_output_text():
    result = probe.message('CP2_NATIVE_OK')
    assert result['type'] == 'message' and result['role'] == 'assistant'
    assert result['content'] == [{'type': 'output_text', 'text': 'CP2_NATIVE_OK'}]
    assert result['id']
    assert 'call_id' not in result


@pytest.mark.parametrize(('cli_version', 'version_matches'), [
    ('0.164.0', True),
    ('0.165.0', False),
    ('0.164.0-alpha.1', False),
])
@pytest.mark.parametrize('variant', probe.VARIANTS)
def test_main_forces_auth_free_loopback_provider_without_network_or_process(
        tmp_path, monkeypatch, capsys, cli_version, version_matches, variant):
    captured = {}

    class Server:
        def __init__(self, address, handler):
            captured['bind'] = address
            self.server_port = 54321
        def serve_forever(self):
            raise AssertionError('No actual HTTP serving allowed in this unit test')
        def shutdown(self):
            captured['shutdown'] = True
        def server_close(self):
            captured['closed'] = True

    class Thread:
        def __init__(self, **kwargs):
            pass
        def start(self):
            pass

    def subprocess_fixture(command, **kwargs):
        captured.setdefault('process_calls', []).append(command)
        if command == ['fixture-only.exe', '--version']:
            return SimpleNamespace(returncode=0, stdout=f'codex-cli {cli_version}\n', stderr='')
        assert command[:3] == ['fixture-only.exe', '--no-daemon', 'exec']
        captured['command'] = command
        return SimpleNamespace(returncode=0, stdout='CP2_NATIVE_OK', stderr='')

    def install_fixture(codex, overrides, output):
        (output / 'native-plugin-install-stderr.txt').write_text('', encoding='utf-8')

    def trust_fixture(codex, overrides, workspace, output):
        (output / 'native-hook-catalog-stderr.txt').write_text('', encoding='utf-8')
        return 'hooks.state={}'

    profile = tmp_path / 'profile.json'
    profile.write_text(json.dumps({'codex_config_overrides': ['model="fixture"'], 'extra_args': []}), encoding='utf-8')
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    output = tmp_path / 'output'
    monkeypatch.setattr(probe, 'ThreadingHTTPServer', Server)
    monkeypatch.setattr(probe.threading, 'Thread', Thread)
    monkeypatch.setattr(probe.subprocess, 'run', subprocess_fixture)
    monkeypatch.setattr(probe, 'install_local_plugin', install_fixture)
    monkeypatch.setattr(probe, 'resolve_hook_trust', trust_fixture)
    arguments = ['native-probe.py', '--codex', 'fixture-only.exe',
        '--profile', str(profile), '--workspace', str(workspace), '--output', str(output)]
    if variant != 'default':
        arguments += ['--variant', variant]
    monkeypatch.setattr('sys.argv', arguments)
    # No requests were delivered: missing native evidence must fail closed.
    assert probe.main() == 1
    command = captured['command']
    overrides = [command[i + 1] for i, arg in enumerate(command[:-1]) if arg == '-c']
    combined = tomllib.loads('\n'.join(overrides))
    provider = combined['model_providers']['cp2_fixture']
    assert captured['bind'] == ('127.0.0.1', 0)
    assert combined['model_provider'] == 'cp2_fixture'
    assert provider['base_url'] == 'http://127.0.0.1:54321/v1'
    assert provider['requires_openai_auth'] is False
    assert provider['supports_websockets'] is False
    assert provider['request_max_retries'] == provider['stream_max_retries'] == 0
    assert captured['shutdown'] and captured['closed']
    assert len(captured['process_calls']) == 2
    assert captured['process_calls'][0] == ['fixture-only.exe', '--version']
    report = json.loads((output / 'native-summary.json').read_text(encoding='utf-8'))
    assert report['paid_model_calls'] == 0 and not report['ok']
    assert report['local_fixture_requests'] == 0
    assert report['cli_version'] == cli_version
    checks = {check['name']: check['passed'] for check in report['checks']}
    assert checks['native_version'] is version_matches
    assert checks['native_user_skills_denied'] is False
    assert checks['native_skill_discovery'] is False
    assert checks['native_skill_invoked'] is False
    assert report['functional_ok'] is False
    assert report['variant'] == variant
    assert report['roles'] == probe.variant_roles(variant)
    assert report['spawn_calls'] == []
    assert report['raw_diagnostics'] == {'plugin-install': '', 'hook-catalogue': '', 'exec': ''}
    assert len(report['checks']) == 21
    capsys.readouterr()


def fake_catalog(monkeypatch, responses, stderr='', stuck_stderr=False, broken_stderr=False):
    captured = {'readers': [], 'joined': []}

    class BrokenPipe:
        def __iter__(self):
            raise OSError('fixture pipe read failure')

    class Input(io.StringIO):
        def close(self):
            captured['requests'] = [json.loads(line) for line in self.getvalue().splitlines()]
            super().close()

    class Process:
        def __init__(self, command, **kwargs):
            captured.update(command=command, options=kwargs)
            self.stdin = Input()
            self.stdout = io.StringIO('\n'.join(json.dumps(r) for r in responses) + '\n')
            self.stderr = BrokenPipe() if broken_stderr else io.StringIO(stderr)
        def wait(self, timeout):
            captured['waited'] = True
            return 0
        def kill(self):
            raise AssertionError('Finite fixture process should exit cleanly')

    class Thread:
        def __init__(self, target, args=(), **kwargs):
            self.target = target
            self.args = args
            self.index = len(captured['readers'])
            self.alive = True
            captured['readers'].append(self)
        def start(self):
            if self.index == 0:
                self.target(*self.args)
                self.alive = False
        def join(self, timeout):
            assert captured['waited'], 'Readers must drain after process reaping'
            captured['joined'].append(self.index)
            if self.alive and not stuck_stderr:
                self.target(*self.args)
                self.alive = False
        def is_alive(self):
            return self.alive

    monkeypatch.setattr(probe.subprocess, 'Popen', Process)
    monkeypatch.setattr(probe.threading, 'Thread', Thread)
    return captured


def test_hook_catalog_trust_uses_native_key_hash_and_auth_free_home(tmp_path, monkeypatch):
    hook = {'eventName': 'PreToolUse', 'command': 'python guard-bridge.py --guard fixture.py',
            'key': 'native-hook:"fixture"', 'currentHash': 'native-hash-value'}
    captured = fake_catalog(monkeypatch, [
        {'id': 1, 'result': {}}, {'method': 'notice'},
        {'id': 2, 'result': {'data': [{'hooks': [hook,
            {'eventName': 'Stop', 'command': 'other-hook', 'key': 'ignore', 'currentHash': 'ignore'}]}]}}])
    override = probe.resolve_hook_trust('fixture.exe', ['model="fixture"'], tmp_path, tmp_path)
    states = tomllib.loads(override)['hooks']['state']
    assert states == {'native-hook:"fixture"': {'trusted_hash': 'native-hash-value', 'enabled': True}}
    assert captured['command'] == ['fixture.exe', '--no-daemon', 'app-server', '--stdio', '--strict-config', '-c', 'model="fixture"']
    assert captured['options']['env']['CODEX_HOME'] == str(tmp_path / 'hook-catalog-home')
    assert [r['method'] for r in captured['requests']] == ['initialize', 'initialized', 'hooks/list']
    assert captured['requests'][-1]['params']['cwds'] == [str(tmp_path)]
    assert captured['waited']
    assert captured['joined'] == [0, 1]
    assert (tmp_path / 'native-hook-catalog.json').is_file()


def test_hook_catalog_preserves_stderr_delivered_after_process_exit(tmp_path, monkeypatch):
    hook = {'eventName': 'PreToolUse', 'command': 'guard-bridge.py',
            'key': 'fixture-key', 'currentHash': 'fixture-hash'}
    captured = fake_catalog(monkeypatch, [{'id': 1, 'result': {}},
        {'id': 2, 'result': {'data': [{'hooks': [hook]}]}}], stderr='ERROR late diagnostic\n')
    probe.resolve_hook_trust('fixture.exe', [], tmp_path, tmp_path)
    assert captured['joined'] == [0, 1]
    assert (tmp_path / 'native-hook-catalog-stderr.txt').read_text() == 'ERROR late diagnostic\n'


@pytest.mark.parametrize(('options', 'error'), [
    ({'stuck_stderr': True}, 'pipe readers did not drain'),
    ({'broken_stderr': True}, 'pipe read failed'),
])
def test_hook_catalog_rejects_incomplete_stderr_capture(tmp_path, monkeypatch, options, error):
    hook = {'eventName': 'PreToolUse', 'command': 'guard-bridge.py',
            'key': 'fixture-key', 'currentHash': 'fixture-hash'}
    captured = fake_catalog(monkeypatch, [{'id': 1, 'result': {}},
        {'id': 2, 'result': {'data': [{'hooks': [hook]}]}}], **options)
    with pytest.raises(RuntimeError, match=error):
        probe.resolve_hook_trust('fixture.exe', [], tmp_path, tmp_path)
    assert captured['waited'] and captured['joined'] == [0, 1]
    assert (tmp_path / 'native-hook-catalog-stderr.txt').is_file()


@pytest.mark.parametrize('hooks', [[], [
    {'eventName': 'PreToolUse', 'command': 'guard-bridge.py', 'key': 'a', 'currentHash': 'a'},
    {'eventName': 'PreToolUse', 'command': 'guard-bridge.py', 'key': 'b', 'currentHash': 'b'},
]])
def test_hook_catalog_rejects_missing_or_ambiguous_guard(tmp_path, monkeypatch, hooks):
    captured = fake_catalog(monkeypatch, [{'id': 1, 'result': {}},
        {'id': 2, 'result': {'data': [{'hooks': hooks}]}}])
    with pytest.raises(RuntimeError, match='exactly one vetted'):
        probe.resolve_hook_trust('fixture.exe', [], tmp_path, tmp_path)
    assert captured['waited']


def test_hook_catalog_rpc_error_fails_and_reaps_process(tmp_path, monkeypatch):
    captured = fake_catalog(monkeypatch, [{'id': 1, 'error': {'code': -1, 'message': 'fixture failure'}}])
    with pytest.raises(RuntimeError, match='catalogue RPC failed'):
        probe.resolve_hook_trust('fixture.exe', [], tmp_path, tmp_path)
    assert captured['waited']


@pytest.mark.parametrize('exit_code', [0, 1])
def test_local_plugin_install_preserves_overrides_and_records_failure(tmp_path, monkeypatch, exit_code):
    captured = {}
    def fixture(command, **kwargs):
        captured.update(command=command, options=kwargs)
        return SimpleNamespace(returncode=exit_code, stdout='{"fixture":true}', stderr='fixture diagnostic')
    monkeypatch.setattr(probe.subprocess, 'run', fixture)
    overrides = ['model="fixture"', 'marketplaces={geeky-eval={source_type="local",source="pinned-export"}}']
    if exit_code:
        with pytest.raises(RuntimeError, match='Pinned local plugin installation failed'):
            probe.install_local_plugin('fixture.exe', overrides, tmp_path)
    else:
        probe.install_local_plugin('fixture.exe', overrides, tmp_path)
    assert captured['command'] == ['fixture.exe', '--no-daemon', 'plugin', 'add',
        'geeky-orchestration@geeky-eval', '--json', '-c', overrides[0], '-c', overrides[1]]
    assert captured['options']['stdin'] == probe.subprocess.DEVNULL
    assert captured['options']['timeout'] == 45
    assert (tmp_path / 'native-plugin-install.json').read_text(encoding='utf-8') == '{"fixture":true}'
    assert (tmp_path / 'native-plugin-install-stderr.txt').read_text(encoding='utf-8') == 'fixture diagnostic'


def test_skill_discovery_rejects_generic_instruction_boilerplate():
    inputs = [{'role': 'developer', 'content': [{'type': 'input_text',
               'text': 'Read SKILL.md and use geeky-plan for planning.'}]}]
    assert set(probe.missing_skill_paths(inputs)) == set(probe.EXPECTED_SKILLS)
    assert len(probe.EXPECTED_SKILLS) == 8


def test_skill_discovery_rejects_partial_catalogue():
    available = probe.EXPECTED_SKILLS[:-1]
    inputs = [{'content': [{'type': 'input_text',
        'text': '\n'.join(f'/isolated/skills/{name}/SKILL.md' for name in available)}]}]
    assert probe.missing_skill_paths(inputs) == [probe.EXPECTED_SKILLS[-1]]


@pytest.mark.parametrize('separator', ['/', '\\'])
def test_skill_discovery_accepts_all_exact_alias_paths(separator):
    inputs = [{'content': [{'type': 'input_text',
        'text': separator.join(['C:', 'isolated', 'skills', name, 'SKILL.md'])}]}
              for name in probe.EXPECTED_SKILLS]
    assert probe.missing_skill_paths(inputs) == []


def task_message(thread, kind='NEW_TASK', payload=None):
    path, marker = probe.THREADS[thread]
    parent = path.rsplit('/', 1)[0]
    return {'type': 'agent_message',
            'author': parent if kind == 'NEW_TASK' else path,
            'recipient': path if kind == 'NEW_TASK' else parent,
            'content': [{'type': 'input_text', 'text': f'Message Type: {kind}\nTask name: {path}\nPayload:\n'},
                        {'type': 'encrypted_content', 'encrypted_content': payload or marker + '.'}]}


def native_request(thread='main', ancestor_inputs=None):
    inputs = list(ancestor_inputs or [{'type': 'message', 'role': 'user',
        'content': [{'type': 'input_text', 'text': 'CP2_NATIVE_MAIN. Local fixture.'}]}])
    if thread != 'main':
        inputs.append(task_message(thread))
    return {'model': 'gpt-6.1-sol' if thread == 'main' else 'gpt-6-luna',
            'reasoning': {'effort': 'medium' if thread == 'main' else 'max'}, 'input': inputs}


def test_routes_latest_addressed_task_despite_inherited_markers_and_calls():
    main = native_request()
    main['input'].append(probe.item('spawn_agent', {
        'message': 'CP2_NATIVE_CHILD_ONLY. CP2_NATIVE_GRANDCHILD_ONLY.'}, 'history', 'collaboration'))
    assert probe.request_thread(main) == 'main'
    child = native_request('child', main['input'])
    grandchild = native_request('grandchild', child['input'])
    fallback = native_request('default', child['input'])
    assert probe.request_thread(child) == 'child'
    assert probe.request_thread(grandchild) == 'grandchild'
    assert probe.request_thread(fallback) == 'default'
    # A child's final answer delivered to its parent cannot route the parent as a child.
    main['input'].append(task_message('child', 'FINAL_ANSWER', 'CP2_NATIVE_CHILD_OK'))
    assert probe.request_thread(main) == 'main'
    assert probe.request_thread({'input': [{'role': 'assistant', 'content': [
        {'text': 'CP2_NATIVE_CHILD_ONLY'}]}]}) is None


@pytest.mark.parametrize('variant', probe.VARIANTS)
def test_script_preserves_tools_and_requires_nested_and_default_final_answers(tmp_path, variant):
    state = probe.fixture_state(variant)
    roles = probe.variant_roles(variant)
    main = native_request()
    outputs = [probe.fixture_output(main, state, tmp_path) for _ in range(4)]
    assert [output['name'] for output in outputs] == ['apply_patch', 'exec_command', 'exec', 'spawn_agent']
    spawn = json.loads(outputs[-1]['arguments'])
    assert spawn['agent_type'] == roles['child']
    assert 'model' not in spawn and 'reasoning_effort' not in spawn
    assert probe.fixture_output(main, state, tmp_path)['name'] == 'wait_agent'
    child = native_request('child', main['input'])
    nested = probe.fixture_output(child, state, tmp_path)
    nested_args = json.loads(nested['arguments'])
    assert nested_args['agent_type'] == roles['grandchild']
    assert 'model' not in nested_args and 'reasoning_effort' not in nested_args
    assert probe.fixture_output(child, state, tmp_path)['name'] == 'wait_agent'
    grandchild = native_request('grandchild', child['input'])
    assert probe.fixture_output(grandchild, state, tmp_path)['content'][0]['text'] == 'CP2_NATIVE_GRANDCHILD_OK'
    child['input'].append(task_message('grandchild', 'FINAL_ANSWER', 'CP2_NATIVE_GRANDCHILD_OK'))
    fallback = probe.fixture_output(child, state, tmp_path)
    fallback_args = json.loads(fallback['arguments'])
    assert fallback['name'] == 'spawn_agent'
    if variant == 'default':
        assert set(fallback_args) == {'task_name', 'message'}
    else:
        assert fallback_args['agent_type'] == 'default'
    for args in (spawn, nested_args, fallback_args):
        if variant == 'paid-roles-forkall':
            assert args['fork_turns'] == 'all'
        else:
            assert 'fork_turns' not in args
    assert fallback_args['task_name'] == 'cp2_native_default'
    assert probe.fixture_output(child, state, tmp_path)['name'] == 'wait_agent'
    default = native_request('default', child['input'])
    assert probe.fixture_output(default, state, tmp_path)['content'][0]['text'] == 'CP2_NATIVE_DEFAULT_OK'
    child['input'].append(task_message('default', 'FINAL_ANSWER', 'CP2_NATIVE_DEFAULT_OK'))
    assert probe.fixture_output(child, state, tmp_path)['content'][0]['text'] == 'CP2_NATIVE_CHILD_OK'
    # Actual request existence alone never releases the main wait.
    assert probe.fixture_output(main, state, tmp_path)['name'] == 'wait_agent'
    main['input'].append(task_message('child', 'FINAL_ANSWER', 'CP2_NATIVE_CHILD_OK'))
    assert probe.fixture_output(main, state, tmp_path)['content'][0]['text'] == 'CP2_NATIVE_OK'
    assert state['child_requests'] > 0 and state['grandchild_requests'] == state['default_requests'] == 1
    assert state['errors'] == []


@pytest.mark.parametrize('thread', ['main', 'child'])
def test_descendant_waits_are_bounded_and_fail_closed(tmp_path, thread):
    state = probe.fixture_state()
    if thread == 'main':
        state['main_step'] = 4
    else:
        state['child_requests'] = 1  # Its spawn has already been dispatched.
    request = native_request(thread)
    for _ in range(probe.MAX_WAITS):
        waiting = probe.fixture_output(request, state, tmp_path)
        assert waiting['name'] == 'wait_agent'
        assert json.loads(waiting['arguments']) == {'timeout_ms': 10000}
    assert probe.fixture_output(request, state, tmp_path)['content'][0]['text'] == 'CP2_NATIVE_WAIT_FAILED'
    assert state['errors'] == [thread + ' exhausted bounded descendant waits']


def test_completion_requires_correct_sender_recipient_and_final_answer():
    child = native_request('child')
    row = task_message('grandchild', 'FINAL_ANSWER', 'CP2_NATIVE_GRANDCHILD_OK')
    child['input'].append(row)
    assert probe.child_completed(child, 'child', 'grandchild', 'CP2_NATIVE_GRANDCHILD_OK')
    row['recipient'] = '/root'
    assert not probe.child_completed(child, 'child', 'grandchild', 'CP2_NATIVE_GRANDCHILD_OK')
    row['recipient'] = probe.THREADS['child'][0]
    row['content'][0]['text'] = 'Message Type: MESSAGE\n'
    assert not probe.child_completed(child, 'child', 'grandchild', 'CP2_NATIVE_GRANDCHILD_OK')


def independent_profile(tmp_path):
    roles = {}
    for name in sorted(set(probe.ROLES.values()) | {'code-explorer'}):
        role = tmp_path / (name + '.toml')
        role.write_text('developer_instructions=' + json.dumps('Exact registered ' + name + ' instructions.'), encoding='utf-8')
        roles[name] = {'config_file': str(role)}
    overrides = ['model="gpt-6.1-sol"', 'model_reasoning_effort="medium"',
                 'developer_instructions="Exact orchestrator instructions."']
    overrides += ['agents.' + role + '.config_file=' + json.dumps(data['config_file'])
                  for role, data in roles.items()]
    return {'codex_config_overrides': overrides, 'model': 'gpt-6.1-sol', 'reasoning': 'medium',
            'worker_model': 'gpt-6-luna', 'worker_reasoning': 'max', 'model_matrix': {
                'orchestrator': {'model': 'gpt-6.1-sol', 'reasoning': 'medium'},
                'workers': {'model': 'gpt-6-luna', 'reasoning': 'max', 'scope': 'all-descendants'}}}


def evidence_requests(instructions):
    requests = []
    for thread in probe.THREADS:
        request = native_request(thread)
        bodies = [instructions['main']]
        if thread != 'main':
            bodies.append(instructions['child'])
        if thread == 'grandchild':
            bodies.append(instructions['grandchild'])
        request['input'].append({'role': 'developer', 'content': [
            {'type': 'input_text', 'text': body} for body in bodies]})
        requests.append(request)
    return requests


@pytest.mark.parametrize('variant', probe.VARIANTS)
def test_independent_model_matrix_and_registered_role_instructions(tmp_path, variant):
    expected, instructions = probe.model_expectations(independent_profile(tmp_path), variant)
    for thread, role in probe.variant_roles(variant).items():
        assert instructions[thread] == 'Exact registered ' + role + ' instructions.'
    requests = evidence_requests(instructions)
    evidence = probe.request_evidence(requests, expected, instructions)
    assert all(row['model_reasoning_ok'] for row in evidence.values())
    assert all(evidence[thread]['instructions_ok'] for thread in ('main', 'child', 'grandchild'))
    assert evidence['grandchild']['requests'][0]['request_index'] == 2
    assert expected['main'] == {'model': 'gpt-6.1-sol', 'reasoning': 'medium'}
    assert expected['child'] == expected['grandchild'] == expected['default'] == {'model': 'gpt-6-luna', 'reasoning': 'max'}


@pytest.mark.parametrize('thread', list(probe.THREADS))
@pytest.mark.parametrize(('key', 'bad_value'), [('model', 'gpt-6.1-sol-wrong'), ('reasoning', 'high')])
def test_request_evidence_rejects_any_request_with_wrong_model_or_reasoning(tmp_path, thread, key, bad_value):
    expected, instructions = probe.model_expectations(independent_profile(tmp_path))
    requests = evidence_requests(instructions)
    bad = native_request(thread)
    if key == 'reasoning':
        bad['reasoning']['effort'] = bad_value
    else:
        bad[key] = bad_value
    requests.append(bad)
    evidence = probe.request_evidence(requests, expected, instructions)
    assert not evidence[thread]['model_reasoning_ok']
    assert len(evidence[thread]['requests']) == 2


def test_request_evidence_rejects_missing_and_inherited_only_role_layers(tmp_path):
    expected, instructions = probe.model_expectations(independent_profile(tmp_path))
    assert not any(row['model_reasoning_ok'] for row in probe.request_evidence([], expected, instructions).values())
    request = native_request('grandchild')
    request['input'].append({'role': 'developer', 'content': [
        {'text': instructions['main']}, {'text': instructions['child']}]})
    assert not probe.request_evidence([request], expected, instructions)['grandchild']['instructions_ok']
    # A complete role body in a user/tool message cannot prove role registration.
    request['input'].append({'role': 'user', 'content': [{'text': instructions['grandchild']}]})
    assert not probe.request_evidence([request], expected, instructions)['grandchild']['instructions_ok']


def test_model_matrix_rejects_disagreement_and_legacy_fields_remain_compatible(tmp_path):
    profile = independent_profile(tmp_path)
    profile['model_matrix']['workers']['reasoning'] = 'medium'
    with pytest.raises(ValueError, match='matrix disagrees'):
        probe.model_expectations(profile)
    expected, instructions = probe.model_expectations({'codex_config_overrides': [
        'model="fixture"', 'model_reasoning_effort="high"']})
    assert expected['main'] == expected['child'] == {'model': 'fixture', 'reasoning': 'high'}
    assert instructions == {'main': '', 'child': '', 'grandchild': ''}


def test_variant_selection_is_local_and_rejects_unknown_variants():
    baseline = dict(probe.ROLES)
    changed = probe.variant_roles('paid-roles-forkall')
    changed['child'] = 'unrelated'
    assert probe.variant_roles('default') == baseline
    assert probe.variant_roles('paid-roles-defaultfork') == {
        'child': 'geeky-orchestrator', 'grandchild': 'code-explorer'}
    assert probe.ROLES == baseline
    with pytest.raises(ValueError, match='Unknown native probe variant'):
        probe.fixture_state('unknown')


@pytest.mark.parametrize('variant', probe.VARIANTS[1:])
def test_paid_variant_requires_actual_code_explorer_registered_body(tmp_path, variant):
    profile = independent_profile(tmp_path)
    expected, instructions = probe.model_expectations(profile, variant)
    request = native_request('grandchild')
    request['input'].append({'role': 'developer', 'content': [
        {'text': instructions['main']}, {'text': instructions['child']}]})
    assert not probe.request_evidence([request], expected, instructions)['grandchild']['instructions_ok']
    request['input'][-1]['content'].append({'text': instructions['grandchild']})
    assert probe.request_evidence([request], expected, instructions)['grandchild']['instructions_ok']
    profile['codex_config_overrides'] = [line for line in profile['codex_config_overrides']
                                         if not line.startswith('agents.code-explorer.')]
    expected, missing_instructions = probe.model_expectations(profile, variant)
    assert missing_instructions['grandchild'] == ''
    assert not probe.request_evidence([request], expected, missing_instructions)['grandchild']['instructions_ok']


def test_spawn_report_uses_request_arguments_and_deduplicates_history():
    main_spawn = probe.item('spawn_agent', {'agent_type': 'geeky-orchestrator',
        'task_name': 'cp2_native_child', 'fork_turns': 'all'}, 'cp2_spawn', 'collaboration')
    nested_spawn = probe.item('spawn_agent', {'agent_type': 'code-explorer',
        'task_name': 'cp2_native_grandchild', 'fork_turns': 'all'}, 'cp2_nested_spawn', 'collaboration')
    requests = [{'input': [main_spawn]}, {'input': [main_spawn, nested_spawn]}]
    assert probe.request_spawn_calls(requests) == [
        {'call_id': 'cp2_spawn', 'request_index': 0, 'arguments': json.loads(main_spawn['arguments'])},
        {'call_id': 'cp2_nested_spawn', 'request_index': 1, 'arguments': json.loads(nested_spawn['arguments'])}]


@pytest.mark.parametrize('role', ['code-reviewer', 'code-architect-reviewer'])
def test_reviewer_probe_checks_distinct_effort_and_actual_role_dispatch(tmp_path, role):
    profile = independent_profile(tmp_path)
    profile.update(reasoning='high', worker_model='gpt-6.1-sol', worker_reasoning='medium', reviewer_reasoning='xhigh')
    profile['model_matrix'] = {
        'orchestrator': {'model': 'gpt-6.1-sol', 'reasoning': 'high'},
        'workers': {'model': 'gpt-6.1-sol', 'reasoning': 'medium', 'scope': 'all-descendants-except-reviewers'},
        'reviewers': {'model': 'gpt-6.1-sol', 'reasoning': 'xhigh',
                     'roles': ['code-reviewer', 'code-architect-reviewer'], 'scope': 'review-assignments'}}
    role_file = tmp_path / (role + '.toml')
    role_file.write_text('developer_instructions=' + json.dumps('Reviewer ' + role))
    profile['codex_config_overrides'].append('agents.' + role + '.config_file=' + json.dumps(str(role_file)))
    expected, instructions = probe.model_expectations(profile, reviewer_role=role)
    assert expected['main']['reasoning'] == 'high'
    assert expected['child'] == expected['default'] == {'model': 'gpt-6.1-sol', 'reasoning': 'medium'}
    assert expected['grandchild'] == {'model': 'gpt-6.1-sol', 'reasoning': 'xhigh'}
    assert instructions['grandchild'] == 'Reviewer ' + role
    state = probe.fixture_state()
    state['roles'] = probe.probe_roles(profile, reviewer_role=role)
    spawn = probe.fixture_output(native_request('child'), state, tmp_path)
    assert json.loads(spawn['arguments'])['agent_type'] == role
    requests = evidence_requests(instructions)
    for request, thread in zip(requests, probe.THREADS):
        request['model'] = expected[thread]['model']
        request['reasoning']['effort'] = expected[thread]['reasoning']
    assert all(row['model_reasoning_ok'] for row in probe.request_evidence(requests, expected, instructions).values())
    requests[2]['reasoning']['effort'] = 'medium'
    assert not probe.request_evidence(requests, expected, instructions)['grandchild']['model_reasoning_ok']
    profile['model_matrix']['reviewers']['reasoning'] = 'medium'
    with pytest.raises(ValueError, match='reviewer matrix'):
        probe.model_expectations(profile, reviewer_role=role)


def test_reviewer_probe_rejects_unregistered_role_before_launch(tmp_path):
    with pytest.raises(ValueError, match='registered reviewer'):
        probe.model_expectations(independent_profile(tmp_path), reviewer_role='code-reviewer')
