"""Actual runner subprocesses; all executable/service boundaries are local fakes.

Only the shared helper's clock expression and atomic replacement boundary are
injected in the disposable copy. Runner bytes are copied and verified unchanged.
No real MXC, contestant, oracle, telemetry, or provider is invoked.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


SOURCE = Path(__file__).parent
PWSH = shutil.which('pwsh')
pytestmark = pytest.mark.skipif(not PWSH, reason='PowerShell 7 required')


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


FAKE_PYTHON = r'''
$a = @($args)
$global:LASTEXITCODE = 0
if ($a[0] -eq '-c') {
    if ($a[1] -eq 'import pytest') { return }
    if ($a[1] -like '*sysconfig*') { $env:FAKE_ROOT; return }
    throw "Unexpected Python -c: $($a[1])"
}
if ($a[0] -eq '-m' -and $a[1] -eq 'pytest') {
    $script:oracleCalls++
    $r = Get-ChildItem (Join-Path $env:FAKE_PLUGIN 'evals/baselines') -Recurse -Filter run.json | Select-Object -First 1
    $record = Get-Content $r.FullName -Raw | ConvertFrom-Json
    if ($script:oracleCalls -eq 1) {
        if ($record.execution.process_outcome -ne 'not-started') { throw 'Seed did not observe prepared record' }
        Copy-Item $r.FullName (Join-Path $env:FAKE_ROOT 'observed-prepared.json')
        [IO.File]::WriteAllText($env:FAKE_CLOCK, $env:FAKE_PRE_ELAPSED)
        if ($env:FAKE_FAILURE -eq 'seed') { throw 'Injected seed oracle failure' }
        '1 failed'; $global:LASTEXITCODE = 1
    } else {
        if ($record.execution.process_outcome -notin 'success','timeout','crash') { throw 'Outcome was not durable before oracle' }
        if ($env:FAKE_FAILURE -eq 'oracle') { throw 'Injected result oracle failure' }
        [IO.File]::WriteAllText($env:FAKE_CLOCK, [string]([double](Get-Content $env:FAKE_CLOCK) + [double]$env:FAKE_POST_ELAPSED))
        '1 passed'
    }
    return
}
$name = Split-Path $a[0] -Leaf
if ($name -eq 'prepare-profile.py') {
    if ($env:FAKE_FAILURE -eq 'preflight') { throw 'Injected preflight failure' }
    $output = $a[[array]::IndexOf($a, '--output') + 1]
    @{ok=$true; worker_model='fixture'; worker_reasoning='high'; model_matrix=@(); codex_config_overrides=@();
      runtime_verified=$false; profile_sha256='fixture-profile'} | ConvertTo-Json | Set-Content $output
    return
}
if ($name -eq 'capture-rollouts.py') {
    $output = $a[[array]::IndexOf($a, '--output') + 1]
    if ($env:FAKE_FAILURE -eq 'native-capture') { throw 'Injected native capture failure' }
    Set-Content (Join-Path $output 'session.jsonl') '{"fixture":"native"}'
    return
}
if ($name -eq 'analyze-run.py') {
    if ($env:FAKE_FAILURE -eq 'analysis') { throw 'Injected analysis failure' }
    $r = Get-Content (Join-Path $a[1] 'run.json') -Raw | ConvertFrom-Json -AsHashtable
    $r['fixture_analyzed'] = $true
    $r['analysis_status'] = 'complete'
    $output = $a[[array]::IndexOf($a, '--out') + 1]
    New-Item -ItemType Directory -Force $output | Out-Null
    $r | ConvertTo-Json -Depth 24 | Set-Content (Join-Path $output 'run.json')
    Set-Content (Join-Path $output 'analysis.json') '{}'
    return
}
throw "DENIED unexpected Python call: $a"
'''


FAKE_MXC = r'''
$a = @($args)
$path = (Get-ChildItem (Join-Path $env:FAKE_PLUGIN 'evals/baselines') -Recurse -Filter run.json | Select-Object -First 1).FullName
$record = Get-Content $path -Raw | ConvertFrom-Json
if ($record.execution.state -ne 'running') { throw 'Missing durable running record' }
$timeout = [int]$a[[array]::IndexOf($a, '--timeout') + 1]
if ($timeout -lt 1) { throw 'DENIED unlimited host timeout' }
$observed = Join-Path $env:FAKE_ROOT 'launches.jsonl'
@{timeout=$timeout; args=$a; execution=$record.execution} | ConvertTo-Json -Compress -Depth 24 | Add-Content $observed
$calls = @(Get-Content $observed).Count
$durations = $env:FAKE_DURATIONS.Split(',')
$elapsed = [double](Get-Content $env:FAKE_CLOCK)
[IO.File]::WriteAllText($env:FAKE_CLOCK, [string]($elapsed + [double]$durations[[Math]::Min($calls-1, $durations.Count-1)]))
if ($record.harness -eq 'claude-code') {
    '{"type":"system","subtype":"init","model":"fixture","claude_code_version":"fixture","skills":[]}'
    '{"type":"result","stop_reason":"refusal","is_error":false,"num_turns":1,"usage":{"input_tokens":1,"output_tokens":1}}'
} else {
    '{"type":"thread.started","thread_id":"fixture-thread"}'
    '{"type":"turn.completed"}'
    '{"type":"mock_summary","ok":true}'
}
Write-Error 'fixture stderr bytes' -ErrorAction Continue
if ($env:FAKE_FAILURE -eq 'capture') { throw 'Injected capture failure after partial bytes' }
$global:LASTEXITCODE = [int]$env:FAKE_EXIT
'''


@pytest.fixture
def estate(tmp_path):
    root = tmp_path / 'repo'
    plugin = root / 'geeky-orchestration'
    scripts = plugin / 'evals/scripts'
    scripts.mkdir(parents=True)
    for name in ('run-baseline.ps1', 'run-codex-baseline.ps1', 'run-lifecycle.ps1'):
        shutil.copy2(SOURCE / name, scripts / name)
    for name in ('run-baseline.ps1', 'run-codex-baseline.ps1'):
        assert hashlib.sha256((scripts / name).read_bytes()).digest() == hashlib.sha256((SOURCE / name).read_bytes()).digest()
    helper = scripts / 'run-lifecycle.ps1'
    body = helper.read_text(encoding='utf-8')
    body = body.replace('[Diagnostics.Stopwatch]::GetTimestamp() / [double][Diagnostics.Stopwatch]::Frequency',
                        '[double](Get-Content -LiteralPath $env:FAKE_CLOCK)')
    body = body.replace('[IO.File]::Move($temporary, $Path, $true)',
                        "if ($env:FAKE_FAILURE -eq 'replacement' -and $Record.execution.state -eq 'finalized') { Copy-Item $Path (Join-Path $env:FAKE_ROOT 'before-replacement.json'); throw 'Injected atomic replacement failure' }\n        [IO.File]::Move($temporary, $Path, $true)")
    helper.write_text(body, encoding='utf-8')
    case = plugin / 'evals/cases/c0-wordstat'
    (case / 'oracle').mkdir(parents=True)
    for name in ('brief.md', 'contract.md'):
        (case / name).write_text('fixture', encoding='utf-8')
    (case / 'case.json').write_text(json.dumps({'wall_time_ceiling_s': 10, 'token_ceiling': 123}))
    (plugin / 'evals/prompts').mkdir()
    (plugin / 'evals/prompts/end-to-end.md').write_text('fixture {{PLANNING_FOLDER}}')
    adapter = plugin / 'evals/adapters/codex'
    adapter.mkdir(parents=True)
    for name in ('prepare-profile.py', 'mock_codex.py', 'trusted-exec.py', 'native-probe.py', 'diagnostics.py'):
        (adapter / name).write_text("raise RuntimeError('DENIED real executable boundary')")
    (adapter / 'copy-vetted-mxc-build.ps1').write_text("function Copy-VettedMxcBuild { if ($env:FAKE_FAILURE -eq 'build') { throw 'Injected build failure' } }")
    (plugin / 'evals/mock-agent').mkdir()
    (plugin / 'evals/mock-agent/mock_claude.py').write_text("raise RuntimeError('DENIED contestant')")
    (plugin / 'evals/telemetry').mkdir()
    (plugin / 'evals/telemetry/codex-flush.py').write_text("raise RuntimeError('DENIED telemetry')")
    (plugin / 'evals/telemetry/telemetry.ps1').write_text(r'''
function Resolve-EvalTelemetry {
    if ($env:FAKE_FAILURE -eq 'configuration') { throw 'Injected telemetry configuration failure' }
    if ($env:FAKE_TELEMETRY -ne '1') { return $null }
    return @{StateDir=$env:FAKE_ROOT; RoPaths=@(); EnvArgs=@(); Record=@{enabled=$true}; SettingsHooks=@()}
}
function Save-EvalTelemetry { if ($env:FAKE_FAILURE -eq 'telemetry') { throw 'Injected telemetry failure' } }
function Invoke-ClaudeTelemetryFlush { throw 'DENIED unexpected Claude replay' }
''')
    (root / 'mxc-sandbox/scripts').mkdir(parents=True)
    (root / 'mxc-sandbox/scripts/mxc.ps1').write_text(FAKE_MXC)
    (plugin / 'mcp').mkdir()
    (plugin / 'mcp/server.py').write_text('# exported fixture')
    for command in (['git', 'init', '-q', str(root)], ['git', '-C', str(root), 'add', '.'],
                    ['git', '-C', str(root), '-c', 'user.name=fixture', '-c', 'user.email=fixture@local', 'commit', '-qm', 'fixture']):
        subprocess.run(command, check=True, capture_output=True)
    tools = tmp_path / 'tools'
    binary = tools / 'agent-py' / ('Scripts' if os.name == 'nt' else 'bin')
    binary.mkdir(parents=True)
    python = binary / ('python.exe' if os.name == 'nt' else 'python')
    python.touch()
    mcp = tools / 'geeky-mcp'
    (mcp / ('Scripts' if os.name == 'nt' else 'bin')).mkdir(parents=True)
    mcp_python = mcp / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    mcp_python.touch()
    (mcp / 'pyvenv.cfg').write_text('home = ' + str(tmp_path))
    (tools / 'codex-home/sessions').mkdir(parents=True)
    codex = tools / 'codex.exe'
    codex.touch()
    work = tmp_path / 'work'
    work.mkdir()
    clock = tmp_path / 'clock.txt'
    clock.write_text('0')
    shim = tmp_path / 'fake-python.ps1'
    shim.write_text(FAKE_PYTHON)

    def run(harness, *, failure='', durations='1', pre_elapsed='0', recoveries=0,
            child_exit=0, prepare=False, waiver=False, post_elapsed='0', extra=()):
        runner = scripts / ('run-baseline.ps1' if harness == 'claude' else 'run-codex-baseline.ps1')
        env = os.environ.copy()
        # No real credentials are needed or delivered to disposable fixtures.
        for key in list(env):
            if any(word in key for word in ('TOKEN', 'API_KEY', 'SECRET', 'LANGFUSE')):
                env.pop(key)
        env.update(FAKE_ROOT=str(tmp_path), FAKE_PLUGIN=str(plugin), FAKE_CLOCK=str(clock),
                   FAKE_DURATIONS=durations, FAKE_PRE_ELAPSED=pre_elapsed, FAKE_EXIT=str(child_exit),
                   FAKE_FAILURE=failure, FAKE_TELEMETRY='1' if failure == 'telemetry' else '0',
                   FAKE_POST_ELAPSED=post_elapsed,
                   CLAUDE_CODE_OAUTH_TOKEN='offline-fixture-only')
        command = [str(runner), '-Case', 'c0-wordstat', '-ToolsDir', str(tools), '-WorkRoot', str(work),
                   '-TimeoutSec', '10', '-CloseoutReserveSec', '2', '-AuthorizationReference', 'offline-fixture']
        if harness == 'claude':
            command += ['-PrepareOnly'] if prepare else ['-MockAgent', '-ResumeOnRefusal', str(recoveries)]
        else:
            command += ['-CodexExe', str(codex)]
            if not prepare:
                command += (['-Launch', '-SkipNativeQualification', '-QualificationOverrideReason', 'fixture-owner',
                             '-MxcBuildSource', str(tmp_path)] if waiver else ['-MockAgent'])
        for key, value in zip(extra[::2], extra[1::2]):
            if key in command:
                command[command.index(key) + 1] = value
            else:
                command += [key, value]
        wrapper = tmp_path / 'wrapper.ps1'
        wrapper.write_text("$ErrorActionPreference='Stop'\n$script:oracleCalls=0\n" +
            f"$fakePython = Get-Content -LiteralPath {quote(shim)} -Raw\n" +
            '\n'.join(f"Set-Item -LiteralPath {quote('Function:global:' + str(path))} -Value ([scriptblock]::Create($fakePython))"
                      for path in (python, mcp_python, Path('C:/Python314/python.exe'))) + '\n' +
            f"Set-Item -LiteralPath {quote('Function:global:' + str(codex))} -Value {{ if ($args[0] -ne '--version') {{ throw 'DENIED unexpected Codex call' }}; 'fixture-codex'; $global:LASTEXITCODE=0 }}\n" +
            # Override discovery too: prevent fallback to any real Python.
            f"function Get-Command {{ [pscustomobject]@{{Source={quote(python)}}} }}\n" +
            '& ' + ' '.join(part if part.startswith('-') and not part[1:].isdigit() else quote(part) for part in command) + '\n', encoding='utf-8')
        result = subprocess.run([PWSH, '-NoProfile', '-File', str(wrapper)], env=env,
                                capture_output=True, text=True, timeout=30)
        records = list((plugin / 'evals/baselines').rglob('run.json')) if (plugin / 'evals/baselines').exists() else []
        record = json.loads(records[0].read_text(encoding='utf-8-sig')) if records else None
        observed = tmp_path / 'launches.jsonl'
        launches = [json.loads(line) for line in observed.read_text(encoding='utf-8-sig').splitlines()] if observed.exists() else []
        return result, record, launches, records[0].parent if records else None

    return run, tmp_path


@pytest.mark.parametrize('harness', ['claude', 'codex'])
def test_actual_runner_prepared_and_running_deadline_context(estate, harness):
    run, root = estate
    result, record, launches, folder = run(harness)
    assert result.returncode == 0, result.stdout + result.stderr
    prepared = json.loads((root / 'observed-prepared.json').read_text(encoding='utf-8-sig'))
    assert prepared['execution']['process_outcome'] == 'not-started'
    assert launches[0]['execution']['state'] == 'running'
    assert launches[0]['timeout'] == 10
    args = launches[0]['args']
    assert 'GEEKY_DEADLINE_UTC=' + record['execution']['initial_deadline_utc'] in args
    assert 'GEEKY_CLOSEOUT_RESERVE_S=2' in args
    assert record['execution']['workflow_acceptance'] == 'not-established'
    assert record['execution']['state'] == 'finalized'
    assert record['execution']['contestant_time_s'] == 1
    assert record['execution']['finalization_time_s'] == 0
    assert record['fixture_analyzed']
    assert record['execution']['artifact_sha256']['stream.jsonl'] == hashlib.sha256((folder / 'stream.jsonl').read_bytes()).hexdigest()


@pytest.mark.parametrize('duration,count,timeouts', [('8', 2, [10, 2]), ('8.1', 2, [10, 1]), ('9.1', 1, [10]), ('10', 1, [10])])
def test_actual_claude_recovery_uses_floor_of_remaining(estate, duration, count, timeouts):
    result, record, launches, _ = estate[0]('claude', durations=duration + ',0.1', recoveries=1)
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(launches) == count
    assert [item['timeout'] for item in launches] == timeouts
    assert record['execution']['allowed_recoveries'] == 1
    assert len({item['execution']['initial_deadline_utc'] for item in launches}) == 1


def test_no_authorized_recovery_never_relaunches(estate):
    result, record, launches, _ = estate[0]('claude', durations='1', recoveries=0)
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(launches) == 1


@pytest.mark.parametrize('harness', ['claude', 'codex'])
def test_expired_attempt_never_launches(estate, harness):
    result, record, launches, _ = estate[0](harness, pre_elapsed='10')
    assert result.returncode != 0
    assert not launches
    assert record['execution']['process_outcome'] == 'not-started'
    assert record['exit_reason'] == 'deadline-exhausted'


@pytest.mark.parametrize('harness', ['claude', 'codex'])
@pytest.mark.parametrize('failure', ['configuration', 'seed', 'capture', 'oracle', 'telemetry', 'analysis', 'replacement'])
def test_actual_runners_preserve_truth_on_failures(estate, harness, failure):
    result, record, launches, folder = estate[0](harness, failure=failure)
    assert result.returncode != 0, result.stdout + result.stderr
    assert record is not None, result.stdout + result.stderr
    assert record['execution']['state'] != 'finalized'
    if failure in ('configuration', 'seed'):
        assert not launches
        assert record['execution']['process_outcome'] == 'not-started'
    else:
        assert (folder / 'stream.jsonl').read_bytes()
        assert 'fixture stderr bytes' in (folder / 'stderr.txt').read_text(encoding='utf-8-sig')
        assert record['execution']['process_outcome'] == ('unknown' if failure == 'capture' else 'success')
    if failure != 'replacement':
        assert record['execution']['failure']
    else:
        assert (folder / 'run.json').read_bytes() == (estate[1] / 'before-replacement.json').read_bytes()
    assert not list(folder.glob('*.tmp'))


@pytest.mark.parametrize('harness', ['claude', 'codex'])
@pytest.mark.parametrize('failure', ['oracle', 'telemetry'])
def test_timeout_survives_postprocessing_failure(estate, harness, failure):
    result, record, launches, folder = estate[0](harness, failure=failure, child_exit=124)
    assert result.returncode != 0
    assert record['exit_reason'] == 'timeout'
    assert record['exit_code'] == 124
    assert record['execution']['process_outcome'] == 'timeout'
    assert record['execution']['invocations'][0]['outcome'] == 'timeout'
    assert (folder / 'stream.jsonl').read_bytes()


@pytest.mark.parametrize('harness', ['claude', 'codex'])
def test_prepare_only_has_no_oracle_or_workload(estate, harness):
    result, record, launches, _ = estate[0](harness, prepare=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert record['execution']['state'] == 'prepared'
    assert not launches
    assert not (estate[1] / 'observed-prepared.json').exists()


def test_waiver_retains_no_extra_probe_semantics(estate):
    result, record, launches, _ = estate[0]('codex', waiver=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(launches) == 1
    assert record['native_qualification']['status'] == 'waived-by-owner'
    assert record['execution']['qualification_waiver']['override_reason'] == 'fixture-owner'
    assert record['diagnostics_passed'] is None
    assert record['runtime_parity_verified'] is False


@pytest.mark.parametrize('harness', ['claude', 'codex'])
@pytest.mark.parametrize('extra', [('-TimeoutSec', '0'), ('-CloseoutReserveSec', '10'), ('-CloseoutReserveSec', '-1')])
def test_invalid_budgets_fail_before_launch(estate, harness, extra):
    result, _, launches, _ = estate[0](harness, extra=extra)
    assert result.returncode != 0
    assert not launches


@pytest.mark.parametrize('failure', ['preflight', 'build', 'native-capture'])
def test_codex_preflight_build_and_native_capture_failures(estate, failure):
    result, record, launches, folder = estate[0]('codex', failure=failure, waiver=failure == 'build')
    assert result.returncode != 0
    assert record['execution']['state'] == 'incomplete'
    assert record['execution']['failure']
    assert bool(launches) == (failure == 'native-capture')
    assert record['execution']['process_outcome'] == ('success' if launches else 'not-started')


@pytest.mark.parametrize('harness', ['claude', 'codex'])
def test_first_launch_also_floors_remaining_attempt_time(estate, harness):
    result, record, launches, _ = estate[0](harness, pre_elapsed='0.01')
    assert result.returncode == 0, result.stdout + result.stderr
    assert [launch['timeout'] for launch in launches] == [9]


@pytest.mark.parametrize('harness', ['claude', 'codex'])
def test_finalization_time_is_separate_and_cannot_extend_contestant_budget(estate, harness):
    result, record, launches, _ = estate[0](harness, durations='8', pre_elapsed='2', post_elapsed='1')
    assert result.returncode == 0, result.stdout + result.stderr
    assert [launch['timeout'] for launch in launches] == [8]
    assert record['execution']['contestant_time_s'] == 8
    assert record['execution']['attempt_elapsed_s'] == 10
    assert record['execution']['finalization_time_s'] == 3
    assert record['wall_time_s'] == 8
    assert record['execution']['workflow_acceptance'] == 'not-established'
