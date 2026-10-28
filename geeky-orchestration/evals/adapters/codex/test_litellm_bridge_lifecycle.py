"""Host listener lifecycle against a local fake upstream; no evaluations/inference."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

HERE = Path(__file__).resolve().parent
PWSH = shutil.which('pwsh')
WINDOWS_VENV_PYTHON = Path('C:/repos/.eval-tools/agent-py/Scripts/python.exe')
pytestmark = pytest.mark.skipif(not PWSH, reason='PowerShell 7 required')


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def clean_env():
    keep = {'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'TEMP', 'TMP',
            'SYSTEMDRIVE', 'USERPROFILE', 'HOME', 'HOMEDRIVE', 'HOMEPATH'}
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    env.update(PYTHONDONTWRITEBYTECODE='1', LITELLM_PROXY_API_KEY='offline-listener-fixture')
    return env


@pytest.mark.parametrize('python_executable', [sys.executable, pytest.param(
    str(WINDOWS_VENV_PYTHON), id='actual-windows-venv-redirector',
    marks=pytest.mark.skipif(os.name != 'nt' or not WINDOWS_VENV_PYTHON.is_file(),
                             reason='Recorded Windows venv launcher unavailable'))])
def test_listener_routes_and_always_stops(tmp_path, python_executable):
    captured = []

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            captured.append((self.path, body))
            response = {'id': 'resp_fixture', 'status': 'completed', 'output': [{
                'type': 'function_call', 'name': body['tools'][0]['name'],
                'call_id': 'call_fixture', 'arguments': '{"message":"OK"}'}]}
            raw = json.dumps(response).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    state = tmp_path / 'bridge state with spaces'
    wrapper = tmp_path / 'lifecycle.ps1'
    wrapper.write_text(f'''$ErrorActionPreference='Stop'
. {quote(HERE / 'litellm-bridge.ps1')}
$bridge=$null
try {{
    $bridge=Start-CodexLitellmBridge -Python {quote(python_executable)} -AdapterDirectory {quote(HERE)} -StateDirectory {quote(state)} -UpstreamBaseUrl 'http://127.0.0.1:{upstream.server_port}'
    $ready=Get-Content -LiteralPath (Join-Path {quote(state)} 'ready.json') -Raw | ConvertFrom-Json
    if($ready.pid -ne $bridge.Process.Id){{throw 'Readiness PID must equal the owned native process'}}
    $body=@{{model='fixture';input=@(@{{type='agent_message';author='/root';recipient='/root/test';content=@(@{{type='input_text';text='synthetic task'}})}});tools=@(@{{type='namespace';name='collaboration';tools=@(@{{type='function';name='send_message';parameters=@{{type='object';properties=@{{message=@{{type='string';encrypted=$true}}}}}}}})}})}} | ConvertTo-Json -Depth 15
    $result=Invoke-RestMethod -Uri ($bridge.Record.base_url+'/responses') -Method Post -Body $body -ContentType 'application/json' -Headers @{{Authorization='Bearer offline-listener-fixture'}}
    @{{record=$bridge.Record;response=$result}} | ConvertTo-Json -Depth 15
}} finally {{if($bridge){{Stop-CodexLitellmBridge -Bridge $bridge}}}}
''', encoding='utf-8')
    try:
        result = subprocess.run([PWSH, '-NoProfile', '-File', str(wrapper)], env=clean_env(),
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report['record']['provider_requests_on_start'] == 0
        assert report['record']['protocol'] == 'codex-v2-to-responses-v1-wire'
        assert report['response']['output'][0]['namespace'] == 'collaboration'
        assert report['response']['output'][0]['encrypted_function_args'] == []
        assert len(captured) == 1 and captured[0][0] == '/v1/responses'
        assert captured[0][1]['input'][0]['type'] == 'message'
        assert captured[0][1]['tools'][0]['type'] == 'function'
        assert not (state / 'ready.json').exists()
        assert json.loads((state / 'stopped.json').read_text())['exited']
        from urllib.parse import urlsplit
        uri = urlsplit(report['record']['base_url'])
        with pytest.raises(OSError):
            socket.create_connection((uri.hostname, uri.port), timeout=0.5)
        assert 'offline-listener-fixture' not in result.stdout + result.stderr
    finally:
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=3)


def test_start_failure_and_existing_state_fail_without_provider(tmp_path):
    state = tmp_path / 'existing'
    state.mkdir()
    wrapper = tmp_path / 'fail.ps1'
    wrapper.write_text(f'''$ErrorActionPreference='Stop'
. {quote(HERE / 'litellm-bridge.ps1')}
$failures=0
try {{Start-CodexLitellmBridge -Python {quote(sys.executable)} -AdapterDirectory {quote(HERE)} -StateDirectory {quote(state)} -UpstreamBaseUrl 'http://127.0.0.1:1'}} catch {{$failures++}}
try {{Start-CodexLitellmBridge -Python {quote(tmp_path / 'nonexistent-python')} -AdapterDirectory {quote(HERE)} -StateDirectory {quote(tmp_path / 'new')} -UpstreamBaseUrl 'http://127.0.0.1:1'}} catch {{$failures++}}
if($failures -ne 2){{throw 'Expected fail-closed starts'}}
'PASS'
''', encoding='utf-8')
    result = subprocess.run([PWSH, '-NoProfile', '-File', str(wrapper)], env=clean_env(),
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0 and 'PASS' in result.stdout, result.stderr
    assert not list(tmp_path.rglob('ready.json'))


def test_invalid_readiness_kills_owned_process_and_removes_ready_without_leaks(tmp_path):
    # This local fixture intentionally reports a wrong PID while owning a real
    # loopback socket. Startup must fail; no arbitrary reported PID is killed.
    adapter = tmp_path / 'invalid adapter with spaces'
    package = adapter / 'litellm_bridge'
    package.mkdir(parents=True)
    (package / '__init__.py').write_text('', encoding='utf-8')
    actual = tmp_path / 'actual-listener.json'
    (package / '__main__.py').write_text(f'''import argparse,json,os,socket,time
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('command')
parser.add_argument('--port')
parser.add_argument('--ready-file')
args=parser.parse_args()
listener=socket.socket()
listener.bind(('127.0.0.1',0))
listener.listen()
port=listener.getsockname()[1]
Path({str(actual)!r}).write_text(json.dumps({{'pid':os.getpid(),'port':port}}),encoding='utf-8')
Path(args.ready_file).write_text(json.dumps({{'base_url':f'http://127.0.0.1:{{port}}/v1','pid':os.getpid()+100000,'fake_secret':'offline-listener-fixture'}}),encoding='utf-8')
time.sleep(60)
''', encoding='utf-8')
    state = tmp_path / 'invalid bridge state'
    wrapper = tmp_path / 'invalid-readiness.ps1'
    wrapper.write_text(f'''$ErrorActionPreference='Stop'
. {quote(HERE / 'litellm-bridge.ps1')}
$rejected=$false
try {{Start-CodexLitellmBridge -Python {quote(sys.executable)} -AdapterDirectory {quote(adapter)} -StateDirectory {quote(state)} -UpstreamBaseUrl 'http://127.0.0.1:1'}} catch {{
    if($_.Exception.Message -ne 'Invalid LiteLLM bridge readiness record.'){{throw}}
    $rejected=$true
}}
if(-not $rejected){{throw 'Invalid readiness accepted'}}
$actual=Get-Content -LiteralPath {quote(actual)} -Raw | ConvertFrom-Json
if(Get-Process -Id $actual.pid -ErrorAction SilentlyContinue){{throw 'Owned listener leaked after invalid readiness'}}
if(Test-Path -LiteralPath {quote(state / 'ready.json')}){{throw 'Invalid readiness file leaked'}}
'PASS'
''', encoding='utf-8')
    result = subprocess.run([PWSH, '-NoProfile', '-File', str(wrapper)], env=clean_env(),
                            capture_output=True, text=True, encoding='utf-8', timeout=25)
    assert result.returncode == 0 and 'PASS' in result.stdout, result.stderr
    assert 'offline-listener-fixture' not in result.stdout + result.stderr
    assert not (state / 'ready.json').exists()
    metadata = json.loads(actual.read_text(encoding='utf-8'))
    with pytest.raises(OSError):
        socket.create_connection(('127.0.0.1', metadata['port']), timeout=0.5)


def test_runner_uses_bridge_only_for_litellm_launch():
    # Source contract supplements actual lifecycle/transport tests above.
    runner = (HERE.parents[1] / 'scripts/run-codex-baseline.ps1').read_text(encoding='utf-8-sig')
    provider_block = runner.split('if ($Litellm) {', 1)[1].split('& $python (Join-Path $adapter', 1)[0]
    assert 'if ($Launch) {' in provider_block
    assert 'Start-CodexLitellmBridge' in provider_block
    assert '$providerBaseUrl = $mappingBridge.Record.base_url' in provider_block
    assert 'Stop-CodexLitellmBridge -Bridge $mappingBridge' in runner
