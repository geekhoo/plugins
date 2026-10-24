"""Offline normalization contracts; no contestant commands are executed."""
import importlib.util
import json
import copy
from pathlib import Path
from unittest.mock import patch
import pytest


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_literal_lane_replacements_preserve_intermediate_moves():
    auto = module('codex-process')
    command = '$b=$b.Replace(\'## Ready\',"## Ready`n- [ ] T8 — title (phase 4)"); Set-Content $p $b; $b=$b.Replace(\'## In Progress\',"## In Progress`n- [ ] T8 — title (phase 4)"); Set-Content $p $b'
    assert auto.lane_insertions(command) == [('T8', 'Ready', 'P4'), ('T8', 'In Progress', 'P4')]
    assert auto.lane_insertions('Get-Content kanban.md; # T8 Done') == []


def test_review_requires_explicit_per_task_verdict():
    auto = module('codex-process')
    assert auto.review_result('**T8: PASS. T9: PASS.** Phase 4 READY TO ADVANCE') == (['T8', 'T9'], 'P4', 'pass', True)
    with pytest.raises(ValueError):
        auto.review_result('Read T8 T9. PASS. READY TO ADVANCE. Phase 4')
    with pytest.raises(ValueError):
        auto.review_result('T8: PASS. T8: FAIL. Phase 4 READY TO ADVANCE')
    with pytest.raises(ValueError, match='Mixed per-task'):
        auto.review_result('T8: PASS. T9: FAIL. Phase 4 NEEDS FIXES')


def test_multi_task_commit_order_cannot_substitute_for_identity():
    auto = module('codex-process')
    reversed_results = [('bbbbbbb', 'feat: second'), ('aaaaaaa', 'feat: first')]
    with pytest.raises(ValueError, match='Ambiguous task'):
        auto.task_commit_bindings('git commit -m "feat: first"; git commit -m "feat: second"', reversed_results, ['T8', 'T9'])
    command = '$msg="feat: first`n`nTasks: T8"; git commit -m $msg; $msg="feat: second`n`nTasks: T9"; git commit -m $msg'
    assert auto.task_commit_bindings(command, reversed_results, ['T8', 'T9']) == {
        'T9': ('bbbbbbb', 'feat: second'), 'T8': ('aaaaaaa', 'feat: first')}
    with pytest.raises(ValueError, match='literal commit-message'):
        auto.task_commit_bindings('$msg="feat: first`nTasks: T8"; $msg=$other; git commit -m $msg', [('aaaaaaa', 'feat: first')], ['T8'])


def test_strict_cli_reports_withheld_composite_as_failure(tmp_path):
    score = module('score-run')
    for name in ('run.json', 'stream.jsonl'):
        (tmp_path / name).write_text('{}')
    result = {'composite': None, 'needs_judge': [], 'dimensions': {
        'quality': {'capped': 1}, 'adherence': {'capped': 1},
        'consistency': {'score': 1}, 'task_tier': {'score': 1}}}
    with patch.object(score, 'Scorer') as scorer, patch.object(score, 'render_md', return_value='incomplete'):
        scorer.return_value.score.return_value = result
        assert score.main([str(tmp_path), '--require-complete']) != 0
        assert json.loads((tmp_path / 'score.json').read_text())['composite'] is None
        assert score.main([str(tmp_path)]) == 0


RUN = Path(__file__).parents[1] / 'baselines/c1-csvledger/20261023T194430Z-c5e04f3f'


@pytest.fixture
def raw_run():
    if not (RUN / 'session.jsonl').exists():
        pytest.skip('Retained raw RUN2 corpus is not installed')
    return module('codex-trace').load(RUN)


def test_retained_raw_slices_derive_complete_process_without_annotation(raw_run):
    assert raw_run['trace_complete'], raw_run['trace_errors']
    process = raw_run['process_evidence']
    assert process['origin'] == 'automatic-raw-trace'
    assert not process['missing']
    assert len(process['lane_moves']) == 11
    assert len(process['reviews']) == 2
    assert len(process['expected_implementation_commits']) == 4
    assert {tuple(c['tasks']) for c in process['contexts'] if c.get('role') == 'coder'} == {('T1',), ('T2',), ('T3',)}
    assert [(r['tasks'], r['verdict'], r['ready']) for r in process['reviews']] == [(['T1', 'T2'], 'pass', True), (['T3'], 'pass', True)]


def test_raw_polled_test_commands_are_one_failure_and_one_pass(raw_run):
    score = module('score-run')
    events = raw_run['stream']
    outputs = {c['tool_use_id']: c['content'] for e in events for c in e.get('message', {}).get('content', []) if c.get('type') == 'tool_result'}
    coder = next(c['call_id'] for c in raw_run['process_evidence']['contexts'] if c.get('role') == 'coder' and c.get('tasks') == ['T3'])
    attempts = []
    for event in events:
        if event.get('parent_tool_use_id') != coder:
            continue
        for call in event.get('message', {}).get('content', []):
            if call.get('type') == 'tool_use' and call.get('name') == 'PowerShell':
                result = score.classify_validation(call['input']['command'], outputs[call['id']])
                if result and not result['excluded']:
                    attempts.append(result['outcome'])
    assert attempts == ['fail', 'pass']


def test_raw_coder_mapping_rejects_conflicting_dispatch(raw_run):
    auto = module('codex-process')
    context = next(c for c in raw_run['process_evidence']['contexts'] if c.get('role') == 'coder')
    source = context['refs'][0]
    dispatch = json.loads((RUN / source['path']).read_text(encoding='utf-8-sig').splitlines()[source['record_index']])
    child_id = raw_run['metas'][context['call_id']]['agentId']
    path = next((RUN / 'subagents').glob('*' + child_id + '.jsonl'))
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    cutoff = rows[0]['payload']['subagent_history_start_ordinal']
    thread = {'rows': [r for r in rows if r.get('ordinal', -1) >= cutoff]}
    assert auto.dispatched_task(thread, dispatch)[0] == context['tasks']
    bad = copy.deepcopy(dispatch)
    args = json.loads(bad['payload']['arguments']); args['task_name'] = 'coder_t99'
    bad['payload']['arguments'] = json.dumps(args)
    with pytest.raises(ValueError, match='Ambiguous coder'):
        auto.dispatched_task(thread, bad)
