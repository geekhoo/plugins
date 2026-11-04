"""Tests for the host-side board watcher, including that it cannot interfere with a contestant's writes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import process_events  # noqa: E402

WATCHER = HERE / 'board-watcher.py'
BOARD = '# Kanban\n\n## Backlog\n- T2-b\n\n## Ready\n- T1-a\n\n## In Progress\n\n## In Review\n\n## Done\n'


def start(tmp_path, interval='0.02', extra=()):
    out, stop = tmp_path / 'board-snapshots.jsonl', tmp_path / 'stop'
    process = subprocess.Popen([sys.executable, '-B', str(WATCHER), '--workspace', str(tmp_path / 'ws'), '--out', str(out), '--stop-file', str(stop), '--interval', interval, *extra])
    return process, out, stop


def board_path(tmp_path):
    path = tmp_path / 'ws' / 'docs' / 'spec-001-feature' / 'kanban.md'
    path.parent.mkdir(parents=True)
    return path


def wait_for(out, count, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if out.exists() and sum('"snapshot"' in line for line in out.read_text(encoding='utf-8').splitlines()) >= count:
            return
        time.sleep(0.02)
    raise AssertionError('watcher did not record the expected snapshots')


def finish(process, stop):
    stop.write_text('x')
    assert process.wait(timeout=10) == 0


def rows(out):
    return [json.loads(line) for line in out.read_text(encoding='utf-8').splitlines()]


def test_records_each_distinct_state_with_start_and_stop(tmp_path):
    path = board_path(tmp_path)
    process, out, stop = start(tmp_path)
    path.write_text(BOARD, encoding='utf-8')
    wait_for(out, 1)
    path.write_text(BOARD, encoding='utf-8')  # New mtime, same content: not a new state.
    time.sleep(0.2)
    path.write_text(BOARD.replace('## Ready\n- T1-a', '## Ready').replace('## In Progress\n', '## In Progress\n- T1-a\n'), encoding='utf-8')
    wait_for(out, 2)
    finish(process, stop)
    records = rows(out)
    assert [row['record'] for row in records] == ['start', 'snapshot', 'snapshot', 'stop'] and records[-1]['reason'] == 'stop-file'
    assert records[1]['path'] == 'docs/spec-001-feature/kanban.md'
    assert process_events.parse_board(records[2]['text'])['T1'] == 'In Progress'


def test_writers_never_fail_and_no_torn_board_is_recorded(tmp_path):
    path = board_path(tmp_path)
    process, out, stop = start(tmp_path, interval='0')
    errors = []
    versions = [BOARD + f'\n<!-- v{index} -->\n' + 'x' * 20000 + '\nEND\n' for index in range(300)]

    def direct():
        for text in versions[:150]:
            try:
                with open(path, 'w', encoding='utf-8', newline='\n') as stream:
                    stream.write(text)
            except OSError as error:
                errors.append(repr(error))

    def replacing():
        for index, text in enumerate(versions[150:]):
            temporary = path.with_suffix(f'.tmp{index}')
            try:
                temporary.write_text(text, encoding='utf-8', newline='\n')
                os.replace(temporary, path)
            except OSError as error:
                errors.append(repr(error))

    direct()
    replacing()
    final = 'FINAL\n' + BOARD
    path.write_text(final, encoding='utf-8', newline='\n')
    time.sleep(0.3)
    finish(process, stop)
    assert errors == []
    records = rows(out)
    snapshots = [row for row in records if row['record'] == 'snapshot']
    assert snapshots[-1]['text'] == final
    assert all(row['text'] == final or row['text'].endswith('\nEND\n') for row in snapshots)


def test_watcher_stops_when_its_parent_exits(tmp_path):
    board_path(tmp_path)
    parent = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(0.5)'])
    process, out, _ = start(tmp_path, extra=('--parent-pid', str(parent.pid)))
    parent.wait(timeout=10)
    assert process.wait(timeout=10) == 0
    assert rows(out)[-1]['reason'] == 'parent-exited'


def test_a_missing_workspace_is_not_an_error(tmp_path):
    process, out, stop = start(tmp_path)
    time.sleep(0.1)
    finish(process, stop)
    assert [row['record'] for row in rows(out)] == ['start', 'stop']


def test_load_snapshots_requires_a_clean_stop(tmp_path):
    path = tmp_path / 'board-snapshots.jsonl'
    assert process_events.load_snapshots(path) is None
    snapshot = {'record': 'snapshot', 'at': '2026-11-04T04:00:00.000Z', 'path': 'docs/x/kanban.md', 'sha256': 'a', 'text': BOARD}
    path.write_text(json.dumps({'record': 'start'}) + '\n' + json.dumps(snapshot) + '\n', encoding='utf-8')
    assert process_events.load_snapshots(path) is None
    with open(path, 'a', encoding='utf-8') as stream:
        stream.write(json.dumps({'record': 'stop'}) + '\n')
    states = process_events.load_snapshots(path)
    assert len(states) == 1 and states[0]['ref'] == 'board-snapshots.jsonl:1' and states[0]['actor'] == 'unknown'


def test_load_snapshots_refuses_two_boards(tmp_path):
    path = tmp_path / 'board-snapshots.jsonl'
    rows = [{'record': 'snapshot', 'at': '2026-11-04T04:00:00.000Z', 'path': f'docs/{name}/kanban.md', 'sha256': 'a', 'text': BOARD} for name in 'ab'] + [{'record': 'stop'}]
    path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n', encoding='utf-8')
    assert process_events.load_snapshots(path) is None


def workspace_with_board(tmp_path, text):
    workspace = tmp_path / 'contestant'
    board = workspace / 'docs' / 'spec-001' / 'kanban.md'
    board.parent.mkdir(parents=True)
    board.write_text(text, encoding='utf-8', newline='\n')
    for command in (['init', '-q'], ['add', '-A'], ['-c', 'user.name=t', '-c', 'user.email=t@local', 'commit', '-q', '-m', 'board']):
        subprocess.run(['git', '-C', str(workspace), *command], check=True, capture_output=True)
    return workspace


def document(workspace, snapshots):
    root = {'id': 'root', 'file': 's', 'role': 'orchestrator', 'agent_type': 'orchestrator', 'path': '', 'start': '2026-11-04T04:00:00Z', 'end': '2026-11-04T05:00:00Z', 'root': True}
    return process_events.build_document({}, workspace, [root], [], [], [], [], 'test', '1', snapshots)


MOVED = BOARD.replace('## Ready\n- T1-a', '## Ready').replace('## Done\n', '## Done\n- T1-a\n')


def test_reconciled_snapshots_give_observed_lane_moves(tmp_path):
    states = [dict(state('2026-11-04T04:10:00Z'), evidence='observed'), dict(state('2026-11-04T04:20:00Z', MOVED), evidence='observed')]
    doc = document(workspace_with_board(tmp_path, MOVED), states)
    assert doc['notes']['board_source'] == 'watcher' and doc['coverage']['lane'] == 'complete'
    moved = [event for event in doc['events'] if event['kind'] == 'lane' and event['to_lane'] == 'Done']
    assert [(event['task_id'], event['at'], event['lane_evidence']) for event in moved] == [('T1', '2026-11-04T04:20:00Z', 'observed')]


def test_snapshots_that_miss_a_committed_board_fall_back_to_commits(tmp_path):
    doc = document(workspace_with_board(tmp_path, MOVED), [dict(state('2026-11-04T04:10:00Z'), evidence='observed')])
    assert doc['notes']['board_source'] == 'commits' and doc['coverage']['lane'] == 'partial'
    assert doc['notes']['board_snapshots']['problem_count'] == 1
    assert {event['lane_evidence'] for event in doc['events'] if event['kind'] == 'lane'} == {'commit-bound'}


def state(at, text=BOARD):
    return {'at': at, 'text': text, 'ref': 'r', 'actor': 'unknown'}


def test_reconcile_window_allows_a_write_just_after_the_gate_call_began():
    reading = {'at': '2026-11-04T04:00:00Z', 'ok': True, 'ref': 'g', 'counts': {'Backlog': 1, 'Ready': 1}}
    late = [state('2026-11-04T04:00:05Z')]
    assert process_events.reconcile(late, [reading], [])[0]
    assert process_events.reconcile(late, [reading], [], window=120)[0] == []
    assert process_events.reconcile([state('2026-11-04T04:05:00Z')], [reading], [], window=120)[0]
