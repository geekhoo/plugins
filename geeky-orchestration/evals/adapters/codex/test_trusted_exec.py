"""Offline launch-contract tests; native catalogue and process are both stubbed."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('trusted_exec', Path(__file__).with_name('trusted-exec.py'))
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)


def setup_launch(tmp_path, monkeypatch, resolve, install=None):
    captured = {}
    overrides = ['model="gpt-6.1-sol"', 'model_reasoning_effort="high"',
                 'mcp_servers={geeky={command="fixture-python",args=["bootstrap.py"]}}']
    profile = tmp_path / 'profile.json'
    profile.write_text(json.dumps({'codex_config_overrides': overrides,
        'extra_args': ['--dangerously-bypass-hook-trust']}), encoding='utf-8')
    canonical = (Path(__file__).resolve().parents[2] / 'prompts/end-to-end.md').read_text(encoding='utf-8-sig')
    prompt = tmp_path / 'prompt.txt'
    prompt.write_text(canonical, encoding='utf-8', newline='\n')
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    output = tmp_path / 'catalogue'

    def load_module(module):
        captured['imported'] = True
        module.resolve_hook_trust = resolve
        module.install_local_plugin = install or (lambda *args: captured.update(installed=args))

    def native_spec(name, path):
        captured['module_path'] = Path(path)
        return SimpleNamespace(loader=SimpleNamespace(exec_module=load_module))

    def subprocess_fixture(command, **kwargs):
        captured.update(command=command, subprocess_options=kwargs)
        return SimpleNamespace(returncode=7)

    def runtime_proof(codex, root):
        captured['runtime_probe'] = (codex, root)
        return {'root': str(root), 'denial_verified': True, 'error_type': 'PermissionError',
                'winerror': 5, 'cli_version': '0.164.0', 'version_returncode': 0,
                'version_stderr': '', 'version_stdout': 'codex-cli 0.164.0\n'}

    monkeypatch.setattr(wrapper.importlib.util, 'spec_from_file_location', native_spec)
    monkeypatch.setattr(wrapper.importlib.util, 'module_from_spec', lambda spec: SimpleNamespace())
    monkeypatch.setattr(wrapper.subprocess, 'run', subprocess_fixture)
    monkeypatch.setattr(wrapper, 'capture_runtime_proof', runtime_proof)
    monkeypatch.setattr('sys.argv', ['trusted-exec.py', '--codex', 'fixture-only.exe',
        '--profile', str(profile), '--workspace', str(workspace), '--output', str(output),
        '--prompt-file', str(prompt), '--forbidden-skill-root', str(tmp_path / 'denied-root')])
    return captured, overrides, canonical, workspace, output


def test_launch_preserves_prompt_profile_and_sandbox_without_trust_bypass(tmp_path, monkeypatch):
    calls = []
    trust = 'hooks.state={native={trusted_hash="verified-hash",enabled=true}}'
    def resolve(*args):
        calls.append(args)
        return trust
    captured, overrides, canonical, workspace, output = setup_launch(tmp_path, monkeypatch, resolve)
    assert wrapper.main() == 7
    assert calls == [('fixture-only.exe', overrides, workspace, output)]
    assert captured['installed'] == ('fixture-only.exe', overrides, output)
    assert captured['module_path'].name == 'native-probe.py'
    expected = ['fixture-only.exe', '--no-daemon', 'exec', '--json', '--sandbox',
        'danger-full-access', '--ignore-user-config', '--ignore-rules', '--strict-config',
        '--cd', str(workspace)]
    for override in overrides:
        expected += ['-c', override]
    expected += ['-c', trust, canonical]
    assert captured['command'] == expected
    assert captured['command'][-1] == canonical
    assert '--ephemeral' not in captured['command']
    assert '--dangerously-bypass-hook-trust' not in captured['command']
    assert not any('model_provider=' in arg or 'model_providers.' in arg for arg in captured['command'])
    assert captured['subprocess_options'] == {'stdin': wrapper.subprocess.DEVNULL}
    assert captured['runtime_probe'] == ('fixture-only.exe', tmp_path / 'denied-root')
    assert json.loads((output / 'runtime-denial-proof.json').read_text())['denial_verified'] is True


def test_trust_resolution_failure_prevents_launch(tmp_path, monkeypatch):
    def reject(*args):
        raise RuntimeError('Unverified native hook hash')
    captured, _, _, _, _ = setup_launch(tmp_path, monkeypatch, reject)
    with pytest.raises(RuntimeError, match='Unverified native hook hash'):
        wrapper.main()
    assert captured['imported']
    assert 'command' not in captured


def test_plugin_install_failure_prevents_trust_and_inference(tmp_path, monkeypatch):
    def reject(*args):
        raise RuntimeError('Pinned local plugin installation failed')
    def unexpected_trust(*args):
        pytest.fail('Trust resolution must not follow failed installation')
    captured, _, _, _, _ = setup_launch(tmp_path, monkeypatch, unexpected_trust, install=reject)
    with pytest.raises(RuntimeError, match='Pinned local plugin installation failed'):
        wrapper.main()
    assert 'command' not in captured


@pytest.mark.parametrize(('denied', 'winerror', 'version', 'passed'), [
    (True, 5, '0.164.0', True), (True, 13, '0.164.0', False),
    (False, None, '0.164.0', False), (True, 5, '0.165.0', False)])
def test_runtime_probe_reads_only_explicit_root_and_pinned_version(tmp_path, monkeypatch, denied, winerror, version, passed):
    root = tmp_path / 'exact-denied-root'
    paths, commands = [], []
    def iterdir(path):
        paths.append(path)
        if denied:
            error = PermissionError('fixture denied')
            error.winerror = winerror
            raise error
        return iter([])
    def run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout='codex-cli ' + version, stderr='')
    monkeypatch.setattr(Path, 'iterdir', iterdir)
    monkeypatch.setattr(wrapper.subprocess, 'run', run)
    monkeypatch.setattr(wrapper.os, 'name', 'nt')   # Windows rule: only ERROR_ACCESS_DENIED counts
    proof = wrapper.capture_runtime_proof('fixture.exe', root)
    assert paths == [root] and commands == [['fixture.exe', '--version']]
    assert (proof['denial_verified'] and proof['cli_version'] == '0.164.0') is passed


@pytest.mark.parametrize(('error', 'passed'), [(FileNotFoundError, True), (PermissionError, True), (None, False)])
def test_runtime_probe_posix_accepts_hidden_or_denied_root(tmp_path, monkeypatch, error, passed):
    def iterdir(path):
        if error:
            raise error('fixture')
        return iter([])
    monkeypatch.setattr(Path, 'iterdir', iterdir)
    monkeypatch.setattr(wrapper.subprocess, 'run', lambda command, **kw: SimpleNamespace(returncode=0, stdout='codex-cli 0.164.0', stderr=''))
    monkeypatch.setattr(wrapper.os, 'name', 'posix')   # Bubblewrap/Seatbelt hide the root instead of denying it
    assert wrapper.capture_runtime_proof('codex', tmp_path / 'root')['denial_verified'] is passed


def test_failed_runtime_proof_is_saved_and_prevents_install_and_inference(tmp_path, monkeypatch):
    def unexpected(*args):
        pytest.fail('No install/trust/inference after failed runtime proof')
    captured, _, _, _, output = setup_launch(tmp_path, monkeypatch, unexpected, install=unexpected)
    monkeypatch.setattr(wrapper, 'capture_runtime_proof', lambda *args: {
        'root': str(tmp_path / 'denied-root'), 'denial_verified': False,
        'cli_version': '0.164.0', 'version_returncode': 0, 'version_stderr': ''})
    with pytest.raises(RuntimeError, match='Runtime denial/version proof failed'):
        wrapper.main()
    assert (output / 'runtime-denial-proof.json').is_file()
    assert 'command' not in captured
