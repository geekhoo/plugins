"""CLI boundaries and two-turn protocol integration; no external endpoint calls."""
import copy
import json
from pathlib import Path

import pytest

from . import cli, transport
from .cases import NONCE


def prepare(tmp_path, profile='responses', cases='message,function_roundtrip', stream='both'):
    out = tmp_path / 'plan'
    args = cli.parser().parse_args(['prepare', '--profile', profile, '--model', 'synthetic-model',
                                    '--cases', cases, '--stream', stream, '--max-requests', '32',
                                    '--output', str(out)])
    cli.make_plan(args)
    return out / 'plan.json'


def response_for(request, missing_metadata=False):
    choice = request.get('tool_choice')
    if isinstance(choice, dict):
        tool = request['tools'][0]
        namespace = tool['name'] if tool['type'] == 'namespace' else None
        definition = tool['tools'][0] if namespace else tool
        arguments = json.loads(request['input'][0]['content'][0]['text'].split(': ', 1)[1])
        items = []
        for index, args in enumerate(arguments if isinstance(arguments, list) else [arguments], start=1):
            item = {'type': 'function_call', 'id': f'fc_{index}', 'call_id': f'call_{index}',
                    'name': definition['name'], 'arguments': json.dumps(args)}
            if namespace:
                item['namespace'] = namespace
                if not missing_metadata and item['name'] != 'wait_agent':
                    item['encrypted_function_args'] = []
            items.append(item)
    else:
        outputs = [item['output'] for item in request['input'] if item.get('type') == 'function_call_output']
        marker = outputs[-1] if outputs else NONCE
        items = [{'type': 'message', 'id': 'msg_1', 'role': 'assistant', 'status': 'completed',
                  'content': [{'type': 'output_text', 'text': marker}]}]
    return {'id': 'resp_1', 'object': 'response', 'status': 'completed',
            'model': 'synthetic-reported-model', 'output': items}


def stream_for(response):
    events = []
    for index, item in enumerate(response['output']):
        added = copy.deepcopy(item)
        if item['type'] == 'function_call':
            added['arguments'] = ''
        else:
            added.update(content=[], status='in_progress')
        events.append({'type': 'response.output_item.added', 'output_index': index, 'item': added})
        if item['type'] == 'function_call':
            events += [{'type': 'response.function_call_arguments.delta', 'item_id': item['id'],
                        'output_index': index, 'delta': item['arguments']},
                       {'type': 'response.function_call_arguments.done', 'item_id': item['id'],
                        'output_index': index, 'arguments': item['arguments']}]
        else:
            marker = item['content'][0]['text']
            events += [{'type': 'response.output_text.delta', 'item_id': item['id'],
                        'output_index': index, 'content_index': 0, 'delta': marker},
                       {'type': 'response.output_text.done', 'item_id': item['id'],
                        'output_index': index, 'content_index': 0, 'text': marker}]
        events.append({'type': 'response.output_item.done', 'output_index': index, 'item': item})
    events.append({'type': 'response.completed', 'response': response})
    raw = ''.join('event: ' + event['type'] + '\ndata: ' + json.dumps(event) + '\n\n' for event in events).encode()
    return events, raw


def fake_exchange(calls, missing_metadata=False):
    def exchange(endpoint, request, headers, **kwargs):
        calls.append(copy.deepcopy(request))
        response = response_for(request, missing_metadata)
        if request.get('stream'):
            events, raw = stream_for(response)
            reconstructed, errors = transport.reconstruct_response(events)
            assert errors == []
        else:
            events, raw = [], json.dumps(response).encode()
            reconstructed, errors = response, []
        return {'http_status': 200, 'content_type': 'text/event-stream' if events else 'application/json',
                'body': raw, 'response': reconstructed, 'events': events, 'errors': errors,
                'elapsed_s': .01, 'request_count': 1}
    return exchange


def probe_args(plan, output, *extra):
    return ['probe', '--plan', str(plan), '--endpoint', 'http://127.0.0.1:1/v1',
            '--auth', 'none', '--allow-network', '--output', str(output), *extra]


def test_prepare_and_catalog_never_read_credentials_or_network(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, 'credentials', lambda *_: pytest.fail('offline credentials read'))
    monkeypatch.setattr(transport, 'exchange', lambda *_a, **_k: pytest.fail('network call'))
    assert cli.main(['catalog']) == 0
    plan = prepare(tmp_path)
    assert cli.load_plan(plan)['limits']['planned_max_requests'] == 6
    assert cli.load_plan(plan)['synthetic_only']
    assert 'network_executed' in capsys.readouterr().out


@pytest.mark.parametrize('profile', cli.PROFILES)
def test_full_json_sse_function_roundtrip_without_executing_tools(tmp_path, monkeypatch, profile):
    cases = 'function_roundtrip' if profile == 'responses' else 'v2_send_roundtrip'
    plan = prepare(tmp_path, profile, cases)
    calls = []
    monkeypatch.setattr(transport, 'exchange', fake_exchange(calls))
    out = tmp_path / 'result'
    assert cli.main(probe_args(plan, out)) == 0
    report = cli.read_json(out / 'report.json')
    assert report['outcome'] == 'passed' and report['request_count'] == 4
    assert not report['actual_tools_executed'] and not report['evaluation_started']
    assert calls[1]['input'][-2]['type'] == 'function_call_output'
    assert calls[1]['input'][-2]['call_id'] == 'call_1'
    if profile == 'codex-v2-bridge':
        assert report['native_v2_support'] == 'not_tested'
        assert calls[0]['tools'][0]['type'] == 'function'
        assert 'namespace' not in calls[1]['input'][1]


def test_native_metadata_failure_is_not_masked_and_stops_remaining_cases(tmp_path, monkeypatch):
    plan = prepare(tmp_path, 'codex-v2-native', 'v2_send,v2_wait')
    calls = []
    monkeypatch.setattr(transport, 'exchange', fake_exchange(calls, missing_metadata=True))
    out = tmp_path / 'result'
    assert cli.main(probe_args(plan, out)) == 1
    report = cli.read_json(out / 'report.json')
    assert report['request_count'] == 1
    assert report['results'][0]['errors'][0]['code'] == 'plaintext_metadata'
    assert all(row['outcome'] == 'not_run' for row in report['results'][1:])


def test_missing_network_flag_never_calls_or_creates_output(tmp_path, monkeypatch):
    monkeypatch.setattr(transport, 'exchange', lambda *_a, **_k: pytest.fail('network call'))
    out = tmp_path / 'result'
    args = probe_args(tmp_path / 'absent-plan', out)
    args.remove('--allow-network')
    assert cli.main(args) == 2 and not out.exists()


@pytest.mark.parametrize('variant', ['request', 'pins', 'budget', 'duplicate'])
def test_tampered_plan_rejected_before_transport(tmp_path, monkeypatch, variant):
    plan = prepare(tmp_path)
    data = cli.read_json(plan)
    if variant == 'request':
        data['items'][0]['request']['input'][0]['content'][0]['text'] = 'arbitrary prompt'
    elif variant == 'pins':
        data['source_sha256']['fake'] = '0' * 64
    elif variant == 'budget':
        data['limits']['planned_max_requests'] = 1
    else:
        data['items'].append(data['items'][0])
    cli.save_json(plan, data)
    monkeypatch.setattr(transport, 'exchange', lambda *_a, **_k: pytest.fail('network call'))
    out = tmp_path / 'result'
    assert cli.main(probe_args(plan, out)) == 2 and not out.exists()


def test_fresh_directories_prevent_evidence_overwrite(tmp_path):
    prepare(tmp_path)
    with pytest.raises(FileExistsError):
        prepare(tmp_path)


def test_key_echo_is_redacted_from_body_and_derived_report(tmp_path, monkeypatch):
    plan = prepare(tmp_path, cases='message', stream='json')
    monkeypatch.setenv('CONTRACT_TEST_KEY', 'secret-diagnostic-key')
    def hostile(endpoint, request, headers, **kwargs):
        result = fake_exchange([])(endpoint, request, headers, **kwargs)
        result['response']['model'] = 'secret-diagnostic-key'
        result['body'] += b'secret-diagnostic-key'
        return result
    monkeypatch.setattr(transport, 'exchange', hostile)
    out = tmp_path / 'result'
    args = probe_args(plan, out)
    args[args.index('--auth') + 1] = 'bearer'
    args += ['--api-key-env', 'CONTRACT_TEST_KEY']
    assert cli.main(args) == 0
    assert all(b'secret-diagnostic-key' not in path.read_bytes() for path in out.iterdir())
    assert cli.read_json(out / 'report.json')['results'][0]['exchanges'][0]['response_redacted']


@pytest.mark.parametrize('mode', ['json', 'sse'])
def test_replay_saved_contract_is_offline_and_reports_no_roundtrip_completion(tmp_path, monkeypatch, mode):
    plan = prepare(tmp_path, cases='function_roundtrip', stream=mode)
    item = cli.read_json(plan)['items'][0]
    response = response_for(item['request'])
    raw = stream_for(response)[1] if mode == 'sse' else json.dumps(response).encode()
    saved = tmp_path / 'wire.raw'
    saved.write_bytes(raw)
    monkeypatch.setattr(transport, 'exchange', lambda *_a, **_k: pytest.fail('network call'))
    out = tmp_path / 'replayed'
    assert cli.main(['replay', '--plan', str(plan), '--item', item['id'],
                     '--response', str(saved), '--output', str(out)]) == 0
    report = cli.read_json(out / 'report.json')
    assert not report['network_executed'] and report['request_count'] == 0
    assert report['results'][0]['roundtrip'] == 'not_executed'


def test_reasoning_is_a_responses_object_in_saved_plan(tmp_path):
    out = tmp_path / 'reasoning'
    assert cli.main(['prepare', '--model', 'synthetic', '--cases', 'message', '--reasoning', 'high',
                     '--output', str(out)]) == 0
    assert cli.load_plan(out / 'plan.json')['items'][0]['request']['reasoning'] == {'effort': 'high'}


@pytest.mark.parametrize('profile', cli.PROFILES)
def test_every_available_case_json_and_sse_through_cli_with_fake_transport(tmp_path, monkeypatch, profile):
    plan = prepare(tmp_path, profile, 'all')
    calls = []
    monkeypatch.setattr(transport, 'exchange', fake_exchange(calls))
    out = tmp_path / 'result'
    assert cli.main(probe_args(plan, out)) == 0
    report = cli.read_json(out / 'report.json')
    assert len(calls) == cli.read_json(plan)['limits']['planned_max_requests']
    assert report['outcome'] == 'passed'
    assert all(row['outcome'] == 'passed' for row in report['results'])


def test_saved_request_validation_never_copies_private_payload_or_calls_endpoint(tmp_path, monkeypatch):
    from .cases import build_case
    request = build_case('v2_send', 'synthetic')['request']
    request['input'][0]['content'][0]['text'] = 'private captured prompt'
    saved = tmp_path / 'captured.json'
    cli.save_json(saved, request)
    monkeypatch.setattr(transport, 'exchange', lambda *_a, **_k: pytest.fail('network call'))
    out = tmp_path / 'validation'
    assert cli.main(['validate-request', '--input', str(saved), '--output', str(out)]) == 0
    report = cli.read_json(out / 'report.json')
    assert not report['network_executed'] and report['request_count'] == 0
    assert b'private captured prompt' not in (out / 'report.json').read_bytes()


def test_redaction_handles_json_escape_variants_and_dictionary_keys():
    raw = b'{"model":"\\u0073ecret","s\\u0065cret":"value"}'
    stored = cli.scrub(raw, ['secret'])
    assert b'secret' not in stored
    assert json.loads(stored) == {'model': '[REDACTED]', '[REDACTED]': 'value'}
    assert cli.scrub_values({'secret': {'model': 'secret'}}, ['secret']) == {'[REDACTED]': {'model': '[REDACTED]'}}


def test_attempt_and_nested_report_model_keys_are_redacted(tmp_path, monkeypatch):
    plan = prepare(tmp_path, cases='message', stream='json')
    monkeypatch.setenv('CONTRACT_TEST_KEY', 'secret-diagnostic-key')
    def hostile(endpoint, request, headers, **kwargs):
        result = fake_exchange([])(endpoint, request, headers, **kwargs)
        result['response']['model'] = {'secret-diagnostic-key': 'value'}
        result['body'] = json.dumps(result['response']).encode()
        return result
    monkeypatch.setattr(transport, 'exchange', hostile)
    out = tmp_path / 'result'
    args = probe_args(plan, out)
    args[args.index('--endpoint') + 1] = 'http://127.0.0.1:1/secret-diagnostic-key/responses'
    args[args.index('--auth') + 1] = 'bearer'
    args += ['--api-key-env', 'CONTRACT_TEST_KEY']
    assert cli.main(args) == 0
    assert all(b'secret-diagnostic-key' not in path.read_bytes() for path in out.iterdir())


@pytest.mark.parametrize('mode,returned', [('json', 'text/event-stream'), ('sse', 'application/json')])
def test_probe_requires_requested_json_or_sse_mode(tmp_path, monkeypatch, mode, returned):
    plan = prepare(tmp_path, cases='message', stream=mode)
    def mismatch(endpoint, request, headers, **kwargs):
        result = fake_exchange([])(endpoint, request, headers, **kwargs)
        result['content_type'] = returned
        return result
    monkeypatch.setattr(transport, 'exchange', mismatch)
    out = tmp_path / 'result'
    assert cli.main(probe_args(plan, out)) == 1
    assert cli.read_json(out / 'report.json')['results'][0]['errors'][0]['code'] == 'response_mode'


def test_offline_replay_rejects_duplicate_response_keys(tmp_path):
    plan = prepare(tmp_path, cases='message', stream='json')
    item = cli.read_json(plan)['items'][0]
    response = response_for(item['request'])
    wire = json.dumps(response).replace('"status": "completed"', '"status": "failed", "status": "completed"', 1)
    saved = tmp_path / 'duplicate.json'
    saved.write_text(wire)
    out = tmp_path / 'replayed'
    assert cli.main(['replay', '--plan', str(plan), '--item', item['id'],
                     '--response', str(saved), '--output', str(out)]) == 1
    assert 'invalid_json' in {e['code'] for e in cli.read_json(out / 'report.json')['results'][0]['errors']}


def test_saved_request_bytes_and_hash_match_actual_http_body(tmp_path):
    from .test_transport import server
    plan = prepare(tmp_path, cases='function', stream='json')
    response = response_for(cli.read_json(plan)['items'][0]['request'])
    out = tmp_path / 'result'
    with server('json', json.dumps(response).encode()) as (endpoint, calls):
        args = probe_args(plan, out)
        args[args.index('--endpoint') + 1] = endpoint
        assert cli.main(args) == 0
    transmitted = calls[0][2]
    artifact = out / 'function-json-turn1.request.json'
    report = cli.read_json(out / 'report.json')
    assert artifact.read_bytes() == transmitted
    assert report['results'][0]['exchanges'][0]['wire_request_sha256'] == cli.digest(transmitted)


def reasoning_drift_fixture():
    from .cases import build_case
    case = build_case('v2_send', 'synthetic', stream=True)
    wire, context, expect = cli.wire_request(case, 'codex-v2-bridge', cli.bridge_module().BridgeState())
    response = response_for(wire)
    events, _ = stream_for(response)
    for event in events:
        if 'output_index' in event:
            event['output_index'] += 1
    done = {'id': 'rs_1', 'type': 'reasoning', 'summary': [{'type': 'summary_text', 'text': 'Synthetic thought.'}]}
    terminal = {'id': 'rs_1', 'type': 'reasoning', 'role': 'assistant', 'status': 'completed',
                'content': [{'type': 'output_text', 'text': 'Synthetic thought.', 'annotations': []}]}
    response['output'].insert(0, terminal)
    events = [{'type': 'response.output_item.added', 'output_index': 0,
               'item': {'id': 'rs_1', 'type': 'reasoning', 'status': 'in_progress'}},
              {'type': 'response.output_item.done', 'output_index': 0, 'item': done}, *events]
    _, raw_errors = transport.reconstruct_response(events)
    result = {'http_status': 200, 'content_type': 'text/event-stream', 'events': events,
              'response': response, 'errors': raw_errors}
    return case, context, expect, result


def test_bridge_rechecks_normalized_stream_while_retaining_raw_wire_findings():
    case, context, expect, result = reasoning_drift_fixture()
    assert 'item_mismatch' in {e['code'] for e in result['errors']}
    client, errors, wire_errors = cli.check_exchange(result, expect, 'codex-v2-bridge', context, stream=True)
    assert errors == []
    assert 'reasoning_summary' in {e['code'] for e in wire_errors}
    assert cli.validate_response(client, case['expect'], 'codex-v2-bridge') == []
    # Native checking still treats the original upstream defect as a failure.
    _, errors, _ = cli.check_exchange(result, expect, 'responses', None, stream=True)
    assert {'item_mismatch', 'reasoning_summary'} <= {e['code'] for e in errors}


@pytest.mark.parametrize('fault', ['function_conflict', 'reasoning_conflict', 'missing_done', 'parse', 'truncated', 'wrong_type'])
def test_bridge_does_not_hide_other_wire_failures(fault):
    case, context, expect, result = reasoning_drift_fixture()
    if fault == 'function_conflict':
        result['response']['output'][1] = {**result['response']['output'][1], 'arguments': '{"message":"wrong"}'}
    elif fault == 'reasoning_conflict':
        result['response']['output'][0]['content'][0]['text'] = 'Different thought.'
    elif fault == 'missing_done':
        result['events'] = [event for event in result['events']
                            if not (event['type'] == 'response.output_item.done' and event['output_index'] == 1)]
    elif fault == 'wrong_type':
        result['response']['output'][0]['type'] = 'message'
    if fault in ('parse', 'truncated'):
        result['errors'].append({'code': 'invalid_sse_json' if fault == 'parse' else 'truncated_sse_frame',
                                  'path': '$', 'message': 'Synthetic parse failure'})
    else:
        _, result['errors'] = transport.reconstruct_response(result['events'])
    client, errors, _ = cli.check_exchange(result, expect, 'codex-v2-bridge', context, stream=True)
    if isinstance(client, dict):
        errors += cli.validate_response(client, case['expect'], 'codex-v2-bridge')
    assert errors
