"""Model-free Codex CLI stand-in for MXC checks, not proof of native discovery.

Accepts exec --json --cd ... -c key=TOML plus --mock-scenario happy (default)
or comma-separated env,skills,guard,pwsh,python,git,mcp. --mock-report stores a
summary. Repeat --mock-forbidden-path to verify denied host/oracle access.
Every check performs real I/O; no workflow, review or solution is simulated.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import tomllib
import uuid

CHECKS = ('env', 'skills', 'guard', 'pwsh', 'python', 'git', 'mcp')
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
    a, _ = p.parse_known_args(argv)
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
    if any(s not in (*CHECKS, 'fail') for s in a.scenarios):
        p.error('unknown mock scenario')
    return a


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


class Trace:
    def __init__(self, codex_home, cwd):
        self.sid = str(uuid.uuid4())
        date = dt.datetime.now(dt.timezone.utc)
        folder = codex_home / 'sessions' / date.strftime('%Y/%m/%d')
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f'rollout-{date.strftime("%Y-%m-%dT%H-%M-%S")}-{self.sid}.jsonl'
        self.file = self.path.open('x', encoding='utf-8')
        self.record('session_meta', {'id': self.sid, 'timestamp': now(), 'cwd': str(cwd),
            'originator': 'mock-codex', 'cli_version': '0.0.0-mock', 'model_provider': 'mock'})
        self.emit({'type': 'thread.started', 'thread_id': self.sid})
        self.emit({'type': 'turn.started'})

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
        require(len(roles) == len(list((plugin / 'agents').glob('*.md'))), 'Agent registration mismatch')
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
            result = run(command, stdin=json.dumps(payload))
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
        return 'PATH Python executes real pytest with writable tmp_path'
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


def main(argv=None):
    a = parse_args(sys.argv[1:] if argv is None else argv)
    os.chdir(a.cd)
    trace = Trace(Path(os.environ['CODEX_HOME']), a.cd)
    checks = []
    scratch = Path(os.environ['TMPDIR']) / ('mock-codex-' + uuid.uuid4().hex)
    scratch.mkdir()  # Avoid Python's Windows user-only mkdtemp ACL inside MXC.
    for name in a.scenarios:
        try:
            detail = perform(name, a, scratch)
            result = {'name': name, 'passed': True, 'detail': detail}
        except Exception as exc:
            result = {'name': name, 'passed': False, 'detail': f'{type(exc).__name__}: {exc}'}
        checks.append(result)
        trace.emit({'type': 'mock_check', **result})
        trace.emit({'type': 'item.completed', 'item': {'id': 'mock-' + name,
            'type': 'agent_message', 'text': f"Mock {name}: {'PASS' if result['passed'] else 'FAIL'}"}})
    summary = trace.finish(checks)
    summary['scratch'] = str(scratch)
    if a.mock_report:
        a.mock_report.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
