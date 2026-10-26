"""Small, source-bound evaluation-inputs sidecar. No trace merging or inference."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

METRICS = ('runtime', 'tokens', 'calls', 'latency_idle', 'commits', 'coverage', 'backend', 'cost')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Scope intervals require timezone-aware timestamps')
    return parsed


def load_scope(path, required_paths=()):
    """Validate declarations and bytes; missing sources stay unknown, never complete."""
    path = Path(path)
    scope = json.loads(path.read_text(encoding='utf-8-sig'))
    if scope.get('schema') != 'geeky-eval.inputs/1':
        raise ValueError('Explicit geeky-eval.inputs/1 scope required')
    sid = scope.get('scope_id')
    if not isinstance(sid, str) or not sid.strip() or scope.get('kind') not in ('initial', 'continuation', 'cumulative'):
        raise ValueError('Invalid scope ID or kind')
    if ('parent_scope_id' not in scope or scope['parent_scope_id'] == sid or
            (scope['parent_scope_id'] is not None and
             (not isinstance(scope['parent_scope_id'], str) or not scope['parent_scope_id'].strip()))):
        raise ValueError('Declare a distinct parent scope (null for initial)')
    if (scope['kind'] == 'initial') != (scope['parent_scope_id'] is None):
        raise ValueError('Resumed scope requires a parent; initial scope has no parent')
    config = scope.get('configuration', {})
    for key, size in (('prompt_sha256', 64), ('plugin_sha', 40)):
        if key not in config or (config[key] is not None and not re.fullmatch(f'[0-9a-f]{{{size}}}', config[key])):
            raise ValueError('Declare prompt hash and plugin commit (null only when unknown)')
    sources, missing, paths = {}, [], set()
    for source in scope.get('sources', []):
        key = source['id']
        source_path = Path(source['path'])
        source_path = source_path if source_path.is_absolute() else path.parent / source_path
        resolved = source_path.resolve()
        if not key or key in sources or resolved in paths or not re.fullmatch('[0-9a-f]{64}', source['sha256']):
            raise ValueError('Duplicate/invalid source identity, path or SHA-256')
        if not isinstance(source.get('ancestry'), list):
            raise ValueError('Every source requires explicit ancestry')
        sources[key] = source
        paths.add(resolved)
        if not source_path.is_file():
            missing.append(key)
        elif sha256(source_path) != source['sha256']:
            raise ValueError(f'Source hash mismatch: {key}')
    if not sources:
        raise ValueError('Scope requires source paths and hashes')
    for required in required_paths:
        if Path(required).resolve() not in paths:
            raise ValueError(f'Input is not bound to scope: {required}')
    for source in sources.values():
        if any(parent not in sources or parent == source['id'] for parent in source['ancestry']):
            raise ValueError('Unknown/self source ancestry')
        seen, todo = set(), list(source['ancestry'])
        while todo:
            ancestor = todo.pop()
            if ancestor == source['id']:
                raise ValueError('Cyclic source ancestry')
            if ancestor not in seen:
                seen.add(ancestor)
                todo.extend(sources[ancestor]['ancestry'])
    segments = scope.get('segments', [])
    if not segments:
        raise ValueError('Authorized segment intervals required')
    segment_ids = set()
    for segment in segments:
        key = segment['segment_id']
        if not key or key in segment_ids or not segment.get('authorization_reference'):
            raise ValueError('Duplicate segment or missing authorization reference')
        segment_ids.add(key)
        if timestamp(segment['start']) >= timestamp(segment['end']):
            raise ValueError('Empty/reversed segment interval')
    derivation = scope.get('ownership', {})
    if derivation.get('method') not in ('native', 'source-reviewed') or not derivation.get('rule'):
        raise ValueError('Explicit ownership derivation required; timestamps alone are insufficient')
    if scope['kind'] != 'initial' and derivation.get('method') != 'source-reviewed':
        raise ValueError('Resumed ownership requires source-reviewed derivation')
    if derivation.get('method') == 'source-reviewed' and derivation.get('evidence_source') not in sources:
        raise ValueError('Source-reviewed ownership requires hashed review evidence')
    if derivation.get('cutoff'):
        timestamp(derivation['cutoff'])
    owned = set()
    for assignment in derivation.get('assignments', []):
        if assignment['source_id'] not in sources:
            raise ValueError('Unknown ownership source')
        for identity in assignment['logical_ids']:
            if not identity or identity in owned:
                raise ValueError('Ambiguous duplicate logical ownership')
            owned.add(identity)
    if scope['kind'] != 'initial' and not owned:
        raise ValueError('Resumed inputs require explicit logical ownership assignments')
    defaults, overrides = scope.get('metric_default', {}), scope.get('metrics', {})
    if set(overrides) - set(METRICS):
        raise ValueError('Unknown metric override')
    labels = {}
    for metric in METRICS:
        label = {**defaults, **overrides.get(metric, {})}
        if (not label.get('scope_id') or not label.get('population') or
                not isinstance(label.get('source_ids'), list) or not label['source_ids'] or
                any(key not in sources for key in label['source_ids']) or
                type(label.get('additive')) is not bool or type(label.get('complete')) is not bool):
            raise ValueError(f'Metric {metric} requires source/population/additive/completeness labels')
        # Medians/coverage/identity/cost estimates cannot be summed across captures.
        if label['additive'] and (metric in ('latency_idle', 'coverage', 'backend', 'cost') or
                                  label['scope_id'] != sid or not label['complete']):
            raise ValueError(f'Unsupported addition for {metric}')
        label['complete'] = label['complete'] and not any(key in missing for key in label['source_ids'])
        labels[metric] = label
    return {**scope, 'input_sha256': sha256(path), 'metric_labels': labels,
            'completeness': 'unknown' if missing else 'sources-verified', 'missing_sources': missing}


def bind_run(scope, run):
    for key in ('prompt_sha256', 'plugin_sha'):
        if scope['configuration'][key] != run.get(key):
            raise ValueError(f'Run configuration differs from scope: {key}')
    execution = run.get('execution') or {}
    if execution.get('schema') == 'geeky-eval.execution/1':
        segment = next((s for s in scope['segments'] if s['segment_id'] == execution['segment_id']), None)
        if (not segment or segment.get('attempt_id') != execution['attempt_id'] or
                segment['authorization_reference'] != execution.get('authorization_reference')):
            raise ValueError('Scope segment/attempt/authorization differs from run execution record')


def scoped_efficiency(efficiency, scope):
    """Null out values whose population cannot establish the requested scope."""
    result = dict(efficiency)
    for field, metric in (('wall_time_s', 'runtime'), ('tokens_total', 'tokens'),
                          ('latency_median_ms', 'latency_idle'), ('commits', 'commits'),
                          ('calls', 'calls'), ('backend', 'backend'), ('cost', 'cost')):
        label = scope['metric_labels'][metric]
        if not label['complete'] or label['scope_id'] != scope['scope_id']:
            result[field] = None
    return result
