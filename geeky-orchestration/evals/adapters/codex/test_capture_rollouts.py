import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('capture_rollouts', Path(__file__).with_name('capture-rollouts.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rollout(root, identity, parent=None, name=None):
    root.mkdir(parents=True, exist_ok=True)
    path = root / (name or f'rollout-{identity}.jsonl')
    path.write_text(json.dumps({'type': 'session_meta', 'payload': {
        'id': identity, 'source': {'subagent': {'thread_spawn': {'parent_thread_id': parent}}}}}) + '\n', encoding='utf-8')


def test_capture_only_proven_descendants(tmp_path):
    sessions = tmp_path / 'sessions'
    for identity, parent in [('main', None), ('child', 'main'), ('nested', 'child'), ('unrelated', None)]:
        rollout(sessions, identity, parent)
    target = tmp_path / 'capture'
    report = module.capture(sessions, 'main', target)
    assert {r['thread_id'] for r in report['threads']} == {'main', 'child', 'nested'}
    assert (target / 'session.jsonl').exists()
    assert len(list((target / 'subagents').glob('*.jsonl'))) == 2
    with pytest.raises(ValueError, match='mix'):
        module.capture(sessions, 'main', target)


def test_missing_and_duplicate_thread_fail(tmp_path):
    with pytest.raises(ValueError, match='main'):
        module.capture(tmp_path, 'missing', tmp_path / 'output')
    rollout(tmp_path, 'main')
    rollout(tmp_path, 'main', name='rollout-duplicate.jsonl')
    with pytest.raises(ValueError, match='ambiguous'):
        module.capture(tmp_path, 'main', tmp_path / 'output')
