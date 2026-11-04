"""Claude Code adapter: turn a retained Claude run's records into `geeky-eval.process-events/1`.

Reads `session.jsonl`, `subagents/` where present, the run record and the contestant's git history. Only this
file knows Claude shapes; `process_events.py` decides what can be asserted. It makes no network call and
changes nothing in the run.

    python claude-process-events.py <run-folder> --workspace <git-checkout> --out <events.json>

Subagents appear as `Agent` calls in their parent's transcript, finishing with a tool result or, when run in the
background, a `<task-notification>`. Early runs retained no subagent transcripts, so a subagent's board writes
or gate calls are visible only when its transcript was kept. Gates run as shell scripts with text output.
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
from process_events import build_document, load_snapshots, role_for  # noqa: E402

ADAPTER_VERSION = '1'
BOARD_WRITE = re.compile(r'Set-Content|Add-Content|Out-File|WriteAllText|write_text|sed -i|>\s*\S*kanban|\.Replace\(')
NOTIFICATION = re.compile(r'<task-notification>.*?</task-notification>', re.S)
COUNTS = re.compile(r'Backlog=(\d+), Ready=(\d+), In Progress=(\d+), In Review=(\d+), Blocked=(\d+), Done=(\d+)')
SHELLS = ('PowerShell', 'Bash')
GATE_NAME = re.compile(r'(validate-kanban|validate-planning-folder|validate-task-schema|check-dod|check-commit)')
TASK_ARG = re.compile(r'(?:--task|-Task)\s+["\']?(T\d+)', re.I)
DOD_LINE = re.compile(r'^\s*(DOD_\w+):\s*(T\d+)', re.M)


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(item.get('text', '') for item in content if isinstance(item, dict) and item.get('type') == 'text')
    return ''


def load_rows(path):
    rows = []
    for line in open(path, encoding='utf-8-sig', errors='replace'):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def transcript(path, role, actor):
    """One retained transcript, as tool uses with their results and any task notifications."""
    uses, results, notices = [], {}, {}
    seen = set()
    rows = load_rows(path)
    for index, row in enumerate(rows):
        content = (row.get('message') or {}).get('content')
        if row.get('type') == 'user':
            for found in NOTIFICATION.findall(text_of(content)):
                call_id = re.search(r'<tool-use-id>(.*?)</tool-use-id>', found)
                result = re.search(r'<result>(.*?)</result>', found, re.S)
                if call_id:
                    notices[call_id.group(1)] = {'at': row.get('timestamp'), 'text': result.group(1) if result else None}
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get('type') == 'tool_use' and item.get('id') not in seen:
                seen.add(item.get('id'))
                uses.append({'id': item.get('id'), 'name': item.get('name'), 'input': item.get('input') or {}, 'at': row.get('timestamp'),
                             'ref': f'{os.path.basename(path)}:{index}', 'role': role, 'actor': actor})
            elif item.get('type') == 'tool_result':
                results[item.get('tool_use_id')] = {'at': row.get('timestamp'), 'text': text_of(item.get('content')), 'error': bool(item.get('is_error')), 'detail': row.get('toolUseResult')}
    stamps = [row.get('timestamp') for row in rows if row.get('timestamp')]
    return {'uses': uses, 'results': results, 'notices': notices, 'start': min(stamps, key=process_trace.stamp) if stamps else None,
            'end': max(stamps, key=process_trace.stamp) if stamps else None, 'file': os.path.basename(path)}


def is_board(path):
    return str(path).replace('\\', '/').endswith('kanban.md')


def board_operations(transcripts):
    ops = []
    for record in transcripts:
        for use in record['uses']:
            result = record['results'].get(use['id'])
            ok = None if result is None else not result['error']
            base = {'at': use['at'], 'ok': ok, 'ref': use['ref'], 'actor': use['role']}
            if use['name'] == 'Write' and is_board(use['input'].get('file_path')):
                ops.append({**base, 'kind': 'set', 'text': use['input'].get('content', '')})
            elif use['name'] == 'Edit' and is_board(use['input'].get('file_path')):
                ops.append({**base, 'kind': 'edit', 'old': use['input'].get('old_string', ''), 'new': use['input'].get('new_string', ''), 'all': bool(use['input'].get('replace_all'))})
            elif use['name'] in SHELLS:
                command = use['input'].get('command', '')
                if 'kanban.md' in command and BOARD_WRITE.search(command):
                    # Early MXC runs flag nearly every shell result `Exit code 5`, so the flag cannot mark this write as failed.
                    ops.append({**base, 'kind': 'shell', 'ok': True})
    return ops


def segment_gate(gate, output):
    """Read one gate's result from shell text. Scripts print fixed OK lines; anything else stays unknown."""
    if gate == 'validate-kanban':
        found = re.search(r'^(.*)task\(s\) tracked[^\n]*', output, re.M) or COUNTS.search(output)
        if not found:
            return 'unknown'
        return 'pass' if re.search(r'^\s*OK:[^\n]*task\(s\) tracked', output, re.M) else 'fail'
    if gate == 'validate-task-schema':
        found = re.search(r'(\d+) task file\(s\) checked, (\d+) failing', output)
        return 'unknown' if not found else ('pass' if found.group(2) == '0' else 'fail')
    if gate == 'validate-planning-folder':
        if 'INVALID_PLANNING_FOLDER' in output:
            return 'fail'
        return 'pass' if 'planning folder valid' in output else 'unknown'
    if gate == 'check-commit':
        if 'INVALID_COMMIT_MESSAGE' in output:
            return 'fail'
        return 'pass' if 'commit message valid' in output else 'unknown'
    return None


def gate_events(transcripts):
    """Each gate named in a shell command, with its result where the output says.

    `check-dod` prints one line per task. `exit N` decides only a lone gate, and an `Exit code 5` flag decides nothing.
    """
    events, readings = [], []
    for record in transcripts:
        for use in record['uses']:
            if use['name'] not in SHELLS:
                continue
            command = use['input'].get('command', '')
            names = sorted(set(GATE_NAME.findall(command)))
            result = record['results'].get(use['id'])
            if not names or result is None:
                continue
            output = result['text']
            task = TASK_ARG.search(command)
            for gate in names:
                if gate == 'check-dod':
                    lines = DOD_LINE.findall(output)
                    if lines:
                        events += [{'kind': 'gate', 'at': use['at'], 'gate_name': gate, 'gate_result': 'pass' if name == 'DOD_OK' else 'fail', 'task_id': task_id,
                                    'actor': use['role'], 'source_ref': use['ref']} for name, task_id in lines]
                        continue
                outcome = segment_gate(gate, output)
                if outcome in (None, 'unknown') and len(names) == 1:
                    code = re.search(r'\bexit[ :=]+(\d+)', output, re.I)
                    outcome = ('pass' if code.group(1) == '0' else 'fail') if code else ('fail' if result['error'] and 'Exit code 5' not in output[:40] else 'unknown')
                events.append({'kind': 'gate', 'at': use['at'], 'gate_name': gate, 'gate_result': outcome or 'unknown', 'task_id': task.group(1) if task and gate == 'check-dod' else None,
                               'actor': use['role'], 'source_ref': use['ref']})
            found = COUNTS.search(output)
            if found and 'validate-kanban' in names:
                counts = dict(zip(('Backlog', 'Ready', 'In Progress', 'In Review', 'Blocked', 'Done'), map(int, found.groups())))
                readings.append({'at': use['at'], 'counts': counts, 'ok': bool(re.search(r'^\s*OK:[^\n]*task\(s\) tracked', output, re.M)), 'ref': use['ref']})
    return events, readings


def build_threads(transcripts, root_record):
    """A thread for the root and for each Agent call, wherever in the tree it was made."""
    threads = [{'id': 'root', 'file': root_record['file'], 'role': 'orchestrator', 'agent_type': 'orchestrator', 'path': '', 'start': root_record['start'], 'end': root_record['end'], 'root': True}]
    finals = []
    notices = {}
    for record in transcripts:
        notices.update(record['notices'])
    for record in transcripts:
        for use in record['uses']:
            if use['name'] not in ('Agent', 'Task'):
                continue
            agent_type = use['input'].get('subagent_type') or 'general-purpose'
            role = role_for(agent_type)
            notice = notices.get(use['id'])
            result = record['results'].get(use['id'])
            launched = result is not None and 'launched' in result['text'][:200].lower()
            done_at = notice['at'] if notice else (result['at'] if result and not launched else None)
            text = notice['text'] if notice else (result['text'] if result and not launched else None)
            scope = use['input'].get('description') or agent_type
            threads.append({'id': use['id'], 'file': record['file'], 'role': role, 'agent_type': agent_type, 'path': scope, 'start': use['at'], 'end': done_at or root_record['end'], 'root': False})
            if role == 'reviewer':
                finals.append({'at': done_at or use['at'], 'scope': scope, 'text': text, 'actor': use['id'], 'agent_type': agent_type, 'ref': use['ref']})
    return threads, finals


def meta_roles(run_dir):
    """Subagent transcript file to agent type, from the sidecar each retained transcript has."""
    roles = {}
    for path in glob.glob(str(run_dir / 'subagents' / '**' / '*.meta.json'), recursive=True):
        try:
            meta = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        except ValueError:
            continue
        roles[path[:-len('.meta.json')] + '.jsonl'] = (meta.get('agentType'), meta.get('toolUseId'))
    return roles


def build(run_dir, workspace):
    run_dir = Path(run_dir)
    run = json.loads((run_dir / 'run.json').read_text(encoding='utf-8-sig'))
    root_record = transcript(run_dir / 'session.jsonl', 'orchestrator', 'root')
    transcripts = [root_record]
    roles = meta_roles(run_dir)
    for path in sorted(glob.glob(str(run_dir / 'subagents' / '**' / '*.jsonl'), recursive=True)):
        agent_type, tool_use = roles.get(path, (None, None))
        transcripts.append(transcript(path, role_for(agent_type), tool_use or os.path.basename(path)))
    threads, finals = build_threads(transcripts, root_record)
    gates, readings = gate_events(transcripts)
    run.setdefault('harness', 'claude-code')
    doc = build_document(run, workspace, threads, board_operations(transcripts), gates, readings, finals, 'claude-process-events', ADAPTER_VERSION,
                         load_snapshots(run_dir / 'board-snapshots.jsonl'))
    agent_calls = sum(1 for thread in threads if not thread['root'])
    doc['notes']['subagent_transcripts'] = {'agent_calls': agent_calls, 'transcripts_retained': len(transcripts) - 1}
    return doc


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
