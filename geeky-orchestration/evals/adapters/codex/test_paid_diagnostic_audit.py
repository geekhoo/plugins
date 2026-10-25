"""Offline paid diagnostic gates: real files/trace parser, no native or model calls."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

spec = importlib.util.spec_from_file_location('paid_audit', Path(__file__).with_name('paid-diagnostic-audit.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

ROOT = 'C:\\Users\\fixture\\.agents\\skills'
DIAGNOSTIC = ('2026-10-23T17:53:39.443409Z ERROR codex_skills_extension::loader::host: '
              'failed to walk skills root file:///C:/Users/fixture/.agents/skills: Access is denied. (os error 5)\n')


def change(path, mutate):
    value = audit.read_json(path)
    mutate(value)
    audit.write_json(path, value)


@pytest.fixture
def evidence(tmp_path):
    run = tmp_path / 'paid'
    native_run = tmp_path / 'native'
    native = native_run / 'native-attempts/probe'
    runtime = tmp_path / 'runtime'
    source = tmp_path / 'source'
    build = tmp_path / 'build'
    for folder in (run, native, runtime, source, build):
        folder.mkdir(parents=True)
    (source / 'fixture.cs').write_text('Model-free fixture source')
    (build / 'MxcClaude.exe').write_text('Fixture bytes; never execute')
    (build / 'MxcClaude.dll').write_text('Fixture DLL bytes; never load')
    source_hash = audit.sha(source / 'fixture.cs')
    (build / '.source-hash').write_text(source_hash)
    pin = {'source_hash': source_hash, 'exe_sha256': audit.sha(build / 'MxcClaude.exe'),
           'dll_sha256': audit.sha(build / 'MxcClaude.dll'), 'sdk_version': '1.0.1'}
    pin_file = tmp_path / 'pin.json'
    audit.write_json(pin_file, pin)
    matrix = {'orchestrator': {'model': 'gpt-6.1-sol', 'reasoning': 'medium'},
              'workers': {'model': 'gpt-6-luna', 'reasoning': 'max', 'scope': 'all-descendants'}}
    record = {'model': 'gpt-6.1-sol', 'reasoning': 'medium', 'worker_model': 'gpt-6-luna',
              'worker_reasoning': 'max', 'model_matrix': matrix, 'plugin_sha': 'a' * 40,
              'exit_code': 0, 'is_error': False, 'plugin_modified_during_run': False,
              'workspace': r'C:\repos\candidate'}
    for folder in (run, native_run):
        audit.write_json(folder / 'run.json', record)
        audit.write_json(folder / 'parity-preflight.json', {'ok': True, 'model_matrix': matrix})
    manifest = [{'path': name, 'sha256': pin[key]} for name, key in (
        ('MxcClaude.exe', 'exe_sha256'), ('MxcClaude.dll', 'dll_sha256'))]
    provenance = {**pin, 'verified': True, 'source_manifest': manifest,
                  'destination_manifest': manifest, 'destination_directory': str(build)}
    audit.write_json(run / 'mxc-build-provenance.json', provenance)
    audit.write_json(native / 'mxc-build-provenance.json', provenance)
    audit.write_json(native / 'mxc-build-proof.json', {**pin, 'pinned_build_verified': True})
    audit.write_json(native / 'native-summary.json', {'ok': True, 'functional_ok': True,
        'cli_version': '0.164.0', 'paid_model_calls': 0, 'unexpected_errors': [],
        'checks': [{'name': name, 'passed': True,
                    'detail': {'path': ROOT, 'winerror': 5} if name == 'native_user_skills_denied' else ''}
                   for name in sorted(audit.NATIVE_CHECKS)],
        'model_matrix': matrix})
    for name in ('native-plugin-install.json', 'native-hook-catalog.json'):
        (runtime / name).write_text('{}')
    for name in ('native-plugin-install-stderr.txt', 'native-hook-catalog-stderr.txt'):
        (runtime / name).write_text('')
    audit.write_json(runtime / 'runtime-denial-proof.json', {
        'root': ROOT, 'denial_verified': True, 'error_type': 'PermissionError', 'winerror': 5,
        'cli_version': '0.164.0', 'version_returncode': 0,
        'version_stdout': 'codex-cli 0.164.0\n', 'version_stderr': ''})
    (run / 'stderr.txt').write_text(DIAGNOSTIC * 2)
    stream = [{'type': 'thread.started', 'thread_id': 'main'}, {'type': 'turn.completed'}]
    (run / 'stream.jsonl').write_text('\n'.join(map(json.dumps, stream)))
    rows = [
        {'type': 'session_meta', 'payload': {'id': 'main'}},
        {'type': 'event_msg', 'timestamp': '2026-10-23T17:53:00Z', 'payload': {
            'type': 'item_completed', 'started_at_ms': 1792777979000,
            'item': {'id': 'read-skill', 'type': 'CommandExecution',
                'command': "Get-Content 'C:/fixture/spec-research/SKILL.md'",
                'aggregated_output': 'Complete fixture skill read', 'exit_code': 0, 'status': 'completed'}}},
        {'type': 'event_msg', 'timestamp': '2026-10-23T17:53:01Z', 'payload': {
            'type': 'token_count', 'info': {'total_token_usage': {'input_tokens': 1, 'output_tokens': 1}}}},
        {'type': 'event_msg', 'timestamp': '2026-10-23T17:53:02Z', 'payload': {'type': 'task_complete'}},
    ]
    (run / 'session.jsonl').write_text('\n'.join(map(json.dumps, rows)))
    return {'run': run, 'native': native, 'runtime': runtime, 'pin': pin_file, 'source': source, 'build': build}


def prepare(evidence):
    return audit.prepare(evidence['run'], evidence['native'], evidence['pin'], evidence['source'], ROOT)


def post(evidence):
    return audit.audit(evidence['run'], evidence['runtime'], ROOT, evidence['pin'], evidence['source'])


def test_full_gate_accepts_exact_recurrences_with_real_trace_and_retains_proof(evidence):
    prepared = prepare(evidence)
    assert prepared['ok'] and len(prepared['files']) == 5
    assert all((evidence['run'] / 'native-proof' / row['copy']).is_file() for row in prepared['files'])
    report = post(evidence)
    assert report['ok']
    assert report['observed_counts'] == {'plugin-install': 0, 'hook-catalogue': 0, 'exec': 2}
    assert len(report['known_diagnostics']) == 2
    assert report['raw_diagnostics']['exec'] == DIAGNOSTIC * 2
    assert report['runtime_denial_verified'] and report['trace_complete']
    assert report['skill_read_evidence'][0]['skill'] == 'spec-research'
    assert report['skill_evidence_scope'] == 'stage-entry-only'
    assert (evidence['run'] / 'native-hook-trust/runtime-denial-proof.json').is_file()
    assert audit.read_json(evidence['run'] / 'diagnostic-report.json')['ok']


def test_reviewer_matrix_requires_new_matching_native_proof(evidence):
    matrix = {
        'orchestrator': {'model': 'gpt-6.1-sol', 'reasoning': 'high'},
        'workers': {'model': 'gpt-6.1-sol', 'reasoning': 'medium', 'scope': 'all-descendants-except-reviewers'},
        'reviewers': {'model': 'gpt-6.1-sol', 'reasoning': 'xhigh',
                     'roles': ['code-reviewer', 'code-architect-reviewer'], 'scope': 'review-assignments'}}
    def update_run(row):
        row.update(reasoning='high', worker_model='gpt-6.1-sol', worker_reasoning='medium',
                   reviewer_reasoning='xhigh', model_matrix=matrix)
    change(evidence['run'] / 'run.json', update_run)
    change(evidence['run'] / 'parity-preflight.json', lambda row: row.update(model_matrix=matrix))
    report = audit.validate_native(evidence['run'], audit.native_files(evidence['native']),
                                   evidence['pin'], evidence['source'], ROOT)
    assert not report['ok']
    assert not next(row['passed'] for row in report['checks'] if row['name'] == 'model_matrix')
    change(evidence['native'].parent.parent / 'run.json', update_run)
    for file in (evidence['native'] / 'native-summary.json', evidence['native'].parent.parent / 'parity-preflight.json'):
        change(file, lambda row: row.update(model_matrix=matrix))
    # Matching labels alone do not establish any actual reviewer requests.
    assert not prepare(evidence)['ok']
    def reviewer_evidence(row, role):
        row.update(roles={'child': 'geeky-coder', 'grandchild': role}, request_evidence={
            'grandchild': {'expected': {'model': 'gpt-6.1-sol', 'reasoning': 'xhigh'},
                'model_reasoning_ok': True, 'instructions_ok': True,
                'requests': [{'model': 'gpt-6.1-sol', 'reasoning': 'xhigh', 'registered_instructions': True}]}})
    change(evidence['native'] / 'native-summary.json', lambda row: reviewer_evidence(row, 'code-reviewer'))
    assert not prepare(evidence)['ok']  # The second reviewer registration is still unproved.
    architect = evidence['native'].parent / 'architect'
    shutil.copytree(evidence['native'], architect)
    change(architect / 'native-summary.json', lambda row: reviewer_evidence(row, 'code-architect-reviewer'))
    report = audit.prepare(evidence['run'], evidence['native'], evidence['pin'], evidence['source'], ROOT, architect)
    assert report['ok'] and len(report['reviewer_files']) == 5
    assert post(evidence)['ok']
    change(evidence['run'] / 'reviewer-native-proof/native-summary.json',
           lambda row: row['request_evidence']['grandchild']['requests'][0].update(reasoning='medium'))
    assert not post(evidence)['ok']
    change(evidence['run'] / 'run.json', lambda row: row.update(reviewer_reasoning='medium'))
    with pytest.raises(ValueError, match='matrix'):
        audit.expected_matrix(audit.read_json(evidence['run'] / 'run.json'))


@pytest.mark.parametrize('failure', ['missing', 'matrix', 'plugin', 'native_check', 'native_version',
    'paid_calls', 'native_build', 'native_provenance', 'launch_build', 'current_source', 'current_binary', 'native_root'])
def test_preflight_rejects_missing_or_mismatched_proof(evidence, failure):
    native = evidence['native']
    if failure == 'missing':
        (native / 'native-summary.json').unlink()
    elif failure == 'matrix':
        change(native / 'native-summary.json', lambda r: r['model_matrix']['workers'].update(reasoning='high'))
    elif failure == 'plugin':
        change(native.parent.parent / 'run.json', lambda r: r.update(plugin_sha='b' * 40))
    elif failure == 'native_check':
        change(native / 'native-summary.json', lambda r: r['checks'][0].update(passed=False))
    elif failure == 'native_version':
        change(native / 'native-summary.json', lambda r: r.update(cli_version='0.165.0'))
    elif failure == 'paid_calls':
        change(native / 'native-summary.json', lambda r: r.update(paid_model_calls=1))
    elif failure == 'native_build':
        change(native / 'mxc-build-proof.json', lambda r: r.update(exe_sha256='wrong'))
    elif failure == 'native_provenance':
        change(native / 'mxc-build-provenance.json', lambda r: r.update(verified=False))
    elif failure == 'launch_build':
        change(evidence['run'] / 'mxc-build-provenance.json', lambda r: r.update(dll_sha256='wrong'))
    elif failure == 'current_source':
        (evidence['source'] / 'fixture.cs').write_text('changed')
    elif failure == 'current_binary':
        (evidence['build'] / 'MxcClaude.exe').write_text('changed')
    elif failure == 'native_root':
        change(native / 'native-summary.json', lambda r: next(
            row for row in r['checks'] if row['name'] == 'native_user_skills_denied')['detail'].update(path=ROOT + '-other'))
    report = prepare(evidence)
    assert not report['ok']
    assert not (evidence['run'] / 'native-proof').exists()
    assert not audit.read_json(evidence['run'] / 'native-proof-validation.json')['ok']


@pytest.mark.parametrize('failure', ['root', 'denial', 'winerror', 'version', 'skill_failed', 'skill_missing',
    'unknown_stderr', 'wrong_root_diagnostic', 'catalogue_diagnostic', 'item_error', 'stream_error',
    'no_completion', 'malformed_stream', 'missing_capture', 'retained_tamper', 'execution_failed'])
def test_post_gate_rejects_each_missing_runtime_proof_or_error(evidence, failure):
    assert prepare(evidence)['ok']
    run, runtime = evidence['run'], evidence['runtime']
    denial = runtime / 'runtime-denial-proof.json'
    if failure == 'root':
        change(denial, lambda r: r.update(root=ROOT + '-different'))
    elif failure == 'denial':
        change(denial, lambda r: r.update(denial_verified=False))
    elif failure == 'winerror':
        change(denial, lambda r: r.update(winerror=13))
    elif failure == 'version':
        change(denial, lambda r: r.update(version_stderr='unexpected'))
    elif failure in ('skill_failed', 'skill_missing'):
        rows = [json.loads(line) for line in (run / 'session.jsonl').read_text().splitlines()]
        item = rows[1]['payload']['item']
        item.update(exit_code=1) if failure == 'skill_failed' else item.update(command='Get-Content brief.md')
        (run / 'session.jsonl').write_text('\n'.join(map(json.dumps, rows)))
    elif failure == 'unknown_stderr':
        (run / 'stderr.txt').write_text(DIAGNOSTIC * 2 + 'ERROR unrelated runtime failure\n')
    elif failure == 'wrong_root_diagnostic':
        (run / 'stderr.txt').write_text(DIAGNOSTIC.replace('/fixture/', '/different/'))
    elif failure == 'catalogue_diagnostic':
        (runtime / 'native-hook-catalog-stderr.txt').write_text(DIAGNOSTIC)
    elif failure in ('item_error', 'stream_error', 'no_completion', 'malformed_stream'):
        stream = run / 'stream.jsonl'
        if failure == 'no_completion':
            stream.write_text(json.dumps({'type': 'thread.started', 'thread_id': 'main'}))
        else:
            extra = {'type': 'item.completed', 'item': {'type': 'error'}} if failure == 'item_error' else {'type': 'error'}
            with stream.open('a') as handle:
                handle.write('\n' + ('invalid JSON' if failure == 'malformed_stream' else json.dumps(extra)))
    elif failure == 'missing_capture':
        (runtime / 'native-plugin-install-stderr.txt').unlink()
    elif failure == 'retained_tamper':
        change(run / 'native-proof/native-summary.json', lambda r: r.update(ok=False))
    elif failure == 'execution_failed':
        change(run / 'run.json', lambda r: r.update(exit_code=1))
    report = post(evidence)
    assert not report['ok']
    assert not audit.read_json(run / 'diagnostic-report.json')['ok']
    assert report['raw_diagnostics']['exec']


def test_runner_requires_native_proof_and_audits_after_preservation_before_analysis():
    runner = (Path(__file__).resolve().parents[2] / 'scripts/run-codex-baseline.ps1').read_text()
    # Native proof remains the Windows default; an explicit owner waiver skips qualification claims.
    assert 'if ($Launch -and -not $SkipNativeQualification -and $windowsHost -and -not $NativeProofFolder) { throw' in runner
    assert 'if ($Launch -and -not $SkipNativeQualification -and $NativeProofFolder) {' in runner
    assert "'--forbidden-skill-root', $forbiddenSkillRoot" in runner
    assert runner.index('--native-proof-folder $NativeProofFolder') < runner.index('& $mxc @hostArgs')
    assert runner.index("'bundle', 'create'") < runner.index('--runtime-evidence (Join-Path $runTmp')
    assert runner.index('--runtime-evidence (Join-Path $runTmp') < runner.index("'analyze-run.py'")
    assert "$record.is_error = $true; $record.exit_reason = 'diagnostics-failed'" in runner
    assert '$record.runtime_parity_verified = $record.diagnostics_passed' in runner
    assert '$record.runtime_toolchain_verified = $record.diagnostics_passed' in runner
    assert 'native_proof_folder = $(if ($Launch -and $NativeProofFolder)' in runner


@pytest.mark.parametrize('arguments,expected,windows_only', [
    (['-SkipNativeQualification'], 'requires an explicit -QualificationOverrideReason', False),
    (['-SkipNativeQualification', '-QualificationOverrideReason', 'owner fixture',
      '-NativeProofFolder', 'fixture-proof'], 'Choose native proof or the owner override', False),
    (['-SkipNativeQualification', '-QualificationOverrideReason', 'owner fixture',
      '-ReviewerProofFolder', 'fixture-proof'], 'Choose native proof or the owner override', False),
    ([], 'requires an explicit -NativeProofFolder', True),
    (['-NativeProofFolder', 'fixture-proof', '-ReviewerReasoning', 'xhigh'],
     'Reviewer settings require an explicit -ReviewerProofFolder', False),
])
def test_runner_launch_guards_reject_invalid_qualification_before_setup(tmp_path, arguments, expected, windows_only):
    pwsh = shutil.which('pwsh')
    if not pwsh or (windows_only and sys.platform != 'win32'):
        pytest.skip('PowerShell on the applicable host is required')
    runner = (Path(__file__).resolve().parents[2] / 'scripts/run-codex-baseline.ps1').read_text()
    # Execute the actual parameter/guard section only. Even a broken guard cannot
    # reach workspace setup, MXC, authentication, or a provider in this fixture.
    guard_script = tmp_path / 'launch-guards.ps1'
    guard_script.write_text(runner[:runner.index('if (-not $WorkerModel)')] +
                            "Write-Output 'GUARDS_RETURNED'\n", encoding='utf-8')
    workspace = tmp_path / 'must-not-be-created'
    result = subprocess.run([pwsh, '-NoProfile', '-NonInteractive', '-File', str(guard_script),
        '-Case', 'c0-wordstat', '-Launch', '-MxcBuildSource', 'fixture-build',
        '-WorkRoot', str(workspace), *arguments], capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert expected in result.stdout + result.stderr
    assert 'GUARDS_RETURNED' not in result.stdout
    assert not workspace.exists()


def test_runner_waiver_records_reason_without_claiming_runtime_qualification():
    pwsh = shutil.which('pwsh')
    if not pwsh:
        pytest.skip('PowerShell is required')
    runner = (Path(__file__).resolve().parents[2] / 'scripts/run-codex-baseline.ps1').read_text()
    qualification = runner.split('    native_qualification = ', 1)[1].split('    provider = ', 1)[0]
    waiver = runner.split('    if ($Launch -and ($SkipNativeQualification -or -not $NativeProofFolder)) {', 1)[1].split('    } elseif ($Launch)', 1)[0]
    # Isolate just the production metadata expressions and waiver body: no launch
    # code or audit branch is ever evaluated, and stale true claims must be cleared.
    command = ("$Launch=$true; $SkipNativeQualification=$true; "
               "$QualificationOverrideReason='explicit fixture waiver'; "
               "$record=[ordered]@{diagnostics_passed=$true; runtime_parity_verified=$true; "
               "runtime_toolchain_verified=$false; native_qualification=" + qualification + "}; " +
               waiver + '; $record | ConvertTo-Json -Compress')
    result = subprocess.run([pwsh, '-NoProfile', '-NonInteractive', '-Command', command],
                            capture_output=True, text=True, check=True, timeout=30)
    record = json.loads(result.stdout)
    assert record['native_qualification'] == {
        'status': 'waived-by-owner', 'override_reason': 'explicit fixture waiver'}
    assert record['diagnostics_passed'] is None
    assert record['runtime_parity_verified'] is False
    assert record['runtime_toolchain_verified'] is False


def patch_failure(evidence, direct=False):
    run = evidence['run']
    target = r'C:\repos\candidate\tests\test_cli.py'
    failure = 'apply_patch verification failed: Failed to find expected lines in ' + target + ':\n    assert old == expected'
    raw = '2026-10-23T17:53:01.010000Z ERROR codex_core::tools::router: error=' + failure
    rows = [json.loads(line) for line in (run / 'session.jsonl').read_text().splitlines()]
    rows[0]['payload']['cwd'] = r'C:\repos\candidate'
    patch = '*** Begin Patch\n*** Update File: tests/test_cli.py\n@@\n-    assert old == expected\n+    assert new == expected\n*** End Patch'
    request = {'type': 'response_item', 'ordinal': 10, 'timestamp': '2026-10-23T17:53:01.000Z',
        'payload': {'type': 'custom_tool_call', 'call_id': 'failed-patch', 'name': 'apply_patch' if direct else 'exec',
            'input': patch if direct else 'const patch=`' + patch + '`; text(await tools.apply_patch(patch));',
            'internal_chat_message_metadata_passthrough': {'turn_id': 'current-turn'}}}
    output = {'type': 'response_item', 'ordinal': 11, 'timestamp': '2026-10-23T17:53:01.020Z',
        'payload': {'type': 'custom_tool_call_output', 'call_id': 'failed-patch',
            'internal_chat_message_metadata_passthrough': {'turn_id': 'current-turn'},
            'output': [{'type': 'input_text', 'text': 'Script failed\nWall time 0.02 seconds\nOutput:\n'},
                       {'type': 'input_text', 'text': 'Script error:\n' + failure}]}}
    rows.extend([request, output])
    (run / 'session.jsonl').write_text('\n'.join(map(json.dumps, rows)))
    (run / 'stderr.txt').write_text(DIAGNOSTIC * 2 + raw + '\n')
    return rows, raw


@pytest.mark.parametrize('direct', [False, True])
def test_correlated_patch_failure_remains_a_failed_candidate_tool(evidence, direct):
    assert prepare(evidence)['ok']
    rows, raw = patch_failure(evidence, direct)
    correlated = audit.correlate_candidate_tool_failures(evidence['run'], DIAGNOSTIC * 2 + raw + '\n')
    report = audit.classify_diagnostics({'plugin-install': '', 'hook-catalogue': '',
        'exec': DIAGNOSTIC * 2 + raw + '\n'}, ROOT, '0.164.0', True, True, True, correlated)
    assert report['ok']
    assert len(report['known_diagnostics']) == 2
    assert len(report['candidate_tool_failures']) == 1
    candidate = report['candidate_tool_failures'][0]
    assert candidate['classification'] == 'candidate_tool_failure'
    assert candidate['call_id'] == 'failed-patch' and candidate['thread_id'] == 'main'
    assert candidate['delta_ms'] == 10 and candidate['raw'] == raw
    assert candidate['failed_tool_record'] == rows[-1]
    assert candidate['paired_request_record'] == rows[-2]
    assert candidate['request_ordinal'] == 10 and candidate['response_ordinal'] == 11
    full_audit = post(evidence)
    assert full_audit['raw_diagnostics']['exec'] == DIAGNOSTIC * 2 + raw + '\n'
    if direct:
        # The unchanged normalizer still rejects unresolved direct-patch write evidence.
        assert not full_audit['ok']
        assert any('Unresolved patch write evidence' in error for error in full_audit['trace_errors'])
    else:
        assert full_audit['ok']


@pytest.mark.parametrize('failure', ['outside_workspace', 'wrong_patch_file', 'missing_request', 'missing_failed_marker',
    'different_failure_text', 'encrypted_output', 'too_late', 'missing_timestamp', 'duplicate_output',
    'duplicate_request', 'inherited_history', 'missing_history_boundary', 'wrong_tool', 'final_prose',
    'wrong_turn', 'repeated_stderr', 'invalid_source_cwd', 'unindented_context'])
def test_patch_correlation_rejects_unproven_or_ambiguous_failure(evidence, failure):
    rows, raw = patch_failure(evidence)
    request, returned = rows[-2:]
    if failure == 'outside_workspace':
        raw = raw.replace(r'C:\repos\candidate\tests', r'C:\repos\other\tests')
        returned['payload']['output'][1]['text'] = 'Script error:\n' + raw.split('error=', 1)[1]
    elif failure == 'wrong_patch_file':
        request['payload']['input'] = request['payload']['input'].replace('tests/test_cli.py', 'tests/other.py')
    elif failure == 'missing_request':
        rows.remove(request)
    elif failure == 'missing_failed_marker':
        returned['payload']['output'][0]['text'] = 'Script completed\nWall time 0.02 seconds\nOutput:\n'
    elif failure == 'different_failure_text':
        returned['payload']['output'][1]['text'] += '\n    additional context'
    elif failure == 'encrypted_output':
        returned['payload']['output'][1]['type'] = 'encrypted_content'
    elif failure == 'too_late':
        returned['timestamp'] = '2026-10-23T17:53:01.111Z'
    elif failure == 'missing_timestamp':
        returned.pop('timestamp')
    elif failure == 'duplicate_output':
        rows.append(dict(returned))
    elif failure == 'duplicate_request':
        rows.append(dict(request))
    elif failure == 'inherited_history':
        rows[0]['payload'].update(parent_thread_id='parent', subagent_history_start_ordinal=12)
    elif failure == 'missing_history_boundary':
        rows[0]['payload']['parent_thread_id'] = 'parent'
    elif failure == 'wrong_tool':
        request['payload'].update(name='exec_command')
    elif failure == 'final_prose':
        returned['payload'] = {'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': raw}]}
    elif failure == 'wrong_turn':
        returned['payload']['internal_chat_message_metadata_passthrough']['turn_id'] = 'other-turn'
    elif failure == 'invalid_source_cwd':
        rows[0]['payload']['cwd'] = r'C:\repos\other'
    elif failure == 'unindented_context':
        raw = raw.replace('\n    assert', '\nassert')
        returned['payload']['output'][1]['text'] = 'Script error:\n' + raw.split('error=', 1)[1]
    (evidence['run'] / 'session.jsonl').write_text('\n'.join(map(json.dumps, rows)))
    stderr = DIAGNOSTIC * 2 + raw + '\n'
    if failure == 'repeated_stderr':
        stderr += raw + '\n'
    try:
        correlated = audit.correlate_candidate_tool_failures(evidence['run'], stderr)
    except ValueError:
        correlated = []
    assert correlated == []
    report = audit.classify_diagnostics({'plugin-install': '', 'hook-catalogue': '', 'exec': stderr},
        ROOT, '0.164.0', True, True, True, correlated)
    assert not report['ok'] and report['candidate_tool_failures'] == []


def test_reaudit_requires_byte_identical_retained_runtime_captures(evidence):
    assert prepare(evidence)['ok']
    assert post(evidence)['ok']
    saved = evidence['run'] / 'native-hook-trust/native-hook-catalog-stderr.txt'
    before = (saved.read_bytes(), saved.stat().st_mtime_ns)
    assert post(evidence)['ok']
    assert (saved.read_bytes(), saved.stat().st_mtime_ns) == before
    (evidence['runtime'] / saved.name).write_text('ERROR changed source')
    report = post(evidence)
    assert not report['ok']
    assert any('differs from source' in error for error in report['proof_errors'])
    assert (saved.read_bytes(), saved.stat().st_mtime_ns) == before


def test_retained_paid_fixture_correlates_exactly_two_physical_failed_calls_read_only():
    run = Path(__file__).resolve().parents[2] / 'baselines/c1-csvledger/20261023T182024Z-5fa13924'
    source = run / 'subagents/rollout-01a16a06-b192-70a0-8d10-58bcd309ef80.jsonl'
    files = [run / 'run.json', run / 'stderr.txt', source]
    before = {path: audit.sha(path) for path in files}
    stderr = (run / 'stderr.txt').read_text(encoding='utf-8-sig')
    failures = audit.correlate_candidate_tool_failures(run, stderr)
    assert [(row['call_id'], row['response_ordinal'], row['delta_ms']) for row in failures] == [
        ('call_3fdf940f6118420c8642aae673e7ff26', 414, 16.649),
        ('call_9f2bfde8dbd245bab8086c54a3200eae', 427, 1.247)]
    assert all(row['thread_id'] == '01a16a06-b192-70a0-8d10-58bcd309ef80' for row in failures)
    assert {path: audit.sha(path) for path in files} == before
