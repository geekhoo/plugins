"""Model-free Codex CLI stand-in for MXC checks, not proof of native discovery.

Accepts exec --json --cd ... -c key=TOML plus --mock-scenario happy (default)
or comma-separated env,skills,guard,pwsh,python,git,mcp. --mock-report stores a
summary. Repeat --mock-forbidden-path to verify denied host/oracle access.
Every check performs real I/O; no workflow, review or solution is simulated.
The rollout has Codex's turn shape (task_started, user_message, one function
call per check, task_complete). When the -c overrides declare a Stop hook (the
Langfuse tracer), a final telemetry check runs it on that rollout as Codex does
and requires the hook's delivery sidecar to record the turn.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import queue
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import tomllib
import uuid

CHECKS = ('env', 'skills', 'guard', 'pwsh', 'python', 'gates', 'git', 'mcp')
ZERO_USAGE = {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0}


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('-c', '--config', action='append', default=[])
    p.add_argument('-C', '--cd', type=Path, default=Path.cwd())
    p.add_argument('--mock-scenario', default='happy')
    p.add_argument('--mock-report', type=Path)
    p.add_argument('--mock-forbidden-path', action='append', type=Path, default=[])
    # These take values; ignoring them individually would misread their values.
    p.add_argument('--model', '-m')
    p.add_argument('--sandbox')
    a, rest = p.parse_known_args(argv)
    a.prompt = next((x for x in reversed(rest) if not x.startswith('-')), '')
    config = {}
    for raw in a.config:
        parsed = tomllib.loads(raw)
        def merge(dst, src):
            for k, v in src.items():
                if isinstance(v, dict) and isinstance(dst.get(k), dict):
                    merge(dst[k], v)
                else:
                    dst[k] = v
        merge(config, parsed)
    a.config = config
    a.scenarios = list(CHECKS) if a.mock_scenario in ('happy', 'all') else a.mock_scenario.split(',')
    if any(s not in (*CHECKS, 'fail', 'c0-full', 'slow', 'crash') for s in a.scenarios):
        p.error('unknown mock scenario')
    if 'c0-full' in a.scenarios and (a.scenarios != ['c0-full'] or (config.get('hooks') or {}).get('Stop')):
        p.error('c0-full must run alone with no telemetry/Stop hooks')
    return a


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


class Trace:
    def __init__(self, codex_home, cwd, model='mock', prompt=''):
        self.sid = str(uuid.uuid4())
        self.turn_id = 'turn-' + uuid.uuid4().hex[:12]
        date = dt.datetime.now(dt.timezone.utc)
        folder = codex_home / 'sessions' / date.strftime('%Y/%m/%d')
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f'rollout-{date.strftime("%Y-%m-%dT%H-%M-%S")}-{self.sid}.jsonl'
        self.file = self.path.open('x', encoding='utf-8')
        self.record('session_meta', {'id': self.sid, 'timestamp': now(), 'cwd': str(cwd),
            'originator': 'mock-codex', 'cli_version': '0.0.0-mock', 'model_provider': 'mock'})
        self.emit({'type': 'thread.started', 'thread_id': self.sid})
        self.emit({'type': 'turn.started'})
        self.record('event_msg', {'type': 'task_started', 'turn_id': self.turn_id})
        self.record('turn_context', {'model': model, 'effort': 'mock'})
        self.record('event_msg', {'type': 'user_message', 'message': prompt or '(no prompt)'})

    def tool_call(self, name, result):
        call_id = 'call-' + uuid.uuid4().hex[:12]
        self.record('response_item', {'type': 'function_call', 'name': 'mock_check', 'call_id': call_id,
                                      'arguments': json.dumps({'check': name})})
        self.record('response_item', {'type': 'function_call_output', 'call_id': call_id,
                                      'output': json.dumps(result)})

    def file_change(self, path, content, output, started_at_ms, added):
        self.record('event_msg', {'type': 'item_completed', 'started_at_ms': started_at_ms, 'item': {
            'id': 'file-' + uuid.uuid4().hex[:12], 'type': 'FileChange', 'status': 'completed',
            'exit_code': 0, 'stdout': output,
            'changes': {str(path): {'type': 'add' if added else 'update', 'content': content}}}})

    def command_execution(self, argv, stdout, stderr, exit_code, started_at_ms):
        command = subprocess.list2cmdline([str(x) for x in argv]) if os.name == 'nt' else shlex.join([str(x) for x in argv])
        self.record('event_msg', {'type': 'item_completed', 'started_at_ms': started_at_ms, 'item': {
            'id': 'command-' + uuid.uuid4().hex[:12], 'type': 'CommandExecution',
            'status': 'completed' if exit_code == 0 else 'failed', 'exit_code': exit_code,
            'command': command, 'stdout': stdout, 'stderr': stderr}})

    def skill_read(self, skill, args, plugin):
        call_id = 'call-' + uuid.uuid4().hex[:12]
        self.record('response_item', {'type': 'function_call', 'name': 'Skill', 'call_id': call_id,
                                      'arguments': json.dumps({'skill': skill, 'args': args})})
        path = plugin / 'skills' / skill / 'SKILL.md'
        content = path.read_text(encoding='utf-8')
        result = f'SCRIPTED MOCK read {path} ({len(content)} characters)'
        self.record('response_item', {'type': 'function_call_output', 'call_id': call_id, 'output': result})
        return result

    def complete_turn(self, text):
        self.record('response_item', {'type': 'reasoning', 'summary': [{'type': 'summary_text',
                                      'text': 'Mock reasoning summary: report the check results.'}]})
        self.record('response_item', {'type': 'message', 'role': 'assistant',
                                      'content': [{'type': 'output_text', 'text': text}]})
        self.record('event_msg', {'type': 'agent_message', 'message': text})
        self.record('event_msg', {'type': 'token_count', 'info': {
            'total_token_usage': {**ZERO_USAGE, 'reasoning_output_tokens': 0, 'total_tokens': 0},
            'last_token_usage': {**ZERO_USAGE, 'reasoning_output_tokens': 0, 'total_tokens': 0}}})
        self.record('event_msg', {'type': 'task_complete', 'turn_id': self.turn_id})

    def record(self, kind, payload):
        self.file.write(json.dumps({'timestamp': now(), 'type': kind, 'payload': payload}) + '\n')
        self.file.flush()

    def emit(self, event):
        print(json.dumps(event), flush=True)
        self.record('event_msg', event)

    def finish(self, checks):
        failed = any(not c['passed'] for c in checks)
        summary = {'type': 'mock_summary', 'checks': checks, 'passed': not failed, 'ok': not failed,
                   'model_calls': 0, 'tokens': 0, 'thread_id': self.sid}
        if hasattr(self, 'c0_full'):
            summary.update(c0_full=self.c0_full, label='SCRIPTED MOCK')
        self.emit(summary)
        self.record('event_msg', {'type': 'token_count', 'info': {'total_token_usage': {
            **ZERO_USAGE, 'reasoning_output_tokens': 0, 'total_tokens': 0},
            'last_token_usage': {**ZERO_USAGE, 'reasoning_output_tokens': 0, 'total_tokens': 0}}})
        if failed:
            self.emit({'type': 'turn.failed', 'error': {'message': 'Mock checks failed'}})
        else:
            self.emit({'type': 'turn.completed', 'usage': dict(ZERO_USAGE)})
        self.file.close()
        return summary


def run(argv, cwd=None, stdin=None, timeout=90):
    return subprocess.run(argv, cwd=cwd, input=stdin, text=True, encoding='utf-8', capture_output=True,
                          timeout=timeout, check=False)


def require(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def request_response(messages, request_id, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            raw = messages.get(timeout=min(.5, max(.01, deadline - time.monotonic())))
        except queue.Empty:
            continue
        try:
            value = json.loads(raw)
        except (ValueError, TypeError):
            continue
        if value.get('id') == request_id:
            require('result' in value and 'error' not in value, 'MCP JSON-RPC error')
            return value['result']
    raise RuntimeError(f'MCP response {request_id} timed out')


def check_mcp(config):
    servers = config.get('mcp_servers', {})
    require('geeky' in servers, 'geeky MCP registration missing')
    cfg = servers['geeky']
    process = subprocess.Popen([cfg['command'], *cfg.get('args', [])], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
        env={**os.environ, **cfg.get('env', {})})
    messages = queue.Queue()
    threading.Thread(target=lambda: [messages.put(line) for line in process.stdout], daemon=True).start()
    # Drain stderr without logging environment, credentials or server internals.
    threading.Thread(target=lambda: [None for _ in process.stderr], daemon=True).start()
    def send(method, params=None, mid=None):
        payload = {'jsonrpc': '2.0', 'method': method}
        if mid is not None:
            payload['id'] = mid
        if params is not None:
            payload['params'] = params
        process.stdin.write(json.dumps(payload) + '\n')
        process.stdin.flush()
    try:
        send('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
            'clientInfo': {'name': 'mock-codex', 'version': '0.0.0'}}, 1)
        request_response(messages, 1)
        send('notifications/initialized')
        send('tools/list', mid=2)
        listing = request_response(messages, 2)
        require(any(t['name'] == 'geeky_check_commit' for t in listing.get('tools', [])), 'MCP gate missing')
        send('tools/call', {'name': 'geeky_check_commit', 'arguments': {
            'params': {'message': 'feat(mock): validate scratch\n\nTasks: T1'}}}, 3)
        result = request_response(messages, 3)
        require(not result.get('isError'), 'MCP call returned isError')
        text = '\n'.join(c.get('text', '') for c in result.get('content', []))
        require(bool(text), 'MCP tools/call returned no content')
        gate = result.get('structuredContent') or json.loads(text)
        require(gate.get('ok') is True and gate.get('exit_code') == 0, 'MCP commit gate did not pass')
        return 'initialize, tools/list and geeky_check_commit tools/call responded'
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def versioned_pythons():
    """Each python3.X name the PATH resolves (first hit wins), as a contestant would call it."""
    names = set()
    for directory in os.environ.get('PATH', '').split(os.pathsep):
        if not directory or not os.path.isdir(directory):
            continue
        try:
            names.update(f.name for f in Path(directory).iterdir()
                         if re.fullmatch(r'python3\.\d+', f.name))
        except OSError:
            # Host PATH entries can exist but be unreadable inside MXC.
            continue
    return sorted(n for n in names if shutil.which(n))


def perform(name, a, scratch):
    if name == 'fail':
        raise RuntimeError('Deliberate negative-control scenario')
    home = Path(os.environ['HOME'])
    plugin = Path(os.environ['CLAUDE_PLUGIN_ROOT'])
    if name == 'env':
        require(home.resolve() != Path(os.environ['CODEX_HOME']).resolve(), 'HOME must differ from CODEX_HOME')
        require(os.environ.get('PYTHONDONTWRITEBYTECODE') == '1', 'bytecode suppression missing')
        require(Path(os.environ['TMPDIR']).is_dir(), 'TMPDIR unavailable')
        (scratch / 'write-check').write_text('ok', encoding='utf-8')
        require(not (plugin / 'evals').exists(), 'Export exposes evals')
        for path in a.mock_forbidden_path:
            try:
                list(path.iterdir()) if path.is_dir() else path.read_bytes()
            except (OSError, PermissionError):
                continue
            raise RuntimeError(f'Forbidden path is readable: {path}')
        return 'isolated homes, writable TMPDIR, no evals export; explicit denied paths checked'
    if name == 'skills':
        source = {p.relative_to(plugin / 'skills'): p.read_bytes() for p in (plugin / 'skills').rglob('*') if p.is_file()}
        target = home / '.agents/skills'
        require(source and all((target / rel).read_bytes() == data for rel, data in source.items()), 'Skill tree mismatch')
        roles = {k: v for k, v in a.config.get('agents', {}).items() if isinstance(v, dict) and 'config_file' in v}
        # One role per plugin agent, plus the built-in general-purpose role the skills name.
        expected = {p.stem for p in (plugin / 'agents').glob('*.md')} | {'general-purpose'}
        extra = set(roles) - expected - {'code-architect-reviewer'}   # that one only with --reviewer-reasoning
        require(expected <= set(roles) and not extra, f'Agent registration mismatch: missing {sorted(expected - set(roles))}, extra {sorted(extra)}')
        for role in roles.values():
            data = tomllib.loads(Path(role['config_file']).read_text(encoding='utf-8-sig'))
            require(bool(data.get('developer_instructions')), 'Role instructions missing')
        return f'{len(source)} skill files and {len(roles)} registered roles readable (not native discovery proof)'
    if name == 'guard':
        hooks = a.config['hooks']['PreToolUse']
        command = next(h['command'] for group in hooks for h in group['hooks'] if 'apply_patch' in group['matcher'])
        for leaf, warning in [('implementation-plan.md', True), ('tasks/T1-a.notes.md', False)]:
            payload = {'tool_name': 'apply_patch', 'cwd': str(a.cd), 'tool_input': {
                'command': f'*** Begin Patch\n*** Update File: docs/spec-001-feature/{leaf}\n@@\n-old\n+new\n*** End Patch'}}
            # Windows CreateProcess takes the command line as is; POSIX needs it split.
            result = run(command if os.name == 'nt' else shlex.split(command), stdin=json.dumps(payload))
            require(result.returncode == 0, 'Guard bridge failed')
            content = json.loads(result.stdout)['hookSpecificOutput']['additionalContext'] if result.stdout.strip() else ''
            require(bool(content) == warning, f'Guard warning mismatch for {leaf}')
        return 'frozen patch warns, notes patch remains mutable; bridge invoked directly'
    if name == 'pwsh':
        exe = shutil.which('pwsh') or r'C:\Program Files\PowerShell\7\pwsh.exe'
        result = run([exe, '-NoProfile', '-Command', 'Write-Output mock-pwsh; exit 7'])
        require(result.returncode == 7 and 'mock-pwsh' in result.stdout, 'PowerShell exit/output mismatch')
        require(not result.stderr.strip(), 'PowerShell startup emitted stderr')
        return 'PowerShell output and exit 7 preserved'
    if name == 'python':
        exe = shutil.which('python')
        require(bool(exe), 'Python missing from PATH')
        (scratch / 'test_runtime.py').write_text('def test_runtime(tmp_path):\n    p=tmp_path/"ok"\n    p.write_text("ok", encoding="utf-8")\n    assert p.read_text(encoding="utf-8")=="ok"\n', encoding='utf-8')
        result = run([exe, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', str(scratch / 'test_runtime.py')], cwd=scratch)
        require(result.returncode == 0 and '1 passed' in result.stdout, 'Real pytest tmp_path check failed: ' + result.stdout[-500:] + result.stderr[-500:])
        missing = [v for v in versioned_pythons() if run([v, '-m', 'pytest', '--version']).returncode]
        require(not missing, 'pytest missing for ' + ', '.join(missing) + ' (run scripts/install-agent-pythons.ps1)')
        return 'PATH Python executes real pytest with writable tmp_path; every python3.X on PATH has pytest'
    if name == 'gates':
        # The skills call the plugin's gates as python scripts or, in geeky-implement, through pwsh.
        pwsh = shutil.which('pwsh') or r'C:\Program Files\PowerShell\7\pwsh.exe'
        good, bad = scratch / 'msg-good', scratch / 'msg-bad'
        good.write_text('feat(mock): add stub\n\nTasks: T1\n', encoding='utf-8')
        bad.write_text('feat(mock): add stub\n', encoding='utf-8')
        forms = {'py': [shutil.which('python') or sys.executable],
                 'ps1': [pwsh, '-NoProfile', '-NonInteractive', '-File']}
        for form, prefix in forms.items():
            script = str(plugin / 'scripts' / f'check-commit.{form}')
            for msg, want in ((good, 0), (bad, 1)):
                result = run(prefix + [script, str(msg)])
                require(result.returncode == want, f'check-commit.{form} on {msg.name}: exit {result.returncode}, expected {want}: '
                        + (result.stdout + result.stderr)[-300:])
            result = run(prefix + [str(plugin / 'scripts' / f'validate-kanban.{form}'), str(scratch / 'no-such-folder')])
            require(result.returncode != 0 and 'Traceback' not in result.stderr, f'validate-kanban.{form} on a missing folder: exit '
                    f'{result.returncode}: ' + result.stderr[-300:])
        return 'check-commit accepts/rejects and validate-kanban fails cleanly, as .py and through pwsh'
    if name == 'git':
        result = run(['git', '-C', str(a.cd), 'status', '--porcelain'])
        require(result.returncode == 0, 'Workspace safe.directory check failed')
        repo = scratch / 'git-fixture'
        repo.mkdir()
        for args in [('init', '-q'), ('add', '.'), ('commit', '-q', '-m', 'test(mock): scratch fixture')]:
            if args[0] == 'add':
                (repo / 'fixture.txt').write_text('disposable mock fixture\n', encoding='utf-8')
            result = run(['git', '-C', str(repo), *args])
            require(result.returncode == 0, 'Scratch git ' + args[0] + ' failed: ' + result.stderr[-300:])
        result = run(['git', '-C', str(repo), 'log', '-1', '--format=%an <%ae>|%cn <%ce>'])
        identity = 'geeky-eval-agent <agent@geeky-eval.local>'
        require(result.stdout.strip() == identity + '|' + identity, 'Scratch author/committer identity mismatch')
        return 'workspace trusted; disposable scratch commit has neutral identity'
    if name == 'mcp':
        return check_mcp(a.config)
    raise ValueError(name)


def stop_hooks(config):
    return [h for group in (config.get('hooks') or {}).get('Stop') or []
            for h in group.get('hooks') or [] if h.get('type') == 'command']


def check_telemetry(a, trace):
    """Run each Stop hook on the completed turn; the Langfuse tracer marks a delivered turn in its sidecar."""
    require(a.config.get('model_reasoning_summary') == 'detailed', 'model_reasoning_summary is not detailed')
    payload = json.dumps({'session_id': trace.sid, 'transcript_path': str(trace.path), 'turn_id': trace.turn_id,
                          'hook_event_name': 'Stop', 'cwd': str(a.cd), 'stop_hook_active': False})
    for hook in stop_hooks(a.config):
        # Fail loudly here: the tracer otherwise fails open and would hide an upload error.
        # The generated Windows hook is a CreateProcess command line. Routing it
        # through cmd.exe adds a shell the sandbox does not grant.
        result = subprocess.run(hook['command'], shell=os.name != 'nt', input=payload, text=True, encoding='utf-8',
                                capture_output=True, timeout=hook.get('timeout', 600), check=False,
                                env={**os.environ, 'LANGFUSE_CODEX_FAIL_ON_ERROR': 'true'})
        require(result.returncode == 0, f'Stop hook exit {result.returncode}: {(result.stdout + result.stderr)[-800:]}')
    sidecar = Path(str(trace.path) + '.langfuse')
    delivered = sidecar.read_text(encoding='utf-8').split() if sidecar.exists() else []
    require(trace.turn_id in delivered, f'turn {trace.turn_id} not recorded in {sidecar.name}')
    return f'Stop hook delivered turn {trace.turn_id} of thread {trace.sid}'


def main(argv=None):
    a = parse_args(sys.argv[1:] if argv is None else argv)
    os.chdir(a.cd)
    trace = Trace(Path(os.environ['CODEX_HOME']), a.cd, a.model or 'mock', a.prompt)
    checks = []
    scratch = Path(os.environ['TMPDIR']) / ('mock-codex-' + uuid.uuid4().hex)
    scratch.mkdir()  # Avoid Python's Windows user-only mkdtemp ACL inside MXC.
    for name in a.scenarios:
        if name == 'slow':
            time.sleep(float(os.environ.get('MOCK_SLOW_SECONDS', '600')))
            continue
        if name == 'crash':
            print('SCRIPTED MOCK simulated crash', file=sys.stderr, flush=True)
            os._exit(3)
        try:
            if name == 'c0-full':
                helper_dir = Path(__file__).resolve().parents[2] / 'mock-agent'
                if helper_dir.is_dir():
                    sys.path.insert(0, str(helper_dir))
                from c0_fixture import execute

                def report(stage, item):
                    if 'skill' in item:
                        trace.skill_read(item['skill'], item['args'], Path(os.environ['CLAUDE_PLUGIN_ROOT']))
                    elif 'argv' in item:
                        trace.command_execution(item['argv'], item['stdout'], item['stderr'],
                                                item['exit_code'], item['started_at_ms'])
                    else:
                        trace.tool_call('SCRIPTED MOCK ' + stage, item)
                    trace.emit({'type': 'mock_stage', 'label': 'SCRIPTED MOCK', 'stage': stage, **item})

                def write_kanban(path, content):
                    started_at_ms = int(time.time() * 1000)
                    added = not path.exists()
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(content, encoding='utf-8', newline='\n')
                    except OSError as exc:
                        trace.record('event_msg', {'type': 'item_completed', 'started_at_ms': started_at_ms, 'item': {
                            'id': 'file-' + uuid.uuid4().hex[:12], 'type': 'FileChange', 'status': 'failed',
                            'exit_code': 1, 'stdout': f'{type(exc).__name__}: {exc}',
                            'changes': {str(path): {'type': 'add' if added else 'update', 'content': content}}}})
                        return False
                    trace.file_change(path, content, f'File written successfully at: {path}', started_at_ms, added)
                    return True

                trace.c0_full = execute(a.cd, Path(os.environ['CLAUDE_PLUGIN_ROOT']), a.prompt, report, write_kanban)
                detail = trace.c0_full['completion_report']
            else:
                detail = perform(name, a, scratch)
            result = {'name': name, 'passed': True, 'detail': detail}
        except Exception as exc:
            result = {'name': name, 'passed': False, 'detail': f'{type(exc).__name__}: {exc}'}
        checks.append(result)
        trace.tool_call(name, result)
        trace.emit({'type': 'mock_check', **result})
        trace.emit({'type': 'item.completed', 'item': {'id': 'mock-' + name,
            'type': 'agent_message', 'text': f"Mock {name}: {'PASS' if result['passed'] else 'FAIL'}"}})
    trace.complete_turn(trace.c0_full['completion_report'] if hasattr(trace, 'c0_full') else
        'Mock checks: ' + ', '.join(f"{c['name']}={'PASS' if c['passed'] else 'FAIL'}" for c in checks))
    if stop_hooks(a.config):
        try:
            result = {'name': 'telemetry', 'passed': True, 'detail': check_telemetry(a, trace)}
        except Exception as exc:
            result = {'name': 'telemetry', 'passed': False, 'detail': f'{type(exc).__name__}: {exc}'}
        checks.append(result)
        trace.emit({'type': 'mock_check', **result})
    summary = trace.finish(checks)
    summary['scratch'] = str(scratch)
    if a.mock_report:
        a.mock_report.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
