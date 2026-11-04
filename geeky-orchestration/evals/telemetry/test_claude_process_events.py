"""Offline tests for the Claude adapter and the board operations it adds. No network."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

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


def test_parse_board_reads_linked_and_bold_tasks():
    board = '## Backlog\n- [ ] [T2 — Server](tasks/T2.md)\n\n## Done\n- [x] **T1** core\n\n## Validation Checklist\n- [ ] T9 is not a task\n'
    assert process_events.parse_board(board) == {'T2': 'Backlog', 'T1': 'Done'}


@pytest.mark.parametrize('command,names', [
    ('python3 $P/scripts/validate-kanban.py --path docs/x', ['validate-kanban']),
    ('cd w && python3 scripts/check-dod.py --task T1 ; echo done', ['check-dod']),
    ('pwsh -File scripts/validate-task-schema.ps1 -Path x', ['validate-task-schema']),
    ('& "C:/p/scripts/validate-kanban.ps1" -Path x', ['validate-kanban']),
    ('"$PY" scripts/validate-kanban.py --path x', ['validate-kanban']),
    ('G=$P/scripts/check-commit.py; python3 $G msg.txt', ['check-commit']),
    ('for s in validate-kanban check-dod; do python3 $P/scripts/$s.py --path x; done', ['check-dod', 'validate-kanban']),
    ("python3 - <<'EOF'\nimport subprocess\nsubprocess.run(['python3', 'scripts/validate-kanban.py'])\nEOF", ['validate-kanban']),
    ("foreach($s in 'validate-kanban','check-dod'){ python \"$p/$s.py\" --path $f }", ['check-dod', 'validate-kanban']),
    ('sed -n 1,50p $P/scripts/validate-task-schema.py', []),
    ('cat $P/scripts/check-dod.py; ls $P/scripts', []),
    ('git commit -m "docs: validate-kanban passes"', []),
    ("cat >> review.md <<'EOF'\nvalidate-kanban OK\nEOF\ngit log -1", []),
])
def test_only_running_a_gate_counts(command, names):
    assert adapter.invoked_gates(command) == names


def test_a_gate_run_from_a_generated_script_is_proved_by_its_output():
    command = "cat > lanes.py <<'EOF'\nsubprocess.run([p + '/validate-kanban.py'])\nEOF\npython3 lanes.py T5"
    output = 'T5 Ready 0 OK: 11 task(s) tracked, 11 task file(s). Backlog=6, Ready=1, In Progress=0, In Review=0, Blocked=0, Done=4\n'
    assert adapter.invoked_gates(command, output) == ['validate-kanban']
    assert adapter.segment_gate('validate-kanban', output) == 'pass'
    assert adapter.invoked_gates("cat > lanes.py <<'EOF'\nvalidate-kanban\nEOF\ngit log", 'print("OK: 11 task(s) tracked")') == []


def test_reading_a_gates_source_gives_no_gate_event(tmp_path):
    source = 'print("INVALID_COMMIT_MESSAGE")\nprint("OK: planning folder valid")\n'
    rows = [use('Bash', {'command': 'sed -n 1,50p scripts/check-commit.py'}), result(source)]
    assert adapter.gate_events([record(tmp_path, rows)]) == ([], [])


def test_lost_notice_falls_back_to_the_agents_own_closing_message(tmp_path):
    root_rows = [use('Agent', {'subagent_type': 'geeky-orchestration:code-reviewer', 'description': 'Review domain', 'run_in_background': True}, 'a1'), result('Async agent launched successfully', 'a1')]
    root = record(tmp_path, root_rows)
    closing = {'type': 'assistant', 'timestamp': '2026-10-22T07:09:00Z', 'message': {'content': [{'type': 'text', 'text': 'Verdict: PASS WITH WARNINGS'}]}}
    child = adapter.transcript(write_rows(tmp_path / 'agent.jsonl', [closing]), 'reviewer', 'a1')
    _, finals = adapter.build_threads([root, child], root)
    assert finals[0]['text'] == 'Verdict: PASS WITH WARNINGS' and finals[0]['at'] == '2026-10-22T07:09:00Z'


@pytest.mark.parametrize('text,verdict', [
    ('Detail.\n\n**Can we move to the next phase? READY TO ADVANCE.**\n<usage>tool_uses: 3</usage>', 'READY TO ADVANCE'),
    ('Detail.\n\n**This is NOT READY.**', 'NOT READY'),
    ('Detail.\n\n**This did not PASS.**', None),
    ('Some **READY TO ADVANCE** was considered.\n\nMore to do.', None),
])
def test_bold_last_line_gives_a_verdict(text, verdict):
    reviews, missing = process_events.review_events([{'at': '2026-10-22T07:00:00Z', 'scope': 's', 'text': text, 'actor': 'a', 'agent_type': 'r', 'ref': 'x'}])
    assert ([event['verdict'] for event in reviews], missing) == (([verdict], 0) if verdict else ([], 1))


def planning_workspace(tmp_path, commits):
    workspace = tmp_path / 'ws'
    workspace.mkdir()
    run = lambda *args, **env: subprocess.run(['git', '-C', str(workspace), '-c', 'user.name=t', '-c', 'user.email=t@local', *args], check=True, capture_output=True, env={**os.environ, **env})
    run('init', '-q')
    for index, (message, names) in enumerate(commits):
        for name in names:
            path = workspace / 'docs' / name
            path.parent.mkdir(exist_ok=True)
            path.write_text('x', encoding='utf-8')
        stamp = f'2026-10-22T07:{index + 10}:00+00:00'
        run('add', '-A')
        run('commit', '-q', '-m', message, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)
    return workspace


ROOT_THREAD = {'id': 'root', 'role': 'orchestrator', 'start': '2026-10-22T07:00:00Z', 'end': '2026-10-22T08:00:00Z', 'root': True}
PLANNING = [('spec', ['feature-specification.md']), ('plan', ['implementation-plan.md']), ('chore: plan review', ['review-plan.md'])]


def test_no_coder_and_no_lane_progress_gives_no_implement_stage(tmp_path):
    rows, problem = process_events.stage_rows(planning_workspace(tmp_path, PLANNING), ROOT_THREAD, [ROOT_THREAD], [{'task_id': 'T1', 'to_lane': 'Blocked', 'at': '2026-10-22T07:13:00Z'}], [])
    assert [row['stage'] for row in rows] == ['spec-research', 'geeky-plan', 'plan-review'] and problem == 'Implementation never started'


def test_a_coder_after_plan_review_gives_an_implement_stage(tmp_path):
    coder = {'id': 'c', 'role': 'coder', 'start': '2026-10-22T07:20:00Z', 'end': '2026-10-22T07:30:00Z', 'root': False}
    rows, problem = process_events.stage_rows(planning_workspace(tmp_path, PLANNING), ROOT_THREAD, [ROOT_THREAD, coder], [], [])
    assert rows[-1]['stage'] == 'geeky-implement' and problem == 'Final review start not established'


def test_one_commit_closing_two_stages_is_reported(tmp_path):
    commits = [('spec', ['feature-specification.md']), ('chore: plan and plan review', ['implementation-plan.md', 'review-plan.md'])]
    rows, problem = process_events.stage_rows(planning_workspace(tmp_path, commits), ROOT_THREAD, [ROOT_THREAD], [], [])
    assert rows[2]['start'] == rows[2]['end'] and problem == 'plan-review has no length: one commit closed two stages'


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
