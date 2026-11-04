"""Regression tests for the source-bound C1 parity wrapper."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


PATH = Path(__file__).with_name('c1-normalized-score.py')
SPEC = importlib.util.spec_from_file_location('c1_normalized', PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def bounds():
    return {'spec-research': ('2026-01-01T00:00:00+00:00', None),
            'geeky-plan': (None, '2026-01-01T00:02:00+00:00'),
            'plan-review': ('2026-01-01T00:02:00+00:00', '2026-01-01T00:03:00+00:00'),
            'geeky-implement': ('2026-01-01T00:03:00+00:00', '2026-01-01T00:04:00+00:00'),
            'impl-review': ('2026-01-01T00:04:00+00:00', '9999')}


def test_spec_boundary_uses_pinned_artifact_commit_without_changing_prescribed_check():
    e = SimpleNamespace(bounds=bounds(), moves=[{'sha': 'a' * 40, 'time': '2026-01-01T00:01:00+00:00',
                                                'files': ['docs/spec-001-feature/feature-specification.md']}])
    MOD.apply_stage_review(e, {'kind': 'specification-commit', 'commit': 'a' * 40}, None, None)
    assert e.bounds['spec-research'][1] == '2026-01-01T00:01:00+00:00'
    assert e.bounds['geeky-plan'][0] == e.bounds['spec-research'][1]
    with pytest.raises(ValueError, match='Unexpected automatic'):
        MOD.apply_stage_review(e, {'kind': 'specification-commit', 'commit': 'a' * 40}, None, None)


def test_spec_boundary_refuses_wrong_or_unordered_commit():
    e = SimpleNamespace(bounds=bounds(), moves=[{'sha': 'a' * 40, 'time': '2026-01-01T00:01:00+00:00',
                                                'files': ['docs/spec-001-feature/feature-specification.md']}])
    with pytest.raises(ValueError, match='does not match'):
        MOD.apply_stage_review(e, {'kind': 'specification-commit', 'commit': 'b' * 40}, None, None)
    e.moves[0]['time'] = '2026-01-01T00:03:00+00:00'
    with pytest.raises(ValueError, match='not ordered'):
        MOD.apply_stage_review(e, {'kind': 'specification-commit', 'commit': 'a' * 40}, None, None)


def test_reviewed_intervals_require_validated_source_and_complete_order():
    e = SimpleNamespace(bounds=bounds())
    with pytest.raises(ValueError, match='validated native'):
        MOD.apply_stage_review(e, {'kind': 'reviewed-process'}, None, None)
    intervals = [{'stage': stage, 'scope_call_id': None,
                  'start': {'timestamp': f'2026-01-01T00:0{i}:00Z'},
                  'end': {'timestamp': f'2026-01-01T00:0{i+1}:00Z'}}
                 for i, stage in enumerate(MOD.STAGES)]
    parity = SimpleNamespace(utc_time=lambda x: x.replace('Z', '+00:00'))
    MOD.apply_stage_review(e, {'kind': 'reviewed-process'}, {'stage_intervals': intervals}, parity)
    assert e.bounds['impl-review'][1] == '9999'
    with pytest.raises(ValueError, match='incomplete or duplicated'):
        MOD.apply_stage_review(e, {'kind': 'reviewed-process'}, {'stage_intervals': intervals[:-1]}, parity)
    intervals[1]['start']['timestamp'] = intervals[1]['end']['timestamp']
    with pytest.raises(ValueError, match='empty or reversed'):
        MOD.apply_stage_review(e, {'kind': 'reviewed-process'}, {'stage_intervals': intervals}, parity)


def test_reviewed_intervals_reject_overlap():
    e = SimpleNamespace(bounds=bounds())
    intervals = [{'stage': stage, 'scope_call_id': None,
                  'start': {'timestamp': f'2026-01-01T00:0{i}:00Z'},
                  'end': {'timestamp': f'2026-01-01T00:0{i+1}:00Z'}}
                 for i, stage in enumerate(MOD.STAGES)]
    intervals[0]['end']['timestamp'] = '2026-01-01T00:02:00Z'
    parity = SimpleNamespace(utc_time=lambda x: x.replace('Z', '+00:00'))
    with pytest.raises(ValueError, match='overlap'):
        MOD.apply_stage_review(e, {'kind': 'reviewed-process'}, {'stage_intervals': intervals}, parity)


def test_manual_inputs_require_explicit_hard_gate_and_evidence():
    good = {'hg.false_completion_claim': {'pass': True, 'note': 'reviewed trace'},
            'a.no_orchestrator_code_edits': {'pass': True, 'note': 'reviewed paths'}}
    MOD.validate_manual(good)
    with pytest.raises(ValueError, match='require explicit'):
        MOD.validate_manual({})
    with pytest.raises(ValueError, match='Invalid'):
        MOD.validate_manual({'hg.false_completion_claim': {'pass': True, 'note': ''}})
    with pytest.raises(ValueError, match='Invalid'):
        MOD.validate_manual({'hg.false_completion_claim': {'pass': 'true', 'note': 'not boolean'}})


def test_source_hash_mismatch_fails_closed(tmp_path):
    path = tmp_path / 'source.json'
    path.write_text('{}', encoding='utf-8')
    item = {'path': str(path), 'sha256': MOD.sha256(path)}
    assert MOD.json_input(item) == {}
    path.write_text('{"changed":true}', encoding='utf-8')
    with pytest.raises(ValueError, match='changed source'):
        MOD.json_input(item)


def test_workspace_state_refuses_unbound_changes(monkeypatch, tmp_path):
    def fake_git(_path, *args):
        if args[0] == 'status':
            return ' M csvledger/core.py\n'
        return ''
    monkeypatch.setattr(MOD, 'git', fake_git)
    with pytest.raises(ValueError, match='unbound changes'):
        MOD.workspace_state(tmp_path)


def test_git_inspection_disables_hooks_fsmonitor_and_inherited_git_config(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setenv('GIT_CONFIG_COUNT', '1')
    monkeypatch.setenv('GIT_CONFIG_KEY_0', 'core.fsmonitor')
    monkeypatch.setenv('GIT_CONFIG_VALUE_0', 'unsafe-helper')

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout='ok')

    monkeypatch.setattr(MOD.subprocess, 'run', fake_run)
    assert MOD.git(tmp_path, 'status', '--porcelain') == 'ok'
    argv, options = calls[0]
    assert 'core.fsmonitor=false' in argv
    assert any(x.startswith('core.hooksPath=') for x in argv)
    assert options['env']['GIT_CONFIG_NOSYSTEM'] == '1'
    assert 'GIT_CONFIG_COUNT' not in options['env']
    assert 'GIT_CONFIG_KEY_0' not in options['env']


def test_campaign_is_deterministic_and_fails_on_incomplete_evidence(monkeypatch, tmp_path):
    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return {'path': str(path), 'sha256': MOD.sha256(path)}

    state = {'head': 'f' * 40, 'status_sha256': 'a' * 64, 'reflog_sha256': 'b' * 64, 'heartbeat_sha256': None}
    monkeypatch.setattr(MOD, 'verify_engine', lambda _campaign: None)
    monkeypatch.setattr(MOD, 'workspace_state', lambda _workspace: state)
    run = {'case': 'c1-csvledger', 'plugin_sha': 'a' * 40, 'prompt_sha256': 'b' * 64,
           'workspace': str(tmp_path), 'harness': 'codex', 'model': 'test-model', 'wall_time_s': 10,
           'session_id': 'session'}
    quality = {'case': 'c1-csvledger', 'plugin_sha': 'a' * 40, 'run': tmp_path.name,
               'harness': 'codex', 'model': 'test-model',
               'process_completeness': {'complete': True}, 'needs_judge': [],
               'dimensions': {'quality': {'capped': 90}}}
    inputs = {'run': write('run.json', run),
              'observations': write('observations.json', [{'id': 'o1', 'sessionId': 'session'}]),
              'quality_score': write('quality.json', quality),
              'manual': write('manual.json', {'hg.false_completion_claim': {'pass': True, 'note': 'reviewed'},
                                              'a.no_orchestrator_code_edits': {'pass': True, 'note': 'reviewed'}}),
              'scope': write('scope.json', {})}

    class FakeEvaluation:
        def __init__(self, *_args):
            self.bounds = {'spec-research': ('1', '2'), 'geeky-plan': ('2', '3'),
                           'plan-review': ('3', '4'), 'geeky-implement': ('4', '5'),
                           'impl-review': ('5', '9999')}

        def evaluate(self):
            return {'quality': 90, 'adherence': 80, 'consistency': 70, 'composite': 81.67,
                    'needs_judge': [], 'checks': [{'id': 'a.no_orchestrator_code_edits'}]}

    parity = SimpleNamespace(load_scope=lambda *_args: {'missing_sources': []}, Evaluation=FakeEvaluation)
    entry = {'id': 'one', 'inputs': inputs, 'workspace': str(tmp_path), 'workspace_state': state,
             'native_run_dir': str(tmp_path),
             'plugin_sha': 'a' * 40, 'prompt_sha256': 'b' * 64, 'langfuse_session_id': 'session',
             'stage_evidence': {'kind': 'existing'}, 'provenance': 'fixture'}
    campaign = {'schema': MOD.SCHEMA, 'runs': [entry]}
    first = MOD.evaluate_campaign(campaign, parity, None)
    assert first == MOD.evaluate_campaign(campaign, parity, None)
    assert first['runs'][0]['score']['composite'] == 81.67
    run['session_id'] = 'different-session'
    inputs['run'] = write('run.json', run)
    with pytest.raises(ValueError, match='not bound to the run'):
        MOD.evaluate_campaign(campaign, parity, None)
    run['session_id'] = 'session'
    inputs['run'] = write('run.json', run)
    quality['run'] = 'another-run'
    inputs['quality_score'] = write('quality.json', quality)
    with pytest.raises(ValueError, match='not bound to the candidate'):
        MOD.evaluate_campaign(campaign, parity, None)
    quality['run'] = tmp_path.name
    quality['process_completeness']['complete'] = False
    inputs['quality_score'] = write('quality.json', quality)
    with pytest.raises(ValueError, match='strict process evidence'):
        MOD.evaluate_campaign(campaign, parity, None)
    quality['process_completeness']['complete'] = True
    inputs['quality_score'] = write('quality.json', quality)
    inputs['observations'] = write('observations.json', [{'id': 'same', 'sessionId': 'session'},
                                                         {'id': 'same', 'sessionId': 'session'}])
    with pytest.raises(ValueError, match='Ambiguous Langfuse'):
        MOD.evaluate_campaign(campaign, parity, None)
