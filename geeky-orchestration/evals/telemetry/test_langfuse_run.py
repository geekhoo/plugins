import importlib.util
import io
import json
from pathlib import Path
import sys
import urllib.parse

HERE = Path(__file__).resolve().parent
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


def test_doubled_delivery_is_counted_once_and_reported():
    row = {'traceId': 't1', 'type': 'GENERATION', 'name': 'LLM', 'usageDetails': {'input': 10, 'total': 10},
           'startTime': '2026-11-04T06:00:00Z'}
    rows = [{**row, 'id': 'g1'}, {**row, 'id': 'g1'}, {**row, 'id': 'g2'}, {**row, 'id': 'g2'},
            {'id': 't1-tool', 'traceId': 't1', 'type': 'TOOL', 'name': 'Tool: shell'},
            {'id': 't1-tool', 'traceId': 't1', 'type': 'TOOL', 'name': 'Tool: shell'},
            {'id': 'a1', 'traceId': 't1', 'type': 'AGENT', 'name': 'Subagent: coder', 'endTime': '2026-11-04T06:21:13Z'},
            {'id': 'a1', 'traceId': 't1', 'type': 'AGENT', 'name': 'Subagent: coder', 'endTime': '2026-11-04T06:23:17Z'}]
    s = lf.summarize('sid', rows)
    assert (s['observations'], s['duplicate_rows']) == (4, 4)
    assert (s['generations'], s['tool_calls'], s['subagents']) == (2, 1, 1)
    assert s['by_type'] == {'GENERATION': 2, 'TOOL': 1, 'AGENT': 1}
    assert s['usage_details'] == {'input': 20, 'total': 20}


def test_single_delivery_is_unchanged_and_idless_rows_still_count():
    assert lf.summarize('sid', [{'id': 'a'}, {'id': 'b'}, {}, {}])['observations'] == 4
    assert lf.summarize('sid', [{'id': 'a'}, {'id': 'b'}, {}, {}])['duplicate_rows'] == 0
    assert lf.summarize('sid', [])['duplicate_rows'] == 0


SESSION = 'c2-ds-full/codex/20261105T000000Z-abcd1234'


def load(name, filename):
    module_spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def assert_session_query(url):
    parsed = urllib.parse.urlsplit(url)
    assert parsed.path == '/api/public/v2/observations'
    assert 'sessionId=c2-ds-full%2Fcodex%2F20261105T000000Z-abcd1234' in parsed.query
    assert urllib.parse.parse_qs(parsed.query)['sessionId'] == [SESSION]


def pages(urls):
    """Two pages, so a follow-up request with a cursor keeps the encoded session too."""
    def respond(request, timeout=None):
        urls.append(request.full_url)
        return io.BytesIO(json.dumps({'data': [{'id': f'o{len(urls)}'}], 'meta': {'cursor': 'next' if len(urls) == 1 else None}}).encode())
    return respond


def test_fetch_encodes_a_session_id_with_slashes(monkeypatch):
    urls = []
    monkeypatch.setattr(lf.urllib.request, 'urlopen', pages(urls))
    rows = lf.fetch_observations('http://fixture.invalid/', 'auth', SESSION, lf.SUMMARY_FIELDS)
    assert [row['id'] for row in rows] == ['o1', 'o2'] and len(urls) == 2
    for url in urls:
        assert_session_query(url)
    assert urllib.parse.parse_qs(urllib.parse.urlsplit(urls[1]).query)['cursor'] == ['next']


def test_codex_flush_reader_encodes_a_session_id_with_slashes(monkeypatch):
    flush = load('codex_flush_url', 'codex-flush.py')
    urls = []

    class Opener:
        open = staticmethod(pages(urls))

    monkeypatch.setattr(flush.urllib.request, 'build_opener', lambda *_: Opener)
    reader = flush.reader_from_environment({'GEEKY_SESSION_ID': SESSION, 'LANGFUSE_PUBLIC_KEY': 'p', 'LANGFUSE_SECRET_KEY': 's',
                                            'LANGFUSE_BASE_URL': 'http://fixture.invalid'})
    assert reader() == {'o1', 'o2'}
    assert_session_query(urls[0])


def test_process_trace_client_encodes_a_session_id_with_slashes(monkeypatch):
    sys.path.insert(0, str(HERE))
    trace = load('process_trace_url', 'process_trace.py')
    client_type = next(value for value in vars(trace).values() if isinstance(value, type) and hasattr(value, 'observations'))
    for name in ('BASE_URL', 'PUBLIC_KEY', 'SECRET_KEY'):
        monkeypatch.setenv(f'LANGFUSE_CODEX_{name}', 'http://fixture.invalid' if name == 'BASE_URL' else 'fixture')
    urls = []
    monkeypatch.setattr(trace.urllib.request, 'urlopen', pages(urls))
    assert len(client_type().observations(sessionId=SESSION)) == 2
    assert_session_query(urls[0])


def test_summary_reads_new_identities_and_counts_subagents_from_metadata():
    rows = [{'id': 'r', 'traceId': 'root', 'type': 'AGENT', 'name': 'orchestrator', 'userId': 'codex/orchestrator', 'environment': 'mxc-win',
             'metadata': {'actor_scope': 'main', 'agent_role': 'orchestrator', 'agent_family': 'codex-mxc-win', 'agent_id': 'a'}},
            {'id': 'c1', 'traceId': 'c1', 'type': 'AGENT', 'name': 'coder', 'userId': 'codex/coder',
             'metadata': {'actor_scope': 'subagent', 'agent_role': 'coder', 'agent_family': 'codex-mxc-win', 'agent_id': 'b'}},
            {'id': 'c2', 'traceId': 'c2', 'type': 'AGENT', 'name': 'coder', 'userId': 'codex/coder',
             'metadata': {'actor_scope': 'subagent', 'agent_role': 'coder', 'agent_family': 'codex-mxc-win', 'agent_id': 'c'}}]
    summary = lf.summarize(SESSION, rows)
    assert summary['session_id'] == SESSION
    assert summary['subagents'] == 2 and summary['traces'] == 3
    assert summary['user_ids'] == ['codex/coder', 'codex/orchestrator']
    assert summary['agent_roles'] == ['coder', 'orchestrator'] and summary['agent_families'] == ['codex-mxc-win']


def test_summary_reports_new_actor_identities_without_losing_subagent_counts():
    row = {'traceId': 'child', 'type': 'AGENT', 'name': 'claude-mxc-win-coder-coder-a',
           'userId': 'claude-mxc-win-coder-a-native-id', 'environment': 'mxc-win',
           'metadata': {'actor_scope': 'subagent', 'agent_role': 'coder', 'agent_family': 'claude-mxc-win'}}
    summary = lf.summarize('named-run', [row])
    assert summary['subagents'] == 1
    assert summary['user_ids'] == ['claude-mxc-win-coder-a-native-id']
    assert summary['agent_roles'] == ['coder']
    assert summary['agent_families'] == ['claude-mxc-win']
