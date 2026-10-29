"""Claude analysis keeps unknown token usage distinct from zero usage."""
import importlib.util
import json
from pathlib import Path

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
