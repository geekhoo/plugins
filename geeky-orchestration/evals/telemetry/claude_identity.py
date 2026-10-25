"""Enrich the pinned Claude hook without modifying its source on disk."""
import contextvars
import functools
import hashlib
import json
import os
from pathlib import Path

from agent_identity import actor_identity


def install(module):
    """Wrap the hook's stable emission boundaries, retaining raw parsing/state."""
    from opentelemetry import context as otel_context

    current = contextvars.ContextVar('geeky_claude_actor', default=None)
    pending_root = contextvars.ContextVar('geeky_claude_agent_root', default=False)
    original_turn = module.emit_turn
    original_subagent = module.emit_subagent_observations
    original_start = module._start_backdated
    original_propagate = module.propagate_attributes
    original_mapping = module.get_subagent_transcripts_by_tool_use_id

    @functools.wraps(original_mapping)
    def mapping(transcript_path):
        result = original_mapping(transcript_path)
        for agent in result.values():
            try:
                meta = json.loads(agent['path'].with_suffix('.meta.json').read_text(encoding='utf-8'))
                if isinstance(meta.get('name'), str) and meta['name']:
                    agent['name'] = meta['name']
            except (OSError, ValueError, TypeError):
                pass
        return result

    @functools.wraps(original_propagate)
    def propagate(**kwargs):
        identity = current.get()
        if identity:
            kwargs.update(session_id=identity['session_id'], user_id=identity['user_id'],
                          trace_name=identity['trace_name'], metadata=identity['metadata'],
                          tags=list(dict.fromkeys([*(kwargs.get('tags') or []), *identity['tags']])))
        return original_propagate(**kwargs)

    @functools.wraps(original_start)
    def start(*args, **kwargs):
        identity = current.get()
        if identity:
            kwargs['metadata'] = {**(kwargs.get('metadata') or {}), **identity['metadata']}
            if kwargs.get('as_root') or pending_root.get():
                kwargs.update(name=identity['trace_name'], as_type='agent')
            if pending_root.get():
                pending_root.set(False)
                # A child needs its own trace to avoid replacing its parent's userId.
                timestamp = kwargs.get('start_time')
                seed = f"{identity['session_id']}:{identity['metadata']['agent_id']}:{timestamp}"
                kwargs.update(parent_otel_span=None, as_root=True,
                              forced_trace_id=hashlib.sha256(seed.encode()).hexdigest()[:32],
                              forced_parent_span_id=None)
        return original_start(*args, **kwargs)

    @functools.wraps(original_turn)
    def turn(langfuse, session_id, turn_num, turn, transcript_path, *args, **kwargs):
        identity = actor_identity(session_id, root=True, native_session_id=session_id)
        token = current.set(identity)
        try:
            return original_turn(langfuse, session_id, turn_num, turn, transcript_path, *args, **kwargs)
        finally:
            current.reset(token)

    @functools.wraps(original_subagent)
    def subagent(langfuse, parent_otel_span, subagent, start_timestamp,
                 span_name=None, extra_metadata=None, **kwargs):
        parent = current.get()
        path = subagent.get('path')
        native_id = subagent.get('agent_id') or (Path(path).stem.removeprefix('agent-') if path else 'unknown')
        parent_context = parent_otel_span.get_span_context() if parent_otel_span else None
        identity = actor_identity(native_id, subagent.get('agent_type'),
                                  name=subagent.get('name') or subagent.get('agent_type'),
                                  parent_agent_id=parent['metadata']['agent_id'] if parent else None,
                                  parent_trace_id=f'{parent_context.trace_id:032x}' if parent_context else None,
                                  parent_observation_id=f'{parent_context.span_id:016x}' if parent_context else None,
                                  native_session_id=parent['metadata'].get('native_session_id') if parent else None)
        token = current.set(identity)
        pending_token = pending_root.set(True)
        context_token = otel_context.attach(otel_context.Context())
        try:
            # Preserve the shared run session, but separate trace ownership by actor.
            with propagate(tags=json.loads(os.environ.get('GEEKY_RUN_TAGS', '[]'))):
                return original_subagent(langfuse, None, subagent, start_timestamp,
                                         span_name=identity['trace_name'],
                                         extra_metadata={**(extra_metadata or {}), **identity['metadata']}, **kwargs)
        finally:
            otel_context.detach(context_token)
            pending_root.reset(pending_token)
            current.reset(token)

    module.propagate_attributes = propagate
    module.emit_turn = turn
    module.emit_subagent_observations = subagent
    module._start_backdated = start
    module.get_subagent_transcripts_by_tool_use_id = mapping
