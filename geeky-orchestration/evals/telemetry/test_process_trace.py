"""Offline tests for the process trace contract, exporter and Codex adapter. No network."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import process_trace  # noqa: E402

spec = importlib.util.spec_from_file_location('codex_process_events', HERE / 'codex-process-events.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

BOARD = '# Kanban\n\n## Backlog\n- T2-b\n\n## Ready\n- T1-a\n\n## In Progress\n\n## In Review\n\n## Done\n\n## Validation Checklist\n- [x] T9 is not a task\n'


def doc(**overrides):
    base = {'schema': process_trace.SCHEMA, 'session_id': 'c2/codex/20261104T000000Z', 'harness': 'codex', 'adapter': 'test', 'adapter_version': '1', 'environment': 'mxc-win',
            'run_start': '2026-11-04T04:00:00Z', 'run_end': '2026-11-04T05:00:00Z', 'tags': ['case:c2'], 'metadata': {'case': 'c2'},
            'coverage': {'stage': 'complete', 'lane': 'complete', 'review': 'partial', 'gate': 'unknown'},
            'stages': [{'stage': 'plan-review', 'start': '2026-11-04T04:00:00Z', 'end': '2026-11-04T04:10:00Z', 'evidence': 'commit', 'source': 'abc1234'},
                       {'stage': 'geeky-implement', 'start': '2026-11-04T04:10:00Z', 'end': '2026-11-04T05:00:00Z', 'evidence': 'commit', 'source': 'def5678'}],
            'tasks': [{'task_id': 'T1', 'start': '2026-11-04T04:11:00Z', 'end': '2026-11-04T04:20:00Z', 'final_lane': 'Done', 'owner_actor': 'thread-1'}],
            'events': [{'kind': 'lane', 'at': '2026-11-04T04:11:00Z', 'task_id': 'T1', 'from_lane': 'Ready', 'to_lane': 'In Progress', 'actor': 'orchestrator', 'source_ref': 's:1'},
                       {'kind': 'gate', 'at': '2026-11-04T04:19:00Z', 'gate_name': 'check-dod', 'gate_result': 'pass', 'task_id': 'T1', 'actor': 'orchestrator', 'source_ref': 's:2'},
                       {'kind': 'review', 'at': '2026-11-04T04:30:00Z', 'review_scope': 'phase-1', 'verdict': 'READY TO ADVANCE', 'actor': 'thread-2', 'source_ref': 's:3'}]}
    base.update(overrides)
    return base


def attrs(span):
    out = {}
    for row in span['attributes']:
        value = row['value']
        out[row['key']] = value.get('stringValue') if 'stringValue' in value else [item['stringValue'] for item in value['arrayValue']['values']]
    return out


def test_spans_follow_the_contract():
    spans = process_trace.build_spans(process_trace.validate(doc()))
    names = [span['name'] for span in spans]
    assert names == ['geeky-orchestration.end-to-end', 'stage:plan-review', 'stage:geeky-implement', 'task', 'lane.move', 'gate:check-dod', 'review.verdict']
    assert len({span['traceId'] for span in spans}) == 1 and len({span['spanId'] for span in spans}) == len(spans)
    for span in spans:
        values = attrs(span)
        assert values['langfuse.session.id'] == 'c2/codex/20261104T000000Z' and values['langfuse.user.id'] == 'codex/workflow'
        assert values['langfuse.trace.name'] == 'geeky-orchestration.end-to-end' and values['langfuse.environment'] == 'mxc-win'
        assert 'process-trace' in values['langfuse.trace.tags']
    lane = next(span for span in spans if span['name'] == 'lane.move')
    task = next(span for span in spans if span['name'] == 'task')
    assert lane['parentSpanId'] == task['spanId'] and lane['startTimeUnixNano'] == lane['endTimeUnixNano']
    values = attrs(lane)
    assert values['langfuse.observation.type'] == 'event' and values['langfuse.observation.metadata.to_lane'] == 'In Progress'
    assert values['langfuse.observation.metadata.workflow_stage'] == 'geeky-implement'


def test_root_output_is_a_chat_timeline_for_session_replay():
    root = attrs(process_trace.build_spans(doc())[0])
    assert json.loads(root['langfuse.observation.input'])[0]['role'] == 'user'
    content = json.loads(root['langfuse.observation.output'])[0]['content']
    assert '04:11:00Z T1: Ready -> In Progress' in content and 'enter geeky-implement' in content and 'check-dod' not in content
    assert root['langfuse.observation.metadata.coverage_gate'] == 'unknown'


def test_commit_bound_move_is_labelled_in_the_timeline():
    event = {'kind': 'lane', 'task_id': 'T1', 'from_lane': 'Ready', 'to_lane': 'Done', 'lane_evidence': 'commit-bound'}
    assert process_trace.event_line(event) == 'T1: Ready -> Done (by this commit)'


def test_span_ids_are_stable_across_builds():
    assert [span['spanId'] for span in process_trace.build_spans(doc())] == [span['spanId'] for span in process_trace.build_spans(doc())]


@pytest.mark.parametrize('change', [{'schema': 'x'}, {'session_id': 'x' * 200}, {'coverage': {'stage': 'yes', 'lane': 'unknown', 'review': 'unknown', 'gate': 'unknown'}},
                                    {'stages': [{'stage': 'made-up', 'start': '2026-11-04T04:00:00Z', 'end': '2026-11-04T04:10:00Z'}]},
                                    {'stages': [{'stage': 'plan-review', 'start': '2026-11-04T05:00:00Z', 'end': '2026-11-04T04:10:00Z'}]},
                                    {'events': [{'kind': 'gate', 'at': '2026-11-04T04:00:00Z', 'gate_name': 'made-up', 'gate_result': 'pass'}]}])
def test_invalid_documents_are_rejected(change):
    with pytest.raises(ValueError):
        process_trace.validate(doc(**change))


class FakeClient:
    def __init__(self, existing=()):
        self.existing, self.sent = list(existing), []

    def observations(self, **query):
        if 'name' in query:
            return self.existing
        return [{'id': span['spanId']} for span in self.sent[-1]['resourceSpans'][0]['scopeSpans'][0]['spans']]

    def export(self, body):
        self.sent.append(body)
        return 200


def test_export_happens_once_and_is_verified(tmp_path):
    client = FakeClient()
    spans = process_trace.build_spans(doc())
    result = process_trace.export_once(doc(), spans, tmp_path, client, wait=5)
    assert len(client.sent) == 1 and result['missing'] == 0 and result['unique'] == len(spans)
    with pytest.raises(SystemExit):
        process_trace.export_once(doc(), spans, tmp_path, client, wait=5)
    assert len(client.sent) == 1


def test_export_refuses_a_session_that_already_has_a_process_trace(tmp_path):
    client = FakeClient(existing=[{'id': 'x'}])
    with pytest.raises(SystemExit):
        process_trace.export_once(doc(), process_trace.build_spans(doc()), tmp_path, client, wait=5)
    assert client.sent == []


def test_parse_board_uses_only_lane_sections():
    assert adapter.parse_board(BOARD) == {'T2': 'Backlog', 'T1': 'Ready'}
    assert adapter.parse_board('## Done\n- [x] T1-a\n- None\n') == {'T1': 'Done'}


def test_apply_update_moves_a_task_and_rejects_a_mismatch():
    body = '\n@@\n ## Ready\n-- T1-a\n@@\n ## In Progress\n+- T1-a\n'
    updated = adapter.apply_update(BOARD, body)
    assert adapter.parse_board(updated)['T1'] == 'In Progress'
    assert adapter.apply_update(BOARD, '\n@@\n-- T7-missing\n') is None


def op(at, kind='patch', ok=True, body=None, action='Update'):
    return {'at': at, 'kind': kind, 'ok': ok, 'ref': f's:{at}', 'actor': 'orchestrator', 'sections': [(action, 'docs/kanban.md', body or '')]}


def add_body(text):
    return '\n' + ''.join(f'+{line}\n' for line in text.split('\n'))


def test_replay_skips_failed_patches_and_flags_unknowable_writes():
    start = op('2026-11-04T04:00:00Z', action='Add', body=add_body(BOARD))
    failed = op('2026-11-04T04:01:00Z', ok=False, body='\n@@\n-- T7-missing\n')
    states, problems = adapter.replay([start, failed])
    assert len(states) == 1 and problems == []
    assert adapter.replay([start, op('2026-11-04T04:02:00Z', kind='shell')])[1]
    assert adapter.replay([start, op('2026-11-04T04:02:00Z', ok=None)])[1]
    assert 'did not apply' in adapter.replay([start, op('2026-11-04T04:02:00Z', body='\n@@\n-- T7-missing\n')])[1][0]


def test_reconcile_reports_a_gate_or_commit_disagreement():
    states = [{'at': '2026-11-04T04:00:00Z', 'text': BOARD, 'ref': 's:1', 'actor': 'orchestrator'}]
    good = {'at': '2026-11-04T04:01:00Z', 'ok': True, 'ref': 'g', 'counts': {'Backlog': 1, 'Ready': 1}}
    bad = {'at': '2026-11-04T04:01:00Z', 'ok': True, 'ref': 'g', 'counts': {'Done': 2}}
    assert adapter.reconcile(states, [good], [{'sha': 'a', 'text': BOARD.replace('\n', '\r\n')}])[0] == []
    assert adapter.reconcile(states, [bad], [])[0]
    assert adapter.reconcile(states, [], [{'sha': 'a', 'text': 'other'}])[0]
    failing_gate = dict(bad, ok=False)
    assert adapter.reconcile(states, [failing_gate], [])[0] == []


@pytest.mark.parametrize('text,verdict', [('## Summary\nVerdict: READY TO ADVANCE', 'READY TO ADVANCE'), ('**Verdict: NEEDS CHANGES.** Details', 'NEEDS CHANGES'), ('## T1: PASS\n', 'PASS'),
                                          ('Some text. **Verdict: NEEDS ATTENTION** until fixed', 'NEEDS ATTENTION'),
                                          ('Affected plan-review alignment verdict: **PASS**', 'PASS'), ('**Affected Alignment Verdict: CHANGES REQUIRED**', 'CHANGES REQUIRED')])
def test_verdict_is_read_from_anchored_text(text, verdict):
    found = adapter.VERDICT_LINE.findall(text) or [first or second for first, second in adapter.VERDICT_BOLD.findall(text)]
    assert found[-1].upper() == verdict


def test_verdict_mentioned_in_a_sentence_is_ignored():
    text = 'The earlier reviewer said READY TO ADVANCE before this change.'
    assert not (adapter.VERDICT_LINE.findall(text) or adapter.VERDICT_BOLD.findall(text))


def test_failed_patch_output_is_recognized():
    assert adapter.succeeded('apply_patch verification failed: Failed to read file') is False
    assert adapter.succeeded('Process exited with code 1') is False
    assert adapter.succeeded('Wall time: 0\nExit code: 0') is True
    assert adapter.succeeded('no status here') is None
    assert adapter.succeeded(None) is None


def test_commit_bound_events_say_so():
    rows = adapter.commit_bound_lane_events([{'sha': 'a', 'at': '2026-11-04T04:00:00Z', 'text': BOARD}, {'sha': 'b', 'at': '2026-11-04T05:00:00Z', 'text': BOARD.replace('## Ready\n- T1-a', '## Ready').replace('## Done\n', '## Done\n- T1-a\n')}])
    moved = rows[-1]
    assert (moved['task_id'], moved['from_lane'], moved['to_lane'], moved['lane_evidence']) == ('T1', 'Ready', 'Done', 'commit-bound')


def test_git_dates_become_utc(tmp_path):
    env = {'GIT_AUTHOR_DATE': '2026-11-04T12:00:00+08:00', 'GIT_COMMITTER_DATE': '2026-11-04T12:00:00+08:00'}
    import os
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs' / 'feature-specification.md').write_text('x', encoding='utf-8')
    subprocess.run(['git', '-C', str(tmp_path), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(tmp_path), '-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-qm', 'spec'], check=True, env={**os.environ, **env})
    assert adapter.first_commit_adding(tmp_path, '*feature-specification.md')[1] == '2026-11-04T04:00:00Z'
