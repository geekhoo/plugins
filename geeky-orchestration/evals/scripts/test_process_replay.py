"""Offline source-bound process/cache replay contracts; no native agents or model calls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest


def module(filename, name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


CT = module('codex-trace.py', 'replay_ct')
SR = module('score-run.py', 'replay_sr')


def fixture(tmp_path):
    row = {'timestamp': '2026-10-24T00:00:00.000Z', 'type': 'response_item',
           'payload': {'type': 'function_call', 'call_id': 'call1',
                       'arguments': json.dumps({'cmd': 'T1 Done PASS critical 1234567'})}}
    source = tmp_path / 'session.jsonl'
    source.write_text(json.dumps(row) + '\n', encoding='utf8')
    ref = {'path': source.name, 'record_index': 0, 'timestamp': row['timestamp'],
           'record_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest(),
           'source_text': 'T1 Done PASS critical 1234567'}
    artifact = {'schema': 'geeky-eval.process-evidence/1',
                'sources': {source.name: hashlib.sha256(source.read_bytes()).hexdigest()},
                'contexts': [{'call_id': 'main:call1', 'role': 'coder', 'tasks': ['T1'], 'refs': [ref]}]}
    path = tmp_path / 'process-evidence.json'
    path.write_text(json.dumps(artifact), encoding='utf8')
    return path, artifact


def test_source_bound_process_accepts_real_visible_record(tmp_path):
    path, artifact = fixture(tmp_path)
    assert CT.process_evidence(tmp_path, {'main:call1'}, path) == artifact


@pytest.mark.parametrize('mutation', ['hash', 'ordinal', 'text', 'time', 'call', 'task'])
def test_process_evidence_rejects_stale_or_unbound_interpretation(tmp_path, mutation):
    path, artifact = fixture(tmp_path)
    ref = artifact['contexts'][0]['refs'][0]
    if mutation == 'hash': artifact['sources']['session.jsonl'] = '0' * 64
    if mutation == 'ordinal': ref['record_index'] = 2
    if mutation == 'text': ref['source_text'] = 'unrecorded claim'
    if mutation == 'time': ref['timestamp'] = '2026-10-24T01:00:00.000Z'
    if mutation == 'call': artifact['contexts'][0]['call_id'] = 'main:other'
    if mutation == 'task': artifact['contexts'][0]['tasks'] = ['T9']
    path.write_text(json.dumps(artifact), encoding='utf8')
    with pytest.raises(ValueError): CT.process_evidence(tmp_path, {'main:call1'}, path)


def test_strict_commit_never_falls_back_to_documentation_head():
    scorer = SR.Scorer.__new__(SR.Scorer)
    scorer.strict = True
    scorer.trace = SimpleNamespace(process=None)
    scorer.commits = [{'stage': 'impl-review', 'tasks': ['T1'], 'files': [('docs/handoff.md', 2)]}]
    with pytest.raises(ValueError, match='fallback forbidden'): scorer.rerun_commit('T1')


def cache_fixture(tmp_path):
    task = tmp_path / 'T1-task.md'
    task.write_text('frozen task', encoding='utf8')
    source = {'T1': {'commit': 'a' * 7, 'results': [{'command': 'python -m pytest -q', 'exit': 0, 'tail': '3 passed'}]}}
    (tmp_path / 'source.json').write_text(json.dumps(source), encoding='utf8')
    (tmp_path / 'stdout.txt').write_text('3 passed', encoding='utf8')
    digest = lambda name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
    entry = {'task': 'T1', 'commit': 'a' * 40, 'task_file_sha256': digest(task.name),
             'command': 'python -m pytest -q', 'exit_code': 0, 'output_scope': 'tail',
             'stdout_path': 'stdout.txt', 'stdout_sha256': digest('stdout.txt'),
             'stderr_path': None, 'stderr_sha256': None, 'duration_ms': None,
             'provenance': {'kind': 'saved-tail'},
             'source_document': {'path': 'source.json', 'sha256': digest('source.json'), 'record_pointer': '/T1/results/0'}}
    path = tmp_path / 'validation-cache.json'
    path.write_text(json.dumps({'schema': 'geeky-eval.validation-cache/1', 'entries': [entry]}), encoding='utf8')
    scorer = SR.Scorer.__new__(SR.Scorer)
    scorer.validation_cache_path, scorer.tasks, scorer.ws = path, ['T1'], tmp_path
    scorer.task_files = {'T1': task}
    scorer.rerun_commit = lambda task: ('a' * 40, False, 'source')
    scorer.validation_commands = lambda task: ['python -m pytest -q']
    return scorer, entry


def test_saved_tail_reuses_source_result_without_executing_validation(tmp_path):
    scorer, _ = cache_fixture(tmp_path)
    with patch.object(SR.subprocess, 'run', return_value=SimpleNamespace(stdout=b'frozen task')) as run:
        scorer.cached_validation()
    assert run.call_count == 1
    assert run.call_args.args[0][:2] == ['git', 'show']
    result = scorer.rerun_results['T1']['results'][0]
    assert result['reused'] and result['output_scope'] == 'tail' and not result['stderr_known']
    assert scorer.rerun_results['T1']['commit'] == 'a' * 40


@pytest.mark.parametrize('field,value', [('task_file_sha256','0'*64), ('exit_code',1), ('command','python different'), ('stdout_sha256','0'*64)])
def test_cache_mismatch_blocks_without_running_validation(tmp_path, field, value):
    scorer, entry = cache_fixture(tmp_path)
    entry[field] = value
    scorer.validation_cache_path.write_text(json.dumps({'schema': 'geeky-eval.validation-cache/1', 'entries': [entry]}), encoding='utf8')
    with patch.object(SR.subprocess, 'run', return_value=SimpleNamespace(stdout=b'frozen task')):
        with pytest.raises(ValueError): scorer.cached_validation()


def test_explicit_missing_process_file_is_not_silent_fallback(tmp_path):
    with pytest.raises(ValueError, match='missing'):
        CT.process_evidence(tmp_path, set(), tmp_path / 'missing.json')


def test_process_ciphertext_is_not_ownership_evidence(tmp_path):
    path, artifact = fixture(tmp_path)
    row = json.loads((tmp_path / 'session.jsonl').read_text())
    row['payload']['arguments'] = '{}'
    row['payload']['encrypted_content'] = 'T1 Done PASS critical 1234567'
    (tmp_path / 'session.jsonl').write_text(json.dumps(row)+'\n', encoding='utf8')
    artifact['sources']['session.jsonl'] = hashlib.sha256((tmp_path / 'session.jsonl').read_bytes()).hexdigest()
    artifact['contexts'][0]['refs'][0]['record_sha256'] = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    path.write_text(json.dumps(artifact), encoding='utf8')
    with pytest.raises(ValueError, match='opaque'): CT.process_evidence(tmp_path, {'main:call1'}, path)


def test_missing_explicit_process_path_marks_normalized_trace_incomplete(tmp_path):
    (tmp_path / 'stream.jsonl').write_text('{"type":"thread.started","thread_id":"main"}\n{"type":"turn.completed"}\n', encoding='utf8')
    (tmp_path / 'session.jsonl').write_text('{"timestamp":"2026-10-24T00:00:00.000Z","type":"session_meta","payload":{"id":"main"}}\n', encoding='utf8')
    result = CT.load(tmp_path, process_path=tmp_path / 'missing.json')
    assert not result['trace_complete']
    assert any('Explicit process evidence file is missing' in e for e in result['trace_errors'])


@pytest.mark.parametrize('name,raw,expected', [
    ('CodexExec', 'text(await tools.exec_command({cmd:"Get-Content kanban.md, handoff.md"}));', False),
    ('PowerShell', 'Get-Content kanban.md, handoff.md', False),
    ('CodexExec', 'text(await tools.exec_command({cmd:"Set-Content kanban.md $body"}));', False),
    ('PowerShell', 'Set-Content kanban.md $body', True),
    ('Edit', '', True)])
def test_native_lane_write_uses_actual_effect_not_read_or_enclosing_js(name, raw, expected):
    call = SimpleNamespace(id='call', name=name, raw=raw)
    assert SR.native_lane_write(call, set()) is expected
    assert SR.native_lane_write(call, {'call'})
