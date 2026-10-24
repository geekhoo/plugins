"""Offline verified-build copying: fixture bytes only, no build or MXC execution."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


@pytest.fixture
def fixture(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'Program.cs').write_text('fixture source')
    (source / 'MxcClaude.csproj').write_text('fixture project')
    source_hash = ''.join(sha(path) for path in sorted(source.iterdir()))
    build = tmp_path / 'vetted-bin'
    build.mkdir()
    for name in ('MxcClaude.exe', 'MxcClaude.dll', 'Microsoft.Mxc.Sdk.dll',
                 'MxcClaude.deps.json', 'MxcClaude.runtimeconfig.json', 'MxcClaude.pdb'):
        (build / name).write_text('fixture bytes: ' + name)
    (build / '.source-hash').write_text(source_hash)
    runtime = build / 'runtimes/linux-x64/native/libmxc_ffi.so'
    runtime.parent.mkdir(parents=True)
    runtime.write_bytes(b'fixture native runtime')
    pin = tmp_path / 'pin.json'
    pin.write_text(json.dumps({'source_hash': source_hash,
        'exe_sha256': sha(build / 'MxcClaude.exe'), 'dll_sha256': sha(build / 'MxcClaude.dll')}))
    harness = tmp_path / 'copy.ps1'
    harness.write_text('''param($Helper,$Build,$State,$Source,$Pin,$Report)
$ErrorActionPreference='Stop'
. $Helper
Copy-VettedMxcBuild -BuildSource $Build -StateRoot $State -SourceDirectory $Source -PinPath $Pin -ReportPath $Report | ConvertTo-Json -Depth 8
''')
    return {'root': tmp_path, 'build': build, 'source': source, 'pin': pin,
            'state': tmp_path / 'private-state', 'report': tmp_path / 'provenance.json',
            'harness': harness}


def invoke(fixture):
    return subprocess.run([shutil.which('pwsh') or 'pwsh', '-NoProfile', '-File',
        str(fixture['harness']), '-Helper', str(HERE / 'copy-vetted-mxc-build.ps1'),
        '-Build', str(fixture['build']), '-State', str(fixture['state']),
        '-Source', str(fixture['source']), '-Pin', str(fixture['pin']),
        '-Report', str(fixture['report'])], capture_output=True, text=True)


def manifest(root):
    return {path.relative_to(root).as_posix(): sha(path)
            for path in root.rglob('*') if path.is_file()}


def test_verified_copy_preserves_complete_bin_and_provenance(fixture):
    before = manifest(fixture['build'])
    result = invoke(fixture)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['verified'] is True
    assert report['source_manifest'] == report['destination_manifest']
    assert manifest(fixture['state'] / 'bin') == before
    assert manifest(fixture['build']) == before
    assert Path(report['source_directory']) == fixture['build']
    assert Path(report['destination_directory']) == fixture['state'] / 'bin'
    assert json.loads(fixture['report'].read_text(encoding='utf-8-sig')) == report
    assert json.loads((fixture['state'] / 'mxc-build-provenance.json').read_text(encoding='utf-8-sig')) == report
    repeat = invoke(fixture)
    assert repeat.returncode != 0 and 'already exists' in repeat.stderr
    assert manifest(fixture['build']) == before
    assert manifest(fixture['state'] / 'bin') == before


@pytest.mark.parametrize('target', ['source', '.source-hash', 'MxcClaude.exe', 'MxcClaude.dll'])
def test_hash_mismatch_fails_before_creating_private_state(fixture, target):
    path = fixture['source'] / 'Program.cs' if target == 'source' else fixture['build'] / target
    path.write_text('tampered fixture')
    result = invoke(fixture)
    assert result.returncode != 0, result.stdout
    assert 'hash' in result.stderr or 'stamp' in result.stderr
    assert not fixture['state'].exists()
    assert not fixture['report'].exists()


@pytest.mark.parametrize('name', ['auth.json', 'runtimes/auth.json', 'credentials/secret.dll'])
def test_unexpected_files_are_rejected_before_copy(fixture, name):
    path = fixture['build'] / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('fixture must not be copied')
    result = invoke(fixture)
    assert result.returncode != 0 and 'Unexpected' in result.stderr
    assert not fixture['state'].exists()


def test_existing_destination_is_not_modified(fixture):
    fixture['state'].mkdir()
    sentinel = fixture['state'] / 'keep.txt'
    sentinel.write_text('keep')
    result = invoke(fixture)
    assert result.returncode != 0 and 'already exists' in result.stderr
    assert sentinel.read_text() == 'keep'
    assert not (fixture['state'] / 'bin').exists()


def test_missing_runtime_directory_is_rejected(fixture):
    shutil.rmtree(fixture['build'] / 'runtimes')
    result = invoke(fixture)
    assert result.returncode != 0 and 'Incomplete MXC build: runtimes' in result.stderr
    assert not fixture['state'].exists()


def test_wrapper_and_helper_powershell_parse():
    paths = [HERE / 'copy-vetted-mxc-build.ps1', HERE / 'run-native-probe.ps1',
             HERE.parents[1] / 'scripts/run-codex-baseline.ps1']
    command = '''$ErrorActionPreference='Stop'; foreach($path in $args){
$tokens=$null; $parseErrors=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw ($parseErrors|Out-String)}
}; 'PowerShell parse PASS'
'''
    # -CommandWithArgs keeps paths separate from the script's syntax.
    result = subprocess.run(['pwsh', '-NoProfile', '-CommandWithArgs', command,
                            *(str(path) for path in paths)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'PowerShell parse PASS' in result.stdout
