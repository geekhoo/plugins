"""Opt-in pure native Responses plaintext adapter; no transport or decryption.

Native namespaces, tool-search identities and reasoning envelopes are preserved.
Only collaboration message schemas request plaintext. Tagged plaintext may be
relabelled on replay only after an exact completed-response provenance match.
Inter-agent messages are lowered to framed user messages before forwarding.
The native launcher selects this mode explicitly; the legacy bridge is separate.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
import json
import threading

from .mapper import MappingError, digest

COLLABORATION_CALLS = {'spawn_agent', 'send_message', 'followup_task'}


@dataclass
class NativePlaintextState:
    max_entries: int = 10000
    _known: dict = field(default_factory=dict, init=False, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def remember(self, entries):
        """Entries bind exact plaintext to request/call/field origin; never user text."""
        values = {digest(value): (value, origin) for value, origin in entries}
        with self._lock:
            if len(set(self._known) | set(values)) > self.max_entries:
                raise MappingError('Native plaintext provenance capacity exceeded')
            self._known.update(values)

    def recover(self, value):
        if not isinstance(value, str):
            raise MappingError('Invalid native tagged content')
        with self._lock:
            known = self._known.get(digest(value))
        if known is None or known[0] != value:
            raise MappingError('Native tagged content has no completed-response plaintext provenance')
        return value


@dataclass
class NativePlaintextContext:
    state: NativePlaintextState
    origin: str
    fields: dict


def _has_encryption(value):
    if isinstance(value, dict):
        return value.get('encrypted') is True or any(_has_encryption(v) for v in value.values())
    return isinstance(value, list) and any(_has_encryption(v) for v in value)


def _normalize_parts(parts, state):
    for part in parts:
        if isinstance(part, dict) and part.get('type') == 'encrypted_content':
            # Do not preserve an opaque field alongside the now-plaintext part.
            if set(part) != {'type', 'encrypted_content'}:
                raise MappingError('Unexpected native tagged-content fields')
            value = state.recover(part['encrypted_content'])
            part.clear()
            part.update(type='input_text', text=value)


def _lower_agent_message(item):
    """Deliver an inter-agent message as a user message, in the bridge mapper's framing.

    The LiteLLM route drops agent_message input items whenever the request carries
    tools, so a cold worker never sees its brief (live probe, 2026-10-30).
    """
    content = item.get('content')
    if not isinstance(content, list) or not all(isinstance(part, dict) and part.get('type') == 'input_text'
                                                and isinstance(part.get('text'), str) for part in content):
        raise MappingError('Native agent message content must be plaintext parts')
    # JSON framing avoids delimiter ambiguity in untrusted agent names.
    envelope = {key: item[key] for key in item if key not in {'type', 'content'}}
    return {'type': 'message', 'role': 'user', 'content': [
        {'type': 'input_text', 'text': 'Agent message envelope: '
         + json.dumps(envelope, sort_keys=True, ensure_ascii=False) + '\n'}, *content]}


def translate_native_request(body, state, *, origin):
    """Return an independent request and its explicit plaintext response contract."""
    if not isinstance(body, dict) or not isinstance(origin, str) or not origin:
        raise MappingError('Native plaintext request needs an object and origin identifier')
    mapped = copy.deepcopy(body)
    fields = {}
    tools = mapped.get('tools', [])
    if not isinstance(tools, list):
        raise MappingError('Native tools must be a list')
    for namespace in tools:
        if not isinstance(namespace, dict) or namespace.get('type') != 'namespace' or namespace.get('name') != 'collaboration':
            continue
        for tool in namespace.get('tools', []):
            if tool.get('type') != 'function' or tool.get('name') not in COLLABORATION_CALLS:
                continue
            identity = ('collaboration', tool['name'])
            if identity in fields:
                raise MappingError('Duplicate native collaboration identity')
            parameters = tool.get('parameters', {})
            properties = parameters.get('properties', {})
            selected = set()
            for name in ('message', 'prompt'):
                schema = properties.get(name)
                if isinstance(schema, dict) and schema.get('type') == 'string':
                    if 'encrypted' in schema and not isinstance(schema['encrypted'], bool):
                        raise MappingError('Native collaboration encryption annotation is invalid')
                    schema.pop('encrypted', None)
                    selected.add(name)
            if not selected or _has_encryption(parameters):
                raise MappingError('Native collaboration plaintext schema is unsupported')
            fields[identity] = selected
    inputs = mapped.get('input', [])
    if isinstance(inputs, list):
        for index, item in enumerate(inputs):
            if not isinstance(item, dict):
                raise MappingError('Invalid native input item')
            key = ('content' if item.get('type') == 'agent_message' else
                   'output' if item.get('type') == 'function_call_output' else None)
            if key and isinstance(item.get(key), list):
                _normalize_parts(item[key], state)
            if item.get('type') == 'agent_message':
                inputs[index] = _lower_agent_message(item)
    elif not isinstance(inputs, str):
        raise MappingError('Native input must be text or a list')
    return mapped, NativePlaintextContext(state, origin, fields)


def _arguments(raw):
    def constant(value):
        raise ValueError('Non-finite JSON constant')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate key')
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=unique, parse_constant=constant)
    except (TypeError, ValueError) as exc:
        raise MappingError('Native plaintext collaboration arguments must be a JSON object') from exc
    if not isinstance(value, dict):
        raise MappingError('Native plaintext collaboration arguments must be a JSON object')
    return value


def _collaboration_fields(item, context):
    if (not isinstance(item, dict) or item.get('type') != 'function_call'
            or item.get('namespace') != 'collaboration' or item.get('name') not in COLLABORATION_CALLS):
        return None
    identity = (item['namespace'], item.get('name'))
    selected = context.fields.get(identity)
    if selected is None:
        raise MappingError('Native collaboration response was not declared plaintext')
    if item.get('encrypted_content') not in (None, '') or ('encrypted_function_args' in item and item['encrypted_function_args'] != []):
        raise MappingError('Opaque native collaboration response is unsupported')
    return selected


def _completed_item(item, context, pending):
    selected = _collaboration_fields(item, context)
    if selected is None:
        return
    identity = (item['namespace'], item['name'])
    if not isinstance(item.get('call_id'), str) or not item['call_id'] or item.get('status') not in (None, 'completed'):
        raise MappingError('Native collaboration response is not a completed identified call')
    arguments = _arguments(item.get('arguments'))
    present = selected & arguments.keys()
    if not present or any(not isinstance(arguments[name], str) for name in present):
        raise MappingError('Native collaboration plaintext message is missing or invalid')
    item['encrypted_function_args'] = []
    pending.extend((arguments[name], (context.origin, identity, item['call_id'], name)) for name in present)


def map_native_response_json(body, context):
    mapped = copy.deepcopy(body)
    if not isinstance(mapped, dict) or not isinstance(mapped.get('output', []), list):
        raise MappingError('Native response must have an output list')
    pending = []
    for item in mapped.get('output', []):
        _completed_item(item, context, pending)
    context.state.remember(pending)
    return mapped


def map_native_sse_event(event, context):
    """Only complete items establish provenance; partial deltas stay untouched."""
    mapped = copy.deepcopy(event)
    if not isinstance(mapped, dict):
        raise MappingError('Native SSE event must be an object')
    pending = []
    if mapped.get('type') == 'response.output_item.added':
        item = mapped.get('item')
        if _collaboration_fields(item, context) is not None:
            if 'arguments' in item and not isinstance(item['arguments'], str):
                raise MappingError('Invalid native collaboration argument fragment')
            item['encrypted_function_args'] = []
    if mapped.get('type') == 'response.output_item.done':
        _completed_item(mapped.get('item'), context, pending)
    response = mapped.get('response')
    if isinstance(response, dict) and mapped.get('type') == 'response.completed':
        if not isinstance(response.get('output', []), list):
            raise MappingError('Native response must have an output list')
        for item in response.get('output', []):
            _completed_item(item, context, pending)
    context.state.remember(pending)
    return mapped


def map_native_sse_frame(frame, context):
    """Preserve SSE framing metadata while mapping the complete data object."""
    lines = frame.decode('utf-8').splitlines()
    data = [line[5:].lstrip(' ') for line in lines if line.startswith('data:')]
    if not data or '\n'.join(data) == '[DONE]':
        return frame
    try:
        mapped = map_native_sse_event(json.loads('\n'.join(data)), context)
    except (TypeError, ValueError) as exc:
        raise MappingError('Invalid native upstream SSE data') from exc
    kept = [line for line in lines if not line.startswith('data:')]
    return ('\n'.join(kept + ['data: ' + json.dumps(mapped, separators=(',', ':'), ensure_ascii=False)]) + '\n\n').encode('utf-8')
