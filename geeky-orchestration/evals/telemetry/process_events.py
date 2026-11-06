"""Harness-neutral logic for building process events. Adapters supply native facts; this decides what can be asserted.

An adapter provides threads, board operations, gate results and reviewer messages in the neutral shapes below.
Everything here works from those and the contestant's git history, so it holds no harness or model knowledge.

    thread      {id, file, role, agent_type, path, start, end, root}
    board op    {at, ok, ref, actor, kind} with kind 'patch' (sections), 'set' (text), 'edit' (old, new, all) or 'shell'
    gate event  {kind: 'gate', at, gate_name, gate_result, task_id, actor, source_ref}
    reading     {at, counts, ok, ref}, lane counts reported by the kanban gate
    final       {at, scope, text, actor, agent_type, ref}, a reviewer's closing message; text None when there is none
"""
import json
import re
import subprocess

import process_trace

LANES = ('Backlog', 'Ready', 'In Progress', 'Blocked', 'In Review', 'Done')
ROLE = {'geeky-coder': 'coder', 'worker': 'coder', 'code-reviewer': 'reviewer', 'code-architect-reviewer': 'reviewer', 'architect-reviewer': 'reviewer',
        'reviewer': 'reviewer', 'plan-reviewer': 'reviewer', 'impl-reviewer': 'reviewer', 'code-explorer': 'planner', 'general-purpose': 'planner',
        'code-architect': 'planner', 'geeky-orchestrator': 'orchestrator', 'geeky-implement-orchestrator': 'orchestrator'}
VERDICT_WORDS = 'READY FOR IMPLEMENTATION|READY TO ADVANCE|NOT READY|PASS WITH WARNINGS|NEEDS FIXES|NEEDS CHANGES|NEEDS ATTENTION|CHANGES REQUIRED|PASS|FAIL'
VERDICT_LINE = re.compile(r'^[\s>*#_`-]*(?:T\d+\s*:\s*)?(?:(?:overall\s+|final\s+|phase\s+)*verdict\s*[:\-]?\s*)?[*_`]*(' + VERDICT_WORDS + r')\b', re.I | re.M)
VERDICT_BOLD = re.compile(r'\*\*\s*(?:overall\s+|final\s+|phase\s+)*verdict\s*[:\-]\s*\*{0,2}\s*(' + VERDICT_WORDS + r')\b'
                          r'|^[\s>*#_`-]*(?:[\w-]+\s+){0,4}verdict\s*[:\-]\s*\*{0,2}\s*(' + VERDICT_WORDS + r')\b', re.I | re.M)
VERDICT_LAST_LINE = re.compile(r'^\s*\*\*.*?(?<![Nn][Oo][Tt] )\b(' + VERDICT_WORDS + r')\b[.!]?\*\*\s*$')
USAGE = re.compile(r'<usage>.*?</usage>', re.S)
TASK = re.compile(r'^\s*[-*]\s*(?:\[[ xX]\]\s*)?[`\[*]*(T\d+)\b')


def role_for(agent_type):
    return ROLE.get(str(agent_type or '').rsplit(':', 1)[-1], 'unknown')


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


def replay(ops):
    """Returns states [{at, text, ref, actor}], plus failures that stop the replay being trustworthy."""
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
        if op['kind'] == 'set':
            text = op['text']
        elif op['kind'] == 'edit':
            current = (text or '').replace('\r\n', '\n')
            old, new = op['old'].replace('\r\n', '\n'), op['new'].replace('\r\n', '\n')
            if text is None or old not in current:
                problems.append(f'{op["ref"]}: edit did not apply to the replayed board')
                return states, problems
            text = current.replace(old, new) if op.get('all') else current.replace(old, new, 1)
        else:
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


def load_snapshots(path):
    """Board states recorded by board-watcher.py, or None when there is no record. A watcher that never stopped proves nothing."""
    try:
        lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    except OSError:
        return None
    states, stopped, boards, name = [], False, set(), getattr(path, 'name', str(path))
    for index, line in enumerate(lines):
        try:
            row = json.loads(line)
        except ValueError:
            return None
        if row.get('record') == 'snapshot':
            boards.add(row['path'])
            states.append({'at': row['at'], 'text': row['text'], 'ref': f'{name}:{index}', 'actor': 'unknown', 'evidence': 'observed'})
        elif row.get('record') == 'stop':
            stopped = True
    # Two boards in one record would interleave into moves that never happened.
    return states if stopped and len(boards) <= 1 else None


def reconcile(states, readings, commits, window=0):
    """Compare the board states with what gates and git independently recorded. Any disagreement is reported.

    A watcher sees a write up to one poll later, and a shell command can write the board and run the gate after
    its call began, so `window` seconds lets a reading match a state that follows it.
    """
    problems = []
    checked = {'gate_readings': 0, 'commits': 0}
    for reading in readings:
        if reading.get('ok') is False:
            continue
        counts = lane_counts(lanes_at(states, reading['at']))
        wanted = {lane: reading['counts'].get(lane, 0) for lane in LANES}
        checked['gate_readings'] += 1
        matched = counts == wanted
        if not matched and window:
            moment = process_trace.stamp(reading['at'])
            matched = any(0 <= (process_trace.stamp(state['at']) - moment).total_seconds() <= window and lane_counts(parse_board(state['text'])) == wanted for state in states)
        if not matched:
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
                event = {'kind': 'lane', 'at': state['at'], 'task_id': task, 'from_lane': previous.get(task, 'none'), 'to_lane': lane,
                         'actor': state['actor'], 'source_ref': state['ref']}
                if state.get('evidence'):
                    event['lane_evidence'] = state['evidence']
                events.append(event)
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
    shared = next((row['stage'] for row in rows if process_trace.stamp(row['start']) == process_trace.stamp(row['end'])), None)
    problem = f'{shared} has no length: one commit closed two stages' if shared else None
    if final_start is None:
        moment = process_trace.stamp(review[1])
        started = any(thread['role'] == 'coder' and thread['start'] and process_trace.stamp(thread['start']) > moment for thread in threads) \
            or any(event['to_lane'] in ('In Progress', 'In Review', 'Done') for event in lane_rows)
        if not started:
            return rows, problem or 'Implementation never started'
        rows.append({'stage': 'geeky-implement', 'start': review[1], 'end': root['end'], 'evidence': 'commit-then-run-end', 'source': review[0][:7]})
        return rows, problem or 'Final review start not established'
    rows.append({'stage': 'geeky-implement', 'start': review[1], 'end': final_start, 'evidence': 'lane-and-thread', 'source': 'all tasks Done'})
    rows.append({'stage': 'impl-review', 'start': final_start, 'end': root['end'], 'evidence': 'lane-and-thread', 'source': 'first reviewer after Done'})
    return rows, problem


def review_events(finals):
    """One verdict per reviewer closing message, from an anchored verdict line or a bold last line ending in a verdict."""
    events, missing = [], 0
    for final in finals:
        if not final.get('text'):
            missing += 1
            continue
        found = VERDICT_LINE.findall(final['text']) or [first or second for first, second in VERDICT_BOLD.findall(final['text'])]
        if not found:
            lines = [line for line in USAGE.sub('', final['text']).splitlines() if line.strip()]
            closing = VERDICT_LAST_LINE.match(lines[-1]) if lines else None
            found = [closing.group(1)] if closing else []
        if not found:
            missing += 1
            continue
        events.append({'kind': 'review', 'at': final['at'], 'review_scope': final['scope'][:120], 'verdict': found[-1].upper(),
                       'actor': final['actor'], 'agent_type': final['agent_type'], 'source_ref': final['ref']})
    return events, missing


def build_document(run, workspace, threads, ops, gates, readings, finals, adapter, adapter_version, snapshots=None):
    """Assemble a process-events document, asserting only what reconciles.

    Snapshots from an outside observer come first, because they do not depend on how a model wrote the file.
    If they do not reconcile, the record falls back to replaying writes, then to what commits show.
    """
    root = next(thread for thread in threads if thread['root'])
    telemetry = run.get('telemetry') or {}
    notes = {}
    ops = sorted(ops, key=lambda op: process_trace.stamp(op['at']))
    commits = board_commits(workspace)
    notes['board_writes'] = {'replayable': sum(op['kind'] != 'shell' for op in ops), 'failed_skipped': sum(op['ok'] is False for op in ops), 'shell_writes': sum(op['kind'] == 'shell' for op in ops)}
    states, watcher_trusted = [], False
    if snapshots:
        states = snapshots
        watcher_problems, checked = reconcile(states, readings, commits, window=120)
        watcher_trusted = not watcher_problems and checked['commits'] > 0
        notes['board_snapshots'] = {'states': len(states), **checked, 'problems': watcher_problems[:20], 'problem_count': len(watcher_problems)}
    if watcher_trusted:
        replay_problems, reconcile_problems = [], []
    else:
        states, replay_problems = replay(ops)
        reconcile_problems, checked = reconcile(states, readings, commits)
    notes['board_source'] = 'watcher' if watcher_trusted else 'replay'
    notes['reconciliation'] = {**checked, 'problems': (replay_problems + reconcile_problems)[:20], 'problem_count': len(replay_problems) + len(reconcile_problems)}
    trusted = not replay_problems and not reconcile_problems and bool(states) and checked['commits'] > 0
    lanes = lane_events(states) if trusted else commit_bound_lane_events(commits)
    if not trusted:
        notes['board_source'] = 'commits'
    stages, stage_problem = stage_rows(workspace, root, threads, lanes, readings)
    if stage_problem:
        notes['stage_problem'] = stage_problem
    tasks = task_spans(lanes, threads, states, root['end']) if trusted else []
    reviews, reviews_missing = review_events(finals)
    notes['reviewer_turns_without_verdict'] = reviews_missing
    coverage = {'stage': 'unknown' if not stages else ('partial' if stage_problem else 'complete'),
                'lane': 'complete' if trusted else ('partial' if lanes else 'unknown'),
                'review': 'unknown' if not reviews else ('partial' if reviews_missing else 'complete'),
                'gate': 'complete' if gates and all(gate['gate_result'] != 'unknown' for gate in gates) else ('partial' if gates else 'unknown')}
    # New runs already tag configured values; the run record's own values replace them.
    tags = [tag for tag in telemetry.get('tags', []) if tag != 'mock' and not tag.startswith(('model:', 'provider:'))]
    tags += [f'model:{run.get("model")}', f'provider:{(run.get("provider") or {}).get("name") or "native"}']
    events = sorted(lanes + reviews + gates, key=lambda event: process_trace.stamp(event['at']))
    return {'schema': process_trace.SCHEMA, 'session_id': telemetry.get('session_id') or run.get('session_id'), 'harness': run.get('harness') or 'unknown', 'adapter': adapter,
            'adapter_version': adapter_version, 'environment': telemetry.get('environment') or 'default', 'run_start': root['start'], 'run_end': root['end'],
            'tags': tags, 'metadata': {'case': run.get('case'), 'run_group_id': (telemetry.get('metadata') or {}).get('run_group_id'), 'configured_model': run.get('model'),
                                       'provider': (run.get('provider') or {}).get('name'), 'plugin_sha': run.get('plugin_sha')},
            'coverage': coverage, 'stages': stages, 'tasks': tasks, 'events': events, 'notes': notes}
