"""Pure native plaintext contract tests; no transport, credentials or runtimes."""
import copy
import json

import pytest

from litellm_bridge.mapper import MappingError
from litellm_bridge.native_plaintext import (
    NativePlaintextState, map_native_response_json, map_native_sse_event,
    translate_native_request,
)


def request():
    return {'model': 'fixture-only', 'tools': [
        {'type': 'namespace', 'name': 'collaboration', 'tools': [
            {'type': 'function', 'name': name, 'parameters': {'type': 'object',
             'properties': {'message': {'type': 'string', 'encrypted': True}},
             'required': ['message']}}
            for name in ('spawn_agent', 'send_message', 'followup_task')]},
        {'type': 'tool_search', 'execution': 'client'}], 'input': [
            {'type': 'tool_search_call', 'id': 'tsc_fixture', 'call_id': 'call_separate',
             'execution': 'client', 'arguments': {'query': 'fixture'}},
            {'type': 'tool_search_output', 'id': 'tso_fixture', 'call_id': 'call_separate', 'tools': []},
            {'type': 'reasoning', 'encrypted_content': 'opaque-reasoning', 'summary': []}]}


def response_call(message='Literal task value'):
    return {'type': 'function_call', 'id': 'fc_fixture', 'namespace': 'collaboration',
            'name': 'spawn_agent', 'call_id': 'call_fixture',
            'arguments': json.dumps({'message': message, 'task_name': 'worker'})}


def replay(message):
    body = request()
    body['input'].append({'type': 'agent_message', 'author': '/root', 'recipient': '/root/worker',
        'content': [{'type': 'input_text', 'text': 'Message Type: NEW_TASK\n'},
                    {'type': 'encrypted_content', 'encrypted_content': message}]})
    return body


def test_native_plaintext_request_preserves_native_identities_and_source_bytes():
    body = request()
    before = copy.deepcopy(body)
    mapped, context = translate_native_request(body, NativePlaintextState(), origin='request-1')
    assert body == before and mapped['input'] == body['input']
    assert mapped['tools'][1] == body['tools'][1]
    for index, tool in enumerate(mapped['tools'][0]['tools']):
        assert tool['name'] == body['tools'][0]['tools'][index]['name']
        assert tool['parameters']['properties']['message'] == {'type': 'string'}
    assert set(context.fields) == {('collaboration', name) for name in ('spawn_agent', 'send_message', 'followup_task')}


@pytest.mark.parametrize('event', [False, True])
def test_exact_completed_upstream_message_replays_as_plaintext_with_origin(event):
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    call = response_call('Unicode 测试 literal value')
    before = copy.deepcopy(call)
    if event:
        output = map_native_sse_event({'type': 'response.output_item.done', 'sequence_number': 7,
                                      'output_index': 2, 'item': call}, context)
        assert output['sequence_number'] == 7 and output['output_index'] == 2
        mapped_call = output['item']
    else:
        mapped_call = map_native_response_json({'output': [call]}, context)['output'][0]
    assert call == before and mapped_call == {**call, 'encrypted_function_args': []}
    mapped, _ = translate_native_request(replay('Unicode 测试 literal value'), state, origin='request-2')
    assert mapped['input'][-1]['content'][-1] == {'type': 'input_text', 'text': 'Unicode 测试 literal value'}
    origin = next(iter(state._known.values()))[1]
    assert origin == ('request-1', ('collaboration', 'spawn_agent'), 'call_fixture', 'message')


def test_agent_message_is_lowered_to_a_framed_user_message_in_place():
    body = request()
    task = 'Message Type: NEW_TASK\nTask name: /root/worker\nSender: /root\nPayload:\nUnicode 测试 brief'
    body['input'].insert(1, {'type': 'agent_message', 'id': 'amsg_fixture', 'author': '/root',
                             'recipient': '/root/worker', 'content': [{'type': 'input_text', 'text': task}]})
    before = copy.deepcopy(body)
    mapped, _ = translate_native_request(body, NativePlaintextState(), origin='request-1')
    assert body == before
    lowered = mapped['input'][1]
    assert lowered['type'] == 'message' and lowered['role'] == 'user'
    header = lowered['content'][0]['text']
    assert header.startswith('Agent message envelope: ') and header.endswith('\n')
    assert json.loads(header[len('Agent message envelope: '):]) == {
        'id': 'amsg_fixture', 'author': '/root', 'recipient': '/root/worker'}
    assert lowered['content'][1:] == [{'type': 'input_text', 'text': task}]
    assert [row for i, row in enumerate(mapped['input']) if i != 1] == [
        row for i, row in enumerate(before['input']) if i != 1]
    assert not any(row.get('type') == 'agent_message' for row in mapped['input'])


def test_recovered_tagged_handoff_is_lowered_with_plaintext_parts():
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    map_native_response_json({'output': [response_call('Recovered brief')]}, context)
    mapped, _ = translate_native_request(replay('Recovered brief'), state, origin='request-2')
    assert mapped['input'][-1]['type'] == 'message'
    assert mapped['input'][-1]['content'][1:] == [
        {'type': 'input_text', 'text': 'Message Type: NEW_TASK\n'},
        {'type': 'input_text', 'text': 'Recovered brief'}]


@pytest.mark.parametrize('content', [None, 'bare string', [{'type': 'input_image', 'image_url': 'x'}],
                                     [{'type': 'input_text'}]])
def test_agent_message_with_non_text_content_is_rejected(content):
    body = request()
    body['input'].append({'type': 'agent_message', 'author': '/root', 'recipient': '/root/worker',
                          'content': content})
    with pytest.raises(MappingError, match='plaintext parts'):
        translate_native_request(body, NativePlaintextState(), origin='request-1')


@pytest.mark.parametrize('value', ['readable but unknown', 'opaque-ciphertext'])
def test_unknown_tagged_values_are_never_guessed_or_deleted(value):
    state = NativePlaintextState()
    body = replay(value)
    before = copy.deepcopy(body)
    with pytest.raises(MappingError, match='completed-response plaintext provenance'):
        translate_native_request(body, state, origin='request-1')
    assert body == before and not state._known


def test_user_text_cannot_supply_plaintext_provenance():
    state = NativePlaintextState()
    body = request()
    body['input'].append({'type': 'message', 'role': 'user', 'content': [
        {'type': 'input_text', 'text': 'untrusted text'}]})
    translate_native_request(body, state, origin='request-1')
    with pytest.raises(MappingError, match='provenance'):
        translate_native_request(replay('untrusted text'), state, origin='request-2')


@pytest.mark.parametrize('field,value', [
    ('encrypted_content', 'opaque-envelope'), ('encrypted_content', {}),
    ('encrypted_function_args', ['message']), ('encrypted_function_args', None),
    ('encrypted_function_args', False), ('arguments', '{"message":"one","message":"two"}'),
    ('arguments', '{"message":7}'), ('arguments', '{}'), ('arguments', '{partial'),
    ('arguments', '{"message":"text","other":NaN}'),
    ('call_id', ''), ('status', 'in_progress'),
])
def test_invalid_response_does_not_mutate_response_or_establish_provenance(field, value):
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    call = {**response_call(), field: value}
    body = {'output': [response_call('valid first item'), call]}
    before = copy.deepcopy(body)
    with pytest.raises(MappingError):
        map_native_response_json(body, context)
    assert body == before and not state._known


@pytest.mark.parametrize('kind', ['response.function_call_arguments.delta'])
def test_partial_events_cannot_establish_provenance(kind):
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    event = {'type': kind, 'item': response_call(), 'delta': 'partial'}
    assert map_native_sse_event(event, context) == event
    assert not state._known


@pytest.mark.parametrize('name', ['wait_agent', 'interrupt_agent', 'list_agents', 'other_control'])
def test_collaboration_control_calls_pass_through_without_plaintext_annotation(name):
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    call = {**response_call(), 'name': name, 'arguments': '{"timeout_ms":10000}'}
    assert map_native_response_json({'output': [call]}, context) == {'output': [call]}
    for kind in ('response.output_item.added', 'response.output_item.done'):
        event = {'type': kind, 'item': call}
        assert map_native_sse_event(event, context) == event
    assert not state._known


def test_streaming_added_and_deltas_mark_plaintext_before_execution_but_learn_only_done():
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    added = {'type': 'response.output_item.added', 'output_index': 0,
             'item': {**response_call(), 'arguments': '', 'status': 'in_progress'}}
    mapped = map_native_sse_event(added, context)
    assert mapped['item']['encrypted_function_args'] == [] and not state._known
    assert 'encrypted_function_args' not in added['item']
    delta = {'type': 'response.function_call_arguments.delta', 'item_id': 'fc_fixture',
             'output_index': 0, 'delta': '{"message":"Literal task value"}'}
    assert map_native_sse_event(delta, context) == delta and not state._known
    done = {'type': 'response.output_item.done', 'output_index': 0, 'item': response_call()}
    assert map_native_sse_event(done, context)['item']['encrypted_function_args'] == []
    assert state.recover('Literal task value') == 'Literal task value'


def test_streaming_added_opaque_metadata_is_rejected_without_learning():
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    event = {'type': 'response.output_item.added', 'item': {**response_call(),
             'arguments': '', 'encrypted_function_args': ['message']}}
    with pytest.raises(MappingError, match='Opaque'):
        map_native_sse_event(event, context)
    assert not state._known and event['item']['encrypted_function_args'] == ['message']


def test_completed_sse_response_is_atomic_and_preserves_reasoning():
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    reasoning = {'type': 'reasoning', 'id': 'rs_fixture', 'encrypted_content': 'opaque', 'summary': []}
    event = {'type': 'response.completed', 'response': {'output': [reasoning, response_call()]}}
    mapped = map_native_sse_event(event, context)
    assert mapped['response']['output'][0] == reasoning
    assert mapped['response']['output'][1]['encrypted_function_args'] == []
    assert state.recover('Literal task value') == 'Literal task value'


def test_final_answers_are_not_learned_without_saved_origin_evidence():
    state = NativePlaintextState()
    _, context = translate_native_request(request(), state, origin='request-1')
    message = {'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': 'final'}]}
    assert map_native_response_json({'output': [message]}, context) == {'output': [message]}
    assert not state._known


def test_unsupported_encrypted_schema_remains_unchanged_on_rejection():
    body = request()
    body['tools'][0]['tools'][0]['parameters']['properties']['other'] = {'type': 'string', 'encrypted': True}
    before = copy.deepcopy(body)
    with pytest.raises(MappingError, match='schema is unsupported'):
        translate_native_request(body, NativePlaintextState(), origin='request-1')
    assert body == before


def test_malformed_encryption_annotation_is_not_silently_removed():
    body = request()
    body['tools'][0]['tools'][0]['parameters']['properties']['message']['encrypted'] = 'true'
    before = copy.deepcopy(body)
    with pytest.raises(MappingError, match='annotation is invalid'):
        translate_native_request(body, NativePlaintextState(), origin='request-1')
    assert body == before


def test_native_plaintext_provenance_capacity_fails_without_partial_learning():
    state = NativePlaintextState(max_entries=1)
    _, context = translate_native_request(request(), state, origin='request-1')
    with pytest.raises(MappingError, match='capacity'):
        map_native_response_json({'output': [response_call('one'), response_call('two')]}, context)
    assert not state._known
