"""Offline Codex trace contract tests; no model calls or source-run mutations."""
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


CT = module('codex-trace.py', 'codex_trace_test')
AR = module('analyze-run.py', 'analyze_codex_test')
SR = module('score-run.py', 'score_codex_test')


def row(kind, payload, second=0, **extra):
    return {'timestamp': f'2026-10-24T00:00:{second:02d}Z', 'type': kind, 'payload': payload, **extra}


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')


def usage(input_=100, cached=40, output=20):
    return {'type': 'token_count', 'info': {'total_token_usage': {
        'input_tokens': input_, 'cached_input_tokens': cached, 'output_tokens': output,
        'reasoning_output_tokens': 5, 'total_tokens': input_ + output}}}


@pytest.fixture
def trace_folder(tmp_path):
    (tmp_path / 'run.json').write_text(json.dumps({'harness': 'codex', 'case': 'c1-csvledger',
        'reference_eligible': False, 'tokens': None}), encoding='utf-8')
    write_jsonl(tmp_path / 'stream.jsonl', [{'type': 'thread.started', 'thread_id': 'main'},
        {'type': 'turn.started'}, {'type': 'turn.completed', 'usage': {'input_tokens': 999999}}])
    rows = [row('session_meta', {'id': 'main', 'cwd': str(tmp_path)}),
        row('response_item', {'type': 'function_call', 'call_id': 'shell', 'name': 'exec_command',
            'arguments': json.dumps({'cmd': 'python validate-kanban.py --path docs/p'})}, 1),
        row('event_msg', {'type': 'item_completed', 'item': {'type': 'CommandExecution', 'id': 'shell',
            'command': ['pwsh', '-NoProfile', '-Command', 'python validate-kanban.py --path docs/p'],
            'aggregated_output': 'OK: 1 task(s) tracked', 'exit_code': 0, 'status': 'completed'}}, 2),
        row('event_msg', usage(), 3), row('event_msg', usage(), 4),
        row('token_usage_record', {'thread_id': 'main', 'response_id': 'r1'}, 4),
        row('token_usage_record', {'thread_id': 'main', 'response_id': 'r1'}, 4),
        row('event_msg', usage(150, 60, 30), 5),
        row('token_usage_record', {'thread_id': 'main', 'response_id': 'r2'}, 5),
        row('response_item', {'type': 'message', 'role': 'assistant',
            'content': [{'type': 'output_text', 'text': 'Final evidence report'}]}, 6),
        row('event_msg', {'type': 'task_complete'}, 7)]
    write_jsonl(tmp_path / 'session.jsonl', rows)
    return tmp_path, rows


def test_latest_cumulative_usage_and_same_rubric_gate(trace_folder):
    folder, _ = trace_folder
    report = AR.analyze(folder)
    assert report['trace_complete'], report['trace_errors']
    assert report['tokens']['input'] == 150
    assert report['tokens']['cached_input'] == 60
    assert report['tokens']['total'] == 180
    assert report['tokens']['cost_usd_estimate'] is None
    assert report['model_calls'] == 2
    assert report['latency_median_ms'] is None
    assert report['gate_results']['validate-kanban']['pass'] == 1
    trace = SR.Trace(folder)
    assert len(trace.calls) == 1 and trace.calls[0].cmd.startswith('python validate-kanban.py')
    assert SR.AR.gate_outcomes(trace.calls[0].name, trace.calls[0].inp,
                               (trace.calls[0].text, trace.calls[0].is_error)) == [('validate-kanban', True)]


def test_completed_patch_keeps_edit_content_without_double_count(trace_folder):
    folder, rows = trace_folder
    rows += [row('response_item', {'type': 'custom_tool_call', 'name': 'apply_patch',
        'call_id': 'patch', 'input': '*** Begin Patch\n*** Update File: docs/p/kanban.md\n@@\n-old\n+## Done\n+- [x] T1\n*** End Patch'}, 8),
        row('event_msg', {'type': 'item_completed', 'item': {'type': 'FileChange', 'id': 'patch',
            'changes': {'docs/p/kanban.md': {'type': 'update', 'unified_diff': '@@ -0,0 +1,2 @@\n+## Done\n+- [x] T1'}},
            'status': 'completed'}}, 9)]
    write_jsonl(folder / 'session.jsonl', rows)
    trace = SR.Trace(folder)
    edits = [c for c in trace.calls if c.name == 'Edit']
    assert len(edits) == 1 and 'T1' in edits[0].inp['new_string']


def add_child(folder, rows, with_activity=True, parent='main'):
    rows += [row('response_item', {'type': 'function_call', 'call_id': 'spawn', 'name': 'spawn_agent',
        'arguments': json.dumps({'agent_type': 'code-reviewer', 'task_name': 'review', 'message': 'Review T1'})}, 8),
        row('response_item', {'type': 'function_call_output', 'call_id': 'spawn',
            'output': '{"task_name":"/root/review"}'}, 9)]
    if with_activity:
        rows += [row('event_msg', {'type': 'item_completed', 'item': {'type': 'SubAgentActivity',
            'kind': 'started', 'id': 'spawn', 'agent_thread_id': 'child'}}, 9)]
    write_jsonl(folder / 'session.jsonl', rows)
    child = [row('session_meta', {'id': 'child', 'parent_thread_id': parent,
        'agent_path': '/root/review', 'agent_role': 'code-reviewer', 'subagent_history_start_ordinal': 10}, ordinal=0),
        row('event_msg', usage(9000, 0, 9000), ordinal=2),
        row('response_item', {'type': 'function_call', 'call_id': 'inherited',
            'name': 'exec_command', 'arguments': '{"cmd":"must not count"}'}, ordinal=3),
        row('event_msg', usage(20, 5, 10), 10, ordinal=10),
        row('token_usage_record', {'thread_id': 'child', 'response_id': 'child-r1'}, 10, ordinal=11),
        row('response_item', {'type': 'message', 'role': 'assistant',
            'content': [{'type': 'output_text', 'text': 'T1 PASS; READY TO ADVANCE'}]}, 11, ordinal=12),
        row('event_msg', {'type': 'task_complete'}, 12, ordinal=13)]
    write_jsonl(folder / 'subagents/rollout-child.jsonl', child)


def test_child_usage_history_and_reviewer_summary(trace_folder):
    folder, rows = trace_folder
    add_child(folder, rows)
    report = CT.load(folder)
    assert report['trace_complete'], report['trace_errors']
    assert report['tokens']['total'] == 210 and report['tokens']['input'] == 170
    assert report['model_calls'] == 3
    trace = SR.Trace(folder)
    assert 'READY TO ADVANCE' in trace.agent_summary['main:spawn']
    assert not any(c.cmd == 'must not count' for c in trace.calls)
    assert trace.by_id['main:spawn'].inp['subagent_type'] == 'code-reviewer'


def test_child_interrupted_by_parent_is_complete(trace_folder):
    folder, rows = trace_folder
    add_child(folder, rows)
    child = folder / 'subagents/rollout-child.jsonl'
    kept = [r for r in map(json.loads, child.read_text(encoding='utf-8').splitlines()) if (r.get('payload') or {}).get('type') != 'task_complete']
    write_jsonl(child, kept + [row('event_msg', {'type': 'turn_aborted', 'reason': 'interrupted'}, 12, ordinal=13)])
    report = CT.load(folder)
    assert report['trace_complete'], report['trace_errors']


def test_main_thread_interruption_still_blocks_scoring(trace_folder):
    folder, rows = trace_folder
    write_jsonl(folder / 'session.jsonl', rows + [row('event_msg', {'type': 'turn_aborted', 'reason': 'interrupted'}, 8)])
    assert not CT.load(folder)['trace_complete']


def test_rejected_spawn_needs_no_child(trace_folder):
    folder, rows = trace_folder
    rows += [row('response_item', {'type': 'function_call', 'call_id': 'bad', 'name': 'spawn_agent',
                                   'arguments': json.dumps({'agent_type': 'code-reviewer', 'task_name': 'Bad-Name', 'message': 'x'})}, 8),
             row('response_item', {'type': 'function_call_output', 'call_id': 'bad',
                                   'output': 'agent_name must use only lowercase letters, digits, and underscores'}, 9)]
    write_jsonl(folder / 'session.jsonl', rows)
    report = CT.load(folder)
    assert report['trace_complete'], report['trace_errors']


@pytest.mark.parametrize('activity', [True, False])
def test_missing_spawned_child_fails_even_without_activity_record(trace_folder, activity):
    folder, rows = trace_folder
    add_child(folder, rows, with_activity=activity)
    (folder / 'subagents/rollout-child.jsonl').unlink()
    assert not CT.load(folder)['trace_complete']
    with pytest.raises(ValueError, match='Incomplete Codex trace'):
        SR.Trace(folder)


def test_unrelated_child_parent_is_rejected(trace_folder):
    folder, rows = trace_folder
    add_child(folder, rows, parent='unrelated')
    report = CT.load(folder)
    assert not report['trace_complete']
    assert any('parent' in error.lower() for error in report['trace_errors'])


def test_missing_usage_remains_null_and_scoring_refuses(trace_folder):
    folder, rows = trace_folder
    write_jsonl(folder / 'session.jsonl', [r for r in rows if r['payload'].get('type') != 'token_count'])
    report = AR.analyze(folder)
    assert not report['trace_complete']
    assert report['tokens']['total'] is None and report['tokens']['cost_usd_estimate'] is None
    with pytest.raises(ValueError, match='Incomplete Codex trace'):
        SR.Trace(folder)


def test_stream_item_shapes_are_partial_evidence_without_rollout(tmp_path):
    write_jsonl(tmp_path / 'stream.jsonl', [
        {'type': 'item.completed', 'item': {'id': 'cmd', 'type': 'command_execution',
            'command': 'python validate-kanban.py', 'aggregated_output': 'INVALID_KANBAN: missing', 'exit_code': 1}},
        {'type': 'item.completed', 'item': {'id': 'file', 'type': 'file_change', 'changes': [{'path': 'src.py'}]}},
        {'type': 'item.completed', 'item': {'id': 'msg', 'type': 'agent_message', 'text': 'Reported completion'}}])
    report = AR.analyze(tmp_path, harness='codex')
    assert not report['trace_complete'] and report['tokens']['total'] is None
    assert report['tool_calls_main'] == {'PowerShell': 1, 'Edit': 1}


def test_failed_skill_read_is_not_invocation(trace_folder):
    folder, rows = trace_folder
    for r in rows:
        item = r['payload'].get('item', {})
        if item.get('type') == 'CommandExecution':
            item.update(command=['pwsh', '-Command', 'Get-Content skills/geeky-plan/SKILL.md'], exit_code=1, status='failed')
    write_jsonl(folder / 'session.jsonl', rows)
    assert AR.analyze(folder)['skill_invocations'] == {}


def test_full_shared_scorer_non_reference_empty_fixture(trace_folder, monkeypatch):
    folder, _ = trace_folder
    ws = folder / 'workspace'
    (ws / '.git').mkdir(parents=True)
    plan = ws / 'docs/p'
    (plan / 'tasks').mkdir(parents=True)
    (plan / 'kanban.md').write_text('## Done\n', encoding='utf-8')
    run = json.loads((folder / 'run.json').read_text())
    run['workspace'] = str(ws)
    (folder / 'run.json').write_text(json.dumps(run), encoding='utf-8')
    # External Git/validator boundaries are isolated; the complete shared rubric runs.
    monkeypatch.setattr(SR, 'git', lambda *args, **kwargs: '')
    monkeypatch.setattr(SR, 'commits', lambda *args: [])
    monkeypatch.setattr(SR, 'run_script', lambda *args: (False, 'Synthetic fixture deliberately incomplete'))
    score = SR.Scorer(folder, rerun=False).score()
    assert score['harness'] == 'codex'
    dimensions = score['dimensions']
    assert score['composite'] == SR.composite(dimensions['quality']['capped'], dimensions['adherence']['capped'],
                                            dimensions['consistency']['score'], dimensions['task_tier']['score'])
    assert any(c['status'] == 'fail' for c in score['checks'])
    assert score['breakdown']['tokens_total'] == 180


def test_nested_child_tools_keep_dispatch_ancestry(trace_folder):
    folder, rows = trace_folder
    add_child(folder, rows)
    path = folder / 'subagents/rollout-child.jsonl'
    child_rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    child_rows += [row('response_item', {'type': 'function_call', 'call_id': 'nested', 'name': 'spawn_agent',
        'arguments': json.dumps({'agent_type': 'geeky-coder', 'task_name': 'nested', 'message': 'Implement T1'})}, 13, ordinal=14),
        row('response_item', {'type': 'function_call_output', 'call_id': 'nested', 'output': '{"task_name":"/root/review/nested"}'}, 14, ordinal=15),
        row('event_msg', {'type': 'item_completed', 'item': {'type': 'SubAgentActivity',
            'kind': 'started', 'id': 'nested', 'agent_thread_id': 'grandchild'}}, 14, ordinal=16)]
    write_jsonl(path, child_rows)
    grandchild = [row('session_meta', {'id': 'grandchild', 'parent_thread_id': 'child',
        'agent_path': '/root/review/nested', 'agent_role': 'geeky-coder'}),
        row('response_item', {'type': 'function_call', 'call_id': 'work', 'name': 'exec_command',
            'arguments': '{"cmd":"python -m pytest"}'}, 15),
        row('event_msg', {'type': 'item_completed', 'item': {'type': 'CommandExecution', 'id': 'work',
            'command': ['pwsh', '-Command', 'python -m pytest'], 'aggregated_output': '1 passed',
            'exit_code': 0, 'status': 'completed'}}, 16),
        row('event_msg', usage(10, 0, 5), 17), row('event_msg', {'type': 'task_complete'}, 18)]
    write_jsonl(folder / 'subagents/nested/rollout-grandchild.jsonl', grandchild)
    report = CT.load(folder)
    assert report['trace_complete'], report['trace_errors']
    assert report['tokens']['total'] == 225
    trace = SR.Trace(folder)
    call = trace.by_id['grandchild:work']
    assert call.parent == 'child:nested'
    assert call.root.id == 'main:spawn'
    assert AR.analyze(folder)['validation_runs']['sub'] == 1


@pytest.mark.parametrize('mutation', ['decreasing_usage', 'bad_subset', 'timestamp', 'aborted', 'missing_output'])
def test_corrupt_or_incomplete_evidence_blocks_scoring(trace_folder, mutation):
    folder, rows = trace_folder
    if mutation == 'decreasing_usage':
        rows += [row('event_msg', usage(1, 0, 5), 8)]
    elif mutation == 'bad_subset':
        rows += [row('event_msg', usage(150, 151, 30), 8)]
    elif mutation == 'timestamp':
        rows[1]['timestamp'] = None
    elif mutation == 'aborted':
        rows += [row('event_msg', {'type': 'turn_aborted'}, 8)]
    elif mutation == 'missing_output':
        rows += [row('response_item', {'type': 'function_call', 'call_id': 'unresolved',
            'name': 'exec_command', 'arguments': '{"cmd":"python -m pytest"}'}, 8)]
    write_jsonl(folder / 'session.jsonl', rows)
    report = CT.load(folder)
    assert not report['trace_complete']
    with pytest.raises(ValueError, match='Incomplete Codex trace'):
        SR.Trace(folder)


def test_truncated_trace_is_not_silently_accepted(trace_folder):
    folder, _ = trace_folder
    with (folder / 'session.jsonl').open('a', encoding='utf-8') as handle:
        handle.write('{"truncated":')
    report = CT.load(folder)
    assert not report['trace_complete']
    assert any('Malformed JSONL' in error for error in report['trace_errors'])


def test_native_completed_error_item_blocks_scoring(trace_folder):
    folder, _ = trace_folder
    with (folder / 'stream.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({'type': 'item.completed', 'item': {
            'id': 'hook-failure', 'type': 'error', 'message': 'Code Mode hook failed'}}) + '\n')
    report = CT.load(folder)
    assert not report['trace_complete'] and 'Failed/error stream' in report['trace_errors']
    with pytest.raises(ValueError, match='Incomplete Codex trace'):
        SR.Trace(folder)


def test_captured_native_fixture_read_only():
    proof = os.environ.get('CODEX_NATIVE_PROOF')
    if not proof:
        pytest.skip('Set CODEX_NATIVE_PROOF to the captured local-only CP2 fixture folder')
    folder = Path(proof)
    before = {p: p.read_bytes() for p in folder.rglob('*.jsonl')}
    report = AR.analyze(folder, harness='codex')
    assert report['trace_complete'], report['trace_errors']
    assert report['model_calls'] == 7
    assert report['tokens']['total'] == 0 and report['tokens']['cost_usd_estimate'] is None
    assert report['subagent_dispatches']['geeky-coder'] == 1
    assert report['gate_results']['check-commit']['pass'] == 1
    assert before == {p: p.read_bytes() for p in folder.rglob('*.jsonl')}


def test_unified_diff_postchange_excludes_removed_done_and_headers():
    diff = ('--- a/docs/p/kanban.md\n+++ b/docs/p/kanban.md\n@@ -1,4 +1,4 @@\n'
            ' ## Backlog\n+- T1\n ## Done\n-- [x] T1\n+- [x] T2\n\\ No newline at end of file\n')
    post = CT.post_change_text({'type': 'update', 'unified_diff': diff})
    assert post == '## Backlog\n- T1\n## Done\n- [x] T2'
    assert SR.done_after(post, set()) == {'T2'}
    assert '---' not in post and '+++' not in post and '@@' not in post
    assert CT.post_change_text({'type': 'add', 'content': '## Done\n- [x] T3'}) == '## Done\n- [x] T3'
    assert CT.post_change_text({'type': 'delete', 'content': '## Done\n- [x] T4'}) == ''


def test_patch_provenance_cannot_reintroduce_removed_handoff_tasks(trace_folder):
    folder, rows = trace_folder
    diff = '--- a/docs/p/handoff.md\n+++ b/docs/p/handoff.md\n@@ -1 +1 @@\n-T1 PASS\n+T2 pending'
    rows += [row('response_item', {'type': 'custom_tool_call', 'name': 'apply_patch',
        'call_id': 'handoff', 'input': 'fixture patch'}, 8),
        row('event_msg', {'type': 'item_completed', 'item': {'type': 'FileChange', 'id': 'handoff',
            'changes': {'docs/p/handoff.md': {'type': 'update', 'unified_diff': diff}}, 'status': 'completed'}}, 9)]
    write_jsonl(folder / 'session.jsonl', rows)
    trace = SR.Trace(folder)
    change = trace.by_id['main:handoff:file0']
    assert change.inp['new_string'] == 'T2 pending'
    assert 'T1' not in change.raw
    provenance = [e['codex_provenance'] for e in CT.load(folder)['stream'] if e.get('codex_provenance')]
    assert {'raw_diff': diff} in provenance


def test_native_mcp_params_attributes_dod_to_task_in_shared_rubric(trace_folder, monkeypatch):
    folder, rows = trace_folder
    arguments = {'params': {'task': 'T1', 'folder': 'docs/p'}}
    rows += [row('event_msg', {'type': 'item_completed', 'started_at_ms': 1792800008000,
        'item': {'type': 'McpToolCall', 'id': 'dod', 'server': 'geeky', 'tool': 'geeky_check_dod',
            'arguments': arguments, 'result': {'structuredContent': {'ok': True, 'exit_code': 0}},
            'status': 'completed'}}, 9)]
    write_jsonl(folder / 'session.jsonl', rows)
    ws = folder / 'workspace'
    (ws / '.git').mkdir(parents=True)
    plan = ws / 'docs/p'
    (plan / 'tasks').mkdir(parents=True)
    (plan / 'kanban.md').write_text('## Done\n- [x] T1\n', encoding='utf-8')
    (plan / 'tasks/T1-fixture.md').write_text('# T1 fixture\n', encoding='utf-8')
    run = json.loads((folder / 'run.json').read_text())
    run['workspace'] = str(ws)
    (folder / 'run.json').write_text(json.dumps(run), encoding='utf-8')
    monkeypatch.setattr(SR, 'git', lambda *args, **kwargs: '')
    monkeypatch.setattr(SR, 'commits', lambda *args: [])
    scorer = SR.Scorer(folder, rerun=False)
    scorer.load()
    scorer.derive()
    call = scorer.trace.by_id['main:dod']
    assert call.inp == {'task': 'T1', 'folder': 'docs/p'}
    assert AR.gate_outcomes(call.name, call.inp, (call.text, call.is_error)) == [('check-dod', True)]
    assert scorer.dod_runs['T1'] == [(call.idx, None)]
    assert SR.gate_before_done(call.idx, -1, scorer.dod_runs['T1'], [(call.idx, True)])
    provenance = [e['codex_provenance'] for e in CT.load(folder)['stream'] if e.get('codex_provenance')]
    assert {'original_arguments': arguments} in provenance
