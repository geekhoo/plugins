"""Focused local subprocess checks; no MXC, network, providers or oracle code."""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

MOCKS = Path(__file__).resolve().parent
PLUGIN = MOCKS.parents[1]
RUNNERS = PLUGIN / 'evals/scripts'
SCORE_SPEC = importlib.util.spec_from_file_location('score_run', RUNNERS / 'score-run.py')
score = importlib.util.module_from_spec(SCORE_SPEC)
SCORE_SPEC.loader.exec_module(score)


def run(argv, cwd, env):
    return subprocess.run([str(v) for v in argv], cwd=cwd, env=env,
                          capture_output=True, encoding='utf-8', timeout=120)


def capture_run_trace(tmp_path, workspace, config, actor, stdout):
    run_dir = tmp_path / f'{actor}-run'
    run_dir.mkdir()
    harness = 'codex' if actor == 'codex' else 'claude-code'
    (run_dir / 'run.json').write_text(json.dumps({
        'workspace': str(workspace), 'case': 'c0-wordstat', 'harness': harness}), encoding='utf-8')
    (run_dir / 'stream.jsonl').write_text(stdout, encoding='utf-8')
    if actor == 'claude':
        event = next(json.loads(line) for line in stdout.splitlines()
                     if json.loads(line).get('subtype') == 'mock_summary')
        session = Path(event['session_file'])
    else:
        session = next((config / 'codex/sessions').rglob('*.jsonl'))
    shutil.copyfile(session, run_dir / 'session.jsonl')
    return run_dir


def board_tasks(body, lane):
    match = re.search(rf'(?ms)^## {re.escape(lane)}\s*\n(.*?)(?=^## |\Z)', body)
    return set(re.findall(r'\bT\d+\b', match.group(1))) if match else set()


def h1_transition_calls(run_dir, actor, workspace):
    trace = score.Trace(run_dir, harness='codex' if actor == 'codex' else 'claude-code')
    boards = [c for c in trace.calls if c.name in ('Write', 'Edit') and not c.is_error
              and str(c.inp.get('file_path', '')).replace('\\', '/').endswith('/kanban.md')]

    def transition(lane):
        hits = [c for c in boards if c.ts and board_tasks(
            c.inp.get('content', '') or c.inp.get('new_string', ''), lane) == {'T1', 'T2'}]
        assert hits, f'missing captured {lane} board transition'
        call = max(hits, key=lambda c: c.ts)
        assert 'successfully' in call.text.lower()
        assert str(workspace).replace('\\', '/') in str(call.inp.get('file_path', '')).replace('\\', '/')
        return call

    return trace, transition('In Progress'), transition('Done')


def derived_scorer(run_dir, actor, workspace):
    scorer = score.Scorer(run_dir, workspace=workspace,
                          harness='codex' if actor == 'codex' else 'claude-code')
    scorer.load()
    scorer.derive()
    return scorer


def validation_commands(task_file, task, actor):
    owner = SimpleNamespace(task_files={task: task_file},
                            run={'harness': 'codex' if actor == 'codex' else 'claude-code'})
    return score.Scorer.validation_commands(owner, task)


def run_at_commit(workspace, sha, commands, env, tmp_path, label):
    tree = tmp_path / f'h1-{label}'
    command_env = {**env, 'PYTHONPYCACHEPREFIX': str(tmp_path / f'pycache-{label}')}
    added = run(['git', '-C', workspace, 'worktree', 'add', '--detach', tree, sha], workspace, env)
    assert added.returncode == 0, added.stdout + added.stderr
    try:
        results = []
        for command in commands:
            result = subprocess.run(shlex.split(command), cwd=tree, env=command_env,
                                    capture_output=True, encoding='utf-8', timeout=120)
            results.append({'command': command, 'exit_code': result.returncode,
                            'stdout': result.stdout, 'stderr': result.stderr})
        return results
    finally:
        removed = run(['git', '-C', workspace, 'worktree', 'remove', tree], workspace, env)
        assert removed.returncode == 0, removed.stdout + removed.stderr


def save_h1_evidence(name, payload):
    folder = os.environ.get('C0_FIXTURE_EVIDENCE_DIR')
    if folder:
        target = Path(folder)
        target.mkdir(parents=True, exist_ok=True)
        (target / f'{name}.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


@pytest.fixture
def candidate(tmp_path):
    workspace = tmp_path / 'candidate'
    workspace.mkdir()
    config = tmp_path / 'config'
    config.mkdir()
    for name in ('brief.md', 'contract.md'):
        shutil.copyfile(PLUGIN / 'evals/cases/c0-wordstat' / name, workspace / name)
    for name in ('mock_claude.py', 'c0_fixture.py'):
        shutil.copyfile(MOCKS / name, config / name)
    shutil.copyfile(PLUGIN / 'evals/adapters/codex/mock_codex.py', config / 'mock_codex.py')
    # Every child Python (including fixture tests and gates) has denied network.
    (config / 'sitecustomize.py').write_text(
        'import socket\n'
        'def denied(*args, **kwargs):\n    raise RuntimeError("test denies network")\n'
        'socket.create_connection = denied\nsocket.socket.connect = denied\n', encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if not any(
        word in k.upper() for word in ('API_KEY', 'OAUTH', 'AUTH_TOKEN', 'LANGFUSE', 'LITELLM',
                                       'GEEKY_MOCK_C0_SPLIT_TESTS', 'C0_FIXTURE_EVIDENCE_DIR'))}
    env.update(PATH=str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', ''),
        PYTHONPATH=str(config), PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        CLAUDE_PLUGIN_ROOT=str(PLUGIN), CLAUDE_CONFIG_DIR=str(config / 'claude'),
        CODEX_HOME=str(config / 'codex'), TMPDIR=str(tmp_path), MOCK_LATENCY_MS='0',
        GEEKY_DEADLINE_UTC=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)).isoformat(),
        GEEKY_CLOSEOUT_RESERVE_S='30', GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory',
        GIT_CONFIG_VALUE_0=str(workspace), GIT_AUTHOR_NAME='scripted mock',
        GIT_AUTHOR_EMAIL='mock@example.invalid', GIT_COMMITTER_NAME='scripted mock',
        GIT_COMMITTER_EMAIL='mock@example.invalid')
    assert run(['git', 'init', '-q'], workspace, env).returncode == 0
    assert run(['git', 'add', '.'], workspace, env).returncode == 0
    assert run(['git', 'commit', '-qm', 'docs: seed public case'], workspace, env).returncode == 0
    return workspace, config, env


@pytest.mark.parametrize('actor', ['claude', 'codex'])
def test_full_scripted_fixture_both_native_shapes(candidate, tmp_path, actor):
    workspace, config, env = candidate
    before = run(['git', 'rev-parse', 'HEAD'], workspace, env).stdout.strip()
    if actor == 'claude':
        argv = [sys.executable, config / 'mock_claude.py', '--plugin-dir', PLUGIN,
                '--mock-scenario', 'c0-full', '--mock-case', 'c0-wordstat',
                '-p', 'Execute docs/spec-001-feature/']
    else:
        argv = [sys.executable, config / 'mock_codex.py', 'exec', '--json', '--cd', workspace,
                '--mock-scenario', 'c0-full', '-c', 'hooks={PreToolUse=[]}',
                'Execute docs/spec-001-feature/']
    result = run(argv, workspace, env)
    (workspace / '.git/actor.stdout.jsonl').write_text(result.stdout, encoding='utf-8')
    (workspace / '.git/actor.stderr.log').write_text(result.stderr, encoding='utf-8')
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    report = json.loads((workspace / '.git/c0-full-summary.json').read_text())
    assert report['label'] == 'SCRIPTED MOCK' and report['model_calls'] == 0
    assert report['deadline_environment'] == {'GEEKY_DEADLINE_UTC': env['GEEKY_DEADLINE_UTC'],
                                             'GEEKY_CLOSEOUT_RESERVE_S': 30}
    assert [s['stage'] for s in report['stages']] == [
        'spec-research', 'geeky-plan', 'plan-review', 'geeky-implement', 'impl-review']
    assert report['tests_passed'] == 17 and len(set(report['commits'])) == 3
    assert report['phase_verdict'] == 'READY TO ADVANCE' and report['final_verdict'] == 'PASS'
    folder = workspace / report['planning_folder']
    assert json.loads((folder / '.heartbeat').read_text())['status'] == 'done'
    assert report['closeout'] == 'done' and (folder / 'run-summary.md').is_file()
    assert len(report['saved_domain_replies']) == 3
    for path in report['saved_domain_replies']:
        reply = (workspace / path).read_text()
        assert 'SCRIPTED MOCK' in reply and 'Verdict: PASS' in reply
        assert report['commits'][1] in reply and '<!-- reviewer-complete:' in reply
    assert (folder / 'review-impl.md').read_text().count('<!-- reviewer-complete:') == 3
    assert (folder / 'review-impl.md').read_text().endswith('Overall: PASS\n')
    assert (folder / 'review-phase-1.md').read_text().count('Phase 1: READY TO ADVANCE') == 1
    commands = json.loads((workspace / '.git/c0-full-commands.json').read_text())
    assert all(c['exit_code'] == 0 for c in commands)
    assert all(Path(c['argv'][0]).name.lower() in ('python.exe', 'python', 'git') for c in commands)
    for gate in ('validate-planning-folder', 'validate-task-schema', 'validate-kanban', 'check-dod', 'check-commit'):
        assert any(c['name'] == gate for c in commands)
    run_dir = capture_run_trace(tmp_path, workspace, config, actor, result.stdout)
    trace, start_call, done_call = h1_transition_calls(run_dir, actor, workspace)
    scorer = derived_scorer(run_dir, actor, workspace)
    kanban_gates = [c for c in trace.calls if c.name == 'PowerShell' and 'validate-kanban.py' in c.cmd]
    assert len(kanban_gates) >= 3 and all(not c.is_error and 'OK:' in c.text for c in kanban_gates)
    assert all(scorer.inprog[t].id == start_call.id and scorer.done_call[t].id == done_call.id
               for t in ('T1', 'T2'))
    final_head = run(['git', 'rev-parse', 'HEAD'], workspace, env).stdout.strip()
    h1_results = {}
    for task, filename in (('T1', 'T1-scaffold-package.md'), ('T2', 'T2-smoke-tests.md')):
        selected_sha, fallback, basis = scorer.rerun_commit(task)
        assert len(selected_sha) == 40 and not fallback
        assert selected_sha == report['commits'][1] and selected_sha != final_head
        assert 'Done move' in basis and 'no Done move' not in basis
        task_commands = validation_commands(folder / 'tasks' / filename, task, actor)
        result_rows = run_at_commit(workspace, selected_sha, task_commands, env, tmp_path,
                                    f'positive-{actor}-{task}')
        assert task_commands and all(r['exit_code'] == 0 for r in result_rows), result_rows
        h1_results[task] = {'selected_sha': selected_sha, 'fallback': fallback, 'basis': basis,
                            'commands': [{'command': r['command'], 'exit_code': r['exit_code'],
                                          'stdout_tail': r['stdout'].strip().splitlines()[-1:]}
                                         for r in result_rows]}
    commits = run(['git', 'rev-list', before + '..HEAD'], workspace, env).stdout.splitlines()
    assert len(commits) == 3
    files = run(['git', 'show', '--format=', '--name-only', report['commits'][1]], workspace, env).stdout
    assert 'wordstat/__main__.py' in files and 'tests/test_wordstat.py' in files
    assert run(['git', 'status', '--porcelain'], workspace, env).stdout == ''
    save_h1_evidence(f'fixture-h1-positive-{actor}', {
        'label': 'SCRIPTED MOCK', 'actor': actor, 'start_write': start_call.text,
        'start_call_id': start_call.id, 'start_path': start_call.inp['file_path'],
        'start_time_utc': start_call.ts.isoformat(), 'done_write': done_call.text,
        'done_call_id': done_call.id, 'done_path': done_call.inp['file_path'],
        'done_time_utc': done_call.ts.isoformat(), 'selected': h1_results,
        'functional_commit_sha': report['commits'][1],
        'final_head_sha': final_head, 'functional_commit_files': files.splitlines(),
        'required_tests_atomic_with_source': True, 'kanban_gate_results': [c.text for c in kanban_gates]})
    if actor == 'claude':
        summary = next(e for e in events if e.get('subtype') == 'mock_summary')
        assert summary['ok'] and summary['model_calls'] == 0
        assert events[-1]['total_cost_usd'] == 0 and events[-1]['modelUsage'] == {}
        assert '17 tests passed' in events[-1]['result'] and 'Commits:' in events[-1]['result']
        assert all(e['message']['usage']['output_tokens'] == 0 for e in events if e['type'] == 'assistant')
    else:
        summary = next(e for e in events if e.get('type') == 'mock_summary')
        assert summary['ok'] and summary['c0_full'] == report | {'completion_report': summary['c0_full']['completion_report']}
        assert events[-1]['type'] == 'turn.completed'
        rollout = next((config / 'codex/sessions').rglob('*.jsonl'))
        payloads = [json.loads(line)['payload'] for line in rollout.read_text().splitlines()]
        assert any(p.get('type') == 'function_call' for p in payloads)
        assert any(p.get('type') == 'task_complete' for p in payloads)
        final = next(p['message'] for p in payloads if p.get('type') == 'agent_message')
        assert 'SCRIPTED MOCK' in final and '17 tests passed' in final and 'Commits:' in final


def test_h1_does_not_substitute_final_head_when_required_tests_are_later(candidate, tmp_path):
    workspace, config, env = candidate
    env['GEEKY_MOCK_C0_SPLIT_TESTS'] = '1'
    result = run([sys.executable, config / 'mock_codex.py', 'exec', '--json', '--cd', workspace,
                  '--mock-scenario', 'c0-full', '-c', 'hooks={PreToolUse=[]}',
                  'Execute docs/spec-001-feature/'], workspace, env)
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr
    report = json.loads((workspace / '.git/c0-full-summary.json').read_text())
    assert report['tests_passed'] == 17 and len(report['commits']) == 4
    folder = workspace / report['planning_folder']
    run_dir = capture_run_trace(tmp_path, workspace, config, 'codex', result.stdout)
    trace, start_call, done_call = h1_transition_calls(run_dir, 'codex', workspace)
    scorer = derived_scorer(run_dir, 'codex', workspace)
    assert all(scorer.inprog[t].id == start_call.id and scorer.done_call[t].id == done_call.id
               for t in ('T1', 'T2'))
    kanban_gates = [c for c in trace.calls if c.name == 'PowerShell' and 'validate-kanban.py' in c.cmd]
    assert len(kanban_gates) >= 3 and all(not c.is_error and 'OK:' in c.text for c in kanban_gates)

    selected_sha, fallback, basis = scorer.rerun_commit('T2')
    source_files = run(['git', 'show', '--format=', '--name-only', report['commits'][1]], workspace, env).stdout
    late_test_files = run(['git', 'show', '--format=', '--name-only', report['commits'][2]], workspace, env).stdout
    assert selected_sha == report['commits'][1] and len(selected_sha) == 40 and not fallback
    assert 'Done move' in basis and 'no Done move' not in basis
    assert 'wordstat/__main__.py' in source_files and 'tests/test_wordstat.py' not in source_files
    assert 'tests/test_wordstat.py' in late_test_files

    task_file = folder / 'tasks/T2-smoke-tests.md'
    commands = validation_commands(task_file, 'T2', 'codex')
    selected_results = run_at_commit(workspace, selected_sha, commands, env, tmp_path, 'negative-selected')
    final_head = run(['git', 'rev-parse', 'HEAD'], workspace, env).stdout.strip()
    assert selected_sha != final_head
    final_results = []
    final_env = {**env, 'PYTHONPYCACHEPREFIX': str(tmp_path / 'pycache-negative-final')}
    for command in commands:
        check = subprocess.run(shlex.split(command), cwd=workspace, env=final_env,
                               capture_output=True, encoding='utf-8', timeout=120)
        final_results.append({'command': command, 'exit_code': check.returncode,
                              'stdout': check.stdout, 'stderr': check.stderr})
    required_test_results = [row for row in selected_results if 'pytest' in row['command']]
    assert required_test_results and all(row['exit_code'] != 0 for row in required_test_results), selected_results
    assert all(row['exit_code'] == 0 for row in final_results), final_results
    save_h1_evidence('fixture-h1-negative-codex', {
        'label': 'SCRIPTED MOCK', 'actor': 'codex', 'start_write': start_call.text,
        'start_call_id': start_call.id, 'start_path': start_call.inp['file_path'],
        'start_time_utc': start_call.ts.isoformat(), 'done_write': done_call.text,
        'done_call_id': done_call.id, 'done_path': done_call.inp['file_path'],
        'done_time_utc': done_call.ts.isoformat(), 'selected_sha': selected_sha,
        'fallback': fallback, 'selected_basis': basis,
        'source_only_commit_sha': report['commits'][1], 'later_test_commit_sha': report['commits'][2],
        'final_head_sha': final_head,
        'selected_validation': [{'command': row['command'], 'exit_code': row['exit_code'],
                                'stdout_tail': row['stdout'].strip().splitlines()[-1:]}
                               for row in selected_results],
        'final_head_validation': [{'command': row['command'], 'exit_code': row['exit_code'],
                                   'stdout_tail': row['stdout'].strip().splitlines()[-1:]}
                                  for row in final_results],
        'source_commit_files': source_files.splitlines(), 'later_test_commit_files': late_test_files.splitlines(),
        'kanban_gate_results': [c.text for c in kanban_gates]})


@pytest.mark.parametrize('deadline,reserve', [('not-utc', '30'), ('2026-10-26T00:00:00', '30'),
    ('2026-10-26T00:00:00Z', '-1')])
def test_invalid_deadline_environment_fails_before_writes(candidate, deadline, reserve):
    workspace, config, env = candidate
    env.update(GEEKY_DEADLINE_UTC=deadline, GEEKY_CLOSEOUT_RESERVE_S=reserve)
    result = run([sys.executable, config / 'mock_codex.py', '--cd', workspace,
                  '--mock-scenario', 'c0-full'], workspace, env)
    assert result.returncode == 1
    assert not (workspace / 'docs').exists() and not (workspace / 'wordstat').exists()


def test_runner_mock_dispatch_is_explicit():
    claude = (RUNNERS / 'run-baseline.ps1').read_text(encoding='utf-8-sig')
    codex = (RUNNERS / 'run-codex-baseline.ps1').read_text(encoding='utf-8-sig')
    for script in (claude, codex):
        assert "if ($MockAgent -and $MockScenario -eq 'c0-full') { $hostArgs += '--deny-net' }" in script
        assert "c0-full requires c0-wordstat and -NoTelemetry" in script
        assert "evals/mock-agent/c0_fixture.py" in script
    assert "if (-not $MockAgent -and -not $env:CLAUDE_CODE_OAUTH_TOKEN)" in claude


def test_old_claude_happy_and_gate_failure_remain_explicit(candidate):
    workspace, config, env = candidate
    result = run([sys.executable, config / 'mock_claude.py', '--plugin-dir', PLUGIN,
                  '--mock-scenario', 'happy,gate-fail', '--mock-case', 'c0-wordstat'], workspace, env)
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    summary = next(e for e in events if e.get('subtype') == 'mock_summary')
    assert summary['ok'] and 'c0_full' not in summary
    assert any(c['name'] == 'happy.pytest' and c['status'] == 'pass' for c in summary['checks'])
    assert any(c['name'] == 'gate-fail.stopped' and c['status'] == 'pass' for c in summary['checks'])
    assert not (workspace / '.git/c0-full-summary.json').exists()
    assert 'mock-agent stub' in (workspace / 'wordstat/__main__.py').read_text()


def test_codex_crash_and_bounded_slow(candidate):
    workspace, config, env = candidate
    env['MOCK_SLOW_SECONDS'] = '0.01'
    result = run([sys.executable, config / 'mock_codex.py', '--cd', workspace,
                  '--mock-scenario', 'slow'], workspace, env)
    assert result.returncode == 0 and 'turn.completed' in result.stdout
    result = run([sys.executable, config / 'mock_codex.py', '--cd', workspace,
                  '--mock-scenario', 'crash'], workspace, env)
    assert result.returncode == 3 and 'simulated crash' in result.stderr
    assert 'turn.completed' not in result.stdout


@pytest.mark.parametrize('actor', ['claude', 'codex'])
def test_full_fixture_rejects_telemetry_hooks(candidate, actor):
    workspace, config, env = candidate
    if actor == 'claude':
        settings = config / 'settings.json'
        settings.write_text(json.dumps({'hooks': {'Stop': [{'hooks': []}]}}))
        args = [config / 'mock_claude.py', '--settings', settings]
    else:
        args = [config / 'mock_codex.py', '--cd', workspace, '-c', 'hooks={Stop=[]}']
        # Nonempty hook arrays are exactly what the profile emits for telemetry.
        args[-1] = 'hooks={Stop=[{hooks=[]}]}'
    result = run([sys.executable, *args, '--mock-scenario', 'c0-full'], workspace, env)
    assert result.returncode != 0 and 'c0-full must run alone' in result.stderr
    assert not (workspace / 'docs').exists()
