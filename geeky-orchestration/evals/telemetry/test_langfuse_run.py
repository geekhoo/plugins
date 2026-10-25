import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('langfuse_run', Path(__file__).with_name('langfuse-run.py'))
lf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lf)


def test_truncated_finds_nested_and_serialized_flags():
    assert lf.truncated({'text': {'truncated': True, 'orig_len': 9}})
    assert lf.truncated('{"thinking": [{"truncated": true}]}')
    assert not lf.truncated({'truncated': False, 'tool': [{'orig_len': 3}]})
    assert not lf.truncated(None)


def test_summarize_counts_types_tools_usage_and_traces():
    observations = [
        {'traceId': 't1', 'type': 'GENERATION', 'name': 'LLM Call', 'usageDetails': {'input': 3, 'output': 5},
         'startTime': '2026-10-24T10:00:01Z', 'environment': 'eval'},
        {'traceId': 't1', 'type': 'TOOL', 'name': 'Tool: Read', 'startTime': '2026-10-24T10:00:02Z',
         'metadata': {'truncated': True}},
        {'traceId': 't2', 'type': 'SPAN', 'name': 'Subagent: review', 'startTime': '2026-10-24T10:00:00Z'},
        {'traceId': 't2', 'type': 'GENERATION', 'name': 'Subagent LLM Call', 'usageDetails': {'input': 1}},
    ]
    s = lf.summarize('sid', observations)
    assert (s['traces'], s['observations'], s['generations'], s['tool_calls'], s['subagents']) == (2, 4, 2, 1, 1)
    assert s['usage_details'] == {'input': 4, 'output': 5}
    assert s['truncated_observations'] == 1 and s['environments'] == ['eval']
    assert s['first_start'] == '2026-10-24T10:00:00Z' and s['last_start'] == '2026-10-24T10:00:02Z'
