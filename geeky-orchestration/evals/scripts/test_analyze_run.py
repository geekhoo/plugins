"""Claude analysis keeps unknown token usage distinct from zero usage."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

spec = importlib.util.spec_from_file_location('analyze_run', Path(__file__).with_name('analyze-run.py'))
AR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AR)


def run_dir(tmp_path, stream):
    (tmp_path / 'stream.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in stream), encoding='utf-8')
    (tmp_path / 'session.jsonl').write_text('', encoding='utf-8')
    return tmp_path


def test_timeout_without_result_reports_unknown_tokens(tmp_path):
    tokens = AR.analyze(run_dir(tmp_path, [{'type': 'system', 'subtype': 'init'}]), harness='claude-code')['tokens']
    assert tokens and all(v is None for v in tokens.values())


def test_result_model_usage_is_summed(tmp_path):
    usage = {'m': {'inputTokens': 10, 'cacheReadInputTokens': 5, 'cacheCreationInputTokens': 2,
                   'outputTokens': 3, 'costUSD': 0.5}}
    tokens = AR.analyze(run_dir(tmp_path, [{'type': 'result', 'modelUsage': usage}]), harness='claude-code')['tokens']
    assert tokens['total'] == 20 and tokens['cached_input'] == 5 and tokens['cost_usd_estimate'] == 0.5


def skill_call(call_id, skill):
    return {'type': 'assistant', 'message': {'content': [
        {'type': 'tool_use', 'id': call_id, 'name': 'Skill', 'input': {'skill': skill}}]}}


def test_impl_review_field_names_what_it_counts(tmp_path):
    stream = [skill_call('1', 'geeky-orchestration:impl-review'), skill_call('2', 'impl-review'), skill_call('3', 'geeky-plan')]
    report = AR.analyze(run_dir(tmp_path, stream), harness='claude-code')
    assert report['impl_review_skill_invocations'] == 2
    assert 'impl_review_rounds' not in report
    assert AR.analyze(run_dir(tmp_path, []), harness='claude-code')['impl_review_skill_invocations'] is None


def test_reanalysing_a_stored_run_keeps_its_historical_value(tmp_path):
    folder = run_dir(tmp_path, [skill_call('1', 'impl-review')])
    (folder / 'run.json').write_text(json.dumps({'impl_review_rounds': 7, 'tokens': None}), encoding='utf-8')
    script = str(Path(__file__).with_name('analyze-run.py'))
    derived = folder / 'derived'
    subprocess.run([sys.executable, script, str(folder), '--harness', 'claude-code', '--out', str(derived)],
                   check=True, capture_output=True)
    assert json.loads((folder / 'run.json').read_text(encoding='utf-8'))['impl_review_rounds'] == 7
    run = json.loads((derived / 'run.json').read_text(encoding='utf-8'))
    assert (run['impl_review_rounds'], run['impl_review_skill_invocations']) == (7, 1)
    subprocess.run([sys.executable, script, str(folder), '--harness', 'claude-code'], check=True, capture_output=True)
    run = json.loads((folder / 'run.json').read_text(encoding='utf-8'))
    assert (run['impl_review_rounds'], run['impl_review_skill_invocations']) == (7, 1)
