"""Reviewed stage annotations are checked against plaintext immutable rollout sources."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


def module(filename, name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


CT = module('codex-trace.py', 'codex_stage_test')
AR = module('analyze-run.py', 'codex_stage_analyzer')


def write_rows(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


@pytest.fixture
def stage_run(tmp_path):
    command = '; '.join('Get-Content skills/' + name + '/SKILL.md' for name in CT.STAGES)
    def row(ordinal, timestamp, kind, payload):
        return {'ordinal': ordinal, 'timestamp': timestamp, 'type': kind, 'payload': payload}
    rows = [row(0, '2026-10-23T18:20:30.000Z', 'session_meta', {'id': 'main'}),
        row(1, '2026-10-23T18:20:41.009Z', 'response_item', {'type': 'function_call',
            'name': 'exec_command', 'call_id': 'bulk', 'arguments': json.dumps({'cmd': command})}),
        row(2, '2026-10-23T18:20:43.059Z', 'event_msg', {'type': 'item_completed', 'item': {
            'type': 'CommandExecution', 'id': 'bulk', 'command': ['pwsh', '-Command', command],
            'exit_code': 0, 'status': 'completed', 'aggregated_output': 'skill texts'}})]
    announcements = [
        ('geeky-plan', '2026-10-23T18:22:23.953Z', 'The specification is committed. I’m now using `geeky-plan` to create phases.'),
        ('plan-review', '2026-10-23T18:24:15.534Z', 'I’m now using `plan-review` for independent checks.'),
        ('geeky-implement', '2026-10-23T18:25:13.043Z', 'I’m now using `geeky-implement`; preflight passed.'),
        ('impl-review', '2026-10-23T18:36:10.957Z', 'I’m now using `impl-review` for the authorized final review.'),
        ('impl-review', '2026-10-23T18:41:10.123Z', 'I’m running `impl-review` again on the affected behavior.')]
    entries = [{'stage': 'spec-research', 'kind': 'skill-read', 'source_ordinal': 2,
                'source_timestamp': rows[2]['timestamp'], 'timestamp': rows[1]['timestamp']}]
    for ordinal, (stage, timestamp, message) in enumerate(announcements, 3):
        rows.append(row(ordinal, timestamp, 'response_item', {'type': 'message', 'role': 'assistant',
            'content': [{'type': 'output_text', 'text': message}]}))
        entries.append({'stage': stage, 'kind': 'announcement', 'source_ordinal': ordinal,
            'source_timestamp': timestamp, 'timestamp': timestamp, 'source_text': message})
    rows += [row(8, '2026-10-23T18:42:54.839Z', 'event_msg', {'type': 'token_count', 'info': {
        'total_token_usage': {'input_tokens': 100, 'output_tokens': 10}}}),
        row(9, '2026-10-23T18:42:54.840Z', 'event_msg', {'type': 'task_complete'})]
    write_rows(tmp_path / 'session.jsonl', rows)
    write_rows(tmp_path / 'stream.jsonl', [{'type': 'thread.started', 'thread_id': 'main'}, {'type': 'turn.completed'}])
    (tmp_path / 'run.json').write_text('{"harness":"codex"}', encoding='utf-8')
    artifact = {'schema': 'geeky-eval.stage-evidence/1',
        'session_sha256': hashlib.sha256((tmp_path / 'session.jsonl').read_bytes()).hexdigest(), 'stages': entries}
    return tmp_path, rows, artifact


def save_artifact(folder, artifact):
    (folder / 'stage-evidence.json').write_text(json.dumps(artifact, ensure_ascii=False), encoding='utf-8')


def test_reviewed_transitions_ignore_bulk_reads_and_repeat_review(stage_run):
    folder, _, artifact = stage_run
    save_artifact(folder, artifact)
    before = (folder / 'session.jsonl').read_bytes()
    normalized = CT.load(folder)
    assert normalized['trace_complete'], normalized['trace_errors']
    assert normalized['stage_evidence_mode'] == 'reviewed'
    report = AR.analyze(folder)
    assert [s['name'] for s in report['stages']] == [e['stage'] for e in artifact['stages']]
    assert report['impl_review_rounds'] == 2
    assert report['tool_calls_main']['CodexSkillRead'] == 5
    assert report['skill_invocations']['geeky-implement'] == 1
    assert report['stages'][3]['minutes'] == 11.0
    annotations = [e for e in normalized['stream'] if (e.get('codex_provenance') or {}).get('kind') == 'announcement']
    assert len(annotations) == 5
    assert (folder / 'session.jsonl').read_bytes() == before


def test_absent_artifact_keeps_legacy_behavior(stage_run):
    folder, _, _ = stage_run
    report = CT.load(folder)
    assert report['trace_complete'] and report['stage_evidence_mode'] == 'legacy-skill-file-read'
    assert AR.analyze(folder)['tool_calls_main']['Skill'] == 5


@pytest.mark.parametrize('mutation', ['sha', 'ordinal', 'text', 'time', 'source-time', 'stage', 'order', 'missing-stage', 'initial-read'])
def test_invalid_artifact_fails_without_legacy_stage_fallback(stage_run, mutation):
    folder, _, artifact = stage_run
    artifact = copy.deepcopy(artifact)
    entry = artifact['stages'][1]
    if mutation == 'sha':
        artifact['session_sha256'] = '0' * 64
    elif mutation == 'ordinal':
        entry['source_ordinal'] = 999
    elif mutation == 'text':
        entry['source_text'] += ' changed'
    elif mutation == 'time':
        entry['timestamp'] = '2026-10-23T18:22:24.953Z'
    elif mutation == 'source-time':
        entry['source_timestamp'] = '2026-10-23T18:22:24.953Z'
    elif mutation == 'stage':
        entry['stage'] = 'archive'
    elif mutation == 'order':
        artifact['stages'][1:3] = reversed(artifact['stages'][1:3])
    elif mutation == 'missing-stage':
        del artifact['stages'][2]
    elif mutation == 'initial-read':
        artifact['stages'][0]['source_ordinal'] = 1
        artifact['stages'][0]['source_timestamp'] = artifact['stages'][0]['timestamp']
    save_artifact(folder, artifact)
    result = CT.load(folder)
    assert not result['trace_complete']
    assert any('Invalid stage evidence' in e for e in result['trace_errors'])
    assert not AR.analyze(folder)['skill_invocations']


@pytest.mark.parametrize(('message', 'role', 'channel'), [
    ('I will use `geeky-plan` next.', 'assistant', None),
    ('I’m not using `geeky-plan`.', 'assistant', None),
    ('I plan to use `geeky-plan`.', 'assistant', None),
    ('I’m now using `geeky-plan` after the research finishes.', 'assistant', None),
    ('"I’m now using `geeky-plan`" is an example.', 'assistant', None),
    ('Final summary: I’m now using `geeky-plan`.', 'assistant', None),
    ('I’m now using `geeky-plan`.', 'user', None),
    ('I’m now using `geeky-plan`.', 'assistant', 'final'),
])
def test_only_plain_main_present_stage_announcements_pass(stage_run, message, role, channel):
    folder, rows, artifact = stage_run
    rows[3]['payload'].update(role=role, content=[{'type': 'output_text', 'text': message}])
    if channel:
        rows[3]['payload']['channel'] = channel
    write_rows(folder / 'session.jsonl', rows)
    artifact['session_sha256'] = hashlib.sha256((folder / 'session.jsonl').read_bytes()).hexdigest()
    artifact['stages'][1]['source_text'] = message
    save_artifact(folder, artifact)
    assert not CT.load(folder)['trace_complete']


def test_actual_reviewed_paid_trace_is_read_only_when_supplied():
    supplied = os.environ.get('CODEX_STAGE_PROOF')
    if not supplied:
        pytest.skip('Set CODEX_STAGE_PROOF after the parent prepares the reviewed artifact')
    folder = Path(supplied)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*.jsonl')}
    result = CT.load(folder)
    assert result['trace_complete'], result['trace_errors']
    assert result['stage_evidence_mode'] == 'reviewed'
    report = AR.analyze(folder)
    assert report['impl_review_rounds'] == 2
    assert report['tokens']['total'] == 17729214
    assert report['model_calls'] == 205
    assert [s['name'] for s in report['stages']] == list(CT.STAGES) + ['impl-review']
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*.jsonl')}
