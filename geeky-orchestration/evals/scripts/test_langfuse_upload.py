"""Offline Langfuse upload contract tests; converters are stubbed, nothing is sent."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

spec = importlib.util.spec_from_file_location('langfuse_upload', Path(__file__).with_name('langfuse-upload.py'))
LU = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LU)

ENV = {'TRACE_TO_LANGFUSE': 'true', 'LANGFUSE_PUBLIC_KEY': 'pk-lf-test', 'LANGFUSE_SECRET_KEY': 'sk-lf-test'}


def run_folder(tmp_path, harness, subagents=('a.jsonl',)):
    folder = tmp_path / 'baselines' / 'c1-csvledger' / '20261025T000000Z'
    (folder / 'subagents').mkdir(parents=True)
    (folder / 'session.jsonl').write_text('{"type":"session_meta"}\n', encoding='utf-8')
    for name in subagents:
        (folder / 'subagents' / name).write_text('{}\n', encoding='utf-8')
    (folder / 'run.json').write_text(json.dumps({'harness': harness, 'case': 'c1-csvledger', 'session_id': 'sid-1',
        'model': 'm', 'gateway': 'litellm', 'oracle': {'passed': 9, 'collected': 10}}), encoding='utf-8')
    return folder


def test_claude_stage_matches_hook_layout(tmp_path):
    folder = run_folder(tmp_path, 'claude-code', ('agent-x.jsonl', 'agent-x.meta.json'))
    stage = tmp_path / 'stage'
    stage.mkdir()
    transcript = LU.stage_claude(folder, stage, 'sid-1')
    assert transcript == stage / 'sid-1.jsonl'
    assert sorted(p.name for p in (stage / 'sid-1' / 'subagents').iterdir()) == ['agent-x.jsonl', 'agent-x.meta.json']


def test_codex_stage_puts_rollouts_in_one_day_folder(tmp_path):
    folder = run_folder(tmp_path, 'codex', ('rollout-child.jsonl',))
    transcript = LU.stage_codex(folder, tmp_path / 'stage', 'sid-1')
    assert transcript.parent.relative_to(tmp_path / 'stage').as_posix() == 'sessions/2000/01/01'
    assert sorted(p.name for p in transcript.parent.iterdir()) == ['rollout-child.jsonl', 'rollout-sid-1.jsonl']


def test_labels_carry_run_facts_only(tmp_path):
    folder = run_folder(tmp_path, 'codex')
    tags, metadata = LU.labels(json.loads((folder / 'run.json').read_text()), folder)
    assert tags == ['geeky-eval', 'c1-csvledger', 'codex', 'gateway:litellm']
    assert metadata['oracle'] == '9/10' and metadata['run_folder'] == folder.name
    assert all(isinstance(v, str) for v in metadata.values())


@pytest.mark.parametrize('env,reason', [({}, 'TRACE_TO_LANGFUSE is not true'),
                                        ({'TRACE_TO_LANGFUSE': 'true'}, 'missing LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY')])
def test_skips_without_opt_in_or_keys(tmp_path, env, reason):
    folder = run_folder(tmp_path, 'codex')
    record = LU.upload(folder, tmp_path / 'tools', env)
    assert record['uploaded'] is False and record['skipped'] == reason
    assert json.loads((folder / 'langfuse.json').read_text())['skipped'] == reason


def test_codex_upload_runs_converter_with_seeded_env(tmp_path, monkeypatch):
    folder = run_folder(tmp_path, 'codex')
    capture = tmp_path / 'captured.json'
    stub = tmp_path / 'stub.py'
    stub.write_text('import json, os, sys\n'
                    'payload = json.load(sys.stdin)\n'
                    f'json.dump({{"payload": payload, "env": dict(os.environ)}}, open({str(capture)!r}, "w"))\n'
                    'open(payload["transcript_path"] + ".langfuse", "w").write("t1\\nt2\\n")\n', encoding='utf-8')
    monkeypatch.setattr(LU.shutil, 'which', lambda name, path=None: sys.executable)
    monkeypatch.setattr(LU, 'codex_entry', lambda tools: stub)
    record = LU.upload(folder, tmp_path / 'tools', dict(ENV, PATH=''))
    assert record['uploaded'] is True and record['turns_uploaded'] == 2
    seen = json.loads(capture.read_text())
    assert seen['payload']['hook_event_name'] == 'Stop'
    assert seen['env']['LANGFUSE_CODEX_TRACE_SEED'] == 'geeky-eval:c1-csvledger:20261025T000000Z'
    assert json.loads(seen['env']['LANGFUSE_CODEX_TAGS'])[0] == 'geeky-eval'
    assert seen['env']['CODEX_HOME'] != str(Path.home() / '.codex')
    assert 'sk-lf-test' not in (folder / 'langfuse.json').read_text()
    assert sorted(p.name for p in folder.iterdir()) == ['langfuse.json', 'run.json', 'session.jsonl', 'subagents']


def test_claude_upload_uses_session_end(tmp_path, monkeypatch):
    folder = run_folder(tmp_path, 'claude-code')
    capture = tmp_path / 'captured.json'
    stub = tmp_path / 'stub.py'
    stub.write_text('import json, os, sys\n'
                    f'json.dump({{"payload": json.load(sys.stdin), "env": dict(os.environ)}}, open({str(capture)!r}, "w"))\n',
                    encoding='utf-8')
    # uv run --quiet --script <hook> -> the stub ignores uv's arguments.
    monkeypatch.setattr(LU.shutil, 'which', lambda name, path=None: sys.executable)
    monkeypatch.setattr(LU, 'claude_hook', lambda tools: stub)
    original = LU.converter
    def direct(*args):
        command, payload, env = original(*args)
        return [sys.executable, command[-1]], payload, env
    monkeypatch.setattr(LU, 'converter', direct)
    record = LU.upload(folder, tmp_path / 'tools', dict(ENV, PATH=''))
    assert record['uploaded'] is True
    seen = json.loads(capture.read_text())
    assert seen['payload']['hook_event_name'] == 'SessionEnd'
    assert seen['payload']['transcript_path'].endswith('sid-1.jsonl')
    assert seen['env']['CC_LANGFUSE_TRACE_TAGS'].startswith('geeky-eval,c1-csvledger,claude-code')
