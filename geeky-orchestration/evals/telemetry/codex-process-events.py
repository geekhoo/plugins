"""Codex adapter: turn a retained Codex run's records into `geeky-eval.process-events/1`.

Reads rollouts (`session.jsonl`, `subagents/`), the run record and the contestant's git history. Only this
file knows Codex shapes; `process_events.py` decides what can be asserted. It makes no network call and
changes nothing in the run.

    python codex-process-events.py <run-folder> --workspace <git-checkout> --out <events.json>
"""
import argparse
import glob
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import process_trace  # noqa: E402
from process_events import (VERDICT_BOLD, VERDICT_LINE, apply_update, build_document, commit_bound_lane_events, first_commit_adding,  # noqa: E402,F401
                            load_snapshots, parse_board, reconcile, replay, role_for)

ADAPTER_VERSION = '1'
SHELL_TOOLS = ('exec_command', 'shell', 'shell_command', 'exec', 'apply_patch')
GATE_TOOLS = {'validate_kanban': 'validate-kanban', 'validate_planning_folder': 'validate-planning-folder', 'validate_task_schema': 'validate-task-schema',
              'check_dod': 'check-dod', 'check_commit': 'check-commit', 'check_frozen_artifact': 'check-frozen-artifact'}
PATCH = re.compile(r'\*\*\* Begin Patch(.*?)\*\*\* End Patch', re.S)
FILE_HEADER = re.compile(r'^\*\*\* (Add|Update|Delete) File: (.+?)\s*$', re.M)
SHELL_WRITE = re.compile(r"Set-Content|Add-Content|Out-File|WriteAllText|write_text|\.Replace\(['\"]##")
EXIT = re.compile(r'(?:exit(?:ed with)? code|exit_code"?)\s*[:=]?\s*(-?\d+)', re.I)


def file_sections(patch):
    """Yield (action, path, body) for each file in one patch."""
    marks = list(FILE_HEADER.finditer(patch))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(patch)
        yield mark.group(1), mark.group(2).replace('\\', '/'), patch[mark.end():end]


def load_thread(path):
    rows = [json.loads(line) for line in open(path, encoding='utf-8-sig', errors='replace') if line.strip()]
    meta = next((row.get('payload') or {} for row in rows if row.get('type') == 'session_meta'), {})
    source = meta.get('source')
    spawn = (source.get('subagent') or {}).get('thread_spawn', {}) if isinstance(source, dict) else {}
    cut = meta.get('subagent_history_start_ordinal') if spawn or meta.get('parent_thread_id') else None
    if cut is not None:
        rows = [row for row in rows if not isinstance(row.get('ordinal'), int) or row['ordinal'] >= cut]
    agent_type = meta.get('agent_role') or spawn.get('agent_role')
    root = not spawn and not meta.get('parent_thread_id')
    return {'file': os.path.basename(path), 'rows': rows, 'root': root, 'id': meta.get('id'),
            'role': 'orchestrator' if root else role_for(agent_type), 'agent_type': agent_type or ('orchestrator' if root else 'unknown'),
            'path': meta.get('agent_path') or spawn.get('agent_path') or meta.get('agent_nickname') or '',
            'start': meta.get('timestamp') or (rows[0].get('timestamp') if rows else None),
            'end': next((row.get('timestamp') for row in reversed(rows) if row.get('timestamp')), None)}


def calls(thread):
    """Yield completed tool calls in a thread, each with its output text."""
    outputs = {}
    for row in thread['rows']:
        payload = row.get('payload') or {}
        if payload.get('type') in ('function_call_output', 'custom_tool_call_output'):
            value = payload.get('output')
            outputs[payload.get('call_id')] = value if isinstance(value, str) else json.dumps(value)
    for index, row in enumerate(thread['rows']):
        payload = row.get('payload') or {}
        if payload.get('type') in ('function_call', 'custom_tool_call'):
            body = payload.get('arguments') if payload.get('type') == 'function_call' else payload.get('input')
            yield {'name': payload.get('name') or '', 'body': body if isinstance(body, str) else json.dumps(body), 'output': outputs.get(payload.get('call_id')),
                   'at': row.get('timestamp'), 'ref': f'{thread["file"]}:{index}', 'thread': thread}


def command_text(call):
    try:
        args = json.loads(call['body'])
    except ValueError:
        return call['body']
    if isinstance(args, dict):
        for key in ('cmd', 'command', 'input', 'patch'):
            value = args.get(key)
            if isinstance(value, list):
                return ' '.join(str(item) for item in value)
            if isinstance(value, str):
                return value
    return call['body']


def succeeded(output):
    """True, False, or None when the output does not say."""
    if output is None:
        return None
    if 'verification failed' in output[:200]:
        return False
    found = EXIT.search(output)
    if found:
        return found.group(1) == '0'
    return None


def board_operations(threads):
    """Every attempted board write, patches separated from opaque shell writes."""
    ops = []
    for thread in threads:
        for call in calls(thread):
            if call['name'].split('__')[-1] not in SHELL_TOOLS:
                continue
            text = command_text(call)
            if 'kanban.md' not in text:
                continue
            ok = succeeded(call['output'])
            sections = [section for patch in PATCH.findall(text) for section in file_sections(patch) if section[1].endswith('kanban.md')]
            if sections:
                ops.append({'at': call['at'], 'kind': 'patch', 'sections': sections, 'ok': ok, 'ref': call['ref'], 'actor': thread['role']})
            elif SHELL_WRITE.search(text) and re.search(r'kanban\.md[^\n]{0,120}(Set-Content|Out-File|Add-Content)|(WriteAllText|write_text)[^\n]{0,160}kanban|\$\w+\s*=\s*[^\n]*kanban\.md', text):
                ops.append({'at': call['at'], 'kind': 'shell', 'ok': ok, 'ref': call['ref'], 'actor': thread['role']})
    return ops


def gate_events(threads):
    events, readings = [], []
    for thread in threads:
        for call in calls(thread):
            name = call['name']
            key = next((tool for tool in GATE_TOOLS if name.endswith(tool)), None)
            if not key or call['output'] is None:
                continue
            data = None
            found = call['output'].find('{')
            if found >= 0:
                try:
                    data, _ = json.JSONDecoder().raw_decode(call['output'][found:])
                except ValueError:
                    data = None
            gate = GATE_TOOLS[key]
            result = 'unknown' if isinstance(data, dict) else 'call-error'
            if isinstance(data, dict):
                if key == 'check_frozen_artifact' and 'frozen' in data:
                    result = 'frozen' if data['frozen'] else 'not-frozen'
                elif isinstance(data.get('ok'), bool):
                    result = 'pass' if data['ok'] else 'fail'
                elif 'exit_code' in data:
                    result = 'pass' if data['exit_code'] == 0 else 'fail'
            try:
                args = json.loads(call['body'])
            except ValueError:
                args = {}
            params = args.get('params', args) if isinstance(args, dict) else {}
            task = params.get('task') if isinstance(params, dict) else None
            events.append({'kind': 'gate', 'at': call['at'], 'gate_name': gate, 'gate_result': result, 'task_id': task, 'actor': thread['role'], 'source_ref': call['ref']})
            if key == 'validate_kanban' and isinstance(data, dict) and isinstance(data.get('lane_counts'), dict):
                readings.append({'at': call['at'], 'counts': data['lane_counts'], 'ok': data.get('ok'), 'ref': call['ref']})
    return events, readings


def reviewer_finals(threads):
    finals = []
    for thread in threads:
        if thread['role'] != 'reviewer':
            continue
        closing = [(row.get('timestamp'), (row.get('payload') or {}).get('last_agent_message')) for row in thread['rows']
                   if (row.get('payload') or {}).get('type') == 'task_complete' and (row.get('payload') or {}).get('last_agent_message')]
        scope = re.sub(r'^/root/', '', thread['path'])
        if not closing:
            finals.append({'at': thread['end'], 'scope': scope, 'text': None, 'actor': thread['id'], 'agent_type': thread['agent_type'], 'ref': thread['file']})
        finals += [{'at': at, 'scope': scope, 'text': text, 'actor': thread['id'], 'agent_type': thread['agent_type'], 'ref': thread['file']} for at, text in closing]
    return finals


def build(run_dir, workspace):
    run_dir = Path(run_dir)
    run = json.loads((run_dir / 'run.json').read_text(encoding='utf-8-sig'))
    paths = [run_dir / 'session.jsonl', *sorted(Path(p) for p in glob.glob(str(run_dir / 'subagents' / '**' / '*.jsonl'), recursive=True))]
    threads = [load_thread(path) for path in paths]
    gates, readings = gate_events(threads)
    run.setdefault('harness', 'codex')
    return build_document(run, workspace, threads, board_operations(threads), gates, readings, reviewer_finals(threads), 'codex-process-events', ADAPTER_VERSION,
                          load_snapshots(run_dir / 'board-snapshots.jsonl'))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    doc = process_trace.validate(build(args.run_dir, args.workspace))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'coverage': doc['coverage'], 'stages': len(doc['stages']), 'tasks': len(doc['tasks']), 'events': len(doc['events']), 'notes': doc['notes']}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
