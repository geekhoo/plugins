"""Offline tests for the Claude adapter and the board operations it adds. No network."""
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import process_events  # noqa: E402

spec = importlib.util.spec_from_file_location('claude_process_events', HERE / 'claude-process-events.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

BOARD = '# Kanban\n\n## Backlog\n- T2-b\n\n## Ready\n- T1-a\n\n## In Progress\n\n## In Review\n\n## Done\n'


def use(name, tool_input, call_id='c1', at='2026-10-22T07:00:00Z'):
    return {'type': 'assistant', 'timestamp': at, 'message': {'content': [{'type': 'tool_use', 'id': call_id, 'name': name, 'input': tool_input}]}}


def result(text, call_id='c1', at='2026-10-22T07:00:01Z', error=False):
    return {'type': 'user', 'timestamp': at, 'message': {'content': [{'type': 'tool_result', 'tool_use_id': call_id, 'content': text, 'is_error': error}]}}


def write_rows(path, rows):
    path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n', encoding='utf-8')
    return path


def record(tmp_path, rows):
    return adapter.transcript(write_rows(tmp_path / 'session.jsonl', rows), 'orchestrator', 'root')


def test_write_and_edit_replay_as_exact_board_states(tmp_path):
    rows = [use('Write', {'file_path': r'C:\w\docs\kanban.md', 'content': BOARD}), result('ok'),
            use('Edit', {'file_path': 'docs/kanban.md', 'old_string': '## Ready\n- T1-a\n\n## In Progress\n', 'new_string': '## Ready\n\n## In Progress\n- T1-a\n'}, 'c2', '2026-10-22T07:01:00Z'), result('ok', 'c2'),
            use('Write', {'file_path': 'docs/other.md', 'content': 'x'}, 'c3'), result('ok', 'c3')]
    ops = adapter.board_operations([record(tmp_path, rows)])
    assert [op['kind'] for op in ops] == ['set', 'edit']
    states, problems = process_events.replay(ops)
    assert problems == [] and process_events.parse_board(states[-1]['text'])['T1'] == 'In Progress'


def test_failed_edit_is_skipped_and_an_unmatched_edit_stops_the_replay(tmp_path):
    rows = [use('Write', {'file_path': 'kanban.md', 'content': BOARD}), result('ok'),
            use('Edit', {'file_path': 'kanban.md', 'old_string': 'nope', 'new_string': 'x'}, 'c2'), result('String not found', 'c2', error=True)]
    ops = adapter.board_operations([record(tmp_path, rows)])
    assert ops[1]['ok'] is False and process_events.replay(ops)[1] == []
    ops[1]['ok'] = True
    assert 'did not apply' in process_events.replay(ops)[1][0]


def test_shell_board_write_is_never_skipped_because_of_exit_code_5(tmp_path):
    command = "$k=Get-Content docs/kanban.md -Raw; $k=$k.Replace('a','b'); Set-Content docs/kanban.md $k"
    ops = adapter.board_operations([record(tmp_path, [use('PowerShell', {'command': command}), result('Exit code 5\n', error=True)])])
    assert ops[0]['kind'] == 'shell' and ops[0]['ok'] is True
    assert 'outside a patch' in process_events.replay(ops)[1][0]


def test_reading_the_board_is_not_a_write(tmp_path):
    ops = adapter.board_operations([record(tmp_path, [use('PowerShell', {'command': 'Get-Content docs/kanban.md'}), result('text')])])
    assert ops == []


def test_multi_gate_shell_output_is_read_from_its_text(tmp_path):
    command = "python check-dod.py --task T1; python check-dod.py --task T2; python validate-kanban.py; python check-commit.py m; python validate-task-schema.py"
    output = ('Exit code 5\nDOD_OK: T1\nDOD_INVALID: T2\nOK: 2 task(s) tracked, 2 task file(s). Backlog=0, Ready=0, In Progress=0, In Review=1, Blocked=0, Done=1\n'
              'OK: commit message valid.\nOK: 2 task file(s) checked, 0 failing.\n')
    events, readings = adapter.gate_events([record(tmp_path, [use('PowerShell', {'command': command}), result(output, error=True)])])
    got = {(event['gate_name'], event.get('task_id')): event['gate_result'] for event in events}
    assert got[('check-dod', 'T1')] == 'pass' and got[('check-dod', 'T2')] == 'fail'
    assert got[('validate-kanban', None)] == 'pass' and got[('check-commit', None)] == 'pass' and got[('validate-task-schema', None)] == 'pass'
    assert readings[0]['counts']['Done'] == 1 and readings[0]['counts']['In Review'] == 1 and readings[0]['ok'] is True


def test_invalid_commit_and_kanban_are_failures(tmp_path):
    output = 'INVALID_COMMIT_MESSAGE:\n  ERROR:   subject exceeds 72 chars (82)\n'
    events, _ = adapter.gate_events([record(tmp_path, [use('PowerShell', {'command': 'python check-commit.py m'}), result(output)])])
    assert events[0]['gate_result'] == 'fail'


def test_exit_code_5_alone_says_nothing_about_a_gate(tmp_path):
    events, _ = adapter.gate_events([record(tmp_path, [use('PowerShell', {'command': 'python check-commit.py m'}), result('Exit code 5\n', error=True)])])
    assert events[0]['gate_result'] == 'unknown'


def test_mentioning_a_gate_with_no_result_records_nothing(tmp_path):
    assert adapter.gate_events([record(tmp_path, [use('PowerShell', {'command': 'python check-commit.py m'})])]) == ([], [])


def test_background_agent_uses_its_notification_for_end_and_verdict(tmp_path):
    notice = ('<task-notification>\n<task-id>a</task-id>\n<tool-use-id>c1</tool-use-id>\n<status>completed</status>\n<result>## Review\nVerdict: READY TO ADVANCE</result>\n</task-notification>')
    rows = [use('Agent', {'description': 'Phase 1 review', 'subagent_type': 'geeky-orchestration:code-reviewer'}), result('Async agent launched successfully.'),
            {'type': 'user', 'timestamp': '2026-10-22T07:05:00Z', 'message': {'content': notice}}]
    rec = record(tmp_path, rows)
    threads, finals = adapter.build_threads([rec], rec)
    reviewer = next(thread for thread in threads if not thread['root'])
    assert reviewer['role'] == 'reviewer' and reviewer['end'] == '2026-10-22T07:05:00Z'
    events, missing = process_events.review_events(finals)
    assert missing == 0 and events[0]['verdict'] == 'READY TO ADVANCE' and events[0]['review_scope'] == 'Phase 1 review'


def test_foreground_agent_uses_its_result(tmp_path):
    rows = [use('Agent', {'description': 'Coder T1', 'subagent_type': 'geeky-coder'}), result('Done\nPASS', at='2026-10-22T07:09:00Z')]
    rec = record(tmp_path, rows)
    threads, finals = adapter.build_threads([rec], rec)
    assert threads[1]['role'] == 'coder' and threads[1]['end'] == '2026-10-22T07:09:00Z' and finals == []


def test_unknown_agent_type_stays_unknown_and_never_counts_as_reviewer():
    assert process_events.role_for('geeky-orchestration:geeky-implement-orchestrator') == 'orchestrator'
    assert process_events.role_for('something-new') == 'unknown'


def test_a_reviewer_with_no_closing_message_is_reported_missing(tmp_path):
    rec = record(tmp_path, [use('Agent', {'description': 'Review', 'subagent_type': 'code-reviewer'}), result('Async agent launched successfully.')])
    assert process_events.review_events(adapter.build_threads([rec], rec)[1]) == ([], 1)


def test_repeated_tool_use_rows_count_once(tmp_path):
    rows = [use('PowerShell', {'command': 'python check-commit.py m'}), use('PowerShell', {'command': 'python check-commit.py m'}), result('OK: commit message valid.')]
    assert len(adapter.gate_events([record(tmp_path, rows)])[0]) == 1
