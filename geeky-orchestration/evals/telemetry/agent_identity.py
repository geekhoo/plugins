"""Explicit MXC run and actor identities shared by the Claude bootstrap and tests.

Identity is derived from structured native metadata. Descriptions and prompt text
never establish a role. Every actor owns a trace; the run session groups them.

New runs (D111): userId is <harness>/<role> and the exact thread stays in agent_id.
The trace name is the plain role: native metadata carries no stage or scope when the
hook emits, so <stage>/<scope>/<role> is left to a post-run adapter.
"""
import hashlib
import json
import os
import re

SCHEMA = 'geeky-eval.agent-identity/2'


def slug(value, fallback='unknown'):
    value = re.sub(r'[^a-z0-9]+', '-', str(value or '').lower()).strip('-')
    return value or fallback


def bounded(value, limit=190):
    value = str(value)
    if len(value) <= limit:
        return value
    return value[:limit - 17] + '-' + hashlib.sha256(value.encode()).hexdigest()[:16]


def role_for(agent_type, *, root=False):
    if root:
        return 'orchestrator'
    role = str(agent_type or '').rsplit(':', 1)[-1]
    if role in ('geeky-orchestrator', 'geeky-implement-orchestrator'):
        return 'orchestrator'
    if role in ('geeky-coder', 'worker'):
        return 'coder'
    if role in ('code-reviewer', 'code-architect-reviewer', 'architect-reviewer',
                'reviewer', 'plan-reviewer', 'impl-reviewer'):
        return 'reviewer'
    # plan-review dispatches this type as its planner. Generic types stay unknown.
    if role == 'code-architect':
        return 'planner'
    return 'unknown'


def run_metadata(env=None):
    env = os.environ if env is None else env
    try:
        metadata = json.loads(env.get('GEEKY_RUN_METADATA', '{}'))
    except ValueError as exc:
        raise ValueError('Invalid GEEKY_RUN_METADATA') from exc
    if not isinstance(metadata, dict):
        raise ValueError('GEEKY_RUN_METADATA must be an object')
    return {str(k): bounded(v) for k, v in metadata.items() if v is not None}


def actor_identity(agent_id, agent_type=None, *, root=False, name=None,
                   parent_agent_id=None, parent_trace_id=None, parent_observation_id=None,
                   native_session_id=None, env=None):
    env = os.environ if env is None else env
    family = env.get('GEEKY_AGENT_FAMILY', 'claude-mxc-unknown')
    run = run_metadata(env)
    role = role_for(agent_type, root=root)
    native_id = str(agent_id or 'unknown')
    agent_name = str(name or agent_type or ('orchestrator' if root else 'unknown'))
    actor_name = f'{family}-{role}' + (f'-{slug(agent_name)}' if slug(agent_name) != role else '')
    metadata = {**run, 'identity_schema': SCHEMA,
                'agent_family': family, 'agent_id': bounded(native_id),
                'agent_role': role, 'agent_type': bounded(agent_type or ('orchestrator' if root else 'unknown')),
                'agent_name': bounded(agent_name),
                # The per-thread key old sessions used as userId, so both forms group through metadata.
                'agent_user_id': bounded(f'{actor_name}-{slug(native_id)}'),
                'actor_scope': 'main' if root else 'subagent'}
    for key, value in {'parent_agent_id': parent_agent_id, 'parent_trace_id': parent_trace_id,
                       'parent_observation_id': parent_observation_id,
                       'native_session_id': native_session_id}.items():
        if value is not None:
            metadata[key] = bounded(value)
    return {'session_id': env.get('GEEKY_SESSION_ID') or native_session_id or native_id,
            'user_id': f"{run.get('harness') or 'claude-code'}/{role}", 'trace_name': role, 'metadata': metadata,
            'tags': [f'agent-role:{role}', f'agent-type:{slug(agent_type or role)}']}
