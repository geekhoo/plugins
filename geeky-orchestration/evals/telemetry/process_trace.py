"""Harness-neutral process trace: validate process events and export them once to Langfuse.

An adapter turns one harness's native records into a `geeky-eval.process-events/1` document. This module
knows nothing about any harness or model. See ../process-trace.md for the contract.

    python process_trace.py <events.json> --out <folder> [--export]

Without --export it only validates and prints the spans it would send. Credentials come from the
LANGFUSE_CODEX_* environment variables and are never printed.
"""
import argparse
import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SCHEMA = 'geeky-eval.process-events/1'
ROOT_NAME = 'geeky-orchestration.end-to-end'
STAGES = ('spec-research', 'geeky-plan', 'plan-review', 'geeky-implement', 'impl-review')
ROLES = ('orchestrator', 'coder', 'reviewer', 'planner', 'unknown')
COVERAGE = ('complete', 'partial', 'unknown')
EVENT_NAMES = {'lane': 'lane.move', 'review': 'review.verdict'}
GATES = ('validate-kanban', 'validate-planning-folder', 'validate-task-schema', 'check-dod', 'check-commit', 'check-frozen-artifact')
MAX_VALUE = 198


def stamp(value):
    return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)


def nanos(value):
    moment = stamp(value)
    return str(int(moment.timestamp()) * 1_000_000_000 + moment.microsecond * 1_000)


def validate(doc):
    """Reject a document the scorer could not trust. Returns the document unchanged."""
    if doc.get('schema') != SCHEMA:
        raise ValueError('Unsupported process-events schema')
    for key in ('session_id', 'harness', 'adapter', 'adapter_version', 'run_start', 'run_end'):
        if not doc.get(key):
            raise ValueError(f'Missing {key}')
    if len(doc['session_id']) >= 200 or not doc['session_id'].isascii():
        raise ValueError('sessionId must be US-ASCII and under 200 characters')
    coverage = doc.get('coverage') or {}
    for area in ('stage', 'lane', 'review', 'gate'):
        if coverage.get(area) not in COVERAGE:
            raise ValueError(f'Invalid coverage for {area}')
    previous = None
    for item in doc.get('stages', []):
        if item['stage'] not in STAGES:
            raise ValueError(f'Unknown stage {item["stage"]}')
        if stamp(item['end']) < stamp(item['start']) or (previous and stamp(item['start']) < previous):
            raise ValueError(f'Stage {item["stage"]} is out of order')
        previous = stamp(item['end'])
    for event in doc.get('events', []):
        if event.get('kind') not in ('lane', 'review', 'gate'):
            raise ValueError(f'Unknown event kind {event.get("kind")}')
        if event['kind'] == 'gate' and event.get('gate_name') not in GATES:
            raise ValueError(f'Unknown gate {event.get("gate_name")}')
        stamp(event['at'])
    return doc


def _attr(key, value):
    if isinstance(value, (list, tuple)):
        return {'key': key, 'value': {'arrayValue': {'values': [{'stringValue': str(item)} for item in value]}}}
    return {'key': key, 'value': {'stringValue': str(value)}}


def _id(size, *parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:size]


def event_line(event):
    if event['kind'] == 'lane':
        bound = ' (by this commit)' if event.get('lane_evidence') == 'commit-bound' else ''
        return f'{event["task_id"]}: {event["from_lane"]} -> {event["to_lane"]}{bound}'
    if event['kind'] == 'review':
        return f'{event["review_scope"]}: {event["verdict"]}'
    target = f' {event["task_id"]}' if event.get('task_id') else ''
    return f'{event["gate_name"]}{target}: {event["gate_result"]}'


def timeline(doc):
    """A readable account of the run. Session replay shows chat-format text, so this is what it displays."""
    rows = [(item['start'], f'enter {item["stage"]}') for item in doc.get('stages', [])]
    rows += [(event['at'], event_line(event)) for event in doc.get('events', []) if event['kind'] != 'gate']
    rows.sort(key=lambda row: stamp(row[0]))
    return '\n'.join(f'{stamp(when).strftime("%H:%M:%SZ")} {text}' for when, text in rows)


def build_spans(doc):
    """One trace per run with new, deterministic span ids. Nothing already exported is touched."""
    session = doc['session_id']
    trace = _id(32, session, 'process-trace')
    user = f'{doc["harness"]}/workflow'
    tags = ['workflow:geeky', 'process-trace', *doc.get('tags', [])]
    common = {'workflow_schema': 'v1', 'adapter': doc['adapter'], 'adapter_version': doc['adapter_version'], **doc.get('metadata', {})}

    def span(key, parent, name, kind, start, end, meta=None, text_in=None, text_out=None, extra=None):
        attrs = {'langfuse.session.id': session, 'langfuse.user.id': user, 'langfuse.trace.name': ROOT_NAME, 'langfuse.trace.tags': tags,
                 'langfuse.environment': doc.get('environment', 'default'), 'langfuse.observation.type': kind, **(extra or {})}
        if text_in is not None:
            attrs['langfuse.observation.input'] = text_in
        if text_out is not None:
            attrs['langfuse.observation.output'] = text_out
        for field, value in {**common, **(meta or {})}.items():
            if value is not None:
                attrs[f'langfuse.observation.metadata.{field}'] = str(value)[:MAX_VALUE]
        row = {'traceId': trace, 'spanId': _id(16, session, key), 'name': name, 'kind': 1, 'startTimeUnixNano': nanos(start),
               'endTimeUnixNano': nanos(end), 'attributes': [_attr(k, v) for k, v in attrs.items()], 'status': {'code': 1}}
        if parent:
            row['parentSpanId'] = parent
        return row

    coverage = {f'coverage_{area}': state for area, state in doc['coverage'].items()}
    root = span('root', None, ROOT_NAME, 'chain', doc['run_start'], doc['run_end'], coverage,
                json.dumps([{'role': 'user', 'content': f'Run {session}'}]),
                json.dumps([{'role': 'assistant', 'content': timeline(doc) or 'No process events observed.'}]),
                {'gen_ai.operation.name': 'invoke_workflow', 'gen_ai.workflow.name': 'geeky-orchestration'})
    spans = [root]
    stage_ids = []
    for item in doc.get('stages', []):
        row = span(('stage', item['stage']), root['spanId'], f'stage:{item["stage"]}', 'chain', item['start'], item['end'],
                   {'workflow_stage': item['stage'], 'stage_evidence': item.get('evidence'), 'stage_source': item.get('source')},
                   f'enter {item["stage"]}', item.get('source'))
        spans.append(row)
        stage_ids.append((stamp(item['start']), stamp(item['end']), item['stage'], row['spanId']))

    def stage_for(when):
        moment = stamp(when)
        for start, end, name, span_id in stage_ids:
            if start <= moment <= end:
                return name, span_id
        return None, root['spanId']

    task_ids = {}
    for task in doc.get('tasks', []):
        name, parent = stage_for(task['start'])
        row = span(('task', task['task_id']), parent, 'task', 'span', task['start'], task['end'],
                   {'workflow_stage': name, 'task_id': task['task_id'], 'owner_actor': task.get('owner_actor')},
                   f'{task["task_id"]} owner {task.get("owner_actor") or "unknown"}', f'{task["task_id"]} {task.get("final_lane") or ""}'.strip())
        spans.append(row)
        task_ids[task['task_id']] = (stamp(task['start']), stamp(task['end']), row['spanId'])
    for index, event in enumerate(doc.get('events', [])):
        name, parent = stage_for(event['at'])
        window = task_ids.get(event.get('task_id'))
        if window and window[0] <= stamp(event['at']) <= window[1]:
            parent = window[2]
        meta = {key: value for key, value in event.items() if key not in ('kind', 'at', 'text')}
        meta['workflow_stage'] = name
        label = f'gate:{event["gate_name"]}' if event['kind'] == 'gate' else EVENT_NAMES[event['kind']]
        spans.append(span(('event', index, event['kind'], event['at']), parent, label, 'event', event['at'], event['at'], meta, event_line(event)))
    return spans


def otlp_body(doc, spans):
    resource = [_attr('service.name', 'geeky-process-trace'), _attr('langfuse.environment', doc.get('environment', 'default'))]
    return {'resourceSpans': [{'resource': {'attributes': resource},
                               'scopeSpans': [{'scope': {'name': 'geeky.process-trace', 'version': doc['adapter_version']}, 'spans': spans}]}]}


class Client:
    def __init__(self):
        self.base = os.environ['LANGFUSE_CODEX_BASE_URL'].rstrip('/')
        token = f"{os.environ['LANGFUSE_CODEX_PUBLIC_KEY']}:{os.environ['LANGFUSE_CODEX_SECRET_KEY']}"
        self.auth = 'Basic ' + base64.b64encode(token.encode()).decode()

    def observations(self, **query):
        rows, cursor = [], None
        while True:
            params = {'limit': 500, 'fields': 'core,basic', **query}
            if cursor:
                params['cursor'] = cursor
            request = urllib.request.Request(f'{self.base}/api/public/v2/observations?{urllib.parse.urlencode(params)}', headers={'Authorization': self.auth})
            with urllib.request.urlopen(request, timeout=120) as response:
                page = json.load(response)
            rows.extend(page.get('data', []))
            cursor = (page.get('meta') or {}).get('cursor')
            if not cursor or not page.get('data'):
                return rows

    def export(self, body):
        request = urllib.request.Request(f'{self.base}/api/public/otel/v1/traces', data=json.dumps(body).encode(), method='POST',
                                         headers={'Authorization': self.auth, 'Content-Type': 'application/json', 'x-langfuse-ingestion-version': '4'})
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status


def export_once(doc, spans, out, client, wait=240):
    """Export a run's process trace at most once. Re-sending a span id is what v4 warns against."""
    claim = Path(out) / 'process-trace.claim.json'
    if claim.exists():
        raise SystemExit('A claim already exists for this output folder; refusing to export twice.')
    if client.observations(sessionId=doc['session_id'], name=ROOT_NAME):
        raise SystemExit('This session already has a process trace; refusing to export twice.')
    ids = sorted(span['spanId'] for span in spans)
    if len(set(ids)) != len(ids):
        raise SystemExit('Duplicate span ids in the process trace.')
    claim.write_text(json.dumps({'session_id': doc['session_id'], 'trace_id': spans[0]['traceId'], 'spans': len(spans),
                                 'utc': datetime.now(timezone.utc).isoformat()}, indent=1) + '\n', encoding='utf-8')
    status = client.export(otlp_body(doc, spans))
    deadline = time.monotonic() + wait
    found = []
    while time.monotonic() < deadline:
        found = client.observations(sessionId=doc['session_id'], traceId=spans[0]['traceId'])
        if {row['id'] for row in found} >= set(ids):
            break
        time.sleep(10)
    result = {'status': status, 'expected': len(ids), 'rows': len(found), 'unique': len({row['id'] for row in found}),
              'missing': len(set(ids) - {row['id'] for row in found}), 'trace_id': spans[0]['traceId']}
    (Path(out) / 'process-trace.export.json').write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('events', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    doc = validate(json.loads(args.events.read_text(encoding='utf-8')))
    spans = build_spans(doc)
    args.out.mkdir(parents=True, exist_ok=True)
    print(json.dumps({'session_id': doc['session_id'], 'spans': len(spans), 'coverage': doc['coverage']}))
    if args.export:
        print(json.dumps(export_once(doc, spans, args.out, Client())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
