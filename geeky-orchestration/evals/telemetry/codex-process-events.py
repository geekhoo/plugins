"""Codex adapter: turn a retained Codex run's records into `geeky-eval.process-events/1`.

Reads rollouts (`session.jsonl`, `subagents/`), the run record and the contestant's git history. Only this
file knows Codex shapes. It makes no network call and changes nothing in the run.

    python codex-process-events.py <run-folder> --workspace <git-checkout> --out <events.json>

Facts it cannot reconcile are not asserted: lane moves are emitted only when the replayed board agrees
with every gate reading and commit, otherwise coverage says `partial` and the reason is recorded.
"""
import argparse
import glob
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import process_trace  # noqa: E402

ADAPTER_VERSION = '1'
LANES = ('Backlog', 'Ready', 'In Progress', 'Blocked', 'In Review', 'Done')
ROLE = {'geeky-coder': 'coder', 'worker': 'coder', 'code-reviewer': 'reviewer', 'code-architect-reviewer': 'reviewer', 'architect-reviewer': 'reviewer',
        'reviewer': 'reviewer', 'plan-reviewer': 'reviewer', 'impl-reviewer': 'reviewer', 'code-explorer': 'planner', 'general-purpose': 'planner',
        'code-architect': 'planner', 'geeky-orchestrator': 'orchestrator', 'geeky-implement-orchestrator': 'orchestrator'}
SHELL_TOOLS = ('exec_command', 'shell', 'shell_command', 'exec', 'apply_patch')
GATE_TOOLS = {'validate_kanban': 'validate-kanban', 'validate_planning_folder': 'validate-planning-folder', 'validate_task_schema': 'validate-task-schema',
              'check_dod': 'check-dod', 'check_commit': 'check-commit', 'check_frozen_artifact': 'check-frozen-artifact'}
PATCH = re.compile(r'\*\*\* Begin Patch(.*?)\*\*\* End Patch', re.S)
FILE_HEADER = re.compile(r'^\*\*\* (Add|Update|Delete) File: (.+?)\s*$', re.M)
SHELL_WRITE = re.compile(r"Set-Content|Add-Content|Out-File|WriteAllText|write_text|\.Replace\(['\"]##")
VERDICT_WORDS = 'READY FOR IMPLEMENTATION|READY TO ADVANCE|NOT READY|PASS WITH WARNINGS|NEEDS FIXES|NEEDS CHANGES|NEEDS ATTENTION|CHANGES REQUIRED|PASS|FAIL'
VERDICT_LINE = re.compile(r'^[\s>*#_`-]*(?:T\d+\s*:\s*)?(?:(?:overall\s+|final\s+|phase\s+)*verdict\s*[:\-]?\s*)?[*_`]*(' + VERDICT_WORDS + r')\b', re.I | re.M)
VERDICT_BOLD = re.compile(r'\*\*\s*(?:overall\s+|final\s+|phase\s+)*verdict\s*[:\-]\s*\*{0,2}\s*(' + VERDICT_WORDS + r')\b'
                          r'|^[\s>*#_`-]*(?:[\w-]+\s+){0,4}verdict\s*[:\-]\s*\*{0,2}\s*(' + VERDICT_WORDS + r')\b', re.I | re.M)
TASK = re.compile(r'^\s*[-*]\s*(?:\[[ xX]\]\s*)?`?(T\d+)\b')
EXIT = re.compile(r'(?:exit(?:ed with)? code|exit_code"?)\s*[:=]?\s*(-?\d+)', re.I)


def board_text(text):
    return re.sub(r'\s+', ' ', text.replace('\r\n', '\n')).strip()


def parse_board(text):
    """Map task id to lane. Headings outside the lane list end the current lane."""
    lanes, current = {}, None
    for line in text.replace('\r\n', '\n').split('\n'):
        heading = re.match(r'^#{1,6}\s*(.+?)\s*$', line)
        if heading:
            title = heading.group(1).strip()
            current = next((lane for lane in LANES if title.lower() == lane.lower()), None)
            continue
        found = TASK.match(line)
        if found and current:
            lanes[found.group(1)] = current
    return lanes


def lane_counts(lanes):
    counts = {lane: 0 for lane in LANES}
    for lane in lanes.values():
        counts[lane] += 1
    return counts


def file_sections(patch):
    """Yield (action, path, body) for each file in one patch."""
    marks = list(FILE_HEADER.finditer(patch))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(patch)
        yield mark.group(1), mark.group(2).replace('\\', '/'), patch[mark.end():end]


def apply_update(text, body):
    """Apply one `*** Update File` body in order. Returns None when a hunk does not match."""
    lines = text.replace('\r\n', '\n').split('\n')
    position = 0
    hunks = re.split(r'^@@.*$', body.replace('\r\n', '\n'), flags=re.M)
    for hunk in hunks:
        rows = [row for row in hunk.split('\n')]
        while rows and rows[-1] == '':
            rows.pop()
        rows = [row for row in rows if not row.startswith('*** ')]
        if not rows:
            continue
        old = [row[1:] for row in rows if row[:1] in (' ', '-') or row == '']
        new = [row[1:] for row in rows if row[:1] in (' ', '+') or row == '']
        if not all(row[:1] in (' ', '-', '+') or row == '' for row in rows):
            return None
        at = None
        for start in range(position, len(lines) - len(old) + 1):
            if [line.rstrip() for line in lines[start:start + len(old)]] == [line.rstrip() for line in old]:
                at = start
                break
        if at is None:
            return None
        lines[at:at + len(old)] = new
        position = at + len(new)
    return '\n'.join(lines)


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
            'role': 'orchestrator' if root else ROLE.get(agent_type, 'unknown'), 'agent_type': agent_type or ('orchestrator' if root else 'unknown'),
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
    """Every attempted board write, in time order, patches separated from opaque shell writes."""
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
    ops.sort(key=lambda op: process_trace.stamp(op['at']))
    return ops


def replay(ops):
    """Returns states [(at, text, ref, actor)], plus failures that stop the replay being trustworthy."""
    states, problems, text = [], [], None
    for op in ops:
        if op['ok'] is False:
            continue
        if op['ok'] is None:
            problems.append(f'{op["ref"]}: board write with no exit status')
            continue
        if op['kind'] == 'shell':
            problems.append(f'{op["ref"]}: board written outside a patch')
            continue
        for action, _, body in op['sections']:
            if action == 'Add':
                text = '\n'.join(row[1:] for row in body.replace('\r\n', '\n').split('\n') if row.startswith('+'))
            elif action == 'Update':
                updated = apply_update(text, body) if text is not None else None
                if updated is None:
                    problems.append(f'{op["ref"]}: patch did not apply to the replayed board')
                    return states, problems
                text = updated
            else:
                text = ''
        states.append({'at': op['at'], 'text': text, 'ref': op['ref'], 'actor': op['actor']})
    return states, problems


def lanes_at(states, when):
    moment = process_trace.stamp(when)
    current = {}
    for state in states:
        if process_trace.stamp(state['at']) > moment:
            break
        current = parse_board(state['text'])
    return current


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


def reconcile(states, readings, commits):
    """Compare the replay with what gates and git independently recorded. Any disagreement is reported."""
    problems = []
    checked = {'gate_readings': 0, 'commits': 0}
    for reading in readings:
        if reading.get('ok') is False:
            continue
        lanes = lanes_at(states, reading['at'])
        counts = lane_counts(lanes)
        wanted = {lane: reading['counts'].get(lane, 0) for lane in LANES}
        checked['gate_readings'] += 1
        if counts != wanted:
            problems.append(f'{reading["ref"]}: gate read {wanted}, replay has {counts}')
    seen = {board_text(state['text']) for state in states}
    for commit in commits:
        checked['commits'] += 1
        if board_text(commit['text']) not in seen:
            problems.append(f'{commit["sha"]}: committed board never appears in the replay')
    return problems, checked


def git(workspace, *args):
    return subprocess.run(['git', '-C', str(workspace), *args], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout


def utc(value):
    return process_trace.stamp(value).strftime('%Y-%m-%dT%H:%M:%SZ')


def first_commit_adding(workspace, pattern):
    log = git(workspace, 'log', '--reverse', '--diff-filter=A', '--format=%H %aI', '--', pattern).splitlines()
    if not log:
        return None
    sha, when = log[0].split(' ', 1)
    return [sha, utc(when)]


def board_commits(workspace):
    commits = []
    for line in git(workspace, 'log', '--reverse', '--format=%H', '--', '*kanban.md').splitlines():
        names = [name for name in git(workspace, 'show', '--name-only', '--format=', line).splitlines() if name.endswith('kanban.md')]
        if names:
            commits.append({'sha': line[:7], 'text': git(workspace, 'show', f'{line}:{names[0]}'),
                            'at': utc(git(workspace, 'show', '-s', '--format=%aI', line).strip())})
    return commits


def lane_events(states):
    events, previous = [], {}
    for state in states:
        lanes = parse_board(state['text'])
        for task, lane in sorted(lanes.items()):
            if previous.get(task) != lane:
                events.append({'kind': 'lane', 'at': state['at'], 'task_id': task, 'from_lane': previous.get(task, 'none'), 'to_lane': lane,
                               'actor': state['actor'], 'source_ref': state['ref']})
        previous = lanes
    return events


def commit_bound_lane_events(commits):
    """Lane changes as seen at each commit. The move happened at or before that time, and the evidence says so."""
    events, previous = [], {}
    for commit in commits:
        lanes = parse_board(commit['text'])
        for task, lane in sorted(lanes.items()):
            if previous.get(task) != lane:
                events.append({'kind': 'lane', 'at': commit['at'], 'task_id': task, 'from_lane': previous.get(task, 'none'), 'to_lane': lane,
                               'actor': 'unknown', 'source_ref': commit['sha'], 'lane_evidence': 'commit-bound'})
        if lanes:
            previous = lanes
    return events


def all_done_time(lane_rows, readings):
    """When every task first stood in Done, from lane events or from a passing gate reading, whichever is earlier."""
    final = {}
    for event in lane_rows:
        final[event['task_id']] = (event['to_lane'], event['at'])
    times = [process_trace.stamp(reading['at']) for reading in readings if reading.get('ok') is not False and reading['counts'].get('Done', 0) > 0
             and not any(reading['counts'].get(lane, 0) for lane in LANES if lane != 'Done')]
    if final and all(lane == 'Done' for lane, _ in final.values()):
        times.append(max(process_trace.stamp(at) for _, at in final.values()))
    return min(times) if times else None


def task_spans(lane_rows, threads, states, run_end):
    tasks = {}
    for event in lane_rows:
        item = tasks.setdefault(event['task_id'], {'task_id': event['task_id'], 'start': None, 'end': None, 'final_lane': None})
        item['final_lane'] = event['to_lane']
        if event['to_lane'] == 'In Progress' and item['start'] is None:
            item['start'] = event['at']
        if event['to_lane'] == 'Done':
            item['end'] = event['at']
    rows = []
    for item in tasks.values():
        if item['start'] is None:
            continue
        item['end'] = item['end'] or run_end
        rows.append(item)
    for thread in threads:
        if thread['role'] != 'coder' or not thread['start']:
            continue
        active = [task for task, lane in lanes_at(states, thread['start']).items() if lane == 'In Progress']
        token = {match.upper() for match in re.findall(r'(?:^|[_/-])(t\d+)(?=$|[_/-])', thread['path'], re.I)}
        owner = active[0] if len(active) == 1 else None
        if token and owner and owner not in token:
            owner = None
        elif token and not owner and len(token) == 1:
            owner = next(iter(token))
        for item in rows:
            if item['task_id'] == owner and not item.get('owner_actor'):
                item['owner_actor'] = thread['id']
    return sorted(rows, key=lambda item: process_trace.stamp(item['start']))


def stage_rows(workspace, root, threads, lane_rows, readings):
    """Stage ends are the first commits adding each artifact; final review starts with the first reviewer after all tasks are Done."""
    spec = first_commit_adding(workspace, '*feature-specification.md')
    plan = first_commit_adding(workspace, '*implementation-plan.md')
    log = git(workspace, 'log', '--reverse', '--format=%H %aI %s').splitlines()
    review = next(([line.split(' ', 2)[0], utc(line.split(' ', 2)[1])] for line in log if re.search(r'plan review', line.split(' ', 2)[2], re.I)), None)
    review = review or first_commit_adding(workspace, '*review-plan.md')
    if not (spec and plan and review):
        return [], 'Missing a planning commit'
    all_done = all_done_time(lane_rows, readings)
    final_start = None
    if all_done is not None:
        final_start = min((thread['start'] for thread in threads if thread['role'] == 'reviewer' and process_trace.stamp(thread['start']) > all_done),
                          key=process_trace.stamp, default=None)
    edges = [(root['start'], None), (spec[1], spec[0]), (plan[1], plan[0]), (review[1], review[0])]
    rows = [{'stage': name, 'start': edges[index][0], 'end': edges[index + 1][0], 'evidence': 'commit', 'source': edges[index + 1][1][:7]}
            for index, name in enumerate(('spec-research', 'geeky-plan', 'plan-review'))]
    if final_start is None:
        rows.append({'stage': 'geeky-implement', 'start': review[1], 'end': root['end'], 'evidence': 'commit-then-run-end', 'source': review[0][:7]})
        return rows, 'Final review start not established'
    rows.append({'stage': 'geeky-implement', 'start': review[1], 'end': final_start, 'evidence': 'lane-and-thread', 'source': 'all tasks Done'})
    rows.append({'stage': 'impl-review', 'start': final_start, 'end': root['end'], 'evidence': 'lane-and-thread', 'source': 'first reviewer after Done'})
    return rows, None


def review_events(threads, stages):
    """One verdict per completed reviewer turn, from an anchored verdict line in that turn's final message."""
    events, missing = [], 0
    for thread in threads:
        if thread['role'] != 'reviewer':
            continue
        finals = []
        for row in thread['rows']:
            payload = row.get('payload') or {}
            if payload.get('type') == 'task_complete' and payload.get('last_agent_message'):
                finals.append((row.get('timestamp'), payload['last_agent_message']))
        if not finals:
            missing += 1
            continue
        for at, text in finals:
            found = VERDICT_LINE.findall(text) or [first or second for first, second in VERDICT_BOLD.findall(text)]
            if not found:
                missing += 1
                continue
            events.append({'kind': 'review', 'at': at, 'review_scope': re.sub(r'^/root/', '', thread['path'])[:120], 'verdict': found[-1].upper(),
                           'actor': thread['id'], 'agent_type': thread['agent_type'], 'source_ref': thread['file']})
    return events, missing


def build(run_dir, workspace):
    run_dir = Path(run_dir)
    run = json.loads((run_dir / 'run.json').read_text(encoding='utf-8-sig'))
    paths = [run_dir / 'session.jsonl', *sorted(Path(p) for p in glob.glob(str(run_dir / 'subagents' / '**' / '*.jsonl'), recursive=True))]
    threads = [load_thread(path) for path in paths]
    root = next(thread for thread in threads if thread['root'])
    telemetry = run.get('telemetry') or {}
    problems, notes = [], {}

    ops = board_operations(threads)
    states, replay_problems = replay(ops)
    gates, readings = gate_events(threads)
    commits = board_commits(workspace)
    reconcile_problems, checked = reconcile(states, readings, commits)
    notes['board_writes'] = {'patches': sum(op['kind'] == 'patch' for op in ops), 'failed_patches_skipped': sum(op['ok'] is False for op in ops), 'shell_writes': sum(op['kind'] == 'shell' for op in ops)}
    notes['reconciliation'] = {**checked, 'problems': (replay_problems + reconcile_problems)[:20], 'problem_count': len(replay_problems) + len(reconcile_problems)}
    trusted = not replay_problems and not reconcile_problems and bool(states) and checked['commits'] > 0
    lanes = lane_events(states) if trusted else commit_bound_lane_events(commits)
    stages, stage_problem = stage_rows(workspace, root, threads, lanes, readings)
    if stage_problem:
        notes['stage_problem'] = stage_problem
    tasks = task_spans(lanes, threads, states, root['end']) if trusted else []
    reviews, reviews_missing = review_events(threads, stages)
    notes['reviewer_turns_without_verdict'] = reviews_missing
    coverage = {'stage': 'unknown' if not stages else ('partial' if stage_problem else 'complete'),
                'lane': 'complete' if trusted else ('partial' if lanes else 'unknown'),
                'review': 'unknown' if not reviews else ('partial' if reviews_missing else 'complete'),
                'gate': 'complete' if gates and all(gate['gate_result'] != 'unknown' for gate in gates) else ('partial' if gates else 'unknown')}
    tags = [tag for tag in telemetry.get('tags', []) if tag != 'mock']
    tags += [f'model:{run.get("model")}', f'provider:{(run.get("provider") or {}).get("name") or "native"}']
    events = sorted(lanes + reviews + gates, key=lambda event: process_trace.stamp(event['at']))
    return {'schema': process_trace.SCHEMA, 'session_id': telemetry.get('session_id') or run.get('session_id'), 'harness': run.get('harness') or 'codex', 'adapter': 'codex-process-events',
            'adapter_version': ADAPTER_VERSION, 'environment': telemetry.get('environment') or 'default', 'run_start': root['start'], 'run_end': root['end'],
            'tags': tags, 'metadata': {'case': run.get('case'), 'run_group_id': (telemetry.get('metadata') or {}).get('run_group_id'), 'configured_model': run.get('model'),
                                       'provider': (run.get('provider') or {}).get('name'), 'plugin_sha': run.get('plugin_sha')},
            'coverage': coverage, 'stages': stages, 'tasks': tasks, 'events': events, 'notes': notes}


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
